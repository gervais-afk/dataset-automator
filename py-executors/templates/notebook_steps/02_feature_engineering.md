# 🔧 Étape 2 — Feature Engineering TimeSeries (Senior)

## Objectif
Préparation avancée pour la modélisation :
- **Transformations non-linéaires** (Log, Box-Cox)
- **Stationnarisation intelligente** (ADF + Différenciation)
- **Analyse de Structure** (ACF/PACF)
- **Features Cycliques & Fenêtrées** (Lags, EWM)

```python
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt

print("🔧 FEATURE ENGINEERING TIMESERIES (Senior)")
print("=" * 60)

# Note: TARGET_COL est déjà défini et potentiellement auto-détecté dans le setup.
NEEDS_DIFF = False

# ── 1. Transformations & Statistics ───────────────────────────
print("📊 1. Transformations & Statistics")

# Utilisation des partitions nettoyées (Anti-Leakage)
if 'train_df_clean' in globals():
    train_df_cleaned = train_df_clean.copy()
    test_df_cleaned  = test_df_clean.copy()
else:
    # Fallback si exécuté en dehors du workflow orchestrateur
    split_idx = int(len(df_clean) * 0.8)
    train_df_cleaned = df_clean.iloc[:split_idx].copy()
    test_df_cleaned  = df_clean.iloc[split_idx:].copy()

def generate_features(df_partition, is_train=True):
    df_out = df_partition.copy()
    
    # Log-transformation (stabilité de la variance)
    if TARGET_COL in df_out.columns:
        df_out[TARGET_COL + "_log"] = np.log1p(df_out[TARGET_COL].clip(lower=0))
        
    # Features de lags & moyennes mobiles
    for w in [7, 14, 30]:
        df_out[TARGET_COL + "_lag_" + str(w)] = df_out[TARGET_COL].shift(w)
        df_out[TARGET_COL + "_roll_mean_" + str(w)] = df_out[TARGET_COL].shift(1).rolling(window=w).mean()
        df_out[TARGET_COL + "_ewm_" + str(w)] = df_out[TARGET_COL].shift(1).ewm(span=w, adjust=False).mean()
        
    # Features Temporelles Cycliques
    if pd.api.types.is_datetime64_any_dtype(df_out.index):
        df_out['month_sin'] = np.sin(2 * np.pi * df_out.index.month / 12)
        df_out['month_cos'] = np.cos(2 * np.pi * df_out.index.month / 12)
        df_out['day_sin']   = np.sin(2 * np.pi * df_out.index.dayofweek / 7)
        df_out['day_cos']   = np.cos(2 * np.pi * df_out.index.dayofweek / 7)
        
    return df_out

# ── 2. Application indépendante sur les partitions ──
print("⚙️  Génération des features sur les partitions...")
train_fe = generate_features(train_df_cleaned, is_train=True).dropna()

# Pour le test, on prépend la fin du train afin de ne pas perdre de lignes au début à cause des lags
warmup_size = 30
combined_test_raw = pd.concat([train_df_cleaned.tail(warmup_size), test_df_cleaned])
test_fe = generate_features(combined_test_raw, is_train=False).iloc[warmup_size:].dropna()

# ── 3. Analyse de Stationnarité (ADF) sur la cible d'entraînement ──
print("\n📊 2. Analyse de Stationnarité (ADF)")
try:
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    
    series_train = train_fe[TARGET_COL].dropna()
    adf_res = adfuller(series_train)
    p_val = adf_res[1]
    
    print(f"   📊 ADF Statistic: {adf_res[0]:.4f} (p-value: {p_val:.4f})")
    
    if p_val > 0.05:
        print("   ⚠️ Série NON-STATIONNAIRE → Différenciation d'ordre 1 requise")
        NEEDS_DIFF = True
        df_target_final = train_fe[TARGET_COL].diff().dropna()
    else:
        print("   ✅ Série STATIONNAIRE")
        NEEDS_DIFF = False
        df_target_final = train_fe[TARGET_COL]

    # Visualisation ACF/PACF sur train uniquement
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4))
    plot_acf(series_train, lags=min(40, len(series_train)//2), ax=ax1)
    plot_pacf(series_train, lags=min(40, len(series_train)//2), ax=ax2, method='ywm')
    plt.suptitle(f"Structure de Corrélation — {TARGET_COL}")
    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"   ⚠️ Diagnostic statsmodels limité : {str(e)[:60]}...")
    NEEDS_DIFF = True
    
    from pandas.plotting import autocorrelation_plot
    plt.figure(figsize=(10, 4))
    autocorrelation_plot(train_fe[TARGET_COL].dropna())
    plt.title("Autocorrélation (Fallback)")
    plt.show()

# ── 4. Finalisation & Scalage ──────────────────────────────────────
print("\n📊 3. Préparation finale (Scaling et Train/Test Split)")

# Définition des features finales (on exclut la cible et les colonnes dérivées)
exclude_cols = [TARGET_COL, TARGET_COL + "_log", TARGET_COL + "_boxcox"]
features = [c for c in train_fe.columns if c not in exclude_cols]

X_train, y_train = train_fe[features], train_fe[TARGET_COL]
X_test, y_test   = test_fe[features], test_fe[TARGET_COL]

from sklearn.preprocessing import RobustScaler
scaler = RobustScaler()
X_train_prep = scaler.fit_transform(X_train)
X_test_prep  = scaler.transform(X_test)
FEATURE_NAMES = list(X_train.columns)

print(f"   ✅ Split : {len(X_train)} train / {len(X_test)} test")
print(f"   ✅ Features : {len(FEATURE_NAMES)} colonnes")

print("\n" + "="*60)
print("✅ FEATURE ENGINEERING TERMINÉ")
print("="*60)
```
