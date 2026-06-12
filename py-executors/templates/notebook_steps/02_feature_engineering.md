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

# Log-transformation (stabilité de la variance)
if (df[TARGET_COL] > 0).all():
    df[TARGET_COL + "_log"] = np.log1p(df[TARGET_COL])

# Box-Cox
try:
    from scipy.stats import boxcox
    if (df[TARGET_COL] > 0).all():
        df[TARGET_COL + "_boxcox"], lambda_param = boxcox(df[TARGET_COL])
        print(f"   ✅ Box-Cox appliqué (λ = {lambda_param:.4f})")
except:
    pass

# Features de lags & moyennes mobiles
for w in [7, 14, 30]:
    if w < len(df) // 3:
        df[TARGET_COL + "_lag_" + str(w)] = df[TARGET_COL].shift(w)
        df[TARGET_COL + "_roll_mean_" + str(w)] = df[TARGET_COL].rolling(window=w).mean()
        df[TARGET_COL + "_ewm_" + str(w)] = df[TARGET_COL].ewm(span=w, adjust=False).mean()

print(f"   ✅ {len([c for c in df.columns if 'lag' in c or 'roll' in c])} features de contexte créées")

# ── 2. Analyse de Stationnarité & Structure ──────────────────────
print("\n📊 2. Analyse de Stationnarité (ADF)")

try:
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
    
    series = df[TARGET_COL].dropna()
    adf_res = adfuller(series)
    p_val = adf_res[1]
    
    print(f"   📊 ADF Statistic: {adf_res[0]:.4f} (p-value: {p_val:.4f})")
    
    if p_val > 0.05:
        print("   ⚠️ Série NON-STATIONNAIRE → Différenciation d'ordre 1 requise")
        NEEDS_DIFF = True
        df_target_final = df[TARGET_COL].diff().dropna()
    else:
        print("   ✅ Série STATIONNAIRE")
        NEEDS_DIFF = False
        df_target_final = df[TARGET_COL]

    # Visualisation ACF/PACF
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 4))
    plot_acf(series, lags=min(40, len(series)//2), ax=ax1)
    plot_pacf(series, lags=min(40, len(series)//2), ax=ax2, method='ywm')
    plt.suptitle(f"Structure de Corrélation — {TARGET_COL}")
    plt.tight_layout()
    plt.show()

except Exception as e:
    print(f"   ⚠️ Diagnostic statsmodels limité : {str(e)[:60]}...")
    NEEDS_DIFF = True
    df_target_final = df[TARGET_COL].diff().dropna()
    
    from pandas.plotting import autocorrelation_plot
    plt.figure(figsize=(10, 4))
    autocorrelation_plot(df[TARGET_COL].dropna())
    plt.title("Autocorrélation (Fallback)")
    plt.show()

# ── 3. Features Cycliques ───────────────────────────────────────────
print("\n📊 3. Features Temporelles Cycliques")
if pd.api.types.is_datetime64_any_dtype(df.index):
    df['month_sin'] = np.sin(2 * np.pi * df.index.month / 12)
    df['month_cos'] = np.cos(2 * np.pi * df.index.month / 12)
    df['day_sin']   = np.sin(2 * np.pi * df.index.dayofweek / 7)
    df['day_cos']   = np.cos(2 * np.pi * df.index.dayofweek / 7)
    print("   ✅ Encodage Sin/Cos (Saisonnalité mensuelle/hebdomadaire)")

# ── 4. Finalisation & Scalage ──────────────────────────────────────
print("\n📊 4. Préparation finale (Train/Test Split)")
df_clean = df.dropna()

# Définition des features finales (on exclut la cible et les colonnes dérivées)
exclude_cols = [TARGET_COL, TARGET_COL + "_log", TARGET_COL + "_boxcox"]
features = [c for c in df_clean.columns if c not in exclude_cols]

split_idx = int(len(df_clean) * 0.85)
X_train, X_test = df_clean[features].iloc[:split_idx], df_clean[features].iloc[split_idx:]
y_train, y_test = df_clean[TARGET_COL].iloc[:split_idx], df_clean[TARGET_COL].iloc[split_idx:]

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
