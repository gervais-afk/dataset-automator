import argparse
import json
import os
import sys
import time
import numpy as np
import matplotlib.image as mpimg
from scipy.stats import skew, kurtosis, spearmanr
from statsmodels.stats.stattools import durbin_watson

def log_stderr(message):
    sys.stderr.write(message + "\n")
    sys.stderr.flush()

def main():
    start_time = time.time()
    
    log_stderr("============================================================")
    log_stderr("📊 DÉBUT DE LA VALIDATION DU GRAPHIQUE (PYTHON GUARDRAIL)")
    log_stderr("============================================================")
    
    parser = argparse.ArgumentParser(description="Validateur statistique et visuel de graphiques.")
    parser.add_argument("--image_path", required=True, help="Chemin absolu de l'image du graphique")
    parser.add_argument("--chart_type", required=True, choices=["confusion_matrix", "residuals"], help="Type de graphique")
    parser.add_argument("--metrics", required=True, help="Donnees de metriques au format JSON")
    
    args = parser.parse_args()
    log_stderr(f"[INFO] Type de graphique : {args.chart_type}")
    log_stderr(f"[INFO] Image cible : {args.image_path}")
    
    visual_patterns = []
    issues = []
    
    # 1. Verification d'integrite de l'image (Oeil de l'IA renforcé en Python)
    log_stderr("[INFO] Étape 1 : Validation de l'intégrité visuelle de l'image...")
    if not os.path.exists(args.image_path):
        err_msg = f"Image introuvable au chemin : {args.image_path}"
        issues.append(err_msg)
        log_stderr(f"🚨 ALERTE : {err_msg}")
    else:
        try:
            # Charger l'image avec matplotlib
            img = mpimg.imread(args.image_path)
            
            # Calcul des statistiques de pixel de base et avancées (skewness, kurtosis)
            img_flat = img.flatten()
            img_std = float(np.std(img))
            img_skew = float(skew(img_flat))
            img_kurt = float(kurtosis(img_flat))
            
            visual_patterns.append(f"Dimensions de l'image : {img.shape}")
            visual_patterns.append(f"Ecart-type des pixels : {img_std:.4f}")
            
            log_stderr(f"[STATS IMAGE] Dimensions : {img.shape}")
            log_stderr(f"[STATS IMAGE] Écart-type : {img_std:.4f} | Skewness : {img_skew:.4f} | Kurtosis : {img_kurt:.4f}")
            
            # Détection d'images vides ou uniformes
            if img_std < 0.005:
                err_msg = "L'image generee est vide ou entierement monochrome (echec du rendu graphique)."
                issues.append(err_msg)
                log_stderr(f"🚨 ALERTE : {err_msg}")
            # Détection d'anomalies de distribution de pixel (ex: trop peu de variations réelles)
            elif abs(img_skew) > 10.0:
                err_msg = f"Distribution des pixels hautement anormale (Skewness: {img_skew:.2f}). L'image peut être altérée."
                issues.append(err_msg)
                log_stderr(f"🚨 ALERTE : {err_msg}")
            else:
                visual_patterns.append("L'image contient des variations de pixels valides.")
                log_stderr("✅ Validation visuelle de base OK : l'image n'est pas vide.")
        except Exception as e:
            err_msg = f"Impossible de lire l'image (fichier corrompu ou format invalide) : {str(e)}"
            issues.append(err_msg)
            log_stderr(f"🚨 ALERTE : {err_msg}")

    # 2. Analyse statistique des metriques
    log_stderr("[INFO] Étape 2 : Analyse statistique des métriques...")
    try:
        metrics_data = json.loads(args.metrics)
    except Exception as e:
        metrics_data = {}
        err_msg = f"Impossible de decoder les metriques JSON : {str(e)}"
        issues.append(err_msg)
        log_stderr(f"🚨 ALERTE : {err_msg}")

    if args.chart_type == "confusion_matrix":
        accuracy = metrics_data.get("accuracy", 1.0)
        macro_f1 = metrics_data.get("macro_f1", 1.0)
        per_class_recall = metrics_data.get("per_class_recall", {})
        
        visual_patterns.append(f"Classification - Accuracy: {accuracy:.4f}, Macro F1: {macro_f1:.4f}")
        log_stderr(f"[STATS ML] Accuracy globale : {accuracy:.4f} | Macro F1 : {macro_f1:.4f}")
        
        # Performance globale
        if accuracy < 0.4 or macro_f1 < 0.35:
            err_msg = f"Performance globale insuffisante (Accuracy: {accuracy:.2f}, F1: {macro_f1:.2f})."
            issues.append(err_msg)
            log_stderr(f"🚨 ALERTE : {err_msg}")
            
        # Detection classe ignoree ou tres faible
        class_recalls = []
        for k, v in per_class_recall.items():
            if k not in ['accuracy', 'macro avg', 'weighted avg']:
                val = float(v)
                class_recalls.append(val)
                if val == 0.0:
                    err_msg = f"La classe '{k}' est totalement ignoree par le modele (Rappel = 0.0)."
                    issues.append(err_msg)
                    log_stderr(f"🚨 ALERTE : {err_msg}")
                elif val < 0.1:
                    err_msg = f"La classe '{k}' a un taux de rappel critique (< 10%)."
                    issues.append(err_msg)
                    log_stderr(f"🚨 ALERTE : {err_msg}")
                    
        # Ecart de performance entre classes (gap de rappel)
        if len(class_recalls) > 1:
            gap = max(class_recalls) - min(class_recalls)
            visual_patterns.append(f"Gap max de rappel entre classes : {gap:.4f}")
            log_stderr(f"[STATS ML] Gap de rappel entre classes : {gap:.4f}")
            if gap > 0.8:
                err_msg = f"Desequilibre extreme de performance entre les classes (Gap de rappel: {gap*100:.1f}%)."
                issues.append(err_msg)
                log_stderr(f"🚨 ALERTE : {err_msg}")
                
    elif args.chart_type == "residuals":
        # Recalcul dynamique si les résidus et prédictions bruts sont fournis
        if "residuals" in metrics_data:
            log_stderr("[INFO] Recalcul dynamique des statistiques de résidus à partir des données brutes...")
            resids = np.array(metrics_data["residuals"])
            r2 = metrics_data.get("r2", 1.0)
            rmse = metrics_data.get("rmse", 0.0)
            skewness_val = float(skew(resids)) if len(resids) > 0 else 0.0
            dw = float(durbin_watson(resids)) if len(resids) > 0 else 2.0
            
            if "predictions" in metrics_data:
                preds = np.array(metrics_data["predictions"])
                try:
                    _, p_val = spearmanr(preds, np.abs(resids))
                    hetero_p = float(p_val)
                except:
                    hetero_p = 1.0
            else:
                hetero_p = metrics_data.get("heteroscedasticity_p_value", 1.0)
        else:
            r2 = metrics_data.get("r2", 1.0)
            rmse = metrics_data.get("rmse", 0.0)
            skewness_val = metrics_data.get("residuals_skewness", 0.0)
            hetero_p = metrics_data.get("heteroscedasticity_p_value", 1.0)
            dw = metrics_data.get("residuals_durbin_watson", 2.0)
        
        visual_patterns.append(f"Regression - R2: {r2:.4f}, RMSE: {rmse:.4f}")
        visual_patterns.append(f"Residus - Skewness: {skewness_val:.4f}, Heteroscedasticite p-val: {hetero_p:.4f}, Durbin-Watson: {dw:.2f}")
        
        log_stderr(f"[STATS ML] R2 : {r2:.4f} | RMSE : {rmse:.4f}")
        log_stderr(f"[STATS ML] Résidus - Skewness : {skewness_val:.4f} | Heteroscedasticité p-val : {hetero_p:.4f} | Durbin-Watson : {dw:.2f}")
        
        # Qualite de prediction
        if r2 < 0.1:
            err_msg = f"Qualite de prediction R2 tres faible ou negative : {r2:.2f}"
            issues.append(err_msg)
            log_stderr(f"🚨 ALERTE : {err_msg}")
            
        # Asymetrie des erreurs
        if abs(skewness_val) > 2.0:
            err_msg = f"Distribution des erreurs fortement asymetrique (Skewness: {skewness_val:.2f})."
            issues.append(err_msg)
            log_stderr(f"🚨 ALERTE : {err_msg}")
            
        # Heteroscedasticite (effet entonnoir)
        if hetero_p < 0.01:
            err_msg = f"Heteroscedasticite critique detectee (p-value={hetero_p:.4f}). La variance des residus n'est pas constante."
            issues.append(err_msg)
            log_stderr(f"🚨 ALERTE : {err_msg}")
            
        # Autocorrelation (independance des erreurs)
        if dw < 1.0 or dw > 3.0:
            err_msg = f"Autocorrelation significative des erreurs (Durbin-Watson: {dw:.2f}). Les residus ne sont pas independants."
            issues.append(err_msg)
            log_stderr(f"🚨 ALERTE : {err_msg}")

    # 3. Output JSON pour l'orchestrateur
    output_result = {
        "visualPatterns": visual_patterns,
        "confirmsMetrics": len(issues) == 0,
        "additionalIssues": issues
    }
    
    # 4. Temps d'exécution
    end_time = time.time()
    duration = end_time - start_time
    
    log_stderr("------------------------------------------------------------")
    log_stderr(f"⏱️ Temps d'exécution de la validation : {duration:.4f} secondes")
    log_stderr(f"✅ Statut final de validation : {'CONFIRMÉ' if len(issues) == 0 else 'REJETÉ'}")
    log_stderr("============================================================")
    
    print(json.dumps(output_result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()
