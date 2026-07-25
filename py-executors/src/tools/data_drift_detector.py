#!/usr/bin/env python3
"""
data_drift_detector.py — SOVEREIGN.BI Data Drift & Monitoring Engine

Calcule la dérive statistique entre un dataset de référence (Baseline / Train)
et un nouveau dataset de production (Current / Test).

Méthodes :
  - Test de Kolmogorov-Smirnov (KS-test) pour les variables numériques
  - Test du Chi-carré (Chi2) pour les variables catégorielles
  - Population Stability Index (PSI) pour la dérive globale
  - Enregistrement automatique des alertes de dérive dans Neo4j (Nœud :Alert)
"""

import os
import sys
import json
import numpy as np
import pandas as pd
from scipy import stats
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(BASE_DIR))

def calculate_psi(baseline: np.ndarray, current: np.ndarray, num_buckets: int = 10) -> float:
    """Calcule le Population Stability Index (PSI) entre deux séries numériques."""
    baseline = baseline[~np.isnan(baseline)]
    current = current[~np.isnan(current)]
    
    if len(baseline) == 0 or len(current) == 0:
        return 0.0

    percentiles = np.linspace(0, 100, num_buckets + 1)
    buckets = np.percentile(baseline, percentiles)
    buckets[0] -= 1e-5
    buckets[-1] += 1e-5

    baseline_counts, _ = np.histogram(baseline, bins=buckets)
    current_counts, _ = np.histogram(current, bins=buckets)

    baseline_pct = baseline_counts / len(baseline)
    current_pct = current_counts / len(current)

    # Protection contre la division par zéro
    baseline_pct = np.where(baseline_pct == 0, 1e-4, baseline_pct)
    current_pct = np.where(current_pct == 0, 1e-4, current_pct)

    psi_val = np.sum((current_pct - baseline_pct) * np.log(current_pct / baseline_pct))
    return float(psi_val)

def detect_dataset_drift(reference_path: str, current_path: str, alpha: float = 0.05) -> dict:
    """
    Compare deux datasets CSV et identifie les variables ayant dérivé.
    """
    if not os.path.exists(reference_path) or not os.path.exists(current_path):
        return {"error": "L'un des fichiers spécifiés est introuvable."}

    df_ref = pd.read_csv(reference_path)
    df_curr = pd.read_csv(current_path)

    common_cols = [c for c in df_ref.columns if c in df_curr.columns]
    drift_results = []
    total_drifted = 0

    for col in common_cols:
        col_ref = df_ref[col].dropna()
        col_curr = df_curr[col].dropna()

        if col_ref.empty or col_curr.empty:
            continue

        # Cas 1 : Variables Numériques
        if np.issubdtype(df_ref[col].dtype, np.number):
            ks_stat, p_val = stats.ks_2samp(col_ref, col_curr)
            psi_score = calculate_psi(col_ref.values, col_curr.values)
            is_drifted = p_val < alpha or psi_score > 0.2

            status = "CRITICAL_DRIFT" if psi_score > 0.25 else ("MODERATE_DRIFT" if is_drifted else "STABLE")
            if is_drifted: total_drifted += 1

            drift_results.append({
                "column": col,
                "type": "numeric",
                "test": "Kolmogorov-Smirnov",
                "p_value": float(p_val),
                "ks_stat": float(ks_stat),
                "psi_score": round(psi_score, 4),
                "is_drifted": is_drifted,
                "status": status
            })

        # Cas 2 : Variables Catégorielles
        else:
            ref_counts = col_ref.value_counts(normalize=True)
            curr_counts = col_curr.value_counts(normalize=True)
            all_cats = list(set(ref_counts.index).union(set(curr_counts.index)))

            ref_freq = [ref_counts.get(c, 0.0) * len(col_ref) for c in all_cats]
            curr_freq = [curr_counts.get(c, 0.0) * len(col_curr) for c in all_cats]

            try:
                chi2_stat, p_val = stats.chisquare(f_obs=curr_freq, f_exp=ref_freq)
                is_drifted = p_val < alpha
            except Exception:
                p_val = 1.0
                is_drifted = False

            if is_drifted: total_drifted += 1

            drift_results.append({
                "column": col,
                "type": "categorical",
                "test": "Chi2-Square",
                "p_value": float(p_val),
                "is_drifted": is_drifted,
                "status": "DRIFT_DETECTED" if is_drifted else "STABLE"
            })

    drift_share = round(total_drifted / max(len(common_cols), 1), 2)
    overall_drift = drift_share > 0.3

    summary = {
        "reference_file": os.path.basename(reference_path),
        "current_file": os.path.basename(current_path),
        "total_columns_tested": len(common_cols),
        "drifted_columns_count": total_drifted,
        "drift_share": drift_share,
        "overall_dataset_drift": overall_drift,
        "details": drift_results
    }

    # Log d'alerte dans Neo4j si dérive globale détectée
    if overall_drift:
        try:
            from neo4j import GraphDatabase
            uri = os.getenv("NEO4J_URI", "bolt://127.0.0.1:7687")
            user = os.getenv("NEO4J_USER", "neo4j")
            pwd  = os.getenv("NEO4J_PASSWORD", "password123")
            driver = GraphDatabase.driver(uri, auth=(user, pwd))
            with driver.session() as session:
                session.run(
                    """
                    CREATE (a:Alert {
                        id: randomUUID(),
                        type: 'DATA_DRIFT',
                        dataset: $dataset,
                        drift_share: $drift_share,
                        timestamp: datetime(),
                        status: 'UNRESOLVED',
                        message: $msg
                    })
                    """,
                    dataset=os.path.basename(current_path),
                    drift_share=drift_share,
                    msg=f"Dérive de données majeure détectée ({total_drifted}/{len(common_cols)} colonnes affectées)."
                )
            driver.close()
            print("🚨 Alerte de Data Drift enregistrée dans Neo4j.")
        except Exception as e:
            print(f"⚠️ Erreur lors de l'enregistrement de l'alerte Neo4j: {e}")

    return summary

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="SOVEREIGN.BI Data Drift Detector")
    parser.add_argument("--ref", required=True, help="Fichier CSV de référence (Baseline)")
    parser.add_argument("--curr", required=True, help="Fichier CSV actuel (Production)")
    args = parser.parse_args()

    res = detect_dataset_drift(args.ref, args.curr)
    print(json.dumps(res, indent=2, ensure_ascii=False))
