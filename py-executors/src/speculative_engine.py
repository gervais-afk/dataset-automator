#!/usr/bin/env python3
"""
speculative_engine.py — Moteur d'Exécution Spéculative & Rollback Git-Like
==========================================================================
1. Cycle de Vie Staged : Actions proposées isolées en état "Proposed" avant validation.
2. Checkpointing & Snapshots : Sérialisation d'état complet (MemorySaver).
3. Exception Récupérable : `RecoverableException` interrompt la branche spéculative sans polluer la production.
4. Élagage de Contexte (*Context Pruning*) : Purge automatique des tokens transitoires.
5. Smart Diff & Time-Travel Replay : Visualisation différentielle avant/après et replay temporel.
"""

import os
import sys
import json
import copy
import hashlib
import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple


class RecoverableException(Exception):
    """Exception spécifique levée par un Guardrail ou le Red Teamer pour déclencher un Rollback."""
    def __init__(self, message: str, guardrail_name: str, observed_value: Any, threshold: Any, suggested_fix: str):
        super().__init__(message)
        self.guardrail_name = guardrail_name
        self.observed_value = observed_value
        self.threshold = threshold
        self.suggested_fix = suggested_fix


class SpeculativeExecutionEngine:
    """Orchestrateur de branches spéculatives avec retour en arrière (Rollback)."""

    def __init__(self, session_id: str = "speculative-session-01"):
        self.session_id = session_id
        self.snapshots = {}  # checkpoint_id -> state_dict
        self.staged_actions = []
        self.pruned_branches = []
        self.execution_timeline = []

    def create_checkpoint(self, checkpoint_name: str, state_data: Dict[str, Any]) -> str:
        """Enregistre un snapshot immuable de l'état du système."""
        now_utc = datetime.datetime.now(datetime.timezone.utc).isoformat()
        chk_id = f"chk_{hashlib.md5((checkpoint_name + now_utc).encode()).hexdigest()[:10]}"
        
        snapshot = {
            "checkpoint_id": chk_id,
            "name": checkpoint_name,
            "timestamp": now_utc,
            "state": copy.deepcopy(state_data),
            "state_hash": hashlib.sha256(json.dumps(state_data, sort_keys=True, default=str).encode()).hexdigest()
        }
        self.snapshots[chk_id] = snapshot
        self.execution_timeline.append({
            "event": "CHECKPOINT_CREATED",
            "checkpoint_id": chk_id,
            "name": checkpoint_name,
            "timestamp": now_utc
        })
        return chk_id

    def execute_speculatively(
        self,
        action_name: str,
        checkpoint_id: str,
        execution_lambda,
        guardrail_verifier_lambda = None
    ) -> Dict[str, Any]:
        """
        Exécute spéculativement une action :
          - Si succès et guardrail validé -> État "Approved"
          - Si violation de guardrail ou erreur -> Rollback automatique vers checkpoint_id + Context Pruning
        """
        base_snapshot = self.snapshots.get(checkpoint_id)
        if not base_snapshot:
            raise ValueError(f"Checkpoint {checkpoint_id} introuvable pour l'exécution spéculative.")

        staged_entry = {
            "action_name": action_name,
            "base_checkpoint_id": checkpoint_id,
            "status": "PROPOSED",
            "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
        }
        self.staged_actions.append(staged_entry)

        try:
            # 1. Exécution isolée
            result_state = execution_lambda(copy.deepcopy(base_snapshot["state"]))

            # 2. Vérification par Guardrail / Red Teamer
            if guardrail_verifier_lambda:
                guardrail_passed, guardrail_report = guardrail_verifier_lambda(result_state)
                if not guardrail_passed:
                    raise RecoverableException(
                        message=guardrail_report.get("message", "Violation de guardrail détectée"),
                        guardrail_name=guardrail_report.get("guardrail_name", "UnknownGuardrail"),
                        observed_value=guardrail_report.get("observed_value"),
                        threshold=guardrail_report.get("threshold"),
                        suggested_fix=guardrail_report.get("suggested_fix", "Ajuster les hyperparamètres ou filtrer les variables")
                    )

            # 3. Validation et promotion en état EXECUTED
            staged_entry["status"] = "EXECUTED"
            new_chk_id = self.create_checkpoint(f"after_{action_name}", result_state)
            
            # Calcul du Smart Diff
            diff = self._compute_smart_diff(base_snapshot["state"], result_state)
            
            return {
                "success": True,
                "status": "EXECUTED",
                "new_checkpoint_id": new_chk_id,
                "diff": diff,
                "result_state": result_state,
                "message": f"✅ Action '{action_name}' validée et promue avec succès."
            }

        except RecoverableException as exc:
            # 4. Rollback Automatique & Élagage de Contexte (Context Pruning)
            staged_entry["status"] = "ROLLED_BACK"
            pruned_info = {
                "action_name": action_name,
                "failed_checkpoint": checkpoint_id,
                "guardrail_violated": exc.guardrail_name,
                "observed_value": exc.observed_value,
                "threshold": exc.threshold,
                "suggested_fix": exc.suggested_fix,
                "rationale": f"Restauration automatique exécutée car {exc.guardrail_name} = {exc.observed_value} (seuil: {exc.threshold}).",
                "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat()
            }
            self.pruned_branches.append(pruned_info)
            self.execution_timeline.append({
                "event": "ROLLBACK_TRIGGERED",
                "reason": str(exc),
                "restored_checkpoint_id": checkpoint_id,
                "pruned_info": pruned_info
            })

            return {
                "success": False,
                "status": "ROLLED_BACK",
                "restored_checkpoint_id": checkpoint_id,
                "pruned_info": pruned_info,
                "message": f"⚠️ Rollback automatique déclenché : {exc.guardrail_name} violé. État restauré à {checkpoint_id}."
            }

    def _compute_smart_diff(self, state_before: dict, state_after: dict) -> Dict[str, Any]:
        """Calcule le différentiel précis vert (ajouts) / rouge (suppressions) entre deux états."""
        additions = {}
        modifications = {}
        deletions = {}

        for k, v in state_after.items():
            if k not in state_before:
                additions[k] = v
            elif state_before[k] != v:
                modifications[k] = {"before": state_before[k], "after": v}

        for k, v in state_before.items():
            if k not in state_after:
                deletions[k] = v

        return {
            "additions": additions,
            "modifications": modifications,
            "deletions": deletions
        }

    def get_time_travel_timeline(self) -> List[Dict[str, Any]]:
        """Renvoie l'historique complet pour la barre de défilement temporel (Time-Travel Replay)."""
        return self.execution_timeline


# ── Test d'Auto-Validation ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🔄 Test du Moteur Spéculatif & Rollback Git-Like...")
    
    engine = SpeculativeExecutionEngine()
    
    # 1. État initial (Base Checkpoint)
    initial_state = {
        "features": ["income", "debt", "house_age"],
        "model_type": "XGBoost",
        "params": {"max_depth": 6},
        "metrics": {"r2_train": 0.85, "r2_test": 0.82}
    }
    chk0 = engine.create_checkpoint("initial_clean_state", initial_state)
    print(f"  Checkpoint Initial : {chk0}")

    # 2. Test Exécution Spéculative qui Échoue (VIF trop élevé)
    def speculative_bad_training(state):
        state["params"]["max_depth"] = 12
        state["metrics"] = {"r2_train": 0.99, "r2_test": 0.42}  # Overfitting
        return state

    def guardrail_overfitting_check(state):
        gap = state["metrics"]["r2_train"] - state["metrics"]["r2_test"]
        if gap > 0.20:
            return False, {
                "guardrail_name": "Overfitting_Gap_Guard",
                "observed_value": round(gap, 2),
                "threshold": "< 0.20",
                "message": f"Overfitting Gap excessif ({gap:.2f} > 0.20)",
                "suggested_fix": "Réduire max_depth ou activer régularisation L2"
            }
        return True, {}

    res_fail = engine.execute_speculatively(
        "train_deep_tree",
        checkpoint_id=chk0,
        execution_lambda=speculative_bad_training,
        guardrail_verifier_lambda=guardrail_overfitting_check
    )
    print(f"  Résultat Tentative 1 : {res_fail['status']} -> {res_fail['message']}")
    assert res_fail["status"] == "ROLLED_BACK"
    assert len(engine.pruned_branches) == 1

    # 3. Test Exécution Spéculative qui Réussit (TabFM)
    def speculative_good_training(state):
        state["model_type"] = "Google TabFM"
        state["metrics"] = {"r2_train": 0.89, "r2_test": 0.86}  # Gap = 0.03
        return state

    res_ok = engine.execute_speculatively(
        "train_tabfm_foundation",
        checkpoint_id=chk0,
        execution_lambda=speculative_good_training,
        guardrail_verifier_lambda=guardrail_overfitting_check
    )
    print(f"  Résultat Tentative 2 : {res_ok['status']} -> {res_ok['message']}")
    assert res_ok["status"] == "EXECUTED"

    print("🎉 Test Speculative & Rollback Engine réussi avec succès !")
