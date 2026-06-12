# 🔍 Étape 1 — Analyse Exploratoire Senior (EDA)

> ⚠️ Toute l'analyse est faite sur **X_train uniquement** (ou df complet pour TS) 
> pour éviter la contamination du test set (Data Leakage).

## 1.1 Audit Qualité & Diagnostic des Données Manquantes (MCAR/MAR/MNAR)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configuration graphique premium
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

IS_TS = globals().get('TYPE_TACHE', '').lower() == 'timeseries'

print("📊 1. Diagnostic des Valeurs Manquantes")
print("=" * 60)

missing_pct = df.isnull().mean() * 100
missing_cols = missing_pct[missing_pct > 0].sort_values(ascending=False)

if not missing_cols.empty:
    print(f"⚠️ {len(missing_cols)} variables ont des valeurs manquantes.")
    for col, pct in missing_cols.items():
        print(f"   - {col}: {pct:.1f}%")
    
    # Diagnostic Senior : Analyse de la nature du manque
    print("\n🔬 Analyse Statistique du Manque (MCAR vs MNAR) :")
    for col in missing_cols.index[:3]: # On analyse les 3 plus critiques
        # On compare la distribution des autres variables quand col est présent vs absent
        # (Simple indicateur de MAR)
        print(f"   🔎 Variable: {col}")
        indicator = df[col].isnull().astype(int)
        numeric_cols = df.select_dtypes(include=[np.number]).columns.drop([col]) if col in df.columns else df.select_dtypes(include=[np.number]).columns
        if not numeric_cols.empty:
            corr_with_missing = df[numeric_cols].corrwith(indicator).abs().sort_values(ascending=False).head(2)
            if corr_with_missing.max() > 0.2:
                print(f"      🚨 Suspicion de MAR : Corrélation détectée avec {corr_with_missing.index.tolist()}")
            else:
                print("      ✅ Probablement MCAR ou MNAR (pas de corrélation évidente avec les autres variables)")
else:
    print("✅ Aucune valeur manquante détectée.")

# Visualisation des manques (Matrix)
if not missing_cols.empty:
    import missingno as msno
    plt.figure(figsize=(10, 4))
    msno.matrix(df, sparkline=False, color=(0.1, 0.4, 0.6))
    plt.title("🔥 Matrice de nullité (Patterns de manques)")
    plt.show()
```

## 1.2 Diagnostic de Structure & Variance (Senior Focus)

```python
print("\n📊 2. Diagnostic de Variance & Structure")
print("=" * 60)
# Les variables à variance nulle ou quasi-nulle n'aident pas à séparer les données (surtout en Clustering)
variances = df.var(numeric_only=True).sort_values()
low_variance_cols = variances[variances < 0.01].index.tolist()

if low_variance_cols:
    print(f"⚠️ Variables à faible variance détectées : {low_variance_cols}")
    print("👉 Conseil : Ces variables pourraient être supprimées car elles n'apportent pas de pouvoir discriminant.")
else:
    print("✅ Toutes les variables numériques présentent une variance significative.")

# ── Analyse des Corrélations ──────────────────────────────────────
print("\n🔗 3. Analyse des Corrélations (Multicolinéarité)")
corr_matrix = df.corr(numeric_only=True).abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]

if to_drop:
    print(f"⚠️ Variables fortement corrélées (>0.95) : {to_drop}")
    print("👉 En non-supervisé, des variables trop corrélées comptent 'double' dans le calcul des distances.")
else:
    print("✅ Pas de multicolinéarité extrême détectée.")
```

## 1.3 Analyse Univariée (Distributions & Outliers)

```python
print("\n📊 2. Analyse Univariée & Outliers")
print("-" * 60)

num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
top_num = num_cols[:min(6, len(num_cols))]

fig, axes = plt.subplots(len(top_num), 2, figsize=(15, 4 * len(top_num)))
for i, col in enumerate(top_num):
    # Distribution & Skewness
    sns.histplot(df[col], kde=True, ax=axes[i, 0], color='steelblue')
    skew = df[col].skew()
    axes[i, 0].set_title(f"Distribution de {col} (Skewness: {skew:.2f})")
    
    # Boxplot pour Outliers
    sns.boxplot(x=df[col], ax=axes[i, 1], color='coral')
    axes[i, 1].set_title(f"Boxplot de {col} (Valeurs aberrantes)")

plt.tight_layout()
plt.savefig(os.path.join(OUTPUT_DIR, '01_univariate_analysis.png'))
plt.show()
```

## 1.3 Étude des Corrélations & Multicolinéarité (VIF)

```python
print("\n📊 3. Étude des Corrélations (Pearson/Spearman)")
print("-" * 60)

try:
    # Pearson (Linéaire) vs Spearman (Monotone)
    corr_p = df.select_dtypes(include=np.number).corr(method='pearson')
    corr_s = df.select_dtypes(include=np.number).corr(method='spearman')
    
    # Détection de Multicolinéarité (VIF)
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    X_vif = df.select_dtypes(include=[np.number]).dropna()
    if X_vif.shape[1] > 1:
        vif_data = pd.DataFrame()
        vif_data["feature"] = X_vif.columns
        vif_data["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(len(X_vif.columns))]
        high_vif = vif_data[vif_data["VIF"] > 10]
        if not high_vif.empty:
            print("⚠️ Multicolinéarité détectée (VIF > 10) :")
            print(high_vif)
    
    # Heatmap
    plt.figure(figsize=(12, 10))
    mask = np.triu(np.ones_like(corr_p, dtype=bool))
    sns.heatmap(corr_p, mask=mask, annot=True, cmap='coolwarm', fmt='.2f')
    plt.title("🔥 Matrice de Corrélation de Pearson")
    plt.show()
except Exception as e:
    print(f"⚠️ Erreur corrélation/VIF : {e}")
```

## 1.4 Vérification des Biais (Bias Surface Mapping)

```python
print("\n📊 4. Analyse des Biais & Déséquilibres Éthiques")
print("-" * 60)

cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
if cat_cols:
    print(f"Variables catégorielles analysées : {cat_cols[:5]}")
    for col in cat_cols[:3]:
        counts = df[col].value_counts(normalize=True)
        imbalance = counts.max() / counts.min() if counts.min() > 0 else np.inf
        if imbalance > 10:
            print(f"⚠️ Déséquilibre fort sur '{col}' : Ratio max/min = {imbalance:.1f}")
            print(counts.head())
else:
    print("✅ Aucune variable catégorielle évidente pour l'étude des biais.")
```

## 1.5 Analyse de la Cible (Target Analysis)

```python
if TARGET_COL in df.columns:
    print(f"\n🎯 Analyse de la cible : {TARGET_COL}")
    if IS_TS:
        # Time Series Target
        plt.figure(figsize=(14, 5))
        df[TARGET_COL].plot(lw=1.5, color='steelblue')
        plt.title(f"📈 Évolution temporelle de {TARGET_COL}")
        plt.show()
    else:
        # Classification/Regression Target
        plt.figure(figsize=(10, 5))
        if df[TARGET_COL].dtype in [np.float64, np.int64]:
            sns.histplot(df[TARGET_COL], kde=True)
        else:
            sns.countplot(y=df[TARGET_COL])
        plt.title(f"📊 Distribution de la cible")
        plt.show()

print("\n✅ EDA SENIOR TERMINÉE")
```
