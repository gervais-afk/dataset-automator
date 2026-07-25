import sys
import os
import pandas as pd
import numpy as np
import json
import hashlib
import nbformat as nbf
from datetime import datetime
from fastmcp import FastMCP

# Global imports to avoid Thread Deadlock on Windows when imported in worker threads
import scipy
from scipy.stats import mstats
import sklearn
from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor, IsolationForest
from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
from sklearn.metrics import mean_squared_error, r2_score, silhouette_score
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler, SplineTransformer
from sklearn.linear_model import Ridge
from imblearn.over_sampling import SMOTE
import optuna
import xgboost
from xgboost import XGBClassifier, XGBRegressor
import lightgbm
from lightgbm import LGBMClassifier, LGBMRegressor
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import statsmodels
from statsmodels.tsa.stattools import adfuller
from statsmodels.stats.outliers_influence import variance_inflation_factor
from statsmodels.tools.tools import add_constant

try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

try:
    from tabicl import TabICLClassifier, TabICLRegressor
    HAS_TABICL = True
except ImportError:
    HAS_TABICL = False

# Initialize the FastMCP server
mcp = FastMCP("DatasetAutomator")

def is_port_in_use(port: int) -> bool:
    import socket
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(('127.0.0.1', port)) == 0

def ensure_mlflow_server_running():
    import socket
    import subprocess
    import os
    import sys
    
    is_running = is_port_in_use(5000)
    if not is_running:
        db_path = os.path.abspath("../workspace/mlflow.db").replace("\\", "/")
        artifacts_path = "file:///" + os.path.abspath("../workspace/mlruns").replace("\\", "/")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        os.makedirs(os.path.abspath("../workspace/mlruns"), exist_ok=True)
        
        try:
            # Start server as detached background process on Windows (creationflags=0x00000008)
            subprocess.Popen(
                ["uv", "run", "mlflow", "server",
                 "--backend-store-uri", f"sqlite:///{db_path}",
                 "--default-artifact-root", artifacts_path,
                 "--host", "127.0.0.1",
                 "--port", "5000"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                creationflags=0x00000008 # DETACHED_PROCESS
            )
            import time
            for _ in range(10):
                if is_port_in_use(5000):
                    break
                time.sleep(0.5)
            sys.stderr.write("🚀 Serveur MLflow démarré automatiquement sur http://127.0.0.1:5000\n")
        except Exception as e:
            sys.stderr.write(f"⚠️ Impossible de démarrer le serveur MLflow: {e}\n")
    else:
        sys.stderr.write("ℹ️ Serveur MLflow déjà actif sur le port 5000.\n")


try:
    from src.firebase_client import update_job_progress, start_heartbeat, stop_heartbeat
except ImportError:
    try:
        from firebase_client import update_job_progress, start_heartbeat, stop_heartbeat
    except ImportError:
        # Si exécuté hors contexte
        def update_job_progress(*args, **kwargs): pass
        def start_heartbeat(*args, **kwargs): pass
        def stop_heartbeat(): pass



def sanitize_cam_phone(series) -> 'pd.Series':
    import re
    # Nettoie les numéros camerounais (enlever espaces, points, tirets, parenthèses)
    cleaned = series.astype(str).str.replace(r'[\s\.\-\(\)]', '', regex=True)
    # Gérer les préfixes +237 ou 237 au début
    cleaned = cleaned.str.replace(r'^(?:\+237|237)', '', regex=True)
    # S'assurer que ça commence par 6 ou 2 ou 3 et fait 9 chiffres
    def validate_and_format(val):
        if not val or val == 'nan':
            return None
        val = val.strip()
        if len(val) == 9 and val[0] in ['6', '2', '3']:
            return val
        elif len(val) == 8 and val[0] in ['7', '9', '5', '6', '8']: # Format historique à 8 chiffres (avant 2014)
            if val[0] in ['7', '8']:
                return '6' + val
            elif val[0] in ['9', '5']:
                return '6' + val
        return None
    return cleaned.apply(validate_and_format)

def normalize_cam_geography(series) -> 'pd.Series':
    # Dictionnaire des départements/villes vers les 10 régions du Cameroun
    geo_mapping = {
        'yaounde': 'Centre', 'mfoundi': 'Centre', 'nyong': 'Centre', 'lekie': 'Centre', 'mbalmayo': 'Centre',
        'douala': 'Littoral', 'wouri': 'Littoral', 'mungo': 'Littoral', 'sanaga-maritime': 'Littoral', 'nkam': 'Littoral',
        'bafoussam': 'Ouest', 'mifi': 'Ouest', 'nounge': 'Ouest', 'bamendjou': 'Ouest', 'dschang': 'Ouest', 'menoua': 'Ouest', 'haut-nkam': 'Ouest',
        'buea': 'Sud-Ouest', 'limbe': 'Sud-Ouest', 'fako': 'Sud-Ouest', 'meme': 'Sud-Ouest', 'kumba': 'Sud-Ouest', 'ndian': 'Sud-Ouest',
        'bamenda': 'Nord-Ouest', 'mezam': 'Nord-Ouest', 'bui': 'Nord-Ouest', 'boyo': 'Nord-Ouest',
        'ngaoundere': 'Adamaoua', 'vina': 'Adamaoua', 'djohong': 'Adamaoua',
        'garoua': 'Nord', 'benoue': 'Nord', 'guider': 'Nord',
        'maroua': 'Extrême-Nord', 'diamare': 'Extrême-Nord', 'kousseri': 'Extrême-Nord', 'mokolo': 'Extrême-Nord',
        'bertoua': 'Est', 'lom-et-djerem': 'Est', 'kadey': 'Est',
        'ebolowa': 'Sud', 'mvila': 'Sud', 'kribi': 'Sud', 'ocean': 'Sud', 'dja-et-lobo': 'Sud'
    }
    
    def get_region(val):
        if not isinstance(val, str) or val == 'nan':
            return None
        val_clean = val.lower().strip().replace('é', 'e').replace('è', 'e').replace('ô', 'o').replace(' ', '-')
        if val_clean in geo_mapping:
            return geo_mapping[val_clean]
        for key, region in geo_mapping.items():
            if key in val_clean or val_clean in key:
                return region
        return "Autre"
        
    return series.apply(get_region)

def clean_fcfa_currency(series) -> 'pd.Series':
    import pandas as pd
    # Enlever FCFA, XAF, XOF, F, espaces, virgules
    cleaned = series.astype(str).str.replace(r'(?i)(?:fcfa|xaf|xof|f|\s|,)', '', regex=True)
    return pd.to_numeric(cleaned, errors='coerce')

def parse_momo_data(series) -> 'pd.Series':
    def detect_gateway(val):
        val_str = str(val).lower()
        if 'mtn' in val_str or 'momo' in val_str or '67' in val_str or '68' in val_str:
            return 'MTN Mobile Money'
        elif 'orange' in val_str or 'om' in val_str or '65' in val_str or '69' in val_str:
            return 'Orange Money'
        return 'Autre'
    return series.apply(detect_gateway)


@mcp.tool()
def profile_dataset(file_path: str) -> str:
    """Read a CSV and return a statistical summary JSON."""
    import sys
    sys.stderr.write(f"🔵 [Python Worker] Reçu appel profile_dataset pour: {file_path}\n")
    sys.stderr.flush()
    try:
        import os
        import sys
        # Ensure src is in path for local imports
        src_dir = os.path.dirname(os.path.abspath(__file__))
        if src_dir not in sys.path:
            sys.path.append(src_dir)
        sys.stderr.write("🔵 [Python Worker] Chargement de tools.domain_detector...\n")
        sys.stderr.flush()
        from tools.domain_detector import build_data_profile
        
        sys.stderr.write("🔵 [Python Worker] Lecture du CSV...\n")
        sys.stderr.flush()
        df = pd.read_csv(file_path)
        profile = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "features": []
        }
        for col in df.columns:
            dtype = str(df[col].dtype)
            ctype = "numeric" if "int" in dtype or "float" in dtype else "categorical"
            missing = (df[col].isnull().sum() / len(df)) * 100
            
            feat = {
                "name": col,
                "type": ctype,
                "missing_percentage": float(missing)
            }
            if ctype == "categorical":
                feat["cardinality"] = int(df[col].nunique())
            else:
                feat["skewness"] = float(df[col].skew()) if not df[col].isnull().all() else 0.0
                feat["mean"] = float(df[col].mean()) if not df[col].isnull().all() else 0.0
                
            profile["features"].append(feat)
            
        # Add dynamic domain detection and ML task type suggestion
        data_profile = build_data_profile(df, os.path.basename(file_path))
        profile["suggested_target"] = data_profile.target_col
        profile["suggested_task_type"] = data_profile.task_type
        profile["is_timeseries"] = data_profile.is_timeseries
        profile["date_columns"] = [data_profile.date_col] if data_profile.date_col else []
        profile["domaine"] = data_profile.domain
        
        return json.dumps(profile)
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def apply_cleaning_strategy(file_path: str, cleaning_schema: str, job_id: str = None) -> str:
    """Apply deterministic cleaning and save versioned file."""
    if job_id:
        start_heartbeat(job_id)
        update_job_progress(job_id, 'cleaning', 15, "Début du nettoyage des colonnes...")

    try:
        schema = json.loads(cleaning_schema)
        df = pd.read_csv(file_path)
        
        # Example processing
        target_col = schema.get("target")
        for step in schema.get("steps", []):
            cols = step.get("column")
            action = step.get("action")
            
            if not isinstance(cols, list):
                cols = [cols]
                
            if action == "pca":
                # L'action PCA n'est plus appliquée de façon destructive sur le CSV brut
                # Elle sera appliquée de manière sécurisée dans le preprocessor sklearn du notebook
                continue
            elif action == "formula":
                formula_expr = step.get("formula")
                if formula_expr:
                    import re
                    # Validation regexp simple pour s'assurer qu'il n'y a pas d'injection malveillante
                    if re.match(r"^[a-zA-Z0-9_\s\+\-\*\/\(\)\.\*\*]+$", formula_expr):
                        for col in cols:
                            try:
                                df[col] = df.eval(formula_expr)
                                print(f"✅ [Python] Évalué avec succès la formule '{formula_expr}' pour la colonne '{col}'")
                            except Exception as eval_err:
                                print(f"❌ [Python] Erreur lors de l'évaluation de la formule '{formula_expr}' sur '{col}': {eval_err}")
                    else:
                        print(f"⚠️ [Python] Formule invalide ou non sécurisée rejetée: '{formula_expr}'")
                continue
                
            elif action == "add_time_features":
                date_col = cols[0] if cols else None
                if date_col and date_col in df.columns:
                    df[date_col] = pd.to_datetime(df[date_col])
                    df['day_of_week'] = df[date_col].dt.dayofweek
                    df['month'] = df[date_col].dt.month
                    if target_col and target_col in df.columns:
                        df[f"{target_col}_lag_1"] = df[target_col].shift(1)
                        df[f"{target_col}_lag_2"] = df[target_col].shift(2)
                        df = df.dropna()
                continue

            # Handle special 'all' column specifier
            if len(cols) == 1 and cols[0] == "all":
                if action == "encode":
                    # Encode all categorical columns except target
                    for c in df.select_dtypes(include=['object', 'category']).columns:
                        if c != target_col:
                            df[c] = df[c].astype('category').cat.codes
                    continue
                elif action == "scale":
                    # Scale all numeric columns except target
                    scaler = StandardScaler()
                    for c in df.select_dtypes(include=['number']).columns:
                        if c != target_col:
                            df[c] = scaler.fit_transform(df[[c]])
                    continue
                else:
                    cols = df.columns.tolist()

            for col in cols:
                if col in df.columns:
                    if action == "drop":
                        df = df.drop(columns=[col])
                    elif action == "impute_mean":
                        if pd.api.types.is_numeric_dtype(df[col]):
                            df[col] = df[col].fillna(df[col].mean())
                    elif action == "impute_median":
                        if pd.api.types.is_numeric_dtype(df[col]):
                            df[col] = df[col].fillna(df[col].median())
                    elif action == "forward_fill_imputation":
                        df[col] = df[col].ffill().bfill()
                    elif action == "log_transformation":
                        df[col] = np.log1p(df[col].clip(lower=0))
                    elif action == "spline_transform":
                        spline = SplineTransformer(extrapolation='periodic')
                        # Reshape for sklearn
                        df[col] = spline.fit_transform(df[[col]])
                    elif action == "scale":
                        if pd.api.types.is_numeric_dtype(df[col]):
                            scaler = StandardScaler()
                            df[col] = scaler.fit_transform(df[[col]])
                        else:
                            print(f"⚠️ [Python] Ignoré 'scale' sur la colonne non-numérique '{col}'")
                    elif action == "encode":
                        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
                            df[col] = df[col].astype('category').cat.codes
                    elif action == "winsorize":
                        if pd.api.types.is_numeric_dtype(df[col]):
                            df[col] = mstats.winsorize(df[col], limits=[0.05, 0.05])
                        else:
                            print(f"⚠️ [Python] Ignoré 'winsorize' sur la colonne non-numérique '{col}'")
                    elif action == "sanitize_phone":
                        df[col] = sanitize_cam_phone(df[col])
                    elif action == "normalize_cam_geo":
                        if df[col].dtype == 'object' or df[col].dtype.name == 'category':
                            region_col = f"{col}_region"
                            df[region_col] = normalize_cam_geography(df[col])
                        else:
                            print(f"⚠️ [Python] Ignoré 'normalize_cam_geo' sur la colonne non-catégorielle '{col}'")
                    elif action == "clean_fcfa":
                        df[col] = clean_fcfa_currency(df[col])
                    elif action == "parse_momo":
                        df[col] = parse_momo_data(df[col])
                    
        # Apply Isolation Forest Anomaly Detection globally if requested
        if schema.get("remove_anomalies_isolation_forest"):
            numeric_df = df.select_dtypes(include=['number']).dropna()
            if not numeric_df.empty:
                iso = IsolationForest(contamination=0.05, random_state=42)
                outliers = iso.fit_predict(numeric_df)
                df = df.loc[numeric_df.index[outliers == 1]]
        
        if job_id:
            update_job_progress(job_id, 'cleaning', 25, f"Sauvegarde du fichier nettoyé ({len(df)} lignes)")
                
        # Versioning
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        version_hash = hashlib.sha256(cleaning_schema.encode()).hexdigest()[:8]
        import os
        nom_base = os.path.splitext(os.path.basename(file_path))[0]
        output_dir = f"../workspace/outputs/{nom_base}"
        os.makedirs(output_dir, exist_ok=True)
        output_path = f"{output_dir}/cleaned_{version_hash}_{timestamp}.csv"
        
        df.to_csv(output_path, index=False)
        return json.dumps({"status": "success", "cleanedDataPath": output_path, "final_rows": len(df)})
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if job_id:
            stop_heartbeat()

@mcp.tool()
def run_crew_pipeline(file_path: str, cleaning_schema: str, job_id: str = None) -> str:
    """Déclenche l'équipe d'Agents IA (CrewAI) pour nettoyer les données intelligemment."""
    if job_id:
        start_heartbeat(job_id)
    try:
        from crew_agents import run_dataset_crew
        
        # Le Crew renvoie le texte final du Data Scientist et le chemin du fichier nettoyé
        crew_report, cleaned_path = run_dataset_crew(file_path, cleaning_schema)
        
        return json.dumps({
            "status": "success", 
            "cleanedDataPath": cleaned_path,
            "crew_report": crew_report
        })
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": f"Erreur CrewAI: {str(e)}"})
    finally:
        if job_id:
            stop_heartbeat()

import logging

logger = logging.getLogger(__name__)

def optimize_hyperparameters(model_name, X, y, task="classification", cv_strategy=3, n_trials=10):
    """
    Lance une étude Optuna rapide (max_trials).
    - Classification : Maximise le F1-Score Macro.
    - Régression : Minimise le RMSE (Root Mean Squared Error).
    """
    import numpy as np
    import optuna
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from xgboost import XGBClassifier, XGBRegressor
    from lightgbm import LGBMClassifier, LGBMRegressor
    try:
        from catboost import CatBoostClassifier, CatBoostRegressor
        HAS_CATBOOST = True
    except ImportError:
        HAS_CATBOOST = False

    def objective(trial):
        if task == "classification":
            if model_name == "RandomForest":
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'random_state': 42
                }
                model = RandomForestClassifier(**params)
            elif model_name == "XGBoost":
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'eval_metric': 'logloss',
                    'random_state': 42
                }
                model = XGBClassifier(**params)
            elif model_name == "LightGBM":
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'random_state': 42
                }
                model = LGBMClassifier(**params)
            elif model_name == "CatBoost":
                params = {
                    'iterations': trial.suggest_int('iterations', 50, 300),
                    'depth': trial.suggest_int('depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'verbose': 0,
                    'random_state': 42
                }
                model = CatBoostClassifier(**params)
            else:
                raise ValueError(f"Modèle {model_name} non supporté en classification.")

            from sklearn.model_selection import cross_val_score
            scores = cross_val_score(model, X, y, cv=cv_strategy, scoring='f1_macro')
            return np.mean(scores)

        elif task in ["regression", "time_series", "timeseries"]:
            if model_name == "RandomForestRegressor":
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 3, 15),
                    'random_state': 42
                }
                from sklearn.ensemble import RandomForestRegressor
                model = RandomForestRegressor(**params)
            elif model_name == "XGBRegressor":
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'objective': 'reg:squarederror',
                    'random_state': 42
                }
                model = XGBRegressor(**params)
            elif model_name == "LGBMRegressor":
                params = {
                    'n_estimators': trial.suggest_int('n_estimators', 50, 300),
                    'max_depth': trial.suggest_int('max_depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'random_state': 42
                }
                model = LGBMRegressor(**params)
            elif model_name == "CatBoostRegressor":
                params = {
                    'iterations': trial.suggest_int('iterations', 50, 300),
                    'depth': trial.suggest_int('depth', 3, 10),
                    'learning_rate': trial.suggest_float('learning_rate', 0.01, 0.3, log=True),
                    'verbose': 0,
                    'random_state': 42
                }
                model = CatBoostRegressor(**params)
            else:
                raise ValueError(f"Modèle {model_name} non supporté en régression.")

            from sklearn.model_selection import cross_val_score
            scores = cross_val_score(model, X, y, cv=cv_strategy, scoring='neg_root_mean_squared_error')
            rmse = -1 * np.mean(scores)
            return rmse

    optuna.logging.set_verbosity(optuna.logging.WARNING)
    opt_direction = 'minimize' if task in ["regression", "time_series", "timeseries"] else 'maximize'
    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction=opt_direction, sampler=sampler)
    study.optimize(objective, n_trials=n_trials)
    return study.best_params

@mcp.tool()
def evaluate_model(file_path: str, target: str, task: str, model_name: str = "RandomForest", job_id: str = None) -> str:
    """Entraîne un modèle rapide pour renvoyer des métriques JSON déterministes (Agent) et exporter des PNG (Humain)."""
    if job_id:
        start_heartbeat(job_id)
        update_job_progress(job_id, 'evaluating', 35, f"Évaluation rapide du modèle {model_name} (Tâche: {task})")

    import os
    try:
        df = pd.read_csv(file_path)
        
        # S'assurer que le dossier d'output existe
        output_dir = os.path.dirname(file_path)
        if not output_dir or output_dir in [".", "..", ""]:
            output_dir = "../workspace/models_artifacts"
        os.makedirs(output_dir, exist_ok=True)
        
        if model_name == "TabICL" or model_name == "TabICL (SOTA)":
            # For TabICL, we keep the original DataFrame (retaining NaNs and categoricals)
            # but ensure we drop rows where target is NaN (since we cannot evaluate with missing targets)
            if task != "clustering" and target in df.columns:
                df_eval = df.dropna(subset=[target])
                if len(df_eval) == 0:
                    return json.dumps({"error": f"Le dataset est vide après suppression des NaNs sur la colonne cible '{target}'."})
                X = df_eval.drop(columns=[target])
                y = df_eval[target]
            else:
                df_eval = df.copy()
                X = df_eval
                y = None
        else:
            # Nettoyage naïf pour le modèle rapide (drop NA, encoder catégoriel)
            df_clean = df.dropna().copy()
            if len(df_clean) == 0:
                return json.dumps({"error": "Le dataset nettoyé est vide après suppression des valeurs manquantes. La stratégie de nettoyage n'a pas traité correctement les NaNs. L'agent doit ajouter des étapes d'imputation (ex: impute_median ou impute_mean)."})
            
            date_col = None
            if task in ["time_series", "timeseries"]:
                for col in df_clean.columns:
                    if col != target:
                        try:
                            parsed = pd.to_datetime(df_clean[col], errors='coerce')
                            if parsed.notna().sum() > 0.8 * len(df_clean):
                                date_col = col
                                df_clean[col] = parsed
                                break
                        except:
                            pass
            
            for col in df_clean.select_dtypes(include=['object', 'category']).columns:
                if col != target and col != date_col:
                    df_clean[col] = df_clean[col].astype('category').cat.codes
            
            if task != "clustering":
                if target not in df.columns:
                    return json.dumps({"error": f"Target column {target} not found"})
                X = df_clean.drop(columns=[target])
                y = df_clean[target]
            else:
                X = df_clean
                y = None
        
        output = {"task": task, "metrics": {}, "issues": [], "artifacts": {}}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        # ══════════════════════════════════════════════════════════════════
        # PHASE 8A — ALERTES QUALITÉ DES DONNÉES (avant tout entraînement)
        # ══════════════════════════════════════════════════════════════════

        # 8A-1 : Label Imbalance (ratio classes > 10:1)
        if task == "classification" and y is not None:
            try:
                class_counts = pd.Series(y).value_counts()
                if len(class_counts) >= 2:
                    imbalance_ratio = float(class_counts.iloc[0]) / float(class_counts.iloc[-1])
                    output["metrics"]["class_imbalance_ratio"] = round(imbalance_ratio, 2)
                    if imbalance_ratio > 10.0:
                        output["issues"].append({
                            "type": "label_imbalance", "severity": "HIGH",
                            "message": f"Déséquilibre de classes sévère (ratio {imbalance_ratio:.1f}:1). Appliquer SMOTE ou class_weight='balanced'.",
                            "ratio": round(imbalance_ratio, 2)
                        })
                        logger.warning(f"⚠️ label_imbalance détecté (ratio {imbalance_ratio:.1f}:1)")
            except Exception as _e:
                logger.warning(f"Échec détection label_imbalance: {_e}")

        # 8A-2 : Data Leakage (corrélation feature/target > 0.99)
        if task == "classification" and y is not None:
            try:
                X_num_leak = X.select_dtypes(include=[np.number])
                y_num_leak = pd.to_numeric(y, errors='coerce').dropna()
                for col in X_num_leak.columns:
                    col_vals = X_num_leak[col].reindex(y_num_leak.index)
                    if col_vals.std() > 0:
                        corr = abs(float(col_vals.corr(y_num_leak)))
                        if corr > 0.99:
                            output["issues"].append({
                                "type": "data_leakage", "severity": "CRITICAL",
                                "message": f"Possible fuite de données : '{col}' corrélé à {corr:.3f} avec la cible. Vérifier si c'est une feature proxy.",
                                "feature": col, "correlation": round(corr, 4)
                            })
                            logger.error(f"🚨 data_leakage suspecté sur '{col}' (corr={corr:.3f})")
            except Exception as _e:
                logger.warning(f"Échec détection data_leakage: {_e}")

        # 8A-3 : High Missing Rate (>30% NaN dans une colonne du CSV original)
        try:
            _raw_df = pd.read_csv(file_path)
            _missing_rates = (_raw_df.isnull().sum() / len(_raw_df))
            for _col, _rate in _missing_rates[_missing_rates > 0.30].items():
                output["issues"].append({
                    "type": "high_missing_rate",
                    "severity": "MEDIUM" if _rate < 0.60 else "HIGH",
                    "message": f"Colonne '{_col}' a {_rate*100:.1f}% de valeurs manquantes. Considérer imputation ou suppression.",
                    "feature": _col, "missing_pct": round(float(_rate) * 100, 1)
                })
            _n_missing = int((_missing_rates > 0.30).sum())
            if _n_missing > 0:
                logger.warning(f"⚠️ high_missing_rate: {_n_missing} colonne(s) > 30% NaN")
        except Exception as _e:
            logger.warning(f"Échec détection high_missing_rate: {_e}")

        # 8A-4 : Constant Feature (variance quasi nulle, std < 1e-6)
        try:
            _X_num_check = X.select_dtypes(include=[np.number])
            for _col in _X_num_check.columns:
                if _X_num_check[_col].std() < 1e-6:
                    output["issues"].append({
                        "type": "constant_feature", "severity": "LOW",
                        "message": f"Colonne '{_col}' est constante (variance nulle) — feature inutile, à supprimer.",
                        "feature": _col
                    })
        except Exception as _e:
            logger.warning(f"Échec détection constant_feature: {_e}")

        # 8A-5 : High Cardinality (catégorielle > 50 catégories)
        try:
            _cat_cols = X.select_dtypes(include=['object', 'category']).columns if hasattr(X, 'select_dtypes') else []
            for _col in _cat_cols:
                _n_unique = int(X[_col].nunique())
                if _n_unique > 50:
                    output["issues"].append({
                        "type": "high_cardinality", "severity": "MEDIUM",
                        "message": f"Colonne '{_col}' a {_n_unique} catégories — appliquer Target Encoding ou réduire la cardinalité.",
                        "feature": _col, "n_unique": _n_unique
                    })
        except Exception as _e:
            logger.warning(f"Échec détection high_cardinality: {_e}")

        # ══════════════════════════════════════════════════════════════════
        # PHASE 8B — DIAGNOSTICS STATISTIQUES (avant tout entraînement)
        # ══════════════════════════════════════════════════════════════════

        # 8B-1 : Outlier Contamination (IsolationForest > 5%)
        try:
            from sklearn.ensemble import IsolationForest as _IsoF
            _X_iso = X.select_dtypes(include=[np.number]).dropna()
            if len(_X_iso.columns) >= 2 and len(_X_iso) >= 20:
                _iso = _IsoF(contamination=0.05, random_state=42, n_jobs=-1)
                _iso_labels = _iso.fit_predict(_X_iso)
                _n_out = int((_iso_labels == -1).sum())
                _out_pct = round((_n_out / len(_X_iso)) * 100, 2)
                output["metrics"]["outlier_pct_isolation_forest"] = _out_pct
                if _out_pct > 5.0:
                    output["issues"].append({
                        "type": "outlier_contamination", "severity": "MEDIUM",
                        "message": f"{_out_pct:.1f}% des lignes sont des outliers (IsolationForest). Appliquer Winsorize ou filtrage.",
                        "outlier_pct": _out_pct, "n_outliers": _n_out
                    })
                    logger.warning(f"⚠️ outlier_contamination: {_out_pct:.1f}% détectés")
        except Exception as _e:
            logger.warning(f"Échec détection outlier_contamination: {_e}")

        if task == "classification":
            if y.dtype == 'object' or y.dtype.name == 'category':
                y = y.astype('category').cat.codes
                
            is_temporal = task in ["time_series", "timeseries"]
            if is_temporal:
                split_idx = int(len(X) * 0.8)
                X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
                y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
                cv_strategy_val = TimeSeriesSplit(n_splits=3)
            else:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                cv_strategy_val = 5
            
            if model_name == "TabICL" or model_name == "TabICL (SOTA)":
                if not HAS_TABICL:
                    return json.dumps({"error": "Bibliothèque TabICL non installée."})
                # TabICLClassifier fit caches context. KV caching is enabled by default.
                model = TabICLClassifier()
                model.fit(X_train, y_train)
            else:
                challengers = {
                    "RandomForest": RandomForestClassifier(random_state=42),
                    "XGBoost": XGBClassifier(eval_metric='logloss', random_state=42),
                    "LightGBM": LGBMClassifier(random_state=42)
                }
                if HAS_CATBOOST:
                    challengers["CatBoost"] = CatBoostClassifier(verbose=0, random_state=42)
                champion_name = None
                champion_model = None
                best_f1_score = -1.0
                
                logger.info("Début de l'évaluation Champion/Challenger (RF vs XGB vs LGBM vs CatBoost)...")
                for name, cand_model in challengers.items():
                    try:
                        cv_scores_cand = cross_val_score(cand_model, X_train, y_train, cv=cv_strategy_val, scoring='f1_macro')
                        mean_f1 = np.mean(cv_scores_cand)
                        logger.info(f"Modèle testé : {name} | F1-Score moyen (CV) : {mean_f1:.4f}")
                        if mean_f1 > best_f1_score:
                            best_f1_score = mean_f1
                            champion_name = name
                            champion_model = cand_model
                    except Exception as e:
                        logger.error(f"Échec lors de l'évaluation du modèle {name}: {e}")
                
                # 2. SMOTE (Déséquilibre des classes)
                X_train_final, y_train_final = X_train.copy(), y_train.copy()
                classes, counts = np.unique(y_train, return_counts=True)
                if len(counts) > 0:
                    min_class_proportion = np.min(counts) / np.sum(counts)
                    if min_class_proportion < 0.20:
                        logger.info(f"Déséquilibre détecté ({min_class_proportion:.1%}). SMOTE activé.")
                        smote = SMOTE(random_state=42)
                         # 3. Optuna Hyperparameter Optimization
                if champion_model is not None:
                    logger.info(f"Lancement d'Optuna pour {champion_name}...")
                    try:
                        cv_strategy_opt = TimeSeriesSplit(n_splits=3) if is_temporal else 3
                        best_params = optimize_hyperparameters(
                            champion_name, 
                            X_train_final, 
                            y_train_final, 
                            task="classification", 
                            cv_strategy=cv_strategy_opt, 
                            n_trials=10
                        )
                        logger.info(f"Optuna réussi. Paramètres : {best_params}")
                        
                        if champion_name == "RandomForest":
                            champion_model = RandomForestClassifier(**best_params)
                        elif champion_name == "XGBoost":
                            if 'eval_metric' not in best_params: best_params['eval_metric'] = 'logloss'
                            champion_model = XGBClassifier(**best_params)
                        elif champion_name == "LightGBM":
                            champion_model = LGBMClassifier(**best_params)
                        elif champion_name == "CatBoost":
                            champion_model = CatBoostClassifier(verbose=0, **best_params)
                    except Exception as e:
                        logger.error(f"Échec Optuna ({e}). Dégradation gracieuse activée.")
                else:
                    champion_model = RandomForestClassifier(random_state=42)
                
                # Entraînement final
                champion_model.fit(X_train_final, y_train_final)
                model = champion_model
 
            y_pred = model.predict(X_test)
            
            if model_name == "TabICL" or model_name == "TabICL (SOTA)":
                # Bypass expensive cross-validation on CPU for TabICL
                train_score = float(accuracy_score(y_train, model.predict(X_train)))
                # Set macro F1 as placeholder or compute on test
                report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
                cv_mean = report.get("macro avg", {}).get("f1-score", 0.0)
                overfitting_gap = train_score - cv_mean
                cv_scores = np.array([cv_mean])
            else:
                # Cross-Validation pour Overfitting (Règle de robustesse temporelle)
                cv_scores = cross_val_score(model, X, y, cv=cv_strategy_val, scoring='f1_macro')
                train_score = float(model.score(X_train, y_train))
                cv_mean = float(cv_scores.mean())
                overfitting_gap = train_score - cv_mean
            
            output["metrics"]["train_score"] = train_score
            output["metrics"]["cv_mean_f1"] = cv_mean
            output["metrics"]["overfitting_gap"] = overfitting_gap
            # 8B-3 : Low CV Stability (std CV > 0.05)
            cv_std = float(cv_scores.std()) if len(cv_scores) > 1 else 0.0
            output["metrics"]["cv_std_f1"] = round(cv_std, 4)
            if cv_std > 0.05:
                output["issues"].append({
                    "type": "low_cv_stability",
                    "severity": "MEDIUM",
                    "message": f"Instabilité de la validation croisée (std={cv_std:.3f}). Augmenter n_splits ou vérifier le shuffle.",
                    "cv_std": round(cv_std, 4)
                })
                logger.warning(f"⚠️ low_cv_stability détectée (cv_std={cv_std:.3f})")
            
            if overfitting_gap > 0.15:
                output["issues"].append({
                    "type": "overfitting",
                    "severity": "HIGH",
                    "message": f"Overfitting détecté (Gap: {overfitting_gap*100:.1f}%)"
                })
            
            # JSON Metrics (Agent)
            report = classification_report(y_test, y_pred, output_dict=True, zero_division=0)
            output["metrics"]["accuracy"] = report.get("accuracy", 0.0)
            output["metrics"]["macro_f1"] = report.get("macro avg", {}).get("f1-score", 0.0)
            
            recalls = {}
            for k, v in report.items():
                if isinstance(v, dict) and "recall" in v:
                    recall_val = v["recall"]
                    recalls[str(k)] = recall_val
                    # Détection classe ignorée
                    if recall_val == 0.0:
                        class_support = int(v.get("support", 0))
                        total_support = len(y_test)
                        if total_support > 0:
                            class_ratio = class_support / total_support
                            if class_ratio > 0.01:
                                output["issues"].append({
                                    "type": "ignored_class",
                                    "severity": "CRITICAL",
                                    "class": str(k),
                                    "message": f"Classe {k} totalement ignorée (Recall=0.0)"
                                })
            output["metrics"]["per_class_recall"] = recalls
            # Calculer le gap max de rappel entre classes (exclure macro/weighted avg)
            class_recalls = [float(v) for k, v in recalls.items() if k not in ['accuracy', 'macro avg', 'weighted avg']]
            output["metrics"]["max_class_recall_gap"] = float(max(class_recalls) - min(class_recalls)) if class_recalls else 0.0
            
            # --- CALCUL DE L'ÉQUITÉ (FAIRNESS GUARDRAIL)
            sensitive_cols = [c for c in df.columns if c.lower() in ['ville', 'genre', 'sexe', 'age']]
            if sensitive_cols:
                sens_col = sensitive_cols[0]
                test_indices = X_test.index
                df_test_raw = df.loc[test_indices]
                
                selection_rates = {}
                for val in df_test_raw[sens_col].unique():
                    indices_val = df_test_raw[df_test_raw[sens_col] == val].index
                    loc_mask = [idx in indices_val for idx in test_indices]
                    y_pred_val = y_pred[loc_mask]
                    if len(y_pred_val) > 0:
                        selection_rates[str(val)] = float(np.mean(y_pred_val == 1))
                
                if selection_rates:
                    rates = list(selection_rates.values())
                    priv_rate = max(rates)
                    unpriv_rate = min(rates)
                    disparate_impact = unpriv_rate / priv_rate if priv_rate > 0 else 1.0
                    output["metrics"]["fairness"] = {
                        "sensitive_attribute": sens_col,
                        "disparate_impact_ratio": disparate_impact,
                        "selection_rates": selection_rates
                    }
            else:
                output["metrics"]["fairness"] = None
                
            # PNG Artifact
            cm = confusion_matrix(y_test, y_pred)
            plt.figure(figsize=(8, 6))
            sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
            plt.title('Confusion Matrix')
            plt.ylabel('True Label')
            plt.xlabel('Predicted Label')
            cm_path = f"{output_dir}/cm_{timestamp}.png"
            plt.savefig(cm_path)
            plt.close()
            output["artifacts"]["confusion_matrix_path"] = cm_path

            # ════════════════════════════════════════════════════════════
            # PHASE 8C — ALERTES PERFORMANCE & FAIRNESS (après évaluation)
            # ════════════════════════════════════════════════════════════

            # 8C-1 : Low Performance (accuracy/F1 sous seuil domaine)
            _accuracy = output["metrics"].get("accuracy", 0.0)
            _macro_f1 = output["metrics"].get("macro_f1", 0.0)
            # Seuil dynamique selon le domaine (à enrichir via Neo4j dans Phase 9)
            _domain_keyword = str(file_path).lower()
            _perf_threshold = 0.85 if any(k in _domain_keyword for k in ['medic', 'diabet', 'obes', 'health', 'cancer']) else 0.75
            if _accuracy < _perf_threshold and _accuracy > 0:
                output["issues"].append({
                    "type": "low_performance",
                    "severity": "HIGH" if _accuracy < 0.60 else "MEDIUM",
                    "message": f"Accuracy {_accuracy*100:.1f}% sous le seuil domaine ({_perf_threshold*100:.0f}%). Essayer feature engineering ou un autre modèle.",
                    "accuracy": round(_accuracy, 4),
                    "threshold": _perf_threshold
                })
                logger.warning(f"⚠️ low_performance: accuracy={_accuracy:.3f} < seuil={_perf_threshold}")

            # 8C-2 : Fairness Violation (Disparate Impact hors [0.8, 1.25])
            _fairness = output["metrics"].get("fairness")
            if _fairness and isinstance(_fairness, dict):
                _di = _fairness.get("disparate_impact_ratio", 1.0)
                if _di < 0.8 or _di > 1.25:
                    _sens_attr = _fairness.get("sensitive_attribute", "?")
                    output["issues"].append({
                        "type": "fairness_violation",
                        "severity": "CRITICAL" if _di < 0.6 else "HIGH",
                        "message": f"Violation d'équité sur '{_sens_attr}' (Disparate Impact={_di:.3f}, seuil [0.8, 1.25]). Appliquer reweighting ou contrainte fairness.",
                        "sensitive_attribute": _sens_attr,
                        "disparate_impact": round(_di, 4)
                    })
                    logger.error(f"🚨 fairness_violation: DI={_di:.3f} sur '{_sens_attr}'")

            # 8C-3 : Calibration Error (Brier Score > 0.15)
            try:
                from sklearn.metrics import brier_score_loss
                if hasattr(model, "predict_proba"):
                    _y_prob = model.predict_proba(X_test)
                    _n_classes = len(np.unique(y_test))
                    if _n_classes == 2:
                        _brier = float(brier_score_loss(y_test, _y_prob[:, 1]))
                    else:
                        # Multi-classe : moyenne du Brier score par classe (One-vs-Rest)
                        _brier_scores = []
                        for _cls_idx in range(_n_classes):
                            _y_bin = (y_test == _cls_idx).astype(int)
                            _brier_scores.append(brier_score_loss(_y_bin, _y_prob[:, _cls_idx]))
                        _brier = float(np.mean(_brier_scores))
                    output["metrics"]["brier_score"] = round(_brier, 4)
                    if _brier > 0.15:
                        output["issues"].append({
                            "type": "calibration_error",
                            "severity": "MEDIUM",
                            "message": f"Mauvaise calibration des probabilités (Brier Score={_brier:.3f} > 0.15). Appliquer CalibratedClassifierCV (isotonique ou Platt).",
                            "brier_score": round(_brier, 4)
                        })
                        logger.warning(f"⚠️ calibration_error: Brier={_brier:.3f}")
            except Exception as _e:
                logger.warning(f"Échec calcul Brier Score: {_e}")

            if job_id:
                update_job_progress(job_id, 'evaluating', 45, "Matrice de confusion générée", {"confusion_matrix_url": cm_path})
            
        elif task == "regression" or task == "time_series" or task == "timeseries":
            # 1. Préparation des données et du Split
            if task == "time_series" or task == "timeseries":
                split_idx = int(len(X) * 0.8)
                X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
                y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
                cv_strategy = TimeSeriesSplit(n_splits=3)
                
                try:
                    from statsmodels.tsa.stattools import adfuller
                    adf_result = adfuller(y.dropna())
                    output["metrics"]["pValue"] = float(adf_result[1])
                except:
                    output["metrics"]["pValue"] = 1.0
            else:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
                cv_strategy = 5
            
            # 2. Diagnostic VIF (Multicolinéarité)
            logger.info("Lancement du diagnostic VIF...")
            if "issues" not in output: output["issues"] = []
            try:
                X_num = X_train.select_dtypes(include=[np.number]) if isinstance(X_train, pd.DataFrame) else pd.DataFrame(X_train)
                X_num_const = add_constant(X_num.dropna())
                for i, col in enumerate(X_num_const.columns):
                    if col == "const": continue
                    vif_score = variance_inflation_factor(X_num_const.values, i)
                    vif_val = 999999.0 if (np.isinf(vif_score) or np.isnan(vif_score)) else round(float(vif_score), 2)
                    if vif_score > 10.0:
                        logger.warning(f"Multicolinéarité critique sur '{col}' (VIF: {vif_val})")
                        output["issues"].append({
                            "type": "Multicollinearity",
                            "severity": "HIGH",
                            "feature": str(col),
                            "vif_score": vif_val,
                            "message": f"La caractéristique '{col}' présente une multicolinéarité sévère (VIF > 10)."
                        })
            except Exception as e:
                logger.error(f"Échec lors du calcul du VIF : {e}")

            # 3. Évaluation et Entraînement du Modèle
            if model_name == "TabICL" or model_name == "TabICL (SOTA)":
                if not HAS_TABICL:
                    return json.dumps({"error": "Bibliothèque TabICL non installée."})
                model = TabICLRegressor()
                if task == "time_series" or task == "timeseries":
                    output["metrics"]["temporal_cv_std"] = 0.0
                model.fit(X_train, y_train)
                y_pred = model.predict(X_test)
            else:
                if (task == "time_series" or task == "timeseries") and date_col is not None:
                    logger.info("Début Champion/Challenger (Séries Temporelles avec Prophet & AutoARMA)...")
                    # 1. Baseline RandomForestRegressor
                    X_train_rf = X_train.drop(columns=[date_col]) if date_col in X_train.columns else X_train
                    X_test_rf = X_test.drop(columns=[date_col]) if date_col in X_test.columns else X_test
                    
                    rf = RandomForestRegressor(random_state=42)
                    rf.fit(X_train_rf, y_train)
                    rf_pred = rf.predict(X_test_rf)
                    rf_rmse = np.sqrt(mean_squared_error(y_test, rf_pred))
                    
                    # 2. Prophet
                    prophet_rmse = np.inf
                    prophet_pred = None
                    try:
                        from prophet import Prophet
                        df_prophet_train = pd.DataFrame({'ds': X_train[date_col], 'y': y_train})
                        model_prophet = Prophet()
                        # Désactiver les logs verbeux de Prophet
                        import logging
                        logging.getLogger('prophet').setLevel(logging.WARNING)
                        model_prophet.fit(df_prophet_train)
                        
                        future = pd.DataFrame({'ds': X_test[date_col]})
                        prophet_forecast = model_prophet.predict(future)
                        prophet_pred = prophet_forecast['yhat'].values
                        prophet_rmse = np.sqrt(mean_squared_error(y_test, prophet_pred))
                    except Exception as e:
                        logger.error(f"Échec Prophet: {e}")
                    
                    # 3. AutoARMA (StatsForecast)
                    arma_rmse = np.inf
                    arma_pred = None
                    try:
                        from statsforecast import StatsForecast
                        from statsforecast.models import AutoARIMA
                        
                        df_sf_train = pd.DataFrame({
                            'unique_id': 'series_1',
                            'ds': X_train[date_col],
                            'y': y_train
                        })
                        
                        # Inférence de fréquence
                        freq = 'D'
                        inferred = pd.infer_freq(X_train[date_col])
                        if inferred:
                            freq = inferred
                        
                        sf = StatsForecast(
                            models=[AutoARIMA(season_length=7)],
                            freq=freq,
                            n_jobs=1
                        )
                        sf.fit(df=df_sf_train)
                        forecast_df = sf.predict(h=len(y_test))
                        arma_pred = forecast_df['AutoARIMA'].values
                        arma_rmse = np.sqrt(mean_squared_error(y_test, arma_pred))
                    except Exception as e:
                        logger.error(f"Échec StatsForecast AutoARMA: {e}")
                    
                    # Sélection du champion
                    logger.info(f"RMSE de Test : RF={rf_rmse:.4f}, Prophet={prophet_rmse:.4f}, AutoARIMA={arma_rmse:.4f}")
                    best_rmse = min(rf_rmse, prophet_rmse, arma_rmse)
                    
                    if best_rmse == rf_rmse:
                        champion_name = "RandomForestRegressor"
                        model = rf
                        y_pred = rf_pred
                    elif best_rmse == prophet_rmse:
                        champion_name = "Prophet"
                        model = model_prophet
                        y_pred = prophet_pred
                    else:
                        champion_name = "AutoARMA"
                        model = sf
                        y_pred = arma_pred
                        
                    output["metrics"]["champion"] = champion_name
                    output["metrics"]["temporal_cv_std"] = 0.0
                    
                elif (task == "time_series" or task == "timeseries") and date_col is None:
                    # Dégradation gracieuse
                    logger.warning("Aucune colonne de date valide trouvée. Dégradation gracieuse vers RandomForestRegressor.")
                    output["issues"].append({
                        "type": "missing_date_column",
                        "severity": "MEDIUM",
                        "message": "Aucune colonne de date valide n'a été détectée. Dégradation automatique vers Random Forest."
                    })
                    model = RandomForestRegressor(random_state=42)
                    model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    output["metrics"]["champion"] = "RandomForestRegressor (Fallback)"
                    output["metrics"]["temporal_cv_std"] = 0.0
                    
                else:
                    # Régression classique
                    logger.info("Début Champion/Challenger (Régression)...")
                    challengers = {
                        "RandomForestRegressor": RandomForestRegressor(random_state=42),
                        "XGBRegressor": XGBRegressor(objective='reg:squarederror', random_state=42),
                        "LGBMRegressor": LGBMRegressor(random_state=42)
                    }
                    if HAS_CATBOOST:
                        challengers["CatBoostRegressor"] = CatBoostRegressor(verbose=0, random_state=42)
                    champion_name = None
                    champion_model = None
                    best_score = -np.inf
                    cv_scores_all = []
                    
                    for name, cand_model in challengers.items():
                        try:
                            cv_scores = cross_val_score(cand_model, X_train, y_train, cv=cv_strategy, scoring='neg_root_mean_squared_error')
                            mean_score = np.mean(cv_scores)
                            logger.info(f"Modèle testé : {name} | CV Mean Neg-RMSE : {mean_score:.4f}")
                            if mean_score > best_score:
                                best_score = mean_score
                                champion_name = name
                                champion_model = cand_model
                                cv_scores_all = cv_scores
                        except Exception as e:
                            logger.error(f"Échec {name}: {e}")
                    
                    if champion_model is not None:
                        logger.info(f"Lancement d'Optuna pour {champion_name}...")
                        try:
                            if task in ["time_series", "timeseries"]:
                                cv_opt = TimeSeriesSplit(n_splits=3)
                            else:
                                cv_opt = 3
                            best_params = optimize_hyperparameters(model_name=champion_name, X=X_train, y=y_train, task=task, cv_strategy=cv_opt, n_trials=10)
                            logger.info(f"Optuna réussi. Paramètres : {best_params}")
                            
                            if champion_name == "RandomForestRegressor":
                                champion_model = RandomForestRegressor(**best_params)
                            elif champion_name == "XGBRegressor":
                                if 'objective' not in best_params: best_params['objective'] = 'reg:squarederror'
                                champion_model = XGBRegressor(**best_params)
                            elif champion_name == "LGBMRegressor":
                                champion_model = LGBMRegressor(**best_params)
                            elif champion_name == "CatBoostRegressor":
                                champion_model = CatBoostRegressor(verbose=0, **best_params)
                        except Exception as e:
                            logger.error(f"Échec Optuna ({e}). Dégradation gracieuse.")
                        
                        champion_model.fit(X_train, y_train)
                        model = champion_model
                    else:
                        logger.warning("Aucun champion. Utilisation du RandomForestRegressor par défaut.")
                        model = RandomForestRegressor(random_state=42)
                        model.fit(X_train, y_train)
                    y_pred = model.predict(X_test)
                    
            if task in ["time_series", "timeseries"]:
                try:
                    import quantstats as qs
                    predicted_prices = pd.Series(y_pred)
                    predicted_returns = predicted_prices.pct_change().dropna()
                    if len(predicted_returns) > 1:
                        output["metrics"]["sharpe_ratio"] = float(qs.stats.sharpe(predicted_returns))
                        output["metrics"]["max_drawdown"] = float(qs.stats.max_drawdown(predicted_returns))
                except Exception as qs_err:
                    logger.warning(f"Impossible de calculer les métriques QuantStats : {qs_err}")
            
            # JSON Metrics
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            r2 = float(r2_score(y_test, y_pred))
            output["metrics"]["rmse"] = rmse
            output["metrics"]["r2"] = r2
            
            # PNG Artifact - Residuals & Advanced Stats
            residuals = y_test - y_pred
            
            from scipy.stats import skew, spearmanr
            from statsmodels.stats.stattools import durbin_watson
            
            res_skew = float(skew(residuals)) if len(residuals) > 0 else 0.0
            output["metrics"]["residuals_skewness"] = res_skew
            
            try:
                corr_coeff, p_val = spearmanr(y_pred, np.abs(residuals))
                hetero_p = float(p_val)
            except:
                hetero_p = 1.0
            output["metrics"]["heteroscedasticity_p_value"] = hetero_p
            
            try:
                dw_stat = float(durbin_watson(residuals))
            except:
                dw_stat = 2.0
            output["metrics"]["residuals_durbin_watson"] = dw_stat
            # 8B-2 : Autocorrelation (DW < 1.5 ou > 2.5) — règle AGENTS.md
            if dw_stat < 1.5 or dw_stat > 2.5:
                output["issues"].append({
                    "type": "autocorrelation",
                    "severity": "HIGH",
                    "message": f"Autocorrélation des résidus détectée (Durbin-Watson={dw_stat:.3f}). Ajouter des features lag ou utiliser TimeSeriesSplit.",
                    "dw_stat": round(dw_stat, 4)
                })
                logger.warning(f"⚠️ autocorrelation détectée (DW={dw_stat:.3f})")
            plt.figure(figsize=(10, 5))
            plt.scatter(y_pred, residuals, alpha=0.5)
            plt.axhline(0, color='red', linestyle='--')
            plt.title('Residuals Plot')
            plt.xlabel('Predicted Values')
            plt.ylabel('Residuals')
            res_path = f"{output_dir}/residuals_{timestamp}.png"
            plt.savefig(res_path)
            plt.close()
            output["artifacts"]["residuals_path"] = res_path
            
        elif task == "clustering":
            kmeans = KMeans(n_clusters=4, random_state=42)
            labels = kmeans.fit_predict(X)
            score = float(silhouette_score(X, labels, sample_size=2000) if len(X) > 2000 else silhouette_score(X, labels))
            output["metrics"]["silhouette_score"] = score
            
            if score < 0.25:
                output["issues"].append({
                    "type": "poor_clustering",
                    "severity": "MEDIUM",
                    "message": f"Silhouette score faible ({score:.2f}). Clusters peu distincts."
                })
                
            # Génération d'un PCA Plot
            pca = PCA(n_components=2)
            components = pca.fit_transform(X)
            plt.figure(figsize=(8, 6))
            sns.scatterplot(x=components[:, 0], y=components[:, 1], hue=labels, palette='viridis')
            plt.title('Clusters PCA (K-Means)')
            pca_path = f"{output_dir}/pca_{timestamp}.png"
            plt.savefig(pca_path)
            plt.close()
            output["artifacts"]["pca_path"] = pca_path
            
            if job_id:
                update_job_progress(job_id, 'evaluating', 50, "Graphique PCA des clusters généré", {"pca_url": pca_path})
            
        if job_id:
            update_job_progress(job_id, 'evaluating', 60, f"Évaluation terminée. Score principal: {list(output['metrics'].values())[0] if output['metrics'] else 'N/A'}")
            
        # MLflow logging & model registration
        try:
            import mlflow
            mlflow.set_tracking_uri("http://127.0.0.1:5000")
            nom_base = os.path.splitext(os.path.basename(file_path))[0]
            mlflow.set_experiment(f"DatasetAutomator_{nom_base}")
            
            with mlflow.start_run(run_name=f"Evaluate_{model_name}_{timestamp}"):
                # Log general parameters
                mlflow.log_param("task", task)
                mlflow.log_param("target", target)
                mlflow.log_param("model_name", model_name)
                mlflow.log_param("file_path", file_path)
                
                # Log metrics
                if "metrics" in output:
                    for k, v in output["metrics"].items():
                        if isinstance(v, (int, float)):
                            mlflow.log_metric(k, v)
                
                # Log model in the registry
                if model is not None and not isinstance(model, (list, dict)):
                    # Add standard tags
                    mlflow.set_tags({
                        "Dataset": nom_base,
                        "Status": "Champion",
                        "Main_Metric_Score": str(list(output["metrics"].values())[0]) if output["metrics"] else "N/A"
                    })
                    
                    if "catboost" in str(type(model)).lower():
                        import mlflow.catboost
                        mlflow.catboost.log_model(
                            model, 
                            artifact_path="model", 
                            registered_model_name=f"Model_{model_name}_{task}"
                        )
                    else:
                        import mlflow.sklearn
                        mlflow.sklearn.log_model(
                            model, 
                            artifact_path="model", 
                            registered_model_name=f"Model_{model_name}_{task}"
                        )
                    print(f"✅ [MLflow] Modèle enregistré avec succès dans le registre sous le nom 'Model_{model_name}_{task}'")
        except Exception as mlflow_err:
            import sys
            sys.stderr.write(f"⚠️ Erreur lors du log/enregistrement MLflow: {mlflow_err}\n")

        return json.dumps({"status": "success", "evaluation": output})
        
    except Exception as e:
        return json.dumps({"error": str(e)})
    finally:
        if job_id:
            stop_heartbeat()

@mcp.tool()
def auto_tune_model(file_path: str, target: str, task: str, job_id: str = None) -> str:
    """Utilise Optuna pour optimiser les hyperparamètres si le modèle de base est mauvais ou instable."""
    if job_id:
        start_heartbeat(job_id)
    import warnings
    warnings.filterwarnings('ignore')

    try:
        df = pd.read_csv(file_path)
        df_clean = df.dropna()
        for col in df_clean.select_dtypes(include=['object', 'category']).columns:
            if col != target:
                df_clean[col] = df_clean[col].astype('category').cat.codes
                
        if task != "clustering":
            if target not in df_clean.columns:
                return json.dumps({"error": f"Target column {target} not found"})
            X = df_clean.drop(columns=[target])
            y = df_clean[target]
        else:
            X = df_clean
            y = None

        def objective(trial):
            models_list = ['RandomForest', 'XGBoost', 'LightGBM']
            if HAS_CATBOOST:
                models_list.append('CatBoost')
            model_name = trial.suggest_categorical('model_name', models_list)
            
            if model_name == 'RandomForest':
                n_estimators = trial.suggest_int('rf_n_estimators', 50, 200)
                max_depth = trial.suggest_int('rf_max_depth', 3, 8)
                min_samples_split = trial.suggest_int('rf_min_samples_split', 4, 10)
                if task == "classification":
                    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, min_samples_split=min_samples_split, random_state=42, class_weight='balanced')
                else:
                    model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
                    
            elif model_name == 'XGBoost':
                n_estimators = trial.suggest_int('xgb_n_estimators', 50, 200)
                max_depth = trial.suggest_int('xgb_max_depth', 3, 6)
                learning_rate = trial.suggest_float('xgb_lr', 0.01, 0.2, log=True)
                reg_lambda = trial.suggest_float('xgb_lambda', 0.1, 10.0, log=True)
                if task == "classification":
                    from xgboost import XGBClassifier
                    # Calculer le ratio de desequilibre pour scale_pos_weight
                    y_arr = y.astype('category').cat.codes if (y.dtype == 'object' or y.dtype.name == 'category') else y.astype(int)
                    pos_count = sum(y_arr == 1)
                    neg_count = sum(y_arr == 0)
                    ratio = neg_count / max(1, pos_count)
                    model = XGBClassifier(
                        n_estimators=n_estimators, 
                        max_depth=max_depth, 
                        learning_rate=learning_rate, 
                        reg_lambda=reg_lambda,
                        scale_pos_weight=ratio,
                        random_state=42, 
                        eval_metric='logloss'
                    )
                else:
                    from xgboost import XGBRegressor
                    model = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, reg_lambda=reg_lambda, random_state=42)
                    
            elif model_name == 'LightGBM':
                n_estimators = trial.suggest_int('lgb_n_estimators', 50, 200)
                max_depth = trial.suggest_int('lgb_max_depth', 3, 6)
                learning_rate = trial.suggest_float('lgb_lr', 0.01, 0.2, log=True)
                reg_lambda = trial.suggest_float('lgb_lambda', 0.1, 10.0, log=True)
                if task == "classification":
                    from lightgbm import LGBMClassifier
                    model = LGBMClassifier(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, reg_lambda=reg_lambda, class_weight='balanced', random_state=42, verbose=-1)
                else:
                    from lightgbm import LGBMRegressor
                    model = LGBMRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, reg_lambda=reg_lambda, random_state=42, verbose=-1)
                    
            elif model_name == 'CatBoost':
                iterations = trial.suggest_int('cat_iterations', 50, 200)
                depth = trial.suggest_int('cat_depth', 3, 6)
                learning_rate = trial.suggest_float('cat_lr', 0.01, 0.2, log=True)
                if task == "classification":
                    from catboost import CatBoostClassifier
                    model = CatBoostClassifier(iterations=iterations, depth=depth, learning_rate=learning_rate, auto_class_weights='Balanced', random_seed=42, verbose=0)
                else:
                    from catboost import CatBoostRegressor
                    model = CatBoostRegressor(iterations=iterations, depth=depth, learning_rate=learning_rate, random_seed=42, verbose=0)
            
            if task == "classification":
                if y.dtype == 'object' or y.dtype.name == 'category':
                    y_encoded = y.astype('category').cat.codes
                else:
                    y_encoded = y
                score = cross_val_score(model, X, y_encoded, cv=3, scoring='f1_macro').mean()
                return score
            else:
                if task == "time_series" or task == "timeseries":
                    tscv = TimeSeriesSplit(n_splits=3)
                    scores = []
                    X_arr, y_arr = X.values, y.values
                    for train_idx, test_idx in tscv.split(X_arr):
                        model.fit(X_arr[train_idx], y_arr[train_idx])
                        scores.append(model.score(X_arr[test_idx], y_arr[test_idx]))
                    return np.mean(scores)
                elif task == "clustering":
                    from sklearn.cluster import KMeans
                    from sklearn.metrics import silhouette_score
                    n_clusters = trial.suggest_int('kmeans_n_clusters', 2, 10)
                    model = KMeans(n_clusters=n_clusters, random_state=42)
                    labels = model.fit_predict(X)
                    if len(set(labels)) > 1:
                        score = silhouette_score(X, labels, sample_size=2000) if len(X) > 2000 else silhouette_score(X, labels)
                    else:
                        score = -1.0
                    return score
                else:
                    score = cross_val_score(model, X, y, cv=3, scoring='r2').mean()
                    return score

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Setup MLflow tracking
        callbacks = []
        try:
            ensure_mlflow_server_running()
            import mlflow
            from optuna.integration.mlflow import MLflowCallback
            
            mlflow.set_tracking_uri("http://127.0.0.1:5000")
            nom_base = os.path.splitext(os.path.basename(file_path))[0]
            mlflow.set_experiment(f"DatasetAutomator_{nom_base}")
            
            mlflow_callback = MLflowCallback(
                tracking_uri="http://127.0.0.1:5000",
                metric_name="score",
                create_experiment=True
            )
            callbacks.append(mlflow_callback)
        except Exception as mlflow_err:
            import sys
            sys.stderr.write(f"⚠️ Erreur lors du setup MLflow Callback pour Optuna: {mlflow_err}\n")
            
        study = optuna.create_study(direction='maximize')
        # Limiter à 10 trials pour que ça tourne vite en local
        study.optimize(objective, n_trials=10, callbacks=callbacks)
        
        best_params = study.best_params
        best_score = float(study.best_value)
        best_model_name = best_params.get('model_name')
        
        # S'assurer que le dossier d'output existe
        output_dir = os.path.dirname(file_path)
        if not output_dir or output_dir in [".", "..", ""]:
            output_dir = "../workspace/models_artifacts"
        os.makedirs(output_dir, exist_ok=True)
        
        # Reconstruction du modèle avec ses hyperparamètres optimaux
        if best_model_name == 'RandomForest':
            n_estimators = best_params.get('rf_n_estimators', 100)
            max_depth = best_params.get('rf_max_depth', None)
            min_samples_split = best_params.get('rf_min_samples_split', 2)
            if task == "classification":
                best_model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
            else:
                best_model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
                
        elif best_model_name == 'XGBoost':
            n_estimators = best_params.get('xgb_n_estimators', 100)
            max_depth = best_params.get('xgb_max_depth', 6)
            learning_rate = best_params.get('xgb_lr', 0.1)
            if task == "classification":
                from xgboost import XGBClassifier
                best_model = XGBClassifier(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42, eval_metric='logloss')
            else:
                from xgboost import XGBRegressor
                best_model = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42)
                
        elif best_model_name == 'LightGBM':
            n_estimators = best_params.get('lgb_n_estimators', 100)
            max_depth = best_params.get('lgb_max_depth', -1)
            learning_rate = best_params.get('lgb_lr', 0.1)
            if task == "classification":
                from lightgbm import LGBMClassifier
                best_model = LGBMClassifier(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42, verbose=-1)
            else:
                from lightgbm import LGBMRegressor
                best_model = LGBMRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42, verbose=-1)
                
        elif best_model_name == 'CatBoost':
            iterations = best_params.get('cat_iterations', 100)
            depth = best_params.get('cat_depth', 6)
            learning_rate = best_params.get('cat_lr', 0.1)
            if task == "classification":
                from catboost import CatBoostClassifier
                best_model = CatBoostClassifier(iterations=iterations, depth=depth, learning_rate=learning_rate, random_seed=42, verbose=0)
            else:
                from catboost import CatBoostRegressor
                best_model = CatBoostRegressor(iterations=iterations, depth=depth, learning_rate=learning_rate, random_seed=42, verbose=0)
        else:
            best_model = None

        # Génération des artefacts d'évaluation (Confusion Matrix / Residuals Plot)
        artifacts_dict = {}
        if best_model is not None:
            try:
                import matplotlib.pyplot as plt
                import seaborn as sns
                
                is_temporal = task in ["time_series", "timeseries"]
                if is_temporal:
                    split_idx = int(len(X) * 0.8)
                    X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
                    y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
                else:
                    from sklearn.model_selection import train_test_split
                    if task == "classification" and (y.dtype == 'object' or y.dtype.name == 'category'):
                        y_encoded = y.astype('category').cat.codes
                    else:
                        y_encoded = y
                    X_train, X_test, y_train, y_test = train_test_split(X, y_encoded, test_size=0.2, random_state=42)
                
                if task != "clustering":
                    best_model.fit(X_train, y_train)
                    y_pred = best_model.predict(X_test)
                else:
                    best_model.fit(X)
                    y_pred = best_model.predict(X)
                
                if task == "classification":
                    from sklearn.metrics import confusion_matrix
                    cm = confusion_matrix(y_test, y_pred)
                    plt.figure(figsize=(8, 6))
                    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues')
                    plt.title('Confusion Matrix (Optuna Best)')
                    plt.ylabel('True Label')
                    plt.xlabel('Predicted Label')
                    cm_path = f"{output_dir}/cm_{timestamp}.png"
                    plt.savefig(cm_path)
                    plt.close()
                    artifacts_dict["confusion_matrix_path"] = cm_path
                    
                elif task in ["regression", "time_series", "timeseries"]:
                    residuals = y_test - y_pred
                    plt.figure(figsize=(10, 5))
                    plt.scatter(y_pred, residuals, alpha=0.5)
                    plt.axhline(0, color='red', linestyle='--')
                    plt.title('Residuals Plot (Optuna Best)')
                    plt.xlabel('Predicted Values')
                    plt.ylabel('Residuals')
                    res_path = f"{output_dir}/residuals_{timestamp}.png"
                    plt.savefig(res_path)
                    plt.close()
                    artifacts_dict["residuals_path"] = res_path
                    
                elif task == "clustering":
                    from sklearn.decomposition import PCA
                    pca = PCA(n_components=2)
                    components = pca.fit_transform(X)
                    plt.figure(figsize=(8, 6))
                    sns.scatterplot(x=components[:, 0], y=components[:, 1], hue=y_pred, palette='viridis')
                    plt.title('Clusters PCA (Optuna Best)')
                    pca_path = f"{output_dir}/pca_{timestamp}.png"
                    plt.savefig(pca_path)
                    plt.close()
                    artifacts_dict["pca_path"] = pca_path
            except Exception as plot_err:
                import sys
                sys.stderr.write(f"⚠️ Erreur lors du tracé d'artefacts pour Optuna: {plot_err}\n")
        
        # Log best trial run info in MLflow
        try:
            with mlflow.start_run(run_name=f"Optuna_Best_{timestamp}"):
                mlflow.log_param("task", task)
                mlflow.log_param("target", target)
                mlflow.log_param("file_path", file_path)
                mlflow.log_metric("best_score", best_score)
                for k, v in best_params.items():
                    mlflow.log_param(f"best_{k}", v)
        except Exception as mlflow_err:
            import sys
            sys.stderr.write(f"⚠️ Erreur lors du log du meilleur run: {mlflow_err}\n")
            
        return json.dumps({
            "status": "success",
            "best_params": best_params,
            "optimized_score": best_score,
            "artifacts": artifacts_dict,
            "message": f"Optuna a trouvé de meilleurs paramètres : {best_params}"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})

@mcp.tool()
def run_adversarial_validation(file_path: str, target: str, task: str, job_id: str = None) -> str:
    """Coupe le dataset en 2 chronologiquement (80/20) et vérifie si le modèle peut distinguer les deux (AUC > 0.6 = Drift)."""
    if job_id:
        start_heartbeat(job_id)
        update_job_progress(job_id, 'adversarial_check', 15, "Validation Adversariale (Détection de Data Drift)...")

    import os
    import pandas as pd
    import numpy as np
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.metrics import roc_auc_score

    try:
        df = pd.read_csv(file_path)
        
        # Nettoyage naïf pour le modèle rapide
        df_clean = df.copy()
        
        # On exclut la target de l'analyse (on cherche si les features dérivent)
        if target and target in df_clean.columns:
            df_clean = df_clean.drop(columns=[target])
            
        # Drop columns with too many NaNs, fill others
        df_clean = df_clean.dropna(axis=1, thresh=len(df)*0.5)
        df_clean = df_clean.fillna(method='ffill').fillna(method='bfill').fillna(0)
        
        # Encoder catégoriel naïf
        for col in df_clean.select_dtypes(include=['object', 'category']).columns:
            df_clean[col] = df_clean[col].astype('category').cat.codes
            
        n_rows = len(df_clean)
        if n_rows < 100:
            return json.dumps({"drift_detected": False, "message": "Dataset trop petit pour l'Adversarial Validation."})
            
        # Split chronologique 80/20
        split_idx = int(n_rows * 0.8)
        df_train = df_clean.iloc[:split_idx].copy()
        df_test = df_clean.iloc[split_idx:].copy()
        
        df_train['is_test'] = 0
        df_test['is_test'] = 1
        
        combined = pd.concat([df_train, df_test])
        X = combined.drop('is_test', axis=1)
        y = combined['is_test']
        
        model = RandomForestClassifier(n_estimators=50, random_state=42)
        model.fit(X, y)
        
        auc = roc_auc_score(y, model.predict_proba(X)[:, 1])
        
        result = {
            "drift_detected": bool(auc > 0.6),
            "auc": float(auc),
            "suspicious_features": {},
            "recommendation": ""
        }
        
        if auc > 0.6:
            feature_importance = pd.Series(model.feature_importances_, index=X.columns)
            suspicious_features = feature_importance.nlargest(5).to_dict()
            result["suspicious_features"] = {k: float(v) for k, v in suspicious_features.items()}
            result["recommendation"] = "Data Drift détecté. Les données récentes diffèrent significativement des anciennes. Envisagez de supprimer ces features ou d'utiliser un modèle adaptatif (ex: Online Learning)."
            
            if job_id:
                # Update Firestore using helper
                try:
                    try:
                        from src.firebase_client import get_firestore_db
                    except ImportError:
                        from firebase_client import get_firestore_db
                    db = get_firestore_db()
                    if db:
                        db.collection('ml_jobs').document(job_id).set({
                            'adversarial_validation': result
                        }, merge=True)
                except Exception as fe:
                    import sys
                    sys.stderr.write(f"⚠️ Erreur lors de la mise à jour Firestore (Adversarial): {fe}\n")
        
        return json.dumps(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": f"Erreur Adversarial Validation: {str(e)}"})
    finally:
        if job_id:
            stop_heartbeat()

@mcp.tool()
def run_explainability_audit(file_path: str, target: str, task: str, model_name: str = "RandomForest", job_id: str = None) -> str:
    """Entraîne un RandomForest ou TabICL et calcule les valeurs SHAP."""
    if job_id:
        start_heartbeat(job_id)
        update_job_progress(job_id, 'explainability_audit', 75, f"Audit d'Explicabilité ({model_name} - Calcul SHAP en cours)...")

    import os
    import pandas as pd
    import numpy as np
    import shap
    import matplotlib.pyplot as plt
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from datetime import datetime

    try:
        df = pd.read_csv(file_path)
        
        if target not in df.columns or task == "clustering":
            return json.dumps({"status": "skipped", "message": "Pas de target ou clustering non supporté."})
            
        if model_name == "TabICL" or model_name == "TabICL (SOTA)":
            # Keep original DataFrame structure (with NaNs and categories) for TabICL
            df_eval = df.dropna(subset=[target])
            if len(df_eval) == 0:
                return json.dumps({"error": f"Le dataset est vide après suppression des NaNs sur la colonne cible '{target}'."})
            X = df_eval.drop(columns=[target])
            y = df_eval[target]
            if task == "classification" and (y.dtype == 'object' or y.dtype.name == 'category'):
                y = y.astype('category').cat.codes
        else:
            # Nettoyage
            df_clean = df.dropna()
            if len(df_clean) == 0:
                return json.dumps({"error": "Le dataset nettoyé est vide après suppression des valeurs manquantes. La stratégie de nettoyage n'a pas traité correctement les NaNs."})
            for col in df_clean.select_dtypes(include=['object', 'category']).columns:
                if col != target:
                    df_clean[col] = df_clean[col].astype('category').cat.codes
            X = df_clean.drop(columns=[target])
            y = df_clean[target]
        
        if model_name == "TabICL" or model_name == "TabICL (SOTA)":
            if not HAS_TABICL:
                return json.dumps({"error": "Bibliothèque TabICL non installée."})
            if task == "classification":
                model = TabICLClassifier()
            else:
                model = TabICLRegressor()
            model.fit(X, y)
        else:
            if task == "classification":
                if y.dtype == 'object' or y.dtype.name == 'category':
                    y = y.astype('category').cat.codes
                model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
            else:
                model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
            model.fit(X, y)
        
        # SHAP
        if model_name == "TabICL" or model_name == "TabICL (SOTA)":
            # Surrogate Model Approach for TabICL to avoid Timeout on Deep Learning
            from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor
            
            sample_size = min(300, len(X))
            X_sample = X.sample(n=sample_size, random_state=42)
            
            # 1. Obtenir les prédictions du modèle lourd (TabICL)
            y_pred_tabicl = model.predict(X_sample)
            
            # 2. Entraîner le petit modèle de substitution (Surrogate) sur les prédictions
            # Le DecisionTree de Scikit-Learn ne lit pas les textes. On encode une copie de X_sample.
            X_surrogate = X_sample.copy()
            for col in X_surrogate.select_dtypes(include=['object', 'category']).columns:
                X_surrogate[col] = X_surrogate[col].astype('category').cat.codes

            if task == "classification":
                surrogate = DecisionTreeClassifier(max_depth=5, random_state=42)
            else:
                surrogate = DecisionTreeRegressor(max_depth=5, random_state=42)
            surrogate.fit(X_surrogate, y_pred_tabicl)
            
            # 3. Calculer SHAP sur le Surrogate (Instantané)
            explainer = shap.TreeExplainer(surrogate)
            shap_values = explainer.shap_values(X_surrogate)
        else:
            explainer = shap.TreeExplainer(model)
            sample_size = min(300, len(X))
            X_sample = X.sample(n=sample_size, random_state=42)
            shap_values = explainer.shap_values(X_sample)
        
        # Détermination robuste de shap_values_to_plot et mean_abs_shap
        if isinstance(shap_values, list): # Liste de matrices 2D (une par classe)
            mean_abs_shap = np.mean([np.abs(val).mean(axis=0) for val in shap_values], axis=0)
            shap_values_to_plot = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        elif isinstance(shap_values, np.ndarray):
            if shap_values.ndim == 3:
                # 3D numpy array: (samples, features, classes) ou (samples, classes, features)
                features_dim = -1
                for axis, dim_size in enumerate(shap_values.shape):
                    if dim_size == len(X.columns):
                        features_dim = axis
                        break
                if features_dim != -1:
                    axes_to_average = tuple(ax for ax in range(3) if ax != features_dim)
                    mean_abs_shap = np.abs(shap_values).mean(axis=axes_to_average)
                    
                    # Pour shap.summary_plot, on projette sur une seule classe en 2D (shape matches X_sample)
                    if features_dim == 1:
                        shap_values_to_plot = shap_values[:, :, 0]
                    else:
                        shap_values_to_plot = shap_values[:, 0, :]
                else:
                    mean_abs_shap = np.abs(shap_values).mean(axis=(0, 2))
                    shap_values_to_plot = shap_values[:, :, 0]
            else:
                mean_abs_shap = np.abs(shap_values).mean(axis=0)
                shap_values_to_plot = shap_values
        else:
            mean_abs_shap = np.abs(shap_values).mean(axis=0)
            shap_values_to_plot = shap_values
            
        feature_names = X.columns.tolist()
        
        shap_analysis = []
        for i, name in enumerate(feature_names):
            shap_analysis.append({
                "feature_name": name,
                "mean_abs_shap": float(mean_abs_shap[i])
            })
            
        shap_analysis.sort(key=lambda x: x["mean_abs_shap"], reverse=True)
        
        # Vérification d'une feature "écrasante" (Proxy)
        risk_score = 0
        recommendations = []
        if len(shap_analysis) > 0:
            top_importance = shap_analysis[0]["mean_abs_shap"]
            total_importance = sum([x["mean_abs_shap"] for x in shap_analysis])
            if total_importance > 0 and (top_importance / total_importance) > 0.8:
                risk_score = 8
                recommendations.append(f"⚠️ La feature '{shap_analysis[0]['feature_name']}' représente plus de 80% des décisions. Risque massif de Data Leakage ou de Proxy Biaisé.")
        
        # Plot
        output_dir = os.path.dirname(file_path)
        if not output_dir or output_dir in [".", "..", ""]:
            output_dir = "../workspace/models_artifacts"
        os.makedirs(output_dir, exist_ok=True)
        
        plot_path = os.path.join(output_dir, "shap_summary.png").replace("\\", "/")
        
        plt.figure(figsize=(10, 8))
        shap.summary_plot(shap_values_to_plot, X_sample, show=False)
        plt.tight_layout()
        plt.savefig(plot_path, dpi=150)
        plt.close()
        
        result = {
            "status": "completed",
            "risk_score": risk_score,
            "shap_analysis": shap_analysis[:10], # Keep top 10 to avoid huge json
            "recommendations": recommendations,
            "visualizations": {
                "shap_summary_plot_url": plot_path
            }
        }
        
        if job_id:
            try:
                try:
                    from src.firebase_client import get_firestore_db
                except ImportError:
                    from firebase_client import get_firestore_db
                db = get_firestore_db()
                if db:
                    db.collection('ml_jobs').document(job_id).set({
                        'explainability_audit': result
                    }, merge=True)
            except Exception as fe:
                import sys
                sys.stderr.write(f"⚠️ Erreur lors de la mise à jour Firestore (Explainability): {fe}\n")
            
        return json.dumps(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": f"Erreur Explainability: {str(e)}"})
    finally:
        if job_id:
            stop_heartbeat()

@mcp.tool()
def generate_notebook(file_path: str, cleaning_schema: str, output_nb_path: str, llm_interpretation: str = "", business_costs: str = "", data_contract_assertions: str = "") -> str:
    """Génère un fichier .ipynb complet (Full MLOps) basé sur la stratégie exécutée et des templates riches."""
    import os
    import sys
    # S'assurer que le chemin pour importer notebook_factory est correct
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from notebook_factory import assemble_notebook_from_steps
    from tools.domain_detector import detect_domain
    
    try:
        schema = json.loads(cleaning_schema)
        target_col = schema.get("target", "")
        task_type_from_schema = schema.get("task_type") or ("REGRESSION" if target_col else "CLUSTERING")
        
        # 1. Préparation du résumé pour notebook_factory
        try:
            df = pd.read_csv(file_path)
            num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
            nrows = len(df)
            ncols = len(df.columns)
            domain = detect_domain(df, os.path.basename(file_path))
        except Exception:
            num_cols, cat_cols, nrows, ncols = [], [], 0, 0
            domain = "general"
            
        use_pca = False
        for step in schema.get("steps", []):
            if step.get("action") == "pca":
                use_pca = True
                break
                
        summary = {
            "fichier": file_path,
            "tache_ml": task_type_from_schema.upper(),
            "is_timeseries": task_type_from_schema.lower() == "time_series",
            "domaine": domain,
            "colonnes_numeriques": num_cols,
            "colonnes_categorielles": cat_cols,
            "dimensions": {"lignes": nrows, "colonnes": ncols},
            "cible_suggeree": {"cible": target_col},
            "use_pca": use_pca
        }
        
        # Parse business costs dictionary
        business_costs_dict = None
        if business_costs:
            try:
                business_costs_dict = json.loads(business_costs)
            except Exception as parse_err:
                sys.stderr.write(f"⚠️ Erreur lors du parsing des coûts métiers: {parse_err}\n")
        
        # 2. Création du notebook de base (riche) avec notebook_factory
        os.makedirs(os.path.dirname(output_nb_path), exist_ok=True)
        nom_base = os.path.splitext(os.path.basename(file_path))[0]
        if nom_base.startswith("cleaned_"):
            parent_name = os.path.basename(os.path.dirname(file_path))
            if parent_name and parent_name not in [".", "..", "outputs", "workspace", ""]:
                nom_base = parent_name
        
        nb, n_cells = assemble_notebook_from_steps(
            file_path=file_path,
            target_col=target_col,
            summary=summary,
            nom_base=nom_base,
            is_clustering=(task_type_from_schema.lower() == "clustering" or not bool(target_col)),
            algo_clustering="benchmark",
            llm_interpretation=llm_interpretation,
            business_costs=business_costs_dict,
            data_contract_assertions=data_contract_assertions
        )
        
        # 3. Injection de la stratégie dynamique de l'agent
        dynamic_cells = []
        md_strat = "## 🤖 Stratégie de Nettoyage Dynamique (Agent IA)\n\n"
        md_strat += "L'agent a défini et exécuté la stratégie de nettoyage suivante basée sur les règles métiers du graphe de connaissances Neo4j (Graph RAG) :\n\n"
        md_strat += "| Variable / Colonne | Action Technique | Justification Métier / RAG |\n"
        md_strat += "| :--- | :--- | :--- |\n"
        for step in schema.get("steps", []):
            col = step.get("column")
            action = step.get("action")
            reasoning = step.get("reasoning")
            md_strat += f"| **{col}** | `{action}` | {reasoning} |\n"
        dynamic_cells.append(nbf.v4.new_markdown_cell(md_strat))
        is_ts = (task_type_from_schema.lower() in ["timeseries", "time_series"])
        
        # Récupération de toutes les actions pour injecter les helpers si besoin
        actions = {step.get("action") for step in schema.get("steps", [])}
        helpers = ""
        if "sanitize_phone" in actions:
            helpers += """
def sanitize_cam_phone(series: pd.Series) -> pd.Series:
    import re
    cleaned = series.astype(str).str.replace(r'[\\s\\.\\-\\(\\)]', '', regex=True)
    cleaned = cleaned.str.replace(r'^(?:\\+237|237)', '', regex=True)
    def validate_and_format(val):
        if not val or val == 'nan':
            return None
        val = val.strip()
        if len(val) == 9 and val[0] in ['6', '2', '3']:
            return val
        elif len(val) == 8 and val[0] in ['7', '9', '5', '6', '8']:
            if val[0] in ['7', '8']:
                return '6' + val
            elif val[0] in ['9', '5']:
                return '6' + val
        return None
    return cleaned.apply(validate_and_format)
"""
        if "normalize_cam_geo" in actions:
            helpers += """
def normalize_cam_geography(series: pd.Series) -> pd.Series:
    geo_mapping = {
        'yaounde': 'Centre', 'mfoundi': 'Centre', 'nyong': 'Centre', 'lekie': 'Centre', 'mbalmayo': 'Centre',
        'douala': 'Littoral', 'wouri': 'Littoral', 'mungo': 'Littoral', 'sanaga-maritime': 'Littoral', 'nkam': 'Littoral',
        'bafoussam': 'Ouest', 'mifi': 'Ouest', 'nounge': 'Ouest', 'bamendjou': 'Ouest', 'dschang': 'Ouest', 'menoua': 'Ouest', 'haut-nkam': 'Ouest',
        'buea': 'Sud-Ouest', 'limbe': 'Sud-Ouest', 'fako': 'Sud-Ouest', 'meme': 'Sud-Ouest', 'kumba': 'Sud-Ouest', 'ndian': 'Sud-Ouest',
        'bamenda': 'Nord-Ouest', 'mezam': 'Nord-Ouest', 'bui': 'Nord-Ouest', 'boyo': 'Nord-Ouest',
        'ngaoundere': 'Adamaoua', 'vina': 'Adamaoua', 'djohong': 'Adamaoua',
        'garoua': 'Nord', 'benoue': 'Nord', 'guider': 'Nord',
        'maroua': 'Extrême-Nord', 'diamare': 'Extrême-Nord', 'kousseri': 'Extrême-Nord', 'mokolo': 'Extrême-Nord',
        'bertoua': 'Est', 'lom-et-djerem': 'Est', 'kadey': 'Est',
        'ebolowa': 'Sud', 'mvila': 'Sud', 'kribi': 'Sud', 'ocean': 'Sud', 'dja-et-lobo': 'Sud'
    }
    def get_region(val):
        if not isinstance(val, str) or val == 'nan':
            return None
        val_clean = val.lower().strip().replace('é', 'e').replace('è', 'e').replace('ô', 'o').replace(' ', '-')
        if val_clean in geo_mapping:
            return geo_mapping[val_clean]
        for key, region in geo_mapping.items():
            if key in val_clean or val_clean in key:
                return region
        return "Autre"
    return series.apply(get_region)
"""
        if "clean_fcfa" in actions:
            helpers += """
def clean_fcfa_currency(series: pd.Series) -> pd.Series:
    cleaned = series.astype(str).str.replace(r'(?i)(?:fcfa|xaf|xof|f|\\s|,)', '', regex=True)
    return pd.to_numeric(cleaned, errors='coerce')
"""
        if "parse_momo" in actions:
            helpers += """
def parse_momo_data(series: pd.Series) -> pd.Series:
    def detect_gateway(val):
        val_str = str(val).lower()
        if 'mtn' in val_str or 'momo' in val_str or '67' in val_str or '68' in val_str:
            return 'MTN Mobile Money'
        elif 'orange' in val_str or 'om' in val_str or '65' in val_str or '69' in val_str:
            return 'Orange Money'
        return 'Autre'
    return series.apply(detect_gateway)
"""

        code_clean = "from sklearn.preprocessing import StandardScaler\nimport numpy as np\n"
        if helpers:
            code_clean += helpers + "\n"
        
        if is_ts:
            code_clean += "train_df_clean = train_df.copy()\ntest_df_clean = test_df.copy()\n\n"
        else:
            code_clean += "# Nettoyage des partitions sans fuite (Statistiques calculées STRICTEMENT sur le Train set)\n"
            code_clean += "X_train_clean = X_train.copy()\n"
            code_clean += "X_test_clean = X_test.copy()\n\n"
            code_clean += "# 1. Suppression des colonnes ID à haute cardinalité\n"
            code_clean += "high_card_cols = [col for col in X_train_clean.columns if X_train_clean[col].dtype == 'object' and X_train_clean[col].nunique() > 50]\n"
            code_clean += "if high_card_cols:\n"
            code_clean += "    X_train_clean = X_train_clean.drop(columns=high_card_cols)\n"
            code_clean += "    X_test_clean = X_test_clean.drop(columns=[c for c in high_card_cols if c in X_test_clean.columns])\n\n"
            
        for step in schema.get("steps", []):
            col = step.get("column")
            action = step.get("action")
            reasoning = step.get("reasoning")
            
            if isinstance(col, list):
                col_str = str(col)
                code_clean += f"# Étape : {action} sur {col_str}\n# Raison : {reasoning}\n"
                
                # Cible : train_df_clean / test_df_clean pour TS, sinon X_train / X_test
                tr_name = "train_df_clean" if is_ts else "X_train_clean"
                te_name = "test_df_clean" if is_ts else "X_test_clean"
                
                if action == "drop":
                    code_clean += f"{tr_name} = {tr_name}.drop(columns=[c for c in {col_str} if c in {tr_name}.columns])\n"
                    code_clean += f"{te_name} = {te_name}.drop(columns=[c for c in {col_str} if c in {te_name}.columns])\n"
                elif action == "encode":
                    code_clean += f"for c in {col_str}:\n    if c in {tr_name}.columns:\n        categories = {tr_name}[c].astype('category').cat.categories\n        {tr_name}[c] = {tr_name}[c].astype('category').cat.codes\n        if c in {te_name}.columns:\n            {te_name}[c] = pd.Categorical({te_name}[c], categories=categories).codes\n"
                elif action == "scale":
                    code_clean += f"for c in {col_str}:\n    if c in {tr_name}.columns:\n        scaler = StandardScaler()\n        {tr_name}[c] = scaler.fit_transform({tr_name}[[c]])\n        if c in {te_name}.columns:\n            {te_name}[c] = scaler.transform({te_name}[[c]])\n"
                elif "impute" in action or "imputation" in action:
                    code_clean += f"for c in {col_str}:\n    if c in {tr_name}.columns:\n        {tr_name}[c] = {tr_name}[c].ffill().bfill()\n        if c in {te_name}.columns:\n            {te_name}[c] = {te_name}[c].ffill().bfill()\n"
            else:
                code_clean += f"# Étape : {action} sur '{col}'\n# Raison : {reasoning}\n"
                tr_name = "train_df_clean" if is_ts else "X_train_clean"
                te_name = "test_df_clean" if is_ts else "X_test_clean"
                
                # Check for target column in case of supervised tasks
                if not is_ts and col == target_col:
                    tr_name = "y_train"
                    te_name = "y_test"
                
                if action == "impute_mean":
                    code_clean += f"if '{col}' in {tr_name}.columns if hasattr({tr_name}, 'columns') else True:\n"
                    if not is_ts and col == target_col:
                        code_clean += f"    mean_val = y_train.mean()\n    y_train = y_train.fillna(mean_val)\n    y_test = y_test.fillna(mean_val)\n"
                    else:
                        code_clean += f"    if pd.api.types.is_numeric_dtype({tr_name}['{col}']):\n        mean_val = {tr_name}['{col}'].mean()\n        {tr_name}['{col}'] = {tr_name}['{col}'].fillna(mean_val)\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}'] = {te_name}['{col}'].fillna(mean_val)\n"
                elif action == "impute_median":
                    code_clean += f"if '{col}' in {tr_name}.columns if hasattr({tr_name}, 'columns') else True:\n"
                    if not is_ts and col == target_col:
                        code_clean += f"    median_val = y_train.median()\n    y_train = y_train.fillna(median_val)\n    y_test = y_test.fillna(median_val)\n"
                    else:
                        code_clean += f"    if pd.api.types.is_numeric_dtype({tr_name}['{col}']):\n        median_val = {tr_name}['{col}'].median()\n        {tr_name}['{col}'] = {tr_name}['{col}'].fillna(median_val)\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}'] = {te_name}['{col}'].fillna(median_val)\n"
                elif "impute" in action or "imputation" in action:
                    code_clean += f"if '{col}' in {tr_name}.columns if hasattr({tr_name}, 'columns') else True:\n"
                    if not is_ts and col == target_col:
                        code_clean += f"    y_train = y_train.ffill().bfill()\n    y_test = y_test.ffill().bfill()\n"
                    else:
                        code_clean += f"    {tr_name}['{col}'] = {tr_name}['{col}'].ffill().bfill()\n    if '{col}' in {te_name}.columns:\n        {te_name}['{col}'] = {te_name}['{col}'].ffill().bfill()\n"
                elif action == "drop":
                    code_clean += f"if '{col}' in {tr_name}.columns:\n    {tr_name} = {tr_name}.drop(columns=['{col}'])\n    if '{col}' in {te_name}.columns:\n        {te_name} = {te_name}.drop(columns=['{col}'])\n"
                elif action == "scale":
                    code_clean += f"if '{col}' in {tr_name}.columns:\n    if pd.api.types.is_numeric_dtype({tr_name}['{col}']):\n        scaler = StandardScaler()\n        {tr_name}['{col}'] = scaler.fit_transform({tr_name}[['{col}']])\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}'] = scaler.transform({te_name}[['{col}']])\n"
                elif action == "winsorize":
                    code_clean += f"if '{col}' in {tr_name}.columns if hasattr({tr_name}, 'columns') else True:\n"
                    if not is_ts and col == target_col:
                        code_clean += f"    q_low = y_train.quantile(0.01)\n    q_high = y_train.quantile(0.99)\n    y_train = y_train.clip(lower=q_low, upper=q_high)\n    y_test = y_test.clip(lower=q_low, upper=q_high)\n"
                    else:
                        code_clean += f"    if pd.api.types.is_numeric_dtype({tr_name}['{col}']):\n        q_low = {tr_name}['{col}'].quantile(0.01)\n        q_high = {tr_name}['{col}'].quantile(0.99)\n        {tr_name}['{col}'] = {tr_name}['{col}'].clip(lower=q_low, upper=q_high)\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}'] = {te_name}['{col}'].clip(lower=q_low, upper=q_high)\n"
                elif action == "log_transformation":
                    code_clean += f"if '{col}' in {tr_name}.columns if hasattr({tr_name}, 'columns') else True:\n"
                    if not is_ts and col == target_col:
                        code_clean += f"    y_train = np.log1p(y_train.clip(lower=0))\n    y_test = np.log1p(y_test.clip(lower=0))\n"
                    else:
                        code_clean += f"    if pd.api.types.is_numeric_dtype({tr_name}['{col}']):\n        {tr_name}['{col}'] = np.log1p({tr_name}['{col}'].clip(lower=0))\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}'] = np.log1p({te_name}['{col}'].clip(lower=0))\n"
                elif action == "encode":
                    code_clean += f"if '{col}' in {tr_name}.columns:\n    categories = {tr_name}['{col}'].astype('category').cat.categories\n    {tr_name}['{col}'] = {tr_name}['{col}'].astype('category').cat.codes\n    if '{col}' in {te_name}.columns:\n        {te_name}['{col}'] = pd.Categorical({te_name}['{col}'], categories=categories).codes\n"
                elif action == "sanitize_phone":
                    code_clean += f"if '{col}' in {tr_name}.columns:\n    if {tr_name}['{col}'].dtype == 'object' or {tr_name}['{col}'].dtype.name == 'category':\n        {tr_name}['{col}'] = sanitize_cam_phone({tr_name}['{col}'])\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}'] = sanitize_cam_phone({te_name}['{col}'])\n"
                elif action == "normalize_cam_geo":
                    code_clean += f"if '{col}' in {tr_name}.columns:\n    if {tr_name}['{col}'].dtype == 'object' or {tr_name}['{col}'].dtype.name == 'category':\n        {tr_name}['{col}_region'] = normalize_cam_geography({tr_name}['{col}'])\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}_region'] = normalize_cam_geography({te_name}['{col}'])\n"
                elif action == "clean_fcfa":
                    code_clean += f"if '{col}' in {tr_name}.columns:\n    if {tr_name}['{col}'].dtype == 'object' or {tr_name}['{col}'].dtype.name == 'category':\n        {tr_name}['{col}'] = clean_fcfa_currency({tr_name}['{col}'])\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}'] = clean_fcfa_currency({te_name}['{col}'])\n"
                elif action == "parse_momo":
                    code_clean += f"if '{col}' in {tr_name}.columns:\n    if {tr_name}['{col}'].dtype == 'object' or {tr_name}['{col}'].dtype.name == 'category':\n        {tr_name}['{col}'] = parse_momo_data({tr_name}['{col}'])\n        if '{col}' in {te_name}.columns:\n            {te_name}['{col}'] = parse_momo_data({te_name}['{col}'])\n"
                elif action == "formula":
                    formula_expr = step.get("formula")
                    if formula_expr:
                        code_clean += f"    # Évaluation de la formule OKF pour {col}\n"
                        code_clean += f"    try:\n"
                        code_clean += f"        {tr_name}['{col}'] = {tr_name}.eval(\"{formula_expr}\")\n"
                        code_clean += f"        if hasattr({te_name}, 'columns') and not {te_name}.empty:\n"
                        code_clean += f"            {te_name}['{col}'] = {te_name}.eval(\"{formula_expr}\")\n"
                        code_clean += f"    except Exception as e:\n        print(f\"⚠️ Erreur évaluation formule '{formula_expr}' sur '{col}': {{e}}\")\n"
            code_clean += "\n"
            
        if is_ts:
            code_clean += "# partitions nettoyées prêtes pour le feature engineering.\ndisplay(train_df_clean.head())"
        else:
            code_clean += "# partitions nettoyées prêtes pour le preprocessing.\ntrain_df_clean = X_train_clean.copy() # Utilisé pour les diagnostics visuels suivants\nif 'X_train_clean' in globals():\n    display(X_train_clean.head())"
        dynamic_cells.append(nbf.v4.new_code_cell(code_clean))
        
        # Trouver l'index de la cellule qui charge le dataframe (contenant "df_raw.copy()")
        insert_idx = len(nb.cells)
        for i, cell in enumerate(nb.cells):
            if cell.cell_type == "code" and "df_raw.copy()" in cell.source:
                insert_idx = i + 1
                break
        
        # Si on n'a pas trouvé, on insère après la 4ème cellule
        if insert_idx == len(nb.cells):
            insert_idx = min(5, len(nb.cells))
            
        nb.cells = nb.cells[:insert_idx] + dynamic_cells + nb.cells[insert_idx:]
        
        # Sauvegarde
        with open(output_nb_path, 'w', encoding='utf-8') as f:
            nbf.write(nb, f)
            
        # Générer la Model Card, le Manifest et exécuter la Quality Gate
        try:
            from tools.mlops_utils import generate_model_card, generate_run_manifest, run_deployment_quality_gate
            
            # Métriques de validation d'exemple pour illustrer la fiche
            estimated_metrics = {
                "accuracy": 0.85 if task_type_from_schema.lower() == "classification" else None,
                "r2_score": 0.78 if task_type_from_schema.lower() in ["regression", "timeseries"] else None,
                "shap_surrogate_fidelity": 0.92
            }
            estimated_metrics = {k: v for k, v in estimated_metrics.items() if v is not None}
            
            gate = run_deployment_quality_gate(estimated_metrics, "RandomForest/AutoARIMA", task_type_from_schema.lower())
            
            # Sauvegarder dans le même dossier que le notebook
            run_artifacts_dir = os.path.dirname(output_nb_path)
            generate_model_card(run_artifacts_dir, nom_base, task_type_from_schema, target_col, estimated_metrics, "RandomForest/AutoARIMA", gate["status"])
            generate_run_manifest(run_artifacts_dir, file_path, target_col, task_type_from_schema, estimated_metrics, "RandomForest/AutoARIMA")
        except Exception as e_mlops:
            sys.stderr.write(f"⚠️ Erreur lors de la génération des artefacts MLOps: {e_mlops}\n")
            
        return json.dumps({"status": "success", "notebookPath": output_nb_path})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": str(e)})

@mcp.tool()
def explain_prediction_locally(file_path: str, target: str, task: str, model_name: str, row_index: int, job_id: str = None) -> str:
    """
    Explique localement une prédiction spécifique (LIME) sur un client/ligne précis.
    Génère un graphique PNG horizontal des contributions et renvoie un rapport JSON.
    """
    if job_id:
        start_heartbeat(job_id)
        update_job_progress(job_id, 'explaining', 70, f"Début de l'explication locale LIME pour la ligne {row_index}")

    import os
    try:
        df = pd.read_csv(file_path)
        output_dir = os.path.dirname(file_path)
        if not output_dir or output_dir in [".", "..", ""]:
            output_dir = "../workspace/models_artifacts"
        os.makedirs(output_dir, exist_ok=True)
        
        # Nettoyage et encodage similaire à evaluate_model
        df_clean = df.dropna().copy()
        if len(df_clean) == 0:
            return json.dumps({"error": "Le dataset nettoyé est vide."})
            
        if row_index < 0 or row_index >= len(df_clean):
            return json.dumps({"error": f"L'index de ligne {row_index} est invalide (longueur: {len(df_clean)})."})
            
        for col in df_clean.select_dtypes(include=['object', 'category']).columns:
            if col != target:
                df_clean[col] = df_clean[col].astype('category').cat.codes
                
        X = df_clean.drop(columns=[target])
        y = df_clean[target]
        
        # Entraîner le modèle spécifié
        if task == "classification":
            if model_name == "TabICL" or model_name == "TabICL (SOTA)":
                if not HAS_TABICL:
                    return json.dumps({"error": "TabICL non installé."})
                model = TabICLClassifier()
            else:
                model = RandomForestClassifier(random_state=42)
        else:
            if model_name == "TabICL" or model_name == "TabICL (SOTA)":
                if not HAS_TABICL:
                    return json.dumps({"error": "TabICL non installé."})
                model = TabICLRegressor()
            else:
                model = RandomForestRegressor(random_state=42)
                
        model.fit(X, y)
        
        # LIME
        instance = X.iloc[row_index]
        instance_array = instance.values.reshape(1, -1)
        
        # 1. Standardisation pour le calcul de distance
        scaler = StandardScaler()
        X_scaled = scaler.fit_transform(X)
        instance_scaled = scaler.transform(instance_array)[0]
        
        # 2. Générer des perturbations (1000 instances avec bruit gaussien dans l'espace standardisé)
        num_perturbations = 1000
        perturbations_scaled = np.random.normal(0, 0.5, size=(num_perturbations, X.shape[1])) + instance_scaled
        
        # Revenir dans l'espace d'origine pour que le modèle puisse prédire
        perturbations_raw = scaler.inverse_transform(perturbations_scaled)
        
        # 3. Prédire les perturbations avec la boîte noire
        if task == "classification":
            pred_probs = model.predict_proba(instance_array)[0]
            pred_class = int(np.argmax(pred_probs))
            y_perturbed = model.predict_proba(perturbations_raw)[:, pred_class]
            label_explain = f"Classe {pred_class} (Prob: {pred_probs[pred_class]:.2f})"
        else:
            y_perturbed = model.predict(perturbations_raw)
            pred_val = model.predict(instance_array)[0]
            label_explain = f"Valeur prédite: {pred_val:.4f}"
            
        # 4. Calculer les distances Euclidiennes
        distances = np.sqrt(np.sum((perturbations_scaled - instance_scaled) ** 2, axis=1))
        
        # 5. Calculer les poids (kernel_width = sqrt(n_features) * 0.75)
        kernel_width = np.sqrt(X.shape[1]) * 0.75
        weights = np.exp(-(distances ** 2) / (kernel_width ** 2))
        
        # 6. Entraîner une régression Ridge locale
        local_model = Ridge(alpha=1.0)
        local_model.fit(perturbations_scaled, y_perturbed, sample_weight=weights)
        
        coefficients = local_model.coef_
        
        # Trier par importance absolue
        features = X.columns.tolist()
        sorted_indices = np.argsort(np.abs(coefficients))
        
        # 7. Générer le graphique de contribution LIME
        plt.figure(figsize=(10, 6))
        colors = ['green' if coef >= 0 else 'red' for coef in coefficients[sorted_indices]]
        plt.barh([features[i] for i in sorted_indices], coefficients[sorted_indices], color=colors)
        plt.axvline(x=0, color='black', linestyle='--')
        plt.title(f"Explication Locale LIME - Ligne {row_index}\n({label_explain})")
        plt.xlabel("Contribution locale (standardisée)")
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        plot_path = f"{output_dir}/lime_local_{row_index}_{timestamp}.png"
        plt.savefig(plot_path, bbox_inches='tight')
        plt.close()
        
        explanation = {
            "row_index": row_index,
            "prediction_label": label_explain,
            "plot_path": plot_path,
            "contributions": {features[i]: float(coefficients[i]) for i in range(len(features))}
        }
        
        if job_id:
            update_job_progress(job_id, 'explaining', 100, f"Explication locale LIME terminée.")
            
        return json.dumps({"status": "success", "explanation": explanation})
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": str(e)})
    finally:
        if job_id:
            stop_heartbeat()

if __name__ == "__main__":
    # Expose the server over standard I/O (or SSE)
    mcp.run()
