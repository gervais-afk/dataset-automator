# ── 0️⃣ SETUP — SÉRIE TEMPORELLE (CRISP-ML(Q)) ───────────────────

## 0.1 Compréhension du Métier (Business Understanding)
> **Objectif MLOps** : Aligner les métriques techniques avec la valeur métier.
* Définissez ici les métriques de succès (ex: MAPE < 5% = optimisation des stocks de X€).
* Identifier les contraintes : Horizon de prédiction, fréquence de mise à jour, explicabilité.

## 0.2 Configuration et Initialisation (Setup & Config)
Configuration initiale du dataset temporel avec chemins absolus et découpage chronologique.

```python
import os, sys, warnings, random
import pandas as pd
import numpy  as np
import matplotlib.pyplot as plt
import matplotlib.dates  as mdates
import matplotlib.ticker as mticker
import seaborn as sns
import mlflow
warnings.filterwarnings("ignore")

# ── Reproductibilité (Random Seeds) ───────────────────────────────────
SEED = 42
random.seed(SEED)
np.random.seed(SEED)

# ═══════════════════════════════════════════════════════════
# 📋 SYSTÈME DE TRAÇAGE (Debugging)
# ═══════════════════════════════════════════════════════════
import logging
from datetime import datetime

logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('notebook_execution.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def log_section(section_name):
    logger.info(f"{'='*60}")
    logger.info(f"DÉBUT SECTION : {section_name}")
    logger.info(f"{'='*60}")

log_section("00 - SETUP & CHARGEMENT")

# ── Chemins (toujours absolus — injectés par notebook_factory) ────
# Utilisation de chaînes brutes (r"") pour éviter les erreurs d'échappement Windows
FILE_PATH      = r"{FILE_PATH}"
TARGET_COL     = "{TARGET_COL}"
OUTPUT_DIR     = r"{OUTPUT_DIR}"
RAW_DIR        = r"{RAW_DIR}"
PROCESSED_DIR  = r"{PROCESSED_DIR}"
INTERIM_DIR    = r"{INTERIM_DIR}"
MODELS_DIR     = r"{MODELS_DIR}"
NB_DIR         = r"{NB_DIR}"
DATE_COL       = "{DATE_COL}"
NOM_BASE       = "{NOM_BASE}"
TYPE_TACHE     = "{TYPE_TACHE}"

# ✅ Création de l'arborescence MLOps stricte
for d in [OUTPUT_DIR, RAW_DIR, PROCESSED_DIR, INTERIM_DIR, MODELS_DIR, NB_DIR]:
    os.makedirs(d, exist_ok=True)

# ── Initialisation MLflow (Tracking) ─────────────────────────────────
from pathlib import Path
mlflow_dir = Path(OUTPUT_DIR) / 'mlruns'
mlflow.set_tracking_uri(mlflow_dir.as_uri())
mlflow.set_experiment(f"Exp_{NOM_BASE}")
print("🔍 Vérification de l'environnement...")
print(f"   MLflow exp : Exp_{NOM_BASE}")

# ── Diagnostic chemin ─────────────────────────────────────────────
# Utilisation de virgules pour éviter les f-strings avec backslashes problématiques
print("📂 Fichier   :", FILE_PATH)
print("📁 Outputs   :", OUTPUT_DIR)
print("📍 CWD actuel:", os.getcwd())

# Vérification existence
if not os.path.isfile(FILE_PATH):
    alt_paths = [
        os.path.join(os.getcwd(), FILE_PATH),
        os.path.join(os.getcwd(), "..", "..", FILE_PATH),
        os.path.join(os.getcwd(), "data", os.path.basename(FILE_PATH)),
    ]
    for alt in alt_paths:
        if os.path.isfile(alt):
            FILE_PATH = alt
            print("✅ Résolu via chemin alternatif :", FILE_PATH)
            break
    else:
        print("❌ Fichier non trouvé à l'emplacement :", FILE_PATH)

print("✅ Fichier prêt :", os.path.isfile(FILE_PATH))

# ── Chargement avec parsing dates ─────────────────────────────────
df_raw = pd.read_csv(FILE_PATH, low_memory=False)
print(f"\n📐 Dimensions brutes : {df_raw.shape}")

# ── Parsing colonne date ───────────────────────────────────────────
DATE_COL_EFFECTIVE = None

if DATE_COL and DATE_COL in df_raw.columns:
    try:
        df_raw[DATE_COL] = pd.to_datetime(df_raw[DATE_COL])
        df = df_raw.sort_values(DATE_COL).set_index(DATE_COL)
        DATE_COL_EFFECTIVE = DATE_COL
        print(f"\n✅ Index temporel configuré sur : '{DATE_COL}'")
    except Exception as e:
        print(f"⚠️  Parsing date '{DATE_COL}' échoué : {e}")
        df = df_raw.copy()
else:
    for col in df_raw.columns:
        if any(kw in col.lower() for kw in ['date', 'time', 'timestamp']):
            try:
                df_raw[col] = pd.to_datetime(df_raw[col])
                df = df_raw.sort_values(col).set_index(col)
                DATE_COL_EFFECTIVE = col
                print(f"\n✅ Date auto-détectée et indexée : '{col}'")
                break
            except: continue
    else:
        df = df_raw.copy()
        print("\n⚠️  Aucune colonne date exploitable pour l'index")

if DATE_COL_EFFECTIVE:
    print(f"   Période   : {df.index.min()} → {df.index.max()}")
    print(f"   Durée     : {len(df)} observations")

# ── Sélection cible et features ────────────────────────────────────
col_num = df.select_dtypes(include=np.number).columns.tolist()

if not TARGET_COL or TARGET_COL not in df.columns:
    TARGET_COL = col_num[-1] if col_num else ""
    print(f"   🎯 Cible auto-détectée : '{TARGET_COL}'")

features = [c for c in col_num if c != TARGET_COL]

print(f"\n📊 Statistiques de '{TARGET_COL}' :")
display(df[TARGET_COL].describe().to_frame().T)

# ── Visualisation série principale ─────────────────────────────────
if TARGET_COL and TARGET_COL in df.columns:
    plt.figure(figsize=(14, 5))
    plt.plot(df.index, df[TARGET_COL], color='#2196F3', lw=1.5)
    plt.title(f"Évolution temporelle : {TARGET_COL} ({NOM_BASE})")
    plt.grid(alpha=0.3)
    
    save_path = os.path.join(OUTPUT_DIR, "00_serie_temporelle.png")
    plt.savefig(save_path, bbox_inches='tight')
    plt.show()

# ── Split Temporel (Anti-Leakage) ─────────────────────────────────────
split_idx = int(len(df) * 0.8)
train_df = df.iloc[:split_idx]
test_df  = df.iloc[split_idx:]

X_train = train_df.drop(columns=[TARGET_COL]) if TARGET_COL in train_df.columns else train_df
y_train = train_df[TARGET_COL] if TARGET_COL in train_df.columns else None

X_test = test_df.drop(columns=[TARGET_COL]) if TARGET_COL in test_df.columns else test_df
y_test = test_df[TARGET_COL] if TARGET_COL in test_df.columns else None

print(f"\n📏 Dimensions Train : {X_train.shape} | Test : {X_test.shape}")
print(f"✅ Setup TS terminé")
```
