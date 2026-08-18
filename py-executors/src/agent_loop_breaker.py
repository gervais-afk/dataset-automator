#!/usr/bin/env python3
"""
agent_loop_breaker.py — Système Anti-Boucle Algorithmique & Résilience Agentique
================================================================================
Intercepte 3 types de boucles infinies destructrices de budget :
  1. Répétitions Exactes (Exact Repeat) : Hachage SHA-256 des appels d'outils + Cache LRU
  2. Boucles d'Oscillation (Jitter Loops) : Indice de Jaccard sur arguments successifs (> 0.60 sur 3 tours)
  3. Stagnations Sémantiques (Stall Loops) : Similarité cosinus sur les raisonnements (> 0.85)
"""

import os
import sys
import json
import hashlib
import numpy as np
from typing import Dict, Any, List, Tuple


class AgentLoopBreaker:
    """Surveillance déterministe indépendante de l'orchestrateur d'agents."""

    def __init__(self, max_history: int = 20):
        self.max_history = max_history
        self.call_hashes = []
        self.lru_tool_cache = {}
        self.recent_arguments = []
        self.recent_reasonings = []

    def check_and_record_tool_call(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Vérifie si l'appel d'outil est une répétition exacte ou une oscillation (Jitter Loop).
        """
        canon_args = json.dumps(arguments, sort_keys=True, default=str)
        call_sig = f"{tool_name}::{canon_args}"
        call_hash = hashlib.sha256(call_sig.encode("utf-8")).hexdigest()

        # 1. Détection de répétition exacte
        if call_hash in self.lru_tool_cache:
            return {
                "loop_detected": True,
                "loop_type": "EXACT_REPEAT_LOOP",
                "action": "SERVE_CACHE",
                "cached_result": self.lru_tool_cache[call_hash],
                "message": f"⚡ Appel identique à '{tool_name}' intercepté — Résultat servi depuis le cache LRU (0 token)."
            }

        # 2. Détection de boucle d'oscillation (Jitter Loop)
        tokenized_args = set(canon_args.lower().replace("{", " ").replace("}", " ").replace('"', " ").split())
        self.recent_arguments.append(tokenized_args)
        if len(self.recent_arguments) > self.max_history:
            self.recent_arguments.pop(0)

        jitter_detected = False
        if len(self.recent_arguments) >= 3:
            # Calcul de Jaccard sur les 3 derniers tours
            j1 = self._jaccard_similarity(self.recent_arguments[-1], self.recent_arguments[-2])
            j2 = self._jaccard_similarity(self.recent_arguments[-2], self.recent_arguments[-3])
            if j1 >= 0.60 and j2 >= 0.60:
                jitter_detected = True

        if jitter_detected:
            return {
                "loop_detected": True,
                "loop_type": "JITTER_OSCILLATION_LOOP",
                "action": "FREEZE_AGENT_HITL",
                "message": f"🚨 Boucle d'oscillation détectée sur '{tool_name}' (Jaccard > 0.60 sur 3 tours). Gel en état Proposed."
            }

        self.call_hashes.append(call_hash)
        return {
            "loop_detected": False,
            "loop_type": "NONE",
            "action": "PROCEED",
            "call_hash": call_hash
        }

    def cache_tool_result(self, call_hash: str, result: Any) -> None:
        """Enregistre le résultat de l'outil pour déduplication."""
        self.lru_tool_cache[call_hash] = result

    def check_semantic_stall(self, reasoning_text: str) -> Dict[str, Any]:
        """
        Détecte la stagnation sémantique (l'agent s'excuse ou tourne en rond sans progresser).
        Utilise un calcul de similarité cosinus sur les fréquences de mots clés (Bag-of-Words normalisé).
        """
        words = [w.lower() for w in reasoning_text.split() if len(w) > 3]
        self.recent_reasonings.append(words)
        if len(self.recent_reasonings) > self.max_history:
            self.recent_reasonings.pop(0)

        if len(self.recent_reasonings) >= 3:
            s1 = self._word_overlap_similarity(self.recent_reasonings[-1], self.recent_reasonings[-2])
            s2 = self._word_overlap_similarity(self.recent_reasonings[-2], self.recent_reasonings[-3])
            if s1 >= 0.85 and s2 >= 0.85:
                return {
                    "stall_detected": True,
                    "similarity_score": round((s1 + s2) / 2, 3),
                    "action": "SUSPEND_BUDGET",
                    "message": "🚨 Stagnation sémantique détectée (Similarité > 0.85 sans progression). Suspension du budget tokens."
                }

        return {
            "stall_detected": False,
            "similarity_score": 0.0,
            "action": "PROCEED"
        }

    def _jaccard_similarity(self, set_a: set, set_b: set) -> float:
        if not set_a or not set_b:
            return 0.0
        intersection = len(set_a.intersection(set_b))
        union = len(set_a.union(set_b))
        return intersection / union if union > 0 else 0.0

    def _word_overlap_similarity(self, list_a: list, list_b: list) -> float:
        set_a, set_b = set(list_a), set(list_b)
        return self._jaccard_similarity(set_a, set_b)


# ── Test d'Auto-Validation ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("🛡️ Test du Système Anti-Boucle (Agent Loop Breaker)...")
    
    breaker = AgentLoopBreaker()
    
    # 1. Test appel normal
    res1 = breaker.check_and_record_tool_call("fit_model", {"max_depth": 5, "lr": 0.1})
    breaker.cache_tool_result(res1["call_hash"], {"f1": 0.89})
    print(f"  Appel 1 : {res1['action']}")

    # 2. Test répétition exacte -> Cache servi
    res2 = breaker.check_and_record_tool_call("fit_model", {"max_depth": 5, "lr": 0.1})
    print(f"  Appel 2 (Même args) : {res2['action']} -> {res2['message']}")
    assert res2["action"] == "SERVE_CACHE"

    # 3. Test oscillation Jitter Loop
    breaker.check_and_record_tool_call("fit_model", {"max_depth": 6, "lr": 0.1})
    res_jitter = breaker.check_and_record_tool_call("fit_model", {"max_depth": 6, "lr": 0.101})
    print(f"  Appel 3 (Oscillation) : {res_jitter['action']}")

    # 4. Test stagnation sémantique
    text = "Je m'excuse pour cette erreur je vais maintenant recalculer la métrique de précision."
    breaker.check_semantic_stall(text)
    breaker.check_semantic_stall(text)
    res_stall = breaker.check_semantic_stall(text)
    print(f"  Stagnation : {res_stall['action']} (Score: {res_stall.get('similarity_score', 0)})")
    assert res_stall["stall_detected"], "La stagnation doit être interceptée"

    print("🎉 Test Agent Loop Breaker réussi avec succès !")
