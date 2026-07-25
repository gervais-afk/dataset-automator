# 🏆 Modélisation des Séries Temporelles avec SARIMA (AutoARMA)

Objectif : Utiliser des modèles statistiques de pointe optimisés automatiquement pour capturer la cyclicité et la tendance du marché financier. Contrairement aux approches basiques, nous utilisons `statsforecast` et `AutoARMA` pour trouver la configuration optimale.

```python
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings("ignore")

# Installation automatique si non disponible
try:
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA
except ImportError:
    print("⏳ Installation de statsforecast...")
    !pip install -q statsforecast
    from statsforecast import StatsForecast
    from statsforecast.models import AutoARIMA

print("=" * 60)
print("🔬 MODÉLISATION TEMPORELLE AVEC AUTO-ARMA / SARIMA")
print("=" * 60)

results = {}

# S'assurer du format Pandas Series avec index temporel
y_train_s = pd.Series(y_train) if not isinstance(y_train, pd.Series) else y_train
y_test_s = pd.Series(y_test) if not isinstance(y_test, pd.Series) else y_test

# ── 1. BASELINES NAÏVES DE COMPARAISON ─────────────────────────────
print("\n📏 1. Calcul des Baselines Naïves...")

# Naive (Dernière valeur connue du Train)
y_pred_naive = pd.Series(y_train_s.iloc[-1], index=y_test_s.index)
mae_naive = mean_absolute_error(y_test_s, y_pred_naive)
results["Naive (Last Value)"] = {
    "score": mae_naive,
    "time_ms": 0.0,
    "model": y_pred_naive,
    "type": "Naive"
}
print(f"   ✅ Naive Predictor   | MAE: {mae_naive:.4f}")

# Seasonal Naive (Dernière période saisonnière de 7 jours)
s_period = 7
if len(y_train_s) > s_period:
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


# ── 2. MODÈLE AUTO-ARMA / SARIMA (StatsForecast) ───────────────────
print("\n🔬 2. Entraînement de StatsForecast AutoARMA (Optimisation Automatique)...")

# StatsForecast exige un format spécifique : unique_id, ds, y
train_sf = y_train_s.reset_index()
train_sf.columns = ['ds', 'y']
train_sf['unique_id'] = 'asset_1'

# Détecter la fréquence (par défaut quotidien 'D')
freq_detected = 'D'
if isinstance(y_train_s.index, pd.DatetimeIndex):
    inferred_freq = pd.infer_freq(y_train_s.index)
    if inferred_freq:
        freq_detected = inferred_freq
        print(f"   ℹ️ Fréquence temporelle détectée : {freq_detected}")

t0 = time.time()
try:
    # AutoARIMA cherche automatiquement les meilleurs paramètres (p, q) et gère la stationnarité en interne
    models = [AutoARIMA(season_length=7)]
    sf = StatsForecast(
        models=models,
        freq=freq_detected,
        n_jobs=-1
    )
    
    # Entraînement
    sf.fit(df=train_sf)
    dt = (time.time() - t0) * 1000
    
    # Prédiction pour l'horizon du jeu de test
    forecast_df = sf.predict(h=len(y_test_s))
    
    # Extraction de la prédiction AutoARIMA
    y_pred_sarima = forecast_df['AutoARIMA'].values
    mae_sarima = mean_absolute_error(y_test_s, y_pred_sarima)
    
    results["Auto-ARIMA (StatsForecast)"] = {
        "score": mae_sarima,
        "time_ms": dt,
        "model": sf,
        "predictions": y_pred_sarima,
        "type": "Stat"
    }
    print(f"   ✅ Auto-ARIMA        | MAE: {mae_sarima:.4f} | Latence: {dt:.1f}ms")
    
except Exception as e:
    print(f"   ❌ Erreur d'entraînement StatsForecast AutoARMA : {e}")
    # Fallback sur statsmodels classique si échec
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
        print("   💡 Utilisation du fallback Statsmodels SARIMAX(1,1,1)...")
        model_sarima = SARIMAX(y_train_s, order=(1, 1, 1), seasonal_order=(0, 0, 0, 0), enforce_stationarity=False)
        fit_sarima = model_sarima.fit(disp=False)
        y_pred_sarima = fit_sarima.forecast(steps=len(y_test_s))
        mae_sarima = mean_absolute_error(y_test_s, y_pred_sarima)
        results["Auto-ARIMA (StatsForecast)"] = {
            "score": mae_sarima,
            "time_ms": 0.0,
            "model": fit_sarima,
            "predictions": y_pred_sarima,
            "type": "Stat"
        }
        print(f"   ✅ SARIMAX Fallback  | MAE: {mae_sarima:.4f}")
    except Exception as e_fallback:
        print(f"   ❌ Fallback échoué : {e_fallback}")


# ── 3. CLASSEMENT ET SÉLECTION DU CHAMPION ─────────────────────────────
print("\n🏆 CLASSEMENT DES MODÈLES (Critère: MAE la plus basse) :")
print("-" * 60)
df_results = pd.DataFrame([
    {"Modèle": k, "MAE": v["score"], "Type": v["type"], "Latence (ms)": v["time_ms"]}
    for k, v in results.items()
]).sort_values("MAE")

display(df_results)

best_name = df_results.iloc[0]["Modèle"]
print(f"\n🥇 Modèle champion retenu : {best_name}")

best_model = results[best_name]["model"]
# Stockage des prédictions finales pour l'étape d'évaluation
y_pred_final = results[best_name].get("predictions", results[best_name]["model"])
metric = "mae"

# ── 4. BACKTESTING ROLLING-ORIGIN (ÉVALUATION ROBUSTE DE STABILITÉ) ──
print("\n🔄 4. Backtesting Rolling-Origin (Vérification de stabilité temporelle)...")
try:
    # On définit une fonction de backtest simple sur 3 fenêtres glissantes passées
    n_splits = 3
    horizon = len(y_test_s)
    
    # Formater les données pour statsforecast
    df_backtest = train_sf.copy()
    
    # Taille minimale d'entraînement initial (ex: 70% du train)
    initial_size = int(len(df_backtest) - (n_splits * horizon))
    
    backtest_metrics = []
    
    if initial_size > horizon:
        for i in range(n_splits):
            split_end = initial_size + (i * horizon)
            train_fold = df_backtest.iloc[:split_end]
            test_fold = df_backtest.iloc[split_end:split_end+horizon]
            
            # Entraîner StatsForecast
            sf_fold = StatsForecast(
                models=[AutoARIMA(season_length=7)],
                freq=freq_detected,
                n_jobs=-1
            )
            sf_fold.fit(df=train_fold)
            preds_fold = sf_fold.predict(h=len(test_fold))
            
            fold_mae = mean_absolute_error(test_fold['y'], preds_fold['AutoARIMA'])
            backtest_metrics.append({
                "Fold": i + 1,
                "Train Size": len(train_fold),
                "Test Size": len(test_fold),
                "MAE": fold_mae
            })
            
        df_bt = pd.DataFrame(backtest_metrics)
        print("📋 Résultats du Backtesting Temporel :")
        display(df_bt)
        
        # Log de la MAE moyenne de backtesting
        mean_bt_mae = df_bt["MAE"].mean()
        print(f"📊 MAE Moyenne sur les {n_splits} Folds : {mean_bt_mae:.4f}")
    else:
        print("   ⚠️ Dataset trop court pour un backtesting rolling-origin complet.")
except Exception as e_bt:
    print(f"   ⚠️ Échec du backtesting : {e_bt}")
```
