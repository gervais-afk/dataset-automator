# ✅ Étape 4 — Évaluation Finale & IA de Confiance

Objectif : Prouver la robustesse, la fiabilité et l'explicabilité du modèle.

```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import (confusion_matrix, classification_report, accuracy_score, 
                             r2_score, mean_absolute_error, mean_squared_error, silhouette_score)

print("=" * 60)
print(f"✅ ÉVALUATION FINALE — {best_name}")
print("=" * 60)

best_model = results[best_name]["model"]
# Gestion hybride predict / fit_predict
if hasattr(best_model, "predict"):
    y_pred = best_model.predict(X_test_prep)
else:
    y_pred = best_model.fit_predict(X_test_prep)

# ── 4.1 Trajectoire : CLASSIFICATION ──────────────────────────────────
if TYPE_TACHE == "classification":
    from sklearn.calibration import CalibratedClassifierCV, CalibrationDisplay
    print("\n📊 Calibration des Probabilités...")
    try:
        calibrated_model = CalibratedClassifierCV(best_model, method='isotonic', cv='prefit')
        calibrated_model.fit(X_test_prep, y_test)
        fig, ax = plt.subplots(figsize=(8, 6))
        CalibrationDisplay.from_estimator(best_model, X_test_prep, y_test, name=best_name, ax=ax)
        plt.title("📈 Courbe de Calibration (Fiabilité)")
        plt.show()
    except Exception as e:
        print(f"⚠️ Calibration non supportée : {e}")

# ── 4.2 Trajectoire : NON-SUPERVISÉ (PROFILING) ───────────────────────
elif TYPE_TACHE == "unsupervised":
    print("\n📊 Profilage des Clusters (Senior Approach)")
    df_profile = pd.DataFrame(X_test_prep, columns=[f"f_{i}" for i in range(X_test_prep.shape[1])])
    df_profile['cluster'] = y_pred
    cluster_means = df_profile.groupby('cluster').mean()
    global_means  = df_profile.drop('cluster', axis=1).mean()
    diff_rel = (cluster_means - global_means) / (global_means + 1e-6) * 100
    print("🔥 Top features par cluster (Écart à la moyenne globale) :")
    display(diff_rel.T.style.background_gradient(cmap='RdYlGn'))

# ── 4.3 Métriques Standards ──────────────────────────────────────────
if TYPE_TACHE == "classification":
    print("\n📋 Rapport de Classification :")
    print(classification_report(y_test, y_pred))
elif TYPE_TACHE == "regression":
    print(f"📊 R² Score : {r2_score(y_test, y_pred):.4f}")
    print(f"📊 MAE      : {mean_absolute_error(y_test, y_pred):.2f}")

# ── 4.4 Interprétabilité (XAI) ────────────────────────────────────────
import shap
print("\n🧠 Analyse SHAP (Interprétabilité Globale)")
try:
    # On utilise un échantillon pour la rapidité
    X_sample = X_test_prep[:200]
    explainer = shap.Explainer(best_model, X_train_prep[:100])
    shap_values = explainer(X_sample)
    
    plt.figure(figsize=(10, 6))
    shap.summary_plot(shap_values, X_sample, show=False)
    plt.title("🌍 Importance Globale des Variables (SHAP)")
    plt.show()
except Exception as e:
    print(f"⚠️ SHAP non disponible pour ce modèle : {e}")

print("\n✅ ÉVALUATION SENIOR TERMINÉE")
```

## Rapport Final

```python
print("\n" + "=" * 60)
print(f"📋 RAPPORT FINAL — {NOM_BASE}")
print("=" * 60)
print(f"  Tâche : {TYPE_TACHE.upper()} | Modèle : {best_name}")
print("  📁 Sorties :", OUTPUT_DIR)
print("=" * 60)
```

## Rapport d'évaluation visuelle

{EVAL_PLOT}

