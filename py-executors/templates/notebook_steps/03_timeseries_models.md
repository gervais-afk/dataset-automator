# 🏆 Benchmarking Modèles de Time Series (Forecasting)

Objectif : Comparer les baselines naïves, les modèles statistiques classiques (SARIMAX) et les modèles de Machine Learning (XGBoost/LightGBM) basés sur les variables de lag et les fenêtres glissantes.

```python
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error, mean_absolute_percentage_error
from xgboost import XGBRegressor
from lightgbm import LGBMRegressor
import warnings
warnings.filterwarnings("ignore")

print("=" * 60)
print("🏆 BENCHMARK MODÈLES DE FORECASTING")
print("=" * 60)

results = {}

# On s'assure que y_train et y_test sont au format Series avec index temporel
y_train_s = pd.Series(y_train) if not isinstance(y_train, pd.Series) else y_train
y_test_s = pd.Series(y_test) if not isinstance(y_test, pd.Series) else y_test

# ── 1. BASELINES NAÏVES ────────────────────────────────────────────────
print("\n📏 1. Calcul des Baselines Naïves...")

# A. Naive (Dernière valeur connue du Train)
y_pred_naive = pd.Series(y_train_s.iloc[-1], index=y_test_s.index)
mae_naive = mean_absolute_error(y_test_s, y_pred_naive)
results["Naive (Last Value)"] = {
    "score": mae_naive,
    "time_ms": 0.0,
    "model": y_pred_naive,
    "type": "Naive"
}
print(f"   ✅ Naive Predictor   | MAE: {mae_naive:.4f}")

# B. Seasonal Naive (Dernière période saisonnière, ex: 7 jours)
s_period = 7
if len(y_train_s) > s_period:
    # On décale la fin de la série de s_period
    y_pred_snaive = y_train_s.iloc[-len(y_test_s)-s_period : -s_period].values
    if len(y_pred_snaive) == len(y_test_s):
        mae_snaive = mean_absolute_error(y_test_s, y_pred_snaive)
        results["Seasonal Naive"] = {
            "score": mae_snaive,
            "time_ms": 0.0,
            "model": y_pred_snaive,
            "type": "Naive"
        }
        print(f"   ✅ Seasonal Naive    | MAE: {mae_snaive:.4f}")

# C. Rolling Mean (Moyenne glissante des 14 derniers points du Train)
w_size = 14
if len(y_train_s) > w_size:
    rolling_mean_val = y_train_s.iloc[-w_size:].mean()
    y_pred_roll = pd.Series(rolling_mean_val, index=y_test_s.index)
    mae_roll = mean_absolute_error(y_test_s, y_pred_roll)
    results["Rolling Mean"] = {
        "score": mae_roll,
        "time_ms": 0.0,
        "model": y_pred_roll,
        "type": "Naive"
    }
    print(f"   ✅ Rolling Mean ({w_size})  | MAE: {mae_roll:.4f}")


# ── 2. MODÈLE STATISTIQUE (SARIMAX) ────────────────────────────────────
print("\n🔬 2. Entraînement du Modèle Statistique (SARIMAX)...")
try:
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    t0 = time.time()
    
    # Configuration SARIMAX simple (1,1,1) pour rapidité de calcul
    model_sarima = SARIMAX(y_train_s, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0), enforce_stationarity=False, enforce_invertibility=False)
    fit_sarima = model_sarima.fit(disp=False)
    
    y_pred_sarima = fit_sarima.forecast(steps=len(y_test_s))
    mae_sarima = mean_absolute_error(y_test_s, y_pred_sarima)
    dt = (time.time() - t0) * 1000
    
    results["SARIMAX (1,1,1)"] = {
        "score": mae_sarima,
        "time_ms": dt,
        "model": fit_sarima,
        "type": "Stat"
    }
    print(f"   ✅ SARIMAX (1,1,1)   | MAE: {mae_sarima:.4f} | Latence: {dt:.1f}ms")
except Exception as e:
    print(f"   ⚠️ SARIMAX en erreur ou non supporté : {e}")


# ── 3. MODÈLES DE MACHINE LEARNING (ML) ────────────────────────────────
print("\n🚀 3. Entraînement des Modèles Machine Learning...")

ML_MODELS = {
    "XGBoost Regressor": XGBRegressor(n_estimators=100, learning_rate=0.08, max_depth=5, random_state=42),
    "LightGBM Regressor": LGBMRegressor(n_estimators=100, learning_rate=0.08, max_depth=5, verbose=-1, random_state=42)
}

for name, model in ML_MODELS.items():
    t0 = time.time()
    try:
        with mlflow.start_run(run_name=name.replace(" ", "_"), nested=True):
            model.fit(X_train_prep, y_train_s)
            y_pred_ml = model.predict(X_test_prep)
            mae_ml = mean_absolute_error(y_test_s, y_pred_ml)
            rmse_ml = np.sqrt(mean_squared_error(y_test_s, y_pred_ml))
            mape_ml = mean_absolute_percentage_error(y_test_s, y_pred_ml) * 100
            dt = (time.time() - t0) * 1000
            
            # Tracking MLflow
            mlflow.log_params(model.get_params())
            mlflow.log_metric("MAE", mae_ml)
            mlflow.log_metric("RMSE", rmse_ml)
            mlflow.log_metric("MAPE", mape_ml)
            mlflow.log_metric("latency_ms", dt)
            mlflow.sklearn.log_model(model, f"model_{name.replace(' ', '_')}")
            
            results[name] = {
                "score": mae_ml,
                "time_ms": dt,
                "model": model,
                "type": "ML"
            }
            print(f"   ✅ {name:<18} | MAE: {mae_ml:.4f} | Latence: {dt:.1f}ms")
    except Exception as e:
        print(f"   ❌ {name:<18} | Erreur: {e}")


# ── 4. CLASSEMENT ET SÉLECTION DU CHAMPION ─────────────────────────────
print("\n🏆 CLASSEMENT DES MODÈLES (Critère: MAE la plus basse) :")
print("-" * 60)
df_results = pd.DataFrame([
    {"Modèle": k, "MAE": v["score"], "Type": v["type"], "Latence (ms)": v["time_ms"]}
    for k, v in results.items()
]).sort_values("MAE")

display(df_results)

# Le meilleur modèle est celui avec le MAE minimal
best_name = df_results.iloc[0]["Modèle"]
print(f"\n🥇 Modèle champion retenu : {best_name}")

# Enregistrement pour l'étape d'évaluation finale
best_model = results[best_name]["model"]
metric = "mae"
```
