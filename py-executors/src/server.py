from fastmcp import FastMCP
import pandas as pd
import json
import hashlib
from datetime import datetime
from sklearn.preprocessing import SplineTransformer
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans, DBSCAN
from sklearn.metrics import silhouette_score
import nbformat as nbf

# Initialize the FastMCP server
mcp = FastMCP("DatasetAutomator")

try:
    from src.firebase_client import update_job_progress, start_heartbeat, stop_heartbeat
except ImportError:
    # Si exécuté hors contexte
    def update_job_progress(*args, **kwargs): pass
    def start_heartbeat(*args, **kwargs): pass
    def stop_heartbeat(): pass
    # Si exécuté hors contexte
    def update_job_progress(*args, **kwargs): pass


@mcp.tool()
def profile_dataset(file_path: str) -> str:
    """Read a CSV and return a statistical summary JSON."""
    try:
        import os
        import sys
        # Ensure src is in path for local imports
        src_dir = os.path.dirname(os.path.abspath(__file__))
        if src_dir not in sys.path:
            sys.path.append(src_dir)
        from tools.domain_detector import build_data_profile
        
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
        for step in schema.get("steps", []):
            cols = step.get("column")
            action = step.get("action")
            
            if not isinstance(cols, list):
                cols = [cols]
                
            for col in cols:
                if col in df.columns:
                    if action == "drop":
                        df = df.drop(columns=[col])
                    elif action == "impute_mean":
                        df[col] = df[col].fillna(df[col].mean())
                    elif action == "impute_median":
                        df[col] = df[col].fillna(df[col].median())
                    elif action == "forward_fill_imputation":
                        df[col] = df[col].ffill().bfill()
                    elif action == "log_transformation":
                        import numpy as np
                        df[col] = np.log1p(df[col].clip(lower=0))
                    elif action == "spline_transform":
                        spline = SplineTransformer(extrapolation='periodic')
                        # Reshape for sklearn
                        df[col] = spline.fit_transform(df[[col]])
                    
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

@mcp.tool()
def evaluate_model(file_path: str, target: str, task: str, job_id: str = None) -> dict:
    """Entraîne un modèle rapide pour renvoyer des métriques JSON déterministes (Agent) et exporter des PNG (Humain)."""
    if job_id:
        start_heartbeat(job_id)
        update_job_progress(job_id, 'evaluating', 35, f"Évaluation rapide du modèle (Tâche: {task})")

    import os
    import numpy as np
    from sklearn.model_selection import train_test_split, cross_val_score, TimeSeriesSplit
    from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
    from sklearn.metrics import confusion_matrix, classification_report, accuracy_score
    from sklearn.metrics import mean_squared_error, r2_score
    from sklearn.cluster import KMeans
    from sklearn.metrics import silhouette_score
    from sklearn.decomposition import PCA
    import matplotlib.pyplot as plt
    import seaborn as sns
    from statsmodels.tsa.stattools import adfuller

    try:
        df = pd.read_csv(file_path)
        
        # S'assurer que le dossier d'output existe
        output_dir = os.path.dirname(file_path)
        if not output_dir or output_dir in [".", "..", ""]:
            output_dir = "../workspace/models_artifacts"
        os.makedirs(output_dir, exist_ok=True)
        
        # Nettoyage naïf pour le modèle rapide (drop NA, encoder catégoriel)
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
        
        output = {"task": task, "metrics": {}, "issues": [], "artifacts": {}}
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if task == "classification":
            if y.dtype == 'object' or y.dtype.name == 'category':
                y = y.astype('category').cat.codes
                
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            model = RandomForestClassifier(n_estimators=50, random_state=42)
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # Cross-Validation pour Overfitting
            cv_scores = cross_val_score(model, X, y, cv=5, scoring='f1_macro')
            train_score = float(model.score(X_train, y_train))
            cv_mean = float(cv_scores.mean())
            overfitting_gap = train_score - cv_mean
            
            output["metrics"]["train_score"] = train_score
            output["metrics"]["cv_mean_f1"] = cv_mean
            output["metrics"]["overfitting_gap"] = overfitting_gap
            
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
            
            if job_id:
                update_job_progress(job_id, 'evaluating', 45, "Matrice de confusion générée", {"confusion_matrix_url": cm_path})
            
        elif task == "regression" or task == "time_series":
            model = RandomForestRegressor(n_estimators=50, random_state=42)
            
            if task == "time_series":
                # TimeSeriesSplit pour éviter la fuite de données
                tscv = TimeSeriesSplit(n_splits=5)
                cv_scores = []
                X_arr = X.values
                y_arr = y.values
                
                for train_idx, test_idx in tscv.split(X_arr):
                    X_train_cv, X_test_cv = X_arr[train_idx], X_arr[test_idx]
                    y_train_cv, y_test_cv = y_arr[train_idx], y_arr[test_idx]
                    
                    from sklearn.base import clone
                    model_clone = clone(model)
                    model_clone.fit(X_train_cv, y_train_cv)
                    score = model_clone.score(X_test_cv, y_test_cv)
                    cv_scores.append(score)
                
                cv_std = float(np.std(cv_scores))
                output["metrics"]["temporal_cv_std"] = cv_std
                
                if cv_std > 0.2:
                    output["issues"].append({
                        "type": "temporal_instability",
                        "severity": "HIGH",
                        "message": f"Instabilité temporelle importante (std: {cv_std:.2f})"
                    })
                
                # Split séquentiel strict pour l'évaluation finale
                split_idx = int(len(X) * 0.8)
                X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
                y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
                
                # Test de stationnarité (ADF)
                try:
                    adf_result = adfuller(y.dropna())
                    output["metrics"]["pValue"] = float(adf_result[1])
                except:
                    output["metrics"]["pValue"] = 1.0
            else:
                X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            model.fit(X_train, y_train)
            y_pred = model.predict(X_test)
            
            # JSON Metrics
            rmse = float(np.sqrt(mean_squared_error(y_test, y_pred)))
            r2 = float(r2_score(y_test, y_pred))
            output["metrics"]["rmse"] = rmse
            output["metrics"]["r2"] = r2
            
            # PNG Artifact - Residuals
            residuals = y_test - y_pred
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
            score = float(silhouette_score(X, labels))
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
            
        return {"status": "success", "evaluation": output}
        
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
    import optuna
    import numpy as np
    from sklearn.model_selection import cross_val_score, TimeSeriesSplit
    from sklearn.ensemble import RandomForestRegressor, RandomForestClassifier
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
            model_name = trial.suggest_categorical('model_name', ['RandomForest', 'XGBoost', 'LightGBM'])
            
            if model_name == 'RandomForest':
                n_estimators = trial.suggest_int('rf_n_estimators', 50, 300)
                max_depth = trial.suggest_int('rf_max_depth', 3, 20)
                min_samples_split = trial.suggest_int('rf_min_samples_split', 2, 10)
                if task == "classification":
                    model = RandomForestClassifier(n_estimators=n_estimators, max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
                else:
                    model = RandomForestRegressor(n_estimators=n_estimators, max_depth=max_depth, min_samples_split=min_samples_split, random_state=42)
                    
            elif model_name == 'XGBoost':
                n_estimators = trial.suggest_int('xgb_n_estimators', 50, 300)
                max_depth = trial.suggest_int('xgb_max_depth', 3, 10)
                learning_rate = trial.suggest_float('xgb_lr', 0.01, 0.3, log=True)
                if task == "classification":
                    from xgboost import XGBClassifier
                    model = XGBClassifier(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42, eval_metric='logloss')
                else:
                    from xgboost import XGBRegressor
                    model = XGBRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42)
                    
            elif model_name == 'LightGBM':
                n_estimators = trial.suggest_int('lgb_n_estimators', 50, 300)
                max_depth = trial.suggest_int('lgb_max_depth', 3, 15)
                learning_rate = trial.suggest_float('lgb_lr', 0.01, 0.3, log=True)
                if task == "classification":
                    from lightgbm import LGBMClassifier
                    model = LGBMClassifier(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42, verbose=-1)
                else:
                    from lightgbm import LGBMRegressor
                    model = LGBMRegressor(n_estimators=n_estimators, max_depth=max_depth, learning_rate=learning_rate, random_state=42, verbose=-1)
            
            if task == "classification":
                if y.dtype == 'object' or y.dtype.name == 'category':
                    y_encoded = y.astype('category').cat.codes
                else:
                    y_encoded = y
                score = cross_val_score(model, X, y_encoded, cv=3, scoring='f1_macro').mean()
                return score
            else:
                if task == "time_series":
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
                        score = silhouette_score(X, labels)
                    else:
                        score = -1.0
                    return score
                else:
                    score = cross_val_score(model, X, y, cv=3, scoring='r2').mean()
                    return score

        study = optuna.create_study(direction='maximize')
        # Limiter à 10 trials pour que ça tourne vite en local
        study.optimize(objective, n_trials=10)
        
        best_params = study.best_params
        best_score = float(study.best_value)
        
        return json.dumps({
            "status": "success",
            "best_params": best_params,
            "optimized_score": best_score,
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
                # Update Firestore
                import firebase_admin
                from firebase_admin import firestore
                db = firestore.client()
                db.collection('ml_jobs').document(job_id).update({
                    'adversarial_validation': result
                })
        
        return json.dumps(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": f"Erreur Adversarial Validation: {str(e)}"})
    finally:
        if job_id:
            stop_heartbeat()

@mcp.tool()
def run_explainability_audit(file_path: str, target: str, task: str, job_id: str = None) -> str:
    """Entraîne un RandomForest et calcule les valeurs SHAP."""
    if job_id:
        start_heartbeat(job_id)
        update_job_progress(job_id, 'explainability_audit', 75, "Audit d'Explicabilité (Calcul SHAP en cours)...")

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
            
        # Nettoyage
        df_clean = df.dropna()
        for col in df_clean.select_dtypes(include=['object', 'category']).columns:
            if col != target:
                df_clean[col] = df_clean[col].astype('category').cat.codes
        
        X = df_clean.drop(columns=[target])
        y = df_clean[target]
        
        if task == "classification":
            if y.dtype == 'object' or y.dtype.name == 'category':
                y = y.astype('category').cat.codes
            model = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
        else:
            model = RandomForestRegressor(n_estimators=50, max_depth=5, random_state=42)
            
        model.fit(X, y)
        
        # SHAP
        explainer = shap.TreeExplainer(model)
        sample_size = min(300, len(X))
        X_sample = X.sample(n=sample_size, random_state=42)
        shap_values = explainer.shap_values(X_sample)
        
        if isinstance(shap_values, list): # Classification binaire ou multiclass
            shap_values_to_plot = shap_values[1] if len(shap_values) > 1 else shap_values[0]
        else:
            shap_values_to_plot = shap_values
            
        # Feature Importance
        mean_abs_shap = np.abs(shap_values_to_plot).mean(axis=0)
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
            import firebase_admin
            from firebase_admin import firestore
            db = firestore.client()
            db.collection('ml_jobs').document(job_id).update({
                'explainability_audit': result
            })
            
        return json.dumps(result)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": f"Erreur Explainability: {str(e)}"})
    finally:
        if job_id:
            stop_heartbeat()

@mcp.tool()
def generate_notebook(file_path: str, cleaning_schema: str, output_nb_path: str) -> str:
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
            
        summary = {
            "fichier": file_path,
            "tache_ml": task_type_from_schema.upper(),
            "is_timeseries": task_type_from_schema.lower() == "time_series",
            "domaine": domain,
            "colonnes_numeriques": num_cols,
            "colonnes_categorielles": cat_cols,
            "dimensions": {"lignes": nrows, "colonnes": ncols},
            "cible_suggeree": {"cible": target_col}
        }
        
        # 2. Création du notebook de base (riche) avec notebook_factory
        os.makedirs(os.path.dirname(output_nb_path), exist_ok=True)
        nom_base = os.path.splitext(os.path.basename(file_path))[0]
        
        nb, n_cells = assemble_notebook_from_steps(
            file_path=file_path,
            target_col=target_col,
            summary=summary,
            nom_base=nom_base,
            is_clustering=(task_type_from_schema.lower() == "clustering" or not bool(target_col)),
            algo_clustering="benchmark"
        )
        
        # 3. Injection de la stratégie dynamique de l'agent
        dynamic_cells = []
        dynamic_cells.append(nbf.v4.new_markdown_cell("## 🤖 Stratégie de Nettoyage Dynamique (Agent IA)\n\nL'agent a défini et exécuté la stratégie suivante basée sur la connaissance (Graph RAG) :"))
        
        code_clean = "df_clean = df.copy()\n\n"
        for step in schema.get("steps", []):
            col = step.get("column")
            action = step.get("action")
            reasoning = step.get("reasoning")
            
            if isinstance(col, list):
                col_str = str(col)
                code_clean += f"# Étape : {action} sur {col_str}\n# Raison : {reasoning}\n"
                if "imputation" in action:
                    code_clean += f"for c in {col_str}:\n    if c in df_clean.columns:\n        df_clean[c] = df_clean[c].fillna(method='ffill').fillna(method='bfill')\n"
            else:
                code_clean += f"# Étape : {action} sur '{col}'\n# Raison : {reasoning}\n"
                if "impute" in action or "imputation" in action:
                    code_clean += f"if '{col}' in df_clean.columns:\n    df_clean['{col}'] = df_clean['{col}'].fillna(method='ffill').fillna(method='bfill')\n"
                elif action == "drop":
                    code_clean += f"if '{col}' in df_clean.columns:\n    df_clean = df_clean.drop(columns=['{col}'])\n"
                elif action == "scale":
                    code_clean += f"if '{col}' in df_clean.columns:\n    scaler = StandardScaler()\n    df_clean['{col}'] = scaler.fit_transform(df_clean[['{col}']])\n"
                elif action == "log_transformation":
                    code_clean += f"if '{col}' in df_clean.columns:\n    df_clean['{col}'] = np.log1p(df_clean['{col}'])\n"
            code_clean += "\n"
            
        code_clean += "# df_clean contient maintenant les données nettoyées par l'agent.\ndisplay(df_clean.head())"
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
            
        return json.dumps({"status": "success", "notebookPath": output_nb_path})
    except Exception as e:
        import traceback
        traceback.print_exc()
        return json.dumps({"error": str(e)})

if __name__ == "__main__":
    # Expose the server over standard I/O (or SSE)
    mcp.run()
