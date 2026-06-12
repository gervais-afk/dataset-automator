# 🔧 Étape 2 — Prétraitement & Feature Engineering Senior

## Objectif
Mise en place d'un pipeline **Scikit-Learn** de niveau industriel :
- **Missing Indicator** : Capture de l'information sur l'absence de données (MNAR).
- **IterativeImputer (MICE)** : Imputation statistique avancée.
- **Feature Generation** : Création de variables métier et transformations.
- **Robustness** : Traitement des outliers et mise à l'échelle robuste.

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
```

## Construction du Pipeline

```python
# Identifier les types de colonnes (sur X_train original)
num_features = X_train.select_dtypes(include=[np.number]).columns.tolist()
cat_features = X_train.select_dtypes(include=['object', 'category']).columns.tolist()

# ── Pipeline Numérique ────────────────────────────────────────────────
numeric_pipeline = Pipeline([
    ('imputer', IMPUTER_NUM),
    ('scaler',  RobustScaler()), # Résistant aux outliers
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
full_pipeline.fit(X_train)
print(f"✅ Fit terminé en {time.time()-t0:.2f}s")

# Transformation
X_train_prep = full_pipeline.transform(X_train)
X_test_prep  = full_pipeline.transform(X_test)

print(f"\n📐 Dimensions finales :")
print(f"   Train: {X_train_prep.shape}")
print(f"   Test : {X_test_prep.shape}")
```

## Gestion du Déséquilibre (SMOTE)

```python
if TYPE_TACHE == "classification":
    from imblearn.over_sampling import SMOTE
    from imblearn.pipeline import Pipeline as ImbPipeline
    
    # Vérification du déséquilibre
    counts = pd.Series(y_train).value_counts(normalize=True)
    if counts.min() < 0.2:
        print(f"⚖️ Déséquilibre détecté ({counts.min():.1%}). Application de SMOTE.")
        smote = SMOTE(random_state=42)
        X_train_prep, y_train = smote.fit_resample(X_train_prep, y_train)
        print(f"✅ Distribution équilibrée : {pd.Series(y_train).value_counts().to_dict()}")
    else:
        print("✅ Classes équilibrées, SMOTE non requis.")

print("\n🔒 PRÉTRAITEMENT SENIOR VALIDÉ")
```
