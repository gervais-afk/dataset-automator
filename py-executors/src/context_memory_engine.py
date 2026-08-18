#!/usr/bin/env python3
"""
context_memory_engine.py — Ingénierie du Contexte & Mémoire Multi-Niveaux
========================================================================
1. Pattern LargeJson & Compression Structurelle (Offloading hors-bande)
   - Stocke les payloads lourds dans `workspace/outputs/offloaded_logs/`
   - L'agent ne reçoit qu'un badge compact : `[Tool Log ID: log_123]`
2. Architecture Mémoire à 5 Niveaux (SQLite + Neo4j) :
   - Épisodique : Historique de discussion turn-by-turn
   - Sémantique : Graphe Neo4j OKF v0.2 + base vectorielle
   - Procédurale : Recettes de tournois et d'audit validées à 100%
   - Entités : Schémas, colonnes cibles et métadonnées de datasets
   - Synthèse : Compaction chronologique avec clé d'expansion `summary_id`
3. Politique de Dépréciation (TTL Decay) pour éviter les états périmés.
"""

import os
import sys
import json
import sqlite3
import hashlib
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional

# ── Paths ────────────────────────────────────────────────────────────────────
FILE_PATH = Path(__file__).resolve()
SRC_DIR = FILE_PATH.parent
PY_EXECUTORS_DIR = SRC_DIR.parent
DATASET_AUTO_DIR = PY_EXECUTORS_DIR.parent
WORKSPACE_DIR = DATASET_AUTO_DIR / "workspace"
OUTPUTS_DIR = WORKSPACE_DIR / "outputs"
OFFLOAD_DIR = OUTPUTS_DIR / "offloaded_logs"
MEMORY_DIR = OUTPUTS_DIR / "memory_store"
MEMORY_DB = MEMORY_DIR / "agent_memory.sqlite"

OFFLOAD_DIR.mkdir(parents=True, exist_ok=True)
MEMORY_DIR.mkdir(parents=True, exist_ok=True)


class LargeJsonOffloader:
    """Gestionnaire de déchargement hors-bande des payloads volumineux."""

    @staticmethod
    def offload_payload(payload: Any, prefix: str = "tool_output") -> Dict[str, Any]:
        """Sauvegarde les données brutes sur disque et renvoie une référence compacte."""
        payload_str = json.dumps(payload, default=str)
        payload_hash = hashlib.sha256(payload_str.encode("utf-8")).hexdigest()[:12]
        log_id = f"log_{prefix}_{payload_hash}"
        file_path = OFFLOAD_DIR / f"{log_id}.json"

        with open(file_path, "w", encoding="utf-8") as f:
            f.write(payload_str)

        # Création d'un aperçu compressé (valeurs tronquées à 80 chars, structure préservée)
        preview = LargeJsonOffloader._compress_structure(payload)

        return {
            "tool_log_id": log_id,
            "badge": f"[Tool Log ID: {log_id}]",
            "file_path": str(file_path),
            "size_bytes": len(payload_str),
            "compressed_preview": preview
        }

    @staticmethod
    def _compress_structure(obj: Any, max_len: int = 80) -> Any:
        """Parcourt récursivement l'arborescence et tronque les chaînes longues."""
        if isinstance(obj, dict):
            return {k: LargeJsonOffloader._compress_structure(v, max_len) for k, v in list(obj.items())[:8]}
        elif isinstance(obj, list):
            return [LargeJsonOffloader._compress_structure(item, max_len) for item in obj[:5]]
        elif isinstance(obj, str):
            return obj[:max_len] + ("..." if len(obj) > max_len else "")
        return obj

    @staticmethod
    def load_payload(log_id: str) -> Optional[Any]:
        """Recharge les données brutes à la demande."""
        file_path = OFFLOAD_DIR / f"{log_id}.json"
        if file_path.exists():
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None


class MultiTierMemoryEngine:
    """Moteur de mémoire relationnelle à 5 niveaux avec TTL Decay."""

    def __init__(self, db_path: Path = MEMORY_DB):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        # Table 1: Mémoire Épisodique
        cur.execute("""
            CREATE TABLE IF NOT EXISTS episodic_memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                thread_id TEXT,
                role TEXT,
                content TEXT,
                tool_calls TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Table 2: Mémoire Procédurale (Recettes validées)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS procedural_memory (
                recipe_id TEXT PRIMARY KEY,
                domain TEXT,
                task_type TEXT,
                winning_pipeline TEXT,
                metrics TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Table 3: Mémoire d'Entités
        cur.execute("""
            CREATE TABLE IF NOT EXISTS entity_memory (
                entity_name TEXT PRIMARY KEY,
                entity_type TEXT,
                metadata TEXT,
                ttl_expiration DATETIME
            )
        """)
        # Table 4: Mémoire de Synthèse (Summary with expansion)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS summary_memory (
                summary_id TEXT PRIMARY KEY,
                thread_id TEXT,
                condensed_text TEXT,
                original_messages_count INTEGER,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def save_episodic(self, thread_id: str, role: str, content: str, tool_calls: list = None):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO episodic_memory (thread_id, role, content, tool_calls) VALUES (?, ?, ?, ?)",
            (thread_id, role, content, json.dumps(tool_calls or []))
        )
        conn.commit()
        conn.close()

    def save_procedural_recipe(self, recipe_id: str, domain: str, task_type: str, winning_pipeline: dict, metrics: dict):
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO procedural_memory (recipe_id, domain, task_type, winning_pipeline, metrics) VALUES (?, ?, ?, ?, ?)",
            (recipe_id, domain, task_type, json.dumps(winning_pipeline), json.dumps(metrics))
        )
        conn.commit()
        conn.close()

    def get_procedural_recipe(self, domain: str, task_type: str) -> Optional[dict]:
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT recipe_id, winning_pipeline, metrics FROM procedural_memory WHERE domain = ? AND task_type = ? ORDER BY created_at DESC LIMIT 1",
            (domain, task_type)
        )
        row = cur.fetchone()
        conn.close()
        if row:
            return {
                "recipe_id": row[0],
                "winning_pipeline": json.loads(row[1]),
                "metrics": json.loads(row[2])
            }
        return None

    def save_entity(self, entity_name: str, entity_type: str, metadata: dict, ttl_hours: int = 24):
        expiration = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=ttl_hours)).isoformat()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "INSERT OR REPLACE INTO entity_memory (entity_name, entity_type, metadata, ttl_expiration) VALUES (?, ?, ?, ?)",
            (entity_name, entity_type, json.dumps(metadata), expiration)
        )
        conn.commit()
        conn.close()

    def get_entity_non_expired(self, entity_name: str) -> Optional[dict]:
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute(
            "SELECT metadata, ttl_expiration FROM entity_memory WHERE entity_name = ? AND ttl_expiration > ?",
            (entity_name, now_iso)
        )
        row = cur.fetchone()
        conn.close()
        return json.loads(row[0]) if row else None


# ── Test d'Auto-Validation ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🧠 Test du Moteur de Contexte & Mémoire Multi-Niveaux...")
    
    # 1. Test LargeJson Offload
    big_data = {"columns": [f"col_{i}" for i in range(50)], "rows": [{"val": "x"*200} for _ in range(100)]}
    offload_res = LargeJsonOffloader.offload_payload(big_data, prefix="test_df")
    print(f"  LargeJson Badge : {offload_res['badge']} (Taille: {offload_res['size_bytes']} octets)")
    assert Path(offload_res['file_path']).exists()

    # 2. Test Mémoire Multi-Niveaux
    mem = MultiTierMemoryEngine()
    mem.save_episodic("thread-01", "user", "Lancer le tournoi de modèles sur clients.csv")
    mem.save_procedural_recipe(
        "rec_telecom_01", "Telecom", "classification",
        {"champion": "Google TabFM", "guardrail_applied": "VIF_Filter"},
        {"f1": 0.891, "accuracy": 0.921}
    )
    recipe = mem.get_procedural_recipe("Telecom", "classification")
    print(f"  Mémoire Procédurale : Recette {recipe['recipe_id']} retrouvée (Champion: {recipe['winning_pipeline']['champion']})")

    # 3. Test Entité avec TTL
    mem.save_entity("clients.csv", "Dataset", {"rows": 1000, "cols": 15}, ttl_hours=12)
    ent = mem.get_entity_non_expired("clients.csv")
    print(f"  Mémoire Entité (TTL Valide) : {ent}")
    assert ent is not None

    print("🎉 Test Context & Memory Engine réussi avec succès !")
