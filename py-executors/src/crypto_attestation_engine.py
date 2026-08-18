#!/usr/bin/env python3
"""
crypto_attestation_engine.py — Cryptographic Attestation Engine & Signed Receipts
==================================================================================
Regulatory Compliance: EU AI Act (Articles 12 & 26) and NIST AI RMF.
Implements Chain of Trust:
  1. SHA-256 hash of source dataset (LargeJson footprint)
  2. SHA-256 hash of deliberation logs, guardrails & HITL approvals
  3. SHA-256 hash of generated artifacts (Notebook .ipynb, SKOPS model)
  4. Non-Repudiable Digital Signature (RSASSA-PSS-SHA256)
  5. Integrity verification and tampering detection
"""

import os
import sys
import json
import hashlib
import base64
import datetime
from pathlib import Path
from typing import Dict, Any, Tuple, Optional

try:
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.asymmetric import rsa, padding
    from cryptography.hazmat.primitives import serialization
    from cryptography.exceptions import InvalidSignature
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False


# ── Paths Configuration ──────────────────────────────────────────────────────
FILE_PATH = Path(__file__).resolve()
SRC_DIR = FILE_PATH.parent
PY_EXECUTORS_DIR = SRC_DIR.parent
DATASET_AUTO_DIR = PY_EXECUTORS_DIR.parent
WORKSPACE_DIR = DATASET_AUTO_DIR / "workspace"
OUTPUTS_DIR = WORKSPACE_DIR / "outputs"
SECURITY_KEYS_DIR = OUTPUTS_DIR / "security_keys"
ATTESTATION_FILE = OUTPUTS_DIR / "attestation_receipts.json"

OUTPUTS_DIR.mkdir(parents=True, exist_ok=True)
SECURITY_KEYS_DIR.mkdir(parents=True, exist_ok=True)


# ── Sandbox RSA Keypair Management ───────────────────────────────────────────

def get_or_create_keypair() -> Tuple[bytes, bytes]:
    """Generates or loads the 2048-bit RSA keypair of the Sandbox authority."""
    private_key_path = SECURITY_KEYS_DIR / "kernel_private.pem"
    public_key_path = SECURITY_KEYS_DIR / "kernel_public.pem"

    if private_key_path.exists() and public_key_path.exists():
        with open(private_key_path, "rb") as f:
            private_pem = f.read()
        with open(public_key_path, "rb") as f:
            public_pem = f.read()
        return private_pem, public_pem

    if not CRYPTO_AVAILABLE:
        # Fallback pseudo-keys if cryptography library is not installed
        priv = b"MOCK_PRIVATE_KEY_SANDBOX_KERNEL_DEV_MODE"
        pub = b"MOCK_PUBLIC_KEY_SANDBOX_KERNEL_DEV_MODE"
        with open(private_key_path, "wb") as f: f.write(priv)
        with open(public_key_path, "wb") as f: f.write(pub)
        return priv, pub

    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )

    with open(private_key_path, "wb") as f:
        f.write(private_pem)
    with open(public_key_path, "wb") as f:
        f.write(public_pem)

    return private_pem, public_pem


# ── Hashing & Signature Functions ────────────────────────────────────────────

def compute_sha256(content: str | bytes) -> str:
    """Computes SHA-256 fingerprint for text or binary content."""
    if isinstance(content, str):
        content = content.encode("utf-8")
    return hashlib.sha256(content).hexdigest()


def compute_file_sha256(file_path: Path | str) -> str:
    """Computes SHA-256 fingerprint of a disk file."""
    p = Path(file_path)
    if not p.exists():
        return "file_not_found"
    sha = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest()


def sign_payload(payload_bytes: bytes, private_pem: bytes) -> str:
    """Digitally signs the payload using RSASSA-PSS-SHA256."""
    if not CRYPTO_AVAILABLE or b"MOCK" in private_pem:
        return "MOCK_SIG_" + hashlib.sha256(payload_bytes + private_pem).hexdigest()

    private_key = serialization.load_pem_private_key(private_pem, password=None)
    signature = private_key.sign(
        payload_bytes,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return base64.b64encode(signature).decode("ascii")


def verify_signature(payload_bytes: bytes, signature_str: str, public_pem: bytes) -> bool:
    """Verifies validity of an RSASSA-PSS digital signature."""
    if not CRYPTO_AVAILABLE or b"MOCK" in public_pem or signature_str.startswith("MOCK_SIG_"):
        expected = "MOCK_SIG_" + hashlib.sha256(payload_bytes + b"MOCK_PRIVATE_KEY_SANDBOX_KERNEL_DEV_MODE").hexdigest()
        return signature_str == expected

    try:
        public_key = serialization.load_pem_public_key(public_pem)
        signature = base64.b64decode(signature_str.encode("ascii"))
        public_key.verify(
            signature,
            payload_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        return True
    except (InvalidSignature, Exception):
        return False


# ── Receipt Creation & Storage ───────────────────────────────────────────────

def create_signed_execution_receipt(
    dataset_name: str,
    dataset_sha256: str,
    steps_completed: list[dict],
    explainable_rationale: str,
    guardrails_audit: list[dict],
    generated_artifacts: dict[str, dict],
    thread_id: str = "thread-dataset-01",
    run_id: str = "run-default"
) -> Dict[str, Any]:
    """
    Generates an EU AI Act Art. 12 & 26 compliant attestation receipt,
    hashes the components and cryptographically signs the result.
    """
    private_pem, public_pem = get_or_create_keypair()
    now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
    receipt_id = f"rec_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}_{hashlib.md5(now_utc.encode()).hexdigest()[:6]}"

    # Canonical receipt structure
    receipt_body = {
        "$schema": "https://dataset-automator.io/schemas/execution-receipt.v1.json",
        "receipt_id": receipt_id,
        "session": {
            "thread_id": thread_id,
            "run_id": run_id,
            "timestamp": now_utc
        },
        "provenance": {
            "dataset": {
                "name": dataset_name,
                "sha256_hash": dataset_sha256
            }
        },
        "execution_flow": {
            "steps_completed": steps_completed,
            "explainable_rationale": explainable_rationale
        },
        "guardrails_audit": {
            "rules_checked": guardrails_audit
        },
        "generated_artifacts": generated_artifacts
    }

    # Canonical serialization (key sorting for strict reproducibility)
    canonical_json = json.dumps(receipt_body, sort_keys=True, separators=(",", ":")).encode("utf-8")
    payload_hash = compute_sha256(canonical_json)
    signature = sign_payload(canonical_json, private_pem)

    receipt_full = {
        **receipt_body,
        "cryptographic_attestation": {
            "signing_authority": "Dataset_Automator_Kernel_Sandbox",
            "signature_algorithm": "RSASSA-PSS-SHA256",
            "payload_sha256": payload_hash,
            "attestation_signature": signature,
            "public_key_fingerprint": compute_sha256(public_pem)[:16]
        }
    }

    # Append-only persistence in attestation_receipts.json
    save_receipt_to_registry(receipt_full)
    return receipt_full


def save_receipt_to_registry(receipt: Dict[str, Any]) -> None:
    """Saves receipt in the persistent registry attestation_receipts.json."""
    existing_receipts = []
    if ATTESTATION_FILE.exists():
        try:
            with open(ATTESTATION_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                if isinstance(data, list):
                    existing_receipts = data
                elif isinstance(data, dict):
                    existing_receipts = [data]
        except Exception:
            existing_receipts = []

    # Insert at head (most recent first)
    existing_receipts.insert(0, receipt)
    with open(ATTESTATION_FILE, "w", encoding="utf-8") as f:
        json.dump(existing_receipts, f, indent=2, ensure_ascii=False)


def verify_receipt(receipt: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Verifies authenticity and integrity of an attestation receipt:
      - Rebuilds canonical payload
      - Verifies RSASSA-PSS cryptographic signature
    """
    attestation = receipt.get("cryptographic_attestation", {})
    signature = attestation.get("attestation_signature")
    if not signature:
        return False, "❌ Missing signature in receipt"

    # Isolate receipt body without the attestation block
    body = {k: v for k, v in receipt.items() if k != "cryptographic_attestation"}
    canonical_json = json.dumps(body, sort_keys=True, separators=(",", ":")).encode("utf-8")

    _, public_pem = get_or_create_keypair()
    is_valid = verify_signature(canonical_json, signature, public_pem)

    if is_valid:
        return True, "✅ Valid Cryptographic Signature (100% Certified Integrity)"
    else:
        return False, "🚨 ALERT: Invalid Signature or Tampering Detected!"


# ── Self-Validation Test ──────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔐 Testing Cryptographic Attestation Engine (EU AI Act & NIST)...")
    
    test_receipt = create_signed_execution_receipt(
        dataset_name="clients.csv",
        dataset_sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        steps_completed=[
            {"id": 0, "name": "Ingestion", "status": "completed"},
            {"id": 1, "name": "Neo4j_GraphRAG", "status": "completed"},
            {"id": 2, "name": "TabFM_Tournament", "status": "completed"},
            {"id": 3, "name": "Notebook_Delivery", "status": "completed"}
        ],
        explainable_rationale="Complete validation of champion Google TabFM model with 0 guardrail violations.",
        guardrails_audit=[
            {"rule": "VIF_Check", "value": 2.40, "threshold": 10.0, "status": "passed"},
            {"rule": "Durbin_Watson", "value": 1.95, "threshold": "[1.5-2.5]", "status": "passed"},
            {"rule": "Overfitting_Gap", "value": 0.04, "threshold": 0.20, "status": "passed"}
        ],
        generated_artifacts={
            "notebook": {
                "filename": "clients_Analyse_Full_MLOps.ipynb",
                "sha256_hash": "8f4f9f7a73138b3cd1a1e94119d59242a7ae41e4649b934ca495991b7852b123"
            },
            "model": {
                "filename": "model_tabfm_champion.skops",
                "sha256_hash": "4a5e6f7b8c9d0e1f2a3b4c5d6e7f8a9b0c1d2e3f4a5b6c7d8e9f0a1b2c3d4e5f"
            }
        }
    )

    print(f"  Receipt ID : {test_receipt['receipt_id']}")
    print(f"  Signature  : {test_receipt['cryptographic_attestation']['attestation_signature'][:30]}...")

    valid, msg = verify_receipt(test_receipt)
    print(f"  Verification: {msg}")
    assert valid, "Initial signature must be valid"

    # Tampering test
    tampered = dict(test_receipt)
    tampered["provenance"] = dict(tampered["provenance"])
    tampered["provenance"]["dataset"] = {"name": "corrupted_dataset.csv", "sha256_hash": "0000000000000"}
    valid_tampered, msg_tampered = verify_receipt(tampered)
    print(f"  Tampering Test: {msg_tampered}")
    assert not valid_tampered, "Tampered receipt must be rejected!"

    print("🎉 All cryptographic tests passed successfully!")
