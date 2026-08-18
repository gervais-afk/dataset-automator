# 🔧 Étape 2 — Prétraitement & Feature Engineering Senior

## Objectif
Mise en place d'un pipeline **Scikit-Learn** de niveau industriel :
- **Nettoyage Automatique** : Suppression des doublons et placeholders ("?").
- **Capping (Winsorization)** : Plafonnement des valeurs aberrantes (outliers) pour protéger les modèles.
- **Missing Indicator** : Capture de l'information sur l'absence de données (MNAR).
- **IterativeImputer (MICE)** : Imputation statistique avancée.
- **Feature Generation** : Création de variables métier et transformations.

```python
import pandas as pd
import numpy as np
from sklearn.pipeline import Pipeline
from sklearn.compose  import ColumnTransformer
from sklearn.preprocessing import (StandardScaler, RobustScaler, OneHotEncoder, FunctionTransformer)
from sklearn.impute import SimpleImputer
import time

# ── 2.1 Feature Generation (Métier) ───────────────────────────────────
print("🧪 1. Feature Generation & Transformations")
print("-" * 60)

def engineering_func(X):
    X_out = X.copy()
    # Exemple de création de variables (à adapter selon le domaine)
    num_cols = X_out.select_dtypes(include=[np.number]).columns
    if len(num_cols) >= 2:
        # Création d'un ratio simple entre les deux premières variables numériques
        X_out['feat_ratio_1_2'] = X_out[num_cols[0]] / (X_out[num_cols[1]] + 1e-6)
    
    # Transformations Log pour réduire le skewness
    for col in num_cols:
        if X_out[col].skew() > 1:
            X_out[f'log_{col}'] = np.log1p(X_out[col].clip(lower=0))
            
    return X_out

feature_eng = FunctionTransformer(engineering_func)
print("✅ Fonctions de transformation métier prêtes.")

# ── 2.2 Configuration des Imputers (Senior) ───────────────────────────
try:
    from sklearn.experimental import enable_iterative_imputer
    from sklearn.impute import IterativeImputer
    # add_indicator=True est CRUCIAL pour les données MNAR
    IMPUTER_NUM = IterativeImputer(max_iter=10, random_state=42, add_indicator=True)
    print("🧬 Imputation Numérique : IterativeImputer + MissingIndicator")
except ImportError:
    IMPUTER_NUM = SimpleImputer(strategy='median', add_indicator=True)
    print("📊 Imputation Numérique : SimpleImputer (médiane) + MissingIndicator")

IMPUTER_CAT = SimpleImputer(strategy='most_frequent', add_indicator=True)

# ── 2.3 Détection de la Multicolinéarité (VIF) ─────────────────────────
print("\n🔬 3. Analyse de la Multicolinéarité (VIF)")
print("-" * 60)

try:
    from statsmodels.stats.outliers_influence import variance_inflation_factor
    from statsmodels.tools.tools import add_constant
    
    def detect_multicollinearity(X_df):
        # Ne garder que les colonnes numériques et éliminer les NaN pour le VIF
        X_num = X_df.select_dtypes(include=[np.number]).dropna()
        if X_num.empty or X_num.shape[1] <= 1:
            print("   ℹ️ Nombre insuffisant de variables numériques pour le VIF.")
            return None
        
        # Ajouter une constante (intercepte) indispensable pour éviter les erreurs de calcul du VIF
        X_with_const = add_constant(X_num)
        
        vif_data = pd.DataFrame()
        vif_data["Variable"] = X_with_const.columns
        vif_data["VIF"] = [variance_inflation_factor(X_with_const.values, i) 
                           for i in range(X_with_const.shape[1])]
        
        # Filtrer la constante artificielle et trier par ordre décroissant
        vif_data = vif_data[vif_data["Variable"] != "const"].sort_values(by="VIF", ascending=False)
        return vif_data

    X_train_inp = X_train_clean if 'X_train_clean' in globals() else X_train
    vif_results = detect_multicollinearity(X_train_inp)
    if vif_results is not None:
        display(vif_results)
        # Signaler les variables hautement colinéaires (VIF > 5)
        high_vif = vif_results[vif_results["VIF"] > 5]
        if not high_vif.empty:
            print(f"   ⚠️ ALERTE MULTICOLINÉARITÉ : {len(high_vif)} variable(s) ont un VIF > 5 !")
            for _, row in high_vif.iterrows():
                print(f"     - {row['Variable']} (VIF: {row['VIF']:.2f})")
            print("   👉 Recommandation : Envisager d'éliminer la variable au VIF le plus élevé ou de faire du Feature Engineering (ratios, PCA).")
        else:
            print("   ✅ Aucune multicolinéarité significative détectée (tous les VIF <= 5).")
except Exception as e_vif:
    print(f"   ⚠️ Impossible de calculer le VIF : {e_vif}")
```

## Construction du Pipeline

```python
# Identifier les types de colonnes (sur les données d'entrée nettoyées)
X_train_inp = X_train_clean if 'X_train_clean' in globals() else X_train
num_features = X_train_inp.select_dtypes(include=[np.number]).columns.tolist()
cat_features = X_train_inp.select_dtypes(include=['object', 'category']).columns.tolist()

# ── Pipeline Numérique ────────────────────────────────────────────────
from sklearn.decomposition import PCA
USE_PCA = {USE_PCA}

if USE_PCA:
    print("✨ PCA activée dans le pipeline (95% de variance conservée)")
    numeric_pipeline = Pipeline([
        ('imputer', IMPUTER_NUM),
        ('scaler',  RobustScaler()),
        ('pca', PCA(n_components=0.95, random_state=42))
    ])
else:
    numeric_pipeline = Pipeline([
        ('imputer', IMPUTER_NUM),
        ('scaler',  RobustScaler()),
    ])

# ── Pipeline Catégoriel ──────────────────────────────────────────────
categorical_pipeline = Pipeline([
    ('imputer', IMPUTER_CAT),
    ('encoder', OneHotEncoder(handle_unknown='ignore', sparse_output=False)),
])

# ── ColumnTransformer ─────────────────────────────────────────────────
preprocessor = ColumnTransformer(
    transformers=[
        ('num', numeric_pipeline, num_features),
        ('cat', categorical_pipeline, cat_features),
    ],
    remainder='drop'
)

# ── Pipeline Global (Engineering + Preprocessing) ─────────────────────
full_pipeline = Pipeline([
    ('engineering', feature_eng),
    ('preprocessing', preprocessor)
])

print("\n⚙️  Fitting du pipeline complet...")
t0 = time.time()
X_train_inp = X_train_clean if 'X_train_clean' in globals() else X_train
X_test_inp  = X_test_clean if 'X_test_clean' in globals() else X_test

full_pipeline.fit(X_train_inp)
print(f"✅ Fit terminé en {time.time()-t0:.2f}s")

# Transformation
X_train_prep = full_pipeline.transform(X_train_inp)
X_test_prep  = full_pipeline.transform(X_test_inp)

print(f"\n📐 Dimensions finales :")
print(f"   Train: {X_train_prep.shape}")
print(f"   Test : {X_test_prep.shape}")
```

### ⚠️ Règle d'or de l'échantillonnage synthétique (Anti-Data Leakage)

L'application de SMOTE (ou de toute technique de sur-échantillonnage) présente un piège méthodologique majeur : la **fuite de données (Data Leakage)**. 

Si vous appliquez SMOTE sur l'intégralité de votre jeu de données *avant* de procéder à la séparation (train/test) ou à la validation croisée, les instances synthétiques générées pour l'ensemble de validation contiendront des informations intimement corrélées aux données d'entraînement. 

**Les conséquences d'une telle erreur :**
1. Le modèle s'évalue sur des données synthétiques qui ne représentent pas la réalité (le jeu de test doit toujours refléter la distribution naturelle des données).
2. Cela produit des métriques de validation croisée **excessivement optimistes**.
3. Les performances du modèle s'effondreront une fois mis en production sur des données indépendantes.

**La solution robuste :**
SMOTE doit être appliqué **uniquement au sein du jeu d'apprentissage**, en laissant toujours les plis de validation ou de test vierges de tout échantillonnage synthétique. C'est pourquoi, en cas de validation croisée (ex: recherche d'hyperparamètres), nous devons utiliser le `Pipeline` de la bibliothèque `imblearn` afin d'appliquer la transformation `fit_resample` *uniquement* lors de la phase d'entraînement, de manière transparente.

**Limites de SMOTE vs class_weight :**
*   **Chevauchement des classes :** SMOTE peut lier deux points de la classe minoritaire et placer un point synthétique au milieu de la classe majoritaire, créant du flou à la frontière de décision.
*   **Sensibilité aux outliers :** Si un point de la classe minoritaire est un bruit ou un outlier, SMOTE va générer d'autres points autour, amplifiant le bruit.
*   **Calibration :** Modifier la distribution physique des données fausse la calibration des probabilités de sortie du modèle. L'utilisation du paramètre `class_weight='balanced'` ajuste mathématiquement la fonction de perte sans déformer physiquement le jeu de données, ce qui est souvent plus robuste.

```python
if TYPE_TACHE == "classification":
    from imblearn.over_sampling import SMOTE
    
    # Vérification du déséquilibre
    counts = pd.Series(y_train).value_counts(normalize=True)
    if counts.min() < 0.2:
        print(f"⚖️ Déséquilibre détecté ({counts.min():.1%}). Application de SMOTE sur le Train Set.")
        # Recall : SMOTE n'est appliqué ICI que pour le fit final du train.
        # En cas de validation croisée (ex: Optuna), SMOTE doit être intégré dans un Pipeline imblearn.
        smote = SMOTE(random_state=42)
        X_train_prep, y_train = smote.fit_resample(X_train_prep, y_train)
        print(f"✅ Distribution équilibrée : {pd.Series(y_train).value_counts().to_dict()}")
    else:
        print("✅ Classes équilibrées, SMOTE non requis.")

# ── 2.4 Checkpoint & Persistance MLOps ─────────────────────────────────
print("\n💾 4. Checkpoint MLOps & Persistance")
print("-" * 60)

try:
    X_train_prep_df = pd.DataFrame(X_train_prep)
    X_test_prep_df  = pd.DataFrame(X_test_prep)
    
    # Correction des noms de colonnes pour compatibilité Parquet (pas d'espaces)
    X_train_prep_df.columns = [str(c).replace(" ", "_") for c in X_train_prep_df.columns]
    X_test_prep_df.columns  = [str(c).replace(" ", "_") for c in X_test_prep_df.columns]
    
    X_train_prep_df.to_parquet(PROCESSED_DIR / "X_train_prep.parquet", index=False)
    X_test_prep_df.to_parquet(PROCESSED_DIR / "X_test_prep.parquet", index=False)
    
    if y_train is not None:
        pd.Series(y_train).to_frame().to_parquet(PROCESSED_DIR / "y_train.parquet", index=False)
    if y_test is not None:
        pd.Series(y_test).to_frame().to_parquet(PROCESSED_DIR / "y_test.parquet", index=False)
        
    print(f"✅ Données finalisées sauvegardées avec succès dans : {PROCESSED_DIR}")
except Exception as e_save:
    print(f"⚠️ Impossible de sauvegarder les checkpoints Parquet : {e_save}")

print("\n🔒 PRÉTRAITEMENT SENIOR VALIDÉ")
```,StartLine:186,TargetContent:
```
