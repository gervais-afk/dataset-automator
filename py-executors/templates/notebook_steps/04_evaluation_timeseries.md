# ✅ Étape 4 — Évaluation TimeSeries Senior

## Objectif
Validation scientifique complète des prédictions temporelles :
- Graphique Réel vs Prédit avec bandes de confiance
- Analyse des résidus (Ljung-Box pour bruit blanc)
- QQ-Plot des résidus
- Métriques complètes : R², RMSE, MAE, MAPE

```python
import matplotlib.pyplot as plt
import numpy as np
from sklearn.metrics import r2_score, mean_squared_error, mean_absolute_error, mean_absolute_percentage_error

print("=" * 60)
print("✅ ÉVALUATION TIMESERIES SENIOR")
print("=" * 60)

# ── Récupération du meilleur modèle ──────────────────────────────────
import mlflow

if 'final_model' in globals() and final_model is not None:
    best_model = final_model
    best_name = "Final Model (Pseudo-Labeling)"
    model_type = "ML"
    print("Using final_model (with Pseudo-Labeling) for evaluation")
elif 'stacking_model' in globals():
    best_model = stacking_model
    best_name = "Stacking Model"
    model_type = "ML"
    print("Using stacking_model for evaluation")
else:
    best_result = results[best_name]
    model_type = best_result.get('type', 'ML')
    best_model = best_result['model']

# Check if model is fitted, if not, fit it
if model_type == "ML" and TYPE_TACHE == "timeseries":
    from sklearn.utils.validation import check_is_fitted
    from sklearn.exceptions import NotFittedError
    try:
        check_is_fitted(best_model)
    except NotFittedError:
        print(f"⏳ Fitting {best_name} on X_train_prep...")
        best_model.fit(X_train_prep, y_train)

# ── Prédictions selon le type de modèle ──────────────────────────────
if model_type == "ML":
    y_pred_final = best_model.predict(X_test_prep)
    y_actual = y_test
elif model_type == "Stat":
    # Récupérer la prédiction statistique
    if 'Auto-ARIMA' in best_name:
        y_pred_final = best_result['model'].predict(n_periods=len(y_test))
        y_actual = y_test
    elif 'Prophet' in best_name:
        y_pred_final = y_pred_p
        y_actual = y_test
    else:
        y_pred_final = best_result['model'].forecast(len(y_test))
        y_actual = y_test
else:
    if hasattr(best_model, "predict"):
        y_pred_final = best_model.predict(X_test_prep)
    else:
        y_pred_final = best_model
    y_actual = y_test

# ── Métriques complètes ──────────────────────────────────────────────
y_act_arr = y_actual.values if hasattr(y_actual, 'values') else np.array(y_actual)
y_pred_arr = np.array(y_pred_final)

r2_final   = r2_score(y_act_arr, y_pred_arr)
rmse_final = np.sqrt(mean_squared_error(y_act_arr, y_pred_arr))
mae_final  = mean_absolute_error(y_act_arr, y_pred_arr)
mape_final = mean_absolute_percentage_error(y_act_arr, y_pred_arr) * 100
residus    = y_act_arr - y_pred_arr

# Enregistrement du modèle champion et de ses métriques dans MLflow
with mlflow.start_run(run_name=f"Champion_{best_name.replace(' ', '_')}", nested=True):
    mlflow.log_metric("final_R2", r2_final)
    mlflow.log_metric("final_RMSE", rmse_final)
    mlflow.log_metric("final_MAE", mae_final)
    mlflow.log_metric("final_MAPE", mape_final)
    mlflow.sklearn.log_model(best_model, "model_champion")

# Enregistrement du modèle champion et de ses métriques pour le rapport d'étape
if best_name not in results:
    results[best_name] = {}
results[best_name]['score'] = mae_final if metric == 'mae' else r2_final
results[best_name]['model'] = best_model
results[best_name]['type'] = 'ML'

print(f"\n📊 MÉTRIQUES FINALES — {best_name}")
print(f"   R²    : {r2_final:.4f}")
print(f"   RMSE  : {rmse_final:,.2f}")
print(f"   MAE   : {mae_final:,.2f}")
print(f"   MAPE  : {mape_final:.2f}%")
```

## Visualisation Prédiction vs Réel

```python
# ── Graphique principal ───────────────────────────────────────────────
fig, axes = plt.subplots(3, 1, figsize=(16, 14))

# 1. Prédiction vs Réel
idx = y_actual.index if hasattr(y_actual, 'index') else range(len(y_actual))
axes[0].plot(idx, y_act_arr, label="Réel", color="steelblue", alpha=0.8, lw=1.5)
axes[0].plot(idx, y_pred_arr, label="Prédiction", color="orange", linestyle="--", lw=1.5)
axes[0].fill_between(idx, y_pred_arr - 1.96*residus.std(), y_pred_arr + 1.96*residus.std(),
                     alpha=0.15, color='orange', label='IC 95%')
axes[0].set_title(f'📈 {best_name} — Prédiction vs Réel (R²={r2_final:.4f})')
axes[0].legend()
axes[0].grid(True, alpha=0.3)

# 2. Résidus dans le temps
axes[1].plot(idx, residus, color='#e74c3c', alpha=0.7, lw=1)
axes[1].axhline(0, color='black', linestyle='--', lw=1)
axes[1].axhline(2*residus.std(), color='gray', linestyle=':', label='+2σ')
axes[1].axhline(-2*residus.std(), color='gray', linestyle=':', label='-2σ')
axes[1].set_title('📊 Résidus dans le Temps')
axes[1].legend()
axes[1].grid(True, alpha=0.3)

# 3. Distribution des résidus
axes[2].hist(residus, bins=40, density=True, alpha=0.7, color='steelblue', edgecolor='white')
from scipy.stats import norm
x_norm = np.linspace(residus.min(), residus.max(), 100)
axes[2].plot(x_norm, norm.pdf(x_norm, residus.mean(), residus.std()), 'r-', lw=2, label='Normale')
axes[2].set_title(f'📊 Distribution des Résidus (μ={residus.mean():.2f}, σ={residus.std():.2f})')
axes[2].legend()

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '04_ts_evaluation.png'), dpi=150, bbox_inches='tight')
plt.show()
```

## Diagnostic Résidus — Ljung-Box (Bruit Blanc)

```python
# ── Test de Ljung-Box : les résidus sont-ils du bruit blanc ? ────────
print("\n🔬 DIAGNOSTIC DES RÉSIDUS (Validation Scientifique)")
print("=" * 55)

# Shapiro-Wilk pour la normalité
from scipy.stats import shapiro
sample_res = residus[:5000] if len(residus) > 5000 else residus
sw_stat, sw_p = shapiro(sample_res)
print(f"\n📊 Shapiro-Wilk (Normalité des résidus)")
print(f"   p-value : {sw_p:.6f}")
print(f"   {'✅ Résidus NORMAUX' if sw_p > 0.05 else '❌ Résidus NON normaux'}")

# Ljung-Box avec Fallback Autocorrelation Plot
try:
    from statsmodels.stats.diagnostic import acorr_ljungbox
    n_lags_test = min(20, len(residus) // 5)
    lb_result = acorr_ljungbox(residus, lags=n_lags_test, return_df=True)
    
    all_white_noise = (lb_result['lb_pvalue'] > 0.05).all()
    print(f"\n📊 Test de Ljung-Box (p-value min: {lb_result['lb_pvalue'].min():.6f})")
    print(f"   {'✅ BRUIT BLANC' if all_white_noise else '⚠️ Auto-corrélation résiduelle détectée'}")
except Exception as e:
    print(f"\n⚠️ Ljung-Box échoué : {str(e)[:80]}")
    print("   💡 Fallback : Vérification visuelle via ACF plot")
    from pandas.plotting import autocorrelation_plot
    autocorrelation_plot(pd.Series(residus))
    plt.title("Autocorrélation des Résidus (Fallback)")
    plt.show()

# ── Residual Lag Plot (Autocorrelation visuelle) ─────────────────────
try:
    print("\n📊 Tracé du Residual Lag Plot (Autocorrélation d'ordre 1)...")
    fig, ax = plt.subplots(figsize=(6, 5))
    ax.scatter(residus[:-1], residus[1:], alpha=0.5, color='purple')
    ax.axhline(0, color='black', linestyle='--', lw=1)
    ax.axvline(0, color='black', linestyle='--', lw=1)
    ax.set_xlabel("Résidus à l'instant t")
    ax.set_ylabel("Résidus à l'instant t+1")
    ax.set_title('Residual Lag Plot (t vs t+1)')
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '04_ts_residual_lag.png'), dpi=120, bbox_inches='tight')
    plt.show()
except Exception as e_lag:
    print(f"⚠️ Impossible de tracer le residual lag plot : {e_lag}")

# SHAP — Interprétabilité Locale (si ML)
if model_type == "ML":
    print("\n🔍 EXPLICATION SHAP (Local Interpretability)")
    try:
        import shap
        # On utilise KernelExplainer ou TreeExplainer selon le modèle
        sample_X = X_test_prep[:50]
        if 'RandomForest' in best_name or 'GradientBoosting' in best_name:
            explainer = shap.TreeExplainer(best_model)
            shap_v = explainer.shap_values(sample_X)
        else:
            explainer = shap.LinearExplainer(best_model, X_train_prep[:100])
            shap_v = explainer.shap_values(sample_X)
        
        shap.summary_plot(shap_v, sample_X, feature_names=FEATURE_NAMES, plot_type="bar")
    except:
        print("   ℹ️ SHAP non configuré ou non installé.")

# ── Résumé Final ──────────────────────────────────────────────────────
print(f"\n📊 RÉSUMÉ FINAL")
print(f"   Champion     : {best_name}")
print(f"   R² Score     : {r2_final:.4f}")
print(f"   RMSE         : {rmse_final:,.2f}")
print(f"   MAPE         : {mape_final:.2f}%")

# ── 4.5 Diagnostics du Data Scientist Senior (Automatisés)
print("\n" + "=" * 60)
print("🧠 DIAGNOSTICS DE ROBUSTESSE (SENIOR DATA SCIENCE AUDIT)")
print("=" * 60)
from scipy.stats import skew
from statsmodels.stats.stattools import durbin_watson

skewness_val = skew(residus)
dw = durbin_watson(residus)

print(f"✅ Erreurs - Asymétrie (Skewness) : {skewness_val:.4f} | Durbin-Watson : {dw:.2f}")

if r2_final < 0.4:
    print("   🚨 ALERTE PERFORMANCE : Le pouvoir prédictif R² est faible.")
    print("   → Recommandation : Intégrer de nouvelles variables exogènes, revoir le feature engineering ou changer d'algorithme.")
if abs(skewness_val) > 1.5:
    print("   🚨 ALERTE ASYMÉTRIE : Les erreurs de prédiction ont une asymétrie marquée (non gausienne).")
    print("   → Recommandation : Appliquer une transformation non-linéaire (ex: log(1+x)) sur la cible ou utiliser une perte robuste (Huber / MAE).")
if dw < 1.5 or dw > 2.5:
    print(f"   🚨 ALERTE AUTOCORRÉLATION ({dw:.2f}) : Les résidus montrent une corrélation sérielle significative.")
    print("   → Recommandation : Ajouter des variables auto-régressives (lags) ou des variables de tendance (indice temporel, jours).")
```

## Rapport d'évaluation visuelle

{EVAL_PLOT}

## 🧠 Rapport d'Interprétation Qualitatif RAG (Agent IA Senior)

{LLM_INTERPRETATION}

