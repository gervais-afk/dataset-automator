# 🔍 Étape 1 — Analyse Exploratoire Senior (EDA) & Diagnostic de Qualité

> 💡 **Note MLOps** : Cette analyse exploratoire s'exécute sur le dataset pré-nettoyé par l'Orchestrateur MLOps. L'objectif de cette étape est de valider scientifiquement la conformité des transformations (imputations, encodages) appliquées par les agents avant de lancer l'entraînement des modèles. Un diagnostic sans valeurs manquantes (0% NaNs) valide le succès de la phase de nettoyage.

## 1.1 Diagnostic du Dataset : Valeurs Manquantes (Cellule 3)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Fallback si train_df_clean n'est pas défini (ex: exécution hors orchestrateur)
if 'train_df_clean' not in globals():
    train_df_clean = df.copy() if 'df' in globals() else df_raw.copy()

print("📊 1. Diagnostic des Valeurs Manquantes")
print("=" * 60)

missing_pct = train_df_clean.isnull().mean() * 100
missing_cols = missing_pct[missing_pct > 0].sort_values(ascending=False)

if not missing_cols.empty:
    print(f"⚠️ {len(missing_cols)} variables ont des valeurs manquantes.")
    for col, pct in missing_cols.items():
        print(f"   - {col}: {pct:.1f}%")
    
    # Diagnostic Senior : Analyse de la nature du manque
    print("\n🔬 Analyse Statistique du Manque (MCAR vs MNAR) :")
    for col in missing_cols.index[:3]:
        print(f"   🔎 Variable: {col}")
        indicator = train_df_clean[col].isnull().astype(int)
        numeric_cols = train_df_clean.select_dtypes(include=[np.number]).columns.drop([col], errors='ignore')
        if not numeric_cols.empty:
            corr_with_missing = train_df_clean[numeric_cols].corrwith(indicator).abs().sort_values(ascending=False).head(2)
            if corr_with_missing.max() > 0.2:
                print(f"      🚨 Suspicion de MAR : Corrélation détectée avec {corr_with_missing.index.tolist()}")
            else:
                print("      ✅ Probablement MCAR ou MNAR (pas de corrélation évidente avec les autres variables)")
else:
    print("✅ Aucune valeur manquante détectée dans le dataset nettoyé.")

# Recherche du fichier brut d'origine pour comparer les manques
try:
    raw_path_possibilities = [
        os.path.join("..", "..", "data", f"{DATASET_NAME}.csv"),
        os.path.join("..", "..", "data", "raw", f"{DATASET_NAME}.csv"),
        os.path.join("C:/Users/HP/cam_data_sov_solutions newversion/data", f"{DATASET_NAME}.csv"),
    ]
    raw_file = None
    for p in raw_path_possibilities:
        if os.path.exists(p):
            raw_file = p
            break
            
    if raw_file:
        df_raw_original = pd.read_csv(raw_file)
        print("\n🔄 Comparaison avec les données brutes d'origine :")
        print(f"   - Fichier brut d'origine : {os.path.basename(raw_file)}")
        print(f"   - Rows : {len(df_raw_original)} | Columns : {len(df_raw_original.columns)}")
        
        # Compter les NaNs d'origine
        nans_original = df_raw_original.isnull().sum()
        total_nans = nans_original.sum()
        if total_nans > 0:
            print(f"   - Total de valeurs manquantes réparées par l'orchestrateur : {total_nans}")
            for col, count in nans_original[nans_original > 0].items():
                print(f"     * Variable '{col}' : {count} NaNs réparés ({count/len(df_raw_original)*100:.1f}%)")
        else:
            print("   - Le fichier brut d'origine ne contenait aucune valeur manquante.")
except Exception as raw_err:
    pass

# Visualisation des manques (Matrix)
if not missing_cols.empty:
    try:
        import missingno as msno
        plt.figure(figsize=(10, 4))
        msno.matrix(train_df_clean, sparkline=False, color=(0.1, 0.4, 0.6))
        plt.title("🔥 Matrice de nullité (Patterns de manques)")
        plt.show()
    except Exception as e:
        print(f"⚠️ Impossible de tracer la matrice de nullité : {e}")
```

## 1.2 Diagnostic de Structure & Variance (Cellule 4)

```python
print("\n📊 2. Diagnostic de Variance & Structure")
print("=" * 60)

# Les variables à variance nulle ou quasi-nulle
variances = train_df_clean.var(numeric_only=True).sort_values()
low_variance_cols = variances[variances < 0.01].index.tolist()

if low_variance_cols:
    print(f"⚠️ Variables à faible variance détectées : {low_variance_cols}")
    print("👉 Conseil : Ces variables pourraient être supprimées car elles n'apportent pas de pouvoir discriminant.")
else:
    print("✅ Toutes les variables numériques présentent une variance significative.")

# ── Analyse des Corrélations ──────────────────────────────────────
print("\n🔗 3. Analyse des Corrélations (Multicolinéarité)")
corr_matrix = train_df_clean.corr(numeric_only=True).abs()
upper = corr_matrix.where(np.triu(np.ones(corr_matrix.shape), k=1).astype(bool))
to_drop = [column for column in upper.columns if any(upper[column] > 0.95)]

if to_drop:
    print(f"⚠️ Variables fortement corrélées (>0.95) : {to_drop}")
else:
    print("✅ Pas de multicolinéarité extrême détectée.")

if TYPE_TACHE == "unsupervised":
    print("\n⚠️ AVERTISSEMENT CLUSTERING :")
    print("👉 Les algorithmes basés sur les distances sont extrêmement sensibles aux échelles des variables.")
    print("👉 Un scaling (ex: RobustScaler / StandardScaler) est OBLIGATOIRE avant l'entraînement.")
```

## 1.3 Analyse Univariée (Cellule 5)

```python
print("\n📊 2. Analyse Univariée & Outliers")
print("-" * 60)

num_cols = train_df_clean.select_dtypes(include=[np.number]).columns.tolist()
top_num = num_cols[:min(6, len(num_cols))]

if top_num:
    fig, axes = plt.subplots(len(top_num), 2, figsize=(15, 4 * len(top_num)))
    if len(top_num) == 1:
        axes = axes.reshape(1, 2)
    for i, col in enumerate(top_num):
        # Distribution & Skewness
        sns.histplot(train_df_clean[col], kde=True, ax=axes[i, 0], color='steelblue')
        skew = train_df_clean[col].skew()
        axes[i, 0].set_title(f"Distribution de {col} (Skewness: {skew:.2f})")
        
        # Boxplot pour Outliers
        sns.boxplot(x=train_df_clean[col], ax=axes[i, 1], color='coral')
        axes[i, 1].set_title(f"Boxplot de {col} (Valeurs aberrantes)")
        
        # Calcul d'interprétation dynamique
        q1 = train_df_clean[col].quantile(0.25)
        q3 = train_df_clean[col].quantile(0.75)
        iqr = q3 - q1
        outliers = train_df_clean[(train_df_clean[col] < q1 - 1.5 * iqr) | (train_df_clean[col] > q3 + 1.5 * iqr)]
        outliers_pct = (len(outliers) / len(train_df_clean)) * 100
        
        print(f"🔎 Variable '{col}' :")
        print(f"   - Asymétrie (Skewness) : {skew:.2f} ({'Forte asymétrie' if abs(skew) > 1 else 'Distribution équilibrée'})")
        print(f"   - Valeurs aberrantes (Outliers) : {outliers_pct:.1f}% de lignes concernées")
        if outliers_pct > 5:
            print(f"     💡 Recommandation : Les outliers (>5%) suggèrent d'utiliser des modèles robustes (arbre de décision) ou un traitement spécifique.")

    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, '01_univariate_analysis.png'))
    plt.show()
else:
    print("⚠️ Aucune variable numérique à analyser.")
```

## 1.4 Corrélations Avancées & VIF (Cellule 6)

```python
print("\n📊 3. Étude des Corrélations (Pearson/Spearman)")
print("-" * 60)

try:
    num_df = train_df_clean.select_dtypes(include=np.number)
    
    if num_df.shape[1] <= 1:
        print("💡 Peu de variables numériques. Encodage temporaire des variables catégorielles.")
        df_encoded = train_df_clean.copy()
        cat_cols = df_encoded.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols:
            df_encoded[col] = df_encoded[col].astype('category').cat.codes
        corr_p = df_encoded.corr(method='pearson')
        corr_s = df_encoded.corr(method='spearman')
        is_mixed = True
    else:
        corr_p = num_df.corr(method='pearson')
        corr_s = num_df.corr(method='spearman')
        is_mixed = False
        
    # Détection de Multicolinéarité (VIF)
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    X_vif = train_df_clean.select_dtypes(include=[np.number]).dropna()
    if X_vif.shape[1] > 1:
        vif_data = pd.DataFrame()
        vif_data["feature"] = X_vif.columns
        vif_data["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(len(X_vif.columns))]
        high_vif = vif_data[vif_data["VIF"] > 10]
        if not high_vif.empty:
            print("⚠️ Multicolinéarité détectée (VIF > 10) :")
            print(high_vif)
            print("\n🔎 Interprétation Multicollinéarité :")
            print(f"   La multicolinéarité est critique pour les variables: {high_vif['feature'].tolist()}.")
            print("   💡 Recommandation : Ces variables redondantes doivent être réduites (PCA/UMAP) ou certaines exclues pour éviter d'altérer la stabilité des coefficients et l'interprétation SHAP.")
    
    if corr_p.shape[1] <= 1:
        print("✅ Pas assez de variables pour tracer une matrice de corrélation.")
    else:
        plt.figure(figsize=(12, 10))
        mask = np.triu(np.ones_like(corr_p, dtype=bool))
        sns.heatmap(corr_p, mask=mask, annot=True, cmap='coolwarm', fmt='.2f')
        title_suffix = " (avec variables catégorielles encodées)" if is_mixed else ""
        plt.title(f"🔥 Matrice de Corrélation de Pearson{title_suffix}")
        plt.show()
except Exception as e:
    print(f"⚠️ Erreur corrélation/VIF : {e}")
```

## 1.5 Tests de Signification Statistique (Chi-Carré & ANOVA) (Cellule 6b)

```python
print("\n📊 3b. Tests de Signification Statistique (Chi-Carré & ANOVA)")
print("-" * 60)

try:
    import scipy.stats as stats
    
    # 1. Test du Chi-carré pour l'indépendance des variables catégorielles
    cat_cols_test = train_df_clean.select_dtypes(include=['object', 'category', 'bool']).columns.tolist()
    if len(cat_cols_test) >= 2:
        print("🎲 Test du Chi-carré d'indépendance sur les variables catégorielles :")
        col1, col2 = cat_cols_test[0], cat_cols_test[1]
        contingency_table = pd.crosstab(train_df_clean[col1], train_df_clean[col2])
        chi2, p_val, dof, expected = stats.chi2_contingency(contingency_table)
        print(f"   - Croisement : '{col1}' et '{col2}'")
        print(f"   - Statistique Chi-carré : {chi2:.2f} | p-value : {p_val:.4e}")
        if p_val < 0.05:
            print("   👉 Interprétation : Rejet de H0 (Alpha = 0.05). Il existe une relation statistiquement significative entre ces variables.")
        else:
            print("   👉 Interprétation : Échec du rejet de H0 (Alpha = 0.05). Les variables semblent indépendantes.")
    else:
        print("   ℹ️ Pas assez de variables catégorielles pour le test du Chi-carré d'indépendance.")

    # 2. Test ANOVA (Analyse de la Variance)
    num_cols_test = train_df_clean.select_dtypes(include=[np.number]).columns.tolist()
    if num_cols_test and cat_cols_test:
        target_num = num_cols_test[0]
        group_cat = cat_cols_test[0]
        print(f"\n🎲 Test ANOVA pour comparer la moyenne de '{target_num}' selon les groupes de '{group_cat}' :")
        
        # Séparer en groupes
        groups = [group[target_num].dropna().values for name, group in train_df_clean.groupby(group_cat)]
        if len(groups) > 1 and all(len(g) > 0 for g in groups):
            f_stat, p_val = stats.f_oneway(*groups)
            print(f"   - Variable continue : '{target_num}' | Groupement : '{group_cat}'")
            print(f"   - Statistique F : {f_stat:.2f} | p-value : {p_val:.4e}")
            if p_val < 0.05:
                print("   👉 Interprétation : Rejet de H0 (Alpha = 0.05). Les moyennes des différents groupes sont significativement différentes.")
            else:
                print("   👉 Interprétation : Échec du rejet de H0 (Alpha = 0.05). Pas de différence de moyennes statistiquement significative.")
        else:
            print("   ℹ️ Données insuffisantes pour exécuter le test ANOVA.")
    else:
        print("   ℹ️ Variables requises manquantes pour exécuter le test ANOVA.")
except Exception as e_stats:
    print(f"⚠️ Erreur lors des tests statistiques : {e_stats}")
```

## 1.6 Analyse Éthique & Biais (Cellule 7)

```python
print("\n📊 4. Analyse des Biais & Déséquilibres Éthiques")
print("-" * 60)

cat_cols = train_df_clean.select_dtypes(include=['object', 'category']).columns.tolist()
if cat_cols:
    print(f"Variables catégorielles analysées : {cat_cols[:5]}")
    for col in cat_cols[:3]:
        counts = train_df_clean[col].value_counts(normalize=True)
        imbalance = counts.max() / counts.min() if counts.min() > 0 else np.inf
        if imbalance > 10:
            print(f"⚠️ Déséquilibre fort sur '{col}' : Ratio max/min = {imbalance:.1f}")
            print(counts.head())
else:
    print("✅ Aucune variable catégorielle évidente pour l'étude des biais.")
```

## 1.7 Analyse de la Cible (Cellule 8)

```python
if 'y_train' in globals() and y_train is not None:
    print(f"\n🎯 Analyse de la cible : {TARGET_COL}")
    target_series = y_train
    if IS_TS:
        # Time Series Target
        plt.figure(figsize=(14, 5))
        target_series.plot(lw=1.5, color='steelblue')
        plt.title(f"📈 Évolution temporelle de {TARGET_COL}")
        plt.show()
    elif TYPE_TACHE == "regression" or (target_series.dtype in [np.float64, np.int64] and TYPE_TACHE != "classification"):
        # Regression Target Analysis
        from scipy import stats
        
        skewness = target_series.skew()
        kurt = target_series.kurtosis()
        
        print(f"   Moyenne  : {target_series.mean():.2f}")
        print(f"   Médiane  : {target_series.median():.2f}")
        print(f"   Skewness (Asymétrie) : {skewness:.3f}")
        print(f"   Kurtosis : {kurt:.3f}")
        
        if abs(skewness) > 1:
            print("   ⚠️ Variable cible asymétrique. Une transformation log ou Box-Cox sera appliquée dans le preprocessing.")
            
        fig, axes = plt.subplots(1, 3, figsize=(18, 5))
        
        # 1. Histogramme + KDE
        sns.histplot(target_series, kde=True, ax=axes[0], color='teal')
        axes[0].set_title(f'Distribution de {TARGET_COL}')
        
        # 2. Boxplot
        sns.boxplot(x=target_series, ax=axes[1], color='teal')
        axes[1].set_title(f'Boxplot de {TARGET_COL}')
        
        # 3. Q-Q Plot
        stats.probplot(target_series, dist="norm", plot=axes[2])
        axes[2].set_title('Normal Q-Q Plot')
        
        plt.tight_layout()
        plt.show()
    else:
        # Classification Target
        print(f"Distribution des classes :")
        counts = target_series.value_counts()
        pct = target_series.value_counts(normalize=True) * 100
        for val in counts.index:
            print(f"   - Classe '{val}' : {counts[val]} ({pct[val]:.1f}%)")
            
        fig, axes = plt.subplots(1, 2, figsize=(14, 5))
        target_series.value_counts().plot(kind='bar', ax=axes[0], color='skyblue')
        axes[0].set_title('Effectifs par classe')
        target_series.value_counts().plot(kind='pie', ax=axes[1], autopct='%1.1f%%', colors=sns.color_palette('pastel'))
        axes[1].set_title('Proportion des classes')
        plt.tight_layout()
        plt.show()
else:
    print("\n🎯 Mode non-supervisé / Clustering actif :")
    print("   -> Aucune variable cible (TARGET_COL) dans ce dataset.")
    print(f"   -> Nombre de variables descriptives à segmenter : {train_df_clean.shape[1]}")

# ── 1.8 Outils One-Line EDA (Interactive & High-Density) ───────────────
print("\n📊 6. Génération de Rapports d'EDA Automatique (Sweetviz / PyGwalker)")
print("=" * 60)

try:
    import sweetviz as sv
    # Génération d'un rapport interactif Sweetviz
    print("⚙️ Génération du rapport comparatif Sweetviz...")
    if 'X_train' in globals() and 'X_test' in globals():
        train_df_sv = X_train.copy()
        test_df_sv = X_test.copy()
        if TARGET_COL and TARGET_COL in df.columns:
            train_df_sv[TARGET_COL] = y_train
            test_df_sv[TARGET_COL] = y_test
        my_report = sv.compare([train_df_sv, "Train Set"], [test_df_sv, "Test Set"], target_feat=TARGET_COL if TARGET_COL else None)
    else:
        my_report = sv.analyze(train_df_clean, target_feat=TARGET_COL if TARGET_COL else None)
    
    # Sauvegarde du rapport HTML
    report_file = BASE_DIR / "EDA_Sweetviz_Report.html"
    my_report.show_html(filepath=str(report_file), open_browser=False)
    print(f"✅ Rapport Sweetviz généré avec succès à l'emplacement : {report_file}")
except Exception as e_sv:
    print(f"⚠️ Impossible de générer le rapport Sweetviz : {e_sv}")

try:
    import pygwalker as pyg
    print("\n📊 Initialisation de l'interface interactive Pygwalker (style Tableau)...")
    # Retourne un composant interactif dans les notebooks Jupyter
    walker = pyg.walk(train_df_clean)
except Exception as e_pyg:
    print(f"⚠️ PyGwalker non disponible ou erreur d'initialisation : {e_pyg}")

print("\n✅ EDA SENIOR ET VISUALISATION INTERACTIVE TERMINÉES")
```,StartLine:291,TargetContent:

```
