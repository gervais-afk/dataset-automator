# ⚙️ Étape 0 — Setup, Chargement & Split (CRISP-ML(Q)) (Cellule 1)

## 0.2 Configuration et Initialisation (Setup & Config)

```python
# ── Magics de rechargement automatique
# Garantit que toute modification dans les modules .py externes est prise en compte instantanément.
%load_ext autoreload
%autoreload 2

import os
import sys
import glob
import time
import warnings
import random
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import matplotlib.dates as mdates
import seaborn as sns

from sklearn.model_selection import train_test_split, RepeatedStratifiedKFold, RepeatedKFold, cross_val_score, TimeSeriesSplit
from sklearn.preprocessing import LabelEncoder, StandardScaler, RobustScaler, OneHotEncoder, FunctionTransformer
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, roc_auc_score, r2_score, mean_absolute_error, mean_squared_error
import mlflow

warnings.filterwarnings('ignore')
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette('husl')

# ── Reproductibilité
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ── Système de Traçage
import logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def log_section(section_name):
    logger.info(f"{'='*60}")
    logger.info(f"DÉBUT SECTION : {section_name}")
    logger.info(f"{'='*60}")


# ── Variables d'environnement / Paramètres de l'Agent IA (injectés)
FILE_PATH      = r"{FILE_PATH}"
TARGET_COL     = "{TARGET_COL}"
DATASET_NAME   = "{DATASET_NAME}"
TYPE_TACHE     = "{TYPE_TACHE}"
IS_TS          = TYPE_TACHE in ["timeseries", "time_series"]

BASE_DIR       = Path(os.getcwd()) / "outputs" / DATASET_NAME
OUTPUT_DIR     = BASE_DIR
RAW_DIR        = BASE_DIR / "data" / "raw"
PROCESSED_DIR  = BASE_DIR / "data" / "processed"
INTERIM_DIR    = BASE_DIR / "data" / "interim"
MODELS_DIR     = BASE_DIR / "models"
NB_DIR         = BASE_DIR / "notebooks"
NOM_BASE       = DATASET_NAME

# ✅ Création de l'arborescence MLOps stricte
for d in [OUTPUT_DIR, RAW_DIR, PROCESSED_DIR, INTERIM_DIR, MODELS_DIR, NB_DIR]:
    d.mkdir(parents=True, exist_ok=True)

# ── Initialisation MLflow
os.environ["MLFLOW_ALLOW_FILE_STORE"] = "true"
mlflow_dir = OUTPUT_DIR / 'mlruns'
mlflow.set_tracking_uri(mlflow_dir.as_uri())
mlflow.set_experiment(f"Exp_{DATASET_NAME}")

print("🔍 Vérification de l'environnement...")
print(f"   MLflow exp : Exp_{DATASET_NAME}")

# Sauvegarde d'un dataset d'entraînement de secours si absent
if not os.path.isfile(FILE_PATH):
    print("⚠️ Fichier introuvable. Génération d'un dataset synthétique supervisé...")
    from sklearn.datasets import make_classification, make_regression
    if TYPE_TACHE == "classification" or TYPE_TACHE == "unsupervised":
        X_arr, y_arr = make_classification(n_samples=1000, n_features=10, n_informative=8, random_state=SEED)
        cols = [f"feature_{i}" for i in range(10)]
        df_fake = pd.DataFrame(X_arr, columns=cols)
        df_fake[TARGET_COL] = y_arr
    else:
        X_arr, y_arr = make_regression(n_samples=1000, n_features=10, noise=0.1, random_state=SEED)
        cols = [f"feature_{i}" for i in range(10)]
        df_fake = pd.DataFrame(X_arr, columns=cols)
        df_fake[TARGET_COL] = y_arr
    FILE_PATH = str(OUTPUT_DIR / "synthetic_supervised.csv")
    df_fake.to_csv(FILE_PATH, index=False)

# Chargement robuste
ext = Path(FILE_PATH).suffix.lower()
df_raw = pd.read_excel(FILE_PATH) if ext in ['.xlsx', '.xls'] else pd.read_csv(FILE_PATH)
df = df_raw.copy()

# Traitement des colonnes temporelles
date_cols_found = []
for col in df.columns:
    if any(k in col.lower() for k in ['date', 'time', 'timestamp']):
        try:
            df[col] = pd.to_datetime(df[col])
            date_cols_found.append(col)
        except:
            pass

if date_cols_found:
    df = df.set_index(date_cols_found[0]).sort_index()
    print(f"✅ Indexation temporelle sur : {date_cols_found[0]}")

# Séparation des features et de la cible
if TYPE_TACHE == "unsupervised" or not TARGET_COL or TARGET_COL not in df.columns:
    X = df.copy()
    y = None
    print("✅ Mode non-supervisé / Clustering actif.")
else:
    X = df.drop(columns=[TARGET_COL])
    y = df[TARGET_COL]

if TYPE_TACHE == "classification" and y is not None and (y.dtype == "object" or y.dtype.name == "category"):
    le = LabelEncoder()
    y = pd.Series(le.fit_transform(y), index=y.index)
    print("✅ Cible catégorielle encodée avec LabelEncoder.")

# Split Anti-Leakage (Temporel si DatetimeIndex, sinon aléatoire)
if isinstance(df.index, pd.DatetimeIndex):
    split = int(len(X) * 0.8)
    X_train, X_test = X.iloc[:split], X.iloc[split:]
    y_train, y_test = (y.iloc[:split], y.iloc[split:]) if y is not None else (None, None)
    print("✅ Split temporel (Chronologique) effectué.")
else:
    strat = y if TYPE_TACHE == "classification" else None
    if y is not None:
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=0.2, random_state=SEED, stratify=strat
        )
    else:
        X_train, X_test = train_test_split(X, test_size=0.2, random_state=SEED)
        y_train, y_test = None, None
    print("✅ Split aléatoire effectué.")

FEATURE_NAMES = list(X.columns)
print(f"✅ Split terminé. Train: {len(X_train)} | Test: {len(X_test)}")
```

## 0.3 Validation du Contrat de Données (Data Quality Contracts)
> **Objectif MLOps** : Valider la conformité des données par rapport aux contraintes sémantiques issues du Knowledge Graph.

```python
# ── ASSERTIONS DE QUALITÉ DE DONNÉES (DATA CONTRACTS)
{DATA_CONTRACT_ASSERTIONS}
```
