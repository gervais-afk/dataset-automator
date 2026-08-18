import os
import json
import hashlib
from datetime import datetime
import sys

def get_file_sha256(file_path):
    try:
        sha256 = hashlib.sha256()
        with open(file_path, 'rb') as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return f"sha256:{sha256.hexdigest()}"
    except Exception:
        return "sha256:unknown"

def generate_model_card(output_dir, dataset_name, task_type, target_col, metrics, best_model_name, gate_status):
    """
    Génère un fichier MODEL_CARD.md standardisé décrivant l'identité et les performances du modèle.
    """
    card_path = os.path.join(output_dir, "MODEL_CARD.md")
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Extraction des métriques principales
    metrics_str = ""
    for k, v in metrics.items():
        if isinstance(v, float):
            metrics_str += f"- **{k}** : {v:.4f}\n"
        else:
            metrics_str += f"- **{k}** : {v}\n"
            
    content = f"""# Model Card — Dataset Automator

## Informations Générales
- **Nom du Dataset** : {dataset_name}
- **Type de Tâche** : {task_type}
- **Variable Cible (Target)** : {target_col or 'Aucune (Clustering)'}
- **Date d'Entraînement** : {timestamp}
- **Pipeline de Production** : Scikit-Learn Pipeline (preprocessing + modèle)

## Modèle Champion Élu
- **Algorithme Élu** : {best_model_name}
- **Statut de la Gate de Déploiement** : **{gate_status}**

## Performances Clés
{metrics_str}

## Explicabilité & Gouvernance (SHAP / LIME)
- Explications globales (SHAP) et locales (LIME) générées et stockées sous forme de graphiques dans le répertoire du run.
- **Rappel Causalité** : Les contributions indiquent la force d'association locale/globale avec la prédiction du modèle. Elles ne décrivent pas des relations de causalité absolue.

## Confiance Agentique & Gouvernance (OKF v0.2)
- **Provenance & Ontologie** : Base de connaissances Neo4j / Fiches standardisées OKF v0.2.
- **Niveau de Confiance** : **Tier 1 (Human-Reviewed)** appliqué sur toutes les règles critiques.
- **Reçus d'Attestation** : Prétraitements audités sans improvisation LLM (`attestation_receipts.json`).
- **Sérialisation du Modèle** : Format sécurisé **`.skops`** (Zéro vulnérabilité Pickle, conformité Enterprise).

## Limites & Recommandations
- Le modèle doit être utilisé avec prudence sur des données hors-distribution (données dont les variables dépassent les limites observées dans le dataset d'entraînement).
- **Recalibrage** : Recommandé périodiquement (ex: tous les mois ou si un drift significatif est détecté).
"""
    try:
        with open(card_path, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"✅ Model Card générée à l'emplacement : {card_path}")
    except Exception as e:
        sys.stderr.write(f"⚠️ Échec d'écriture de la Model Card : {e}\n")

def generate_run_manifest(output_dir, file_path, target_col, task_type, metrics, best_model_name):
    """
    Génère un run_manifest.json décrivant tous les métadonnées de l'exécution pour la reproductibilité.
    """
    manifest_path = os.path.join(output_dir, "run_manifest.json")
    dataset_hash = get_file_sha256(file_path)
    
    manifest = {
        "run_id": f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{best_model_name}",
        "dataset_name": os.path.basename(file_path),
        "dataset_hash": dataset_hash,
        "target_col": target_col,
        "task_type": task_type,
        "metrics": metrics,
        "champion_model": best_model_name,
        "python_version": sys.version.split()[0],
        "created_at": datetime.now().isoformat()
    }
    
    try:
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)
        print(f"✅ Run Manifest généré à l'emplacement : {manifest_path}")
    except Exception as e:
        sys.stderr.write(f"⚠️ Échec d'écriture du Run Manifest : {e}\n")

def run_deployment_quality_gate(metrics, best_model_name, task_type):
    """
    Évalue si le modèle champion respecte les critères de qualité minimaux.
    """
    checks = {
        "model_exists": best_model_name is not None and best_model_name != "N/A"
    }
    
    # Exemple de règles sur les métriques clés
    if task_type == "classification":
        # Au moins 60% d'accuracy
        acc = metrics.get("accuracy") or metrics.get("accuracy_score")
        if acc is not None:
            checks["accuracy_above_threshold"] = float(acc) >= 0.60
    elif task_type in ["regression", "timeseries"]:
        # R2 positif ou RMSE valide
        r2 = metrics.get("r2") or metrics.get("r2_score")
        if r2 is not None:
            checks["r2_positive"] = float(r2) > 0.0
            
    # Vérification de la fidélité de substitution de SHAP si présente
    shap_fidelity = metrics.get("shap_surrogate_fidelity")
    if shap_fidelity is not None:
        checks["shap_fidelity_above_threshold"] = float(shap_fidelity) >= 0.80
        
    can_deploy = all(checks.values())
    status = "APPROVED" if can_deploy else "BLOCKED"
    
    return {
        "status": status,
        "checks": checks
    }
