# ⚙️ Étape 0 — Setup, Chargement & Split (CRISP-ML(Q))

## 0.1 Compréhension du Métier (Business Understanding)
> **Objectif MLOps** : Aligner les métriques techniques avec la valeur métier.

### 🎯 Matrice d'Impact Économique (Exemple)
Pour transformer les scores ML en décisions métier, nous définissons les coûts et bénéfices associés :

| Résultat Modèle | Action Métier | Impact Financier (Estimation) |
| :--- | :--- | :--- |
| **Vrai Positif (TP)** | Intervention réussie | **+ Gain** (ex: Client sauvé, Fraude évitée) |
| **Faux Positif (FP)** | Fausse alerte | **- Coût** (ex: Frais marketing inutiles, temps perdu) |
| **Faux Négatif (FN)** | Opportunité manquée | **- Perte** (ex: Désabonnement client, perte sèche) |
| **Vrai Négatif (TN)** | Statut quo | **0€** (Aucune action nécessaire) |

* **Métriques de succès** : [Définir ici, ex: F1-Score > 0.8 ou ROI > 15%]
* **Contraintes** : Temps d'inférence, explicabilité requise, contraintes éthiques.

## 0.2 Configuration et Initialisation (Setup & Config)

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import seaborn as sns
import os, sys, glob, time, warnings, random
from pathlib import Path
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import LabelEncoder
import mlflow

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')
plt.rcParams.update({
    'figure.figsize'  : (14, 6),
    'font.size'       : 11,
    'axes.titlesize'  : 13,
    'axes.titleweight': 'bold',
    'figure.dpi'      : 100,
})

# ── Reproductibilité (Random Seeds) ───────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)
# tensorflow.random.set_seed(SEED) # si TF
# torch.manual_seed(SEED) # si PyTorch

# ── Variables injectées automatiquement ──────────────────────────────
FILE_PATH      = r"{FILE_PATH}"
TARGET_COL     = "{TARGET_COL}"
OUTPUT_DIR     = r"{OUTPUT_DIR}"
RAW_DIR        = r"{RAW_DIR}"
PROCESSED_DIR  = r"{PROCESSED_DIR}"
INTERIM_DIR    = r"{INTERIM_DIR}"
MODELS_DIR     = r"{MODELS_DIR}"
NB_DIR         = r"{NB_DIR}"
DATASET_NAME   = "{DATASET_NAME}"
TYPE_TACHE     = "{TYPE_TACHE}"

# ✅ Création de l'arborescence MLOps stricte
for d in [OUTPUT_DIR, RAW_DIR, PROCESSED_DIR, INTERIM_DIR, MODELS_DIR, NB_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Initialisation MLflow (Tracking) ─────────────────────────────────
mlflow_dir = Path(OUTPUT_DIR) / 'mlruns'
mlflow.set_tracking_uri(mlflow_dir.as_uri())
mlflow.set_experiment(f"Exp_{DATASET_NAME}")
print("🔍 Vérification de l'environnement...")
print(f"   MLflow exp : Exp_{DATASET_NAME}")

# Vérifier que le fichier existe
if not Path(FILE_PATH).exists():
    nom_fichier = Path(FILE_PATH).name
    print(f"   ⚠️  Non trouvé à l'adresse fixe, recherche récursive...")
    candidats = list(Path(".").rglob(nom_fichier))
    if not candidats:
        candidats = list(Path("../..").rglob(nom_fichier))
    if candidats:
        FILE_PATH = str(candidats[0].resolve())
        print("   ✅ Fichier localisé :", FILE_PATH)
    else:
        raise FileNotFoundError(f"Dataset '{nom_fichier}' introuvable.")

# (Optionnel) Copie du fichier source dans RAW_DIR pour immuabilité
import shutil
if Path(FILE_PATH).parent != Path(RAW_DIR):
    try:
        shutil.copy2(FILE_PATH, RAW_DIR)
        FILE_PATH = str(Path(RAW_DIR) / Path(FILE_PATH).name)
    except: pass

print("\n✅ Setup OK (CRISP-ML(Q) Architecture)")
print("   📁 Dataset  :", Path(FILE_PATH).name)
print("   🎯 Cible    :", TARGET_COL)
print("   📂 Sortie   :", OUTPUT_DIR)
```

## Chargement des Données

```python
# ── Chargement ───────────────────────────────────────────────────────
print(f"⏳ Chargement : {Path(FILE_PATH).name}...")
t0     = time.time()
# Détection format
ext = Path(FILE_PATH).suffix.lower()
if ext in ['.xlsx', '.xls']:
    df_raw = pd.read_excel(FILE_PATH)
else:
    df_raw = pd.read_csv(FILE_PATH)
print(f"✅ Chargé en {time.time()-t0:.2f}s")
print(f"   {df_raw.shape[0]:,} lignes × {df_raw.shape[1]} colonnes")

# Copie de travail (df_raw est conservé comme backup)
df = df_raw.copy()

# Détection et conversion colonnes date
date_cols_found = []
for col in df.columns:
    if any(k in col.lower() for k in ['date','time','timestamp','day']):
        try:
            df[col] = pd.to_datetime(df[col])
            date_cols_found.append(col)
            print(f"📅 Date convertie : {col}")
        except: pass

# Index temporel si applicable (sécurisé)
if date_cols_found:
    df = df.set_index(date_cols_found[0]).sort_index()
    print(f"📅 Index temporel défini sur : {date_cols_found[0]}")

print(f"\n📋 Colonnes : {list(df.columns)}")

if isinstance(df.index, pd.DatetimeIndex):
    print(f"📅 Période  : "
          f"{df.index.min().date()} → {df.index.max().date()}")

df.head(3)
```

## Aperçu & Statistiques

```python
# ── Statistiques rapides ──────────────────────────────────────────────
print("📊 Statistiques descriptives :")
display(df.describe(include='all').round(2))

# Valeurs manquantes
n_miss = df.isnull().sum().sum()
if n_miss > 0:
    print(f"\n⚠️  {n_miss:,} valeurs manquantes :")
    display(df.isnull().sum()[df.isnull().sum() > 0])
    # Traitement automatique
    for col in df.columns:
        if df[col].isnull().any():
            if df[col].dtype in ['float64','int64']:
                df[col] = df[col].fillna(df[col].median())
            else:
                mode = df[col].mode()
                df[col] = df[col].fillna(
                    mode[0] if not mode.empty else 'inconnu')
    print("✅ Valeurs manquantes traitées")
else:
    print("\n✅ Aucune valeur manquante")
```

## Split Train / Test (Anti-Leakage)

```python
# ── Split Train / Test (Anti-Leakage) ─────────────────────────────────
if TYPE_TACHE == "unsupervised" or not TARGET_COL:
    X_train, X_test = train_test_split(df, test_size=0.2, random_state=42)
    y_train, y_test = None, None
    split_type = "Non-Supervisé (Aléatoire)"
else:
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]
    
    if isinstance(df.index, pd.DatetimeIndex):
        split = int(len(X) * 0.8)
        X_train, X_test = X.iloc[:split], X.iloc[split:]
        y_train, y_test = y.iloc[:split], y.iloc[split:]
        split_type = "Temporel (strict)"
    else:
        # Stratifié si classification
        strat = y if TYPE_TACHE == "classification" else None
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=42, stratify=strat)
        split_type = f"Aléatoire ({'Stratifié' if strat is not None else 'Simple'})"

print(f"\n✅ Split : {split_type}")
print(f"   Train : {len(X_train):,} ({len(X_train)/len(df)*100:.0f}%)")
print(f"   Test  : {len(X_test):,}  ({len(X_test)/len(df)*100:.0f}%)")

# Sauvegarder les noms de features pour les étapes suivantes
if TYPE_TACHE == "unsupervised" or not TARGET_COL:
    FEATURE_NAMES = list(df.columns)
else:
    FEATURE_NAMES = list(X.columns)

print(f"\n📋 Features ({len(FEATURE_NAMES)}) :")
print(f"   {FEATURE_NAMES[:10]}{'...' if len(FEATURE_NAMES)>10 else ''}")
```
