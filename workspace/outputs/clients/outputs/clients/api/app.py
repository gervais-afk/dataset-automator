import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union
import sys

# Definition requise pour la deserialisation joblib du pipeline de pretraitement
def engineering_func(X):
    X_out = X.copy()
    num_cols = X_out.select_dtypes(include=[np.number]).columns
    if len(num_cols) >= 2:
        X_out['feat_ratio_1_2'] = X_out[num_cols[0]] / (X_out[num_cols[1]] + 1e-6)

    for col in num_cols:
        if X_out[col].skew() > 1:
            X_out[f'log_{col}'] = np.log1p(X_out[col].clip(lower=0))

    return X_out

sys.modules['__main__'].engineering_func = engineering_func

# Gestionnaire de cycle de vie (Lifespan) pour charger le modele une fois en memoire
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Demarrage : Chargement du modele
    try:
        model_file_local = "pipeline_clients_20260718_1526.joblib"

        def load_model(path):
            if path.endswith('.sav'):
                from tabicl import TabICLClassifier, TabICLRegressor
                try:
                    return TabICLClassifier.load(path)
                except Exception:
                    return TabICLRegressor.load(path)
            else:
                import joblib
                return joblib.load(path)

        local_path = os.path.join(os.path.dirname(__file__), model_file_local)
        if os.path.exists(local_path):
            ml_models["regression_model"] = load_model(local_path)
            print(f"Modele charge depuis le dossier local : {local_path}")
        else:
            model_path = "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/clients/outputs/clients/models/pipeline_clients_20260718_1526.joblib"
            if os.path.exists(model_path):
                ml_models["regression_model"] = load_model(model_path)
            else:
                rel_path = os.path.join(os.path.dirname(__file__), "..", "models", "pipeline_clients_20260718_1526.joblib")
                ml_models["regression_model"] = load_model(rel_path)
                print(f"Modele charge via chemin relatif: {rel_path}")

        # Charger l'echantillon de train pour LIME si disponible
        sample_path = os.path.join(os.path.dirname(__file__), "x_train_sample.csv")
        if os.path.exists(sample_path):
            ml_models["x_train_sample"] = pd.read_csv(sample_path)
            print("Echantillon d'entrainement charge pour les explications LIME.")

    except Exception as e:
        print(f"Erreur critique lors du chargement du modele : {e}")
    yield
    # Extinction : Liberation de la memoire
    ml_models.clear()

app = FastAPI(
    title="API de Prediction - clients",
    description="API FastAPI generee automatiquement avec lifespan pour servir le modele TabICL (SOTA).",
    version="1.2.0",
    lifespan=lifespan
)

class PredictionInput(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any]]

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "clients",
        "model_loaded": "regression_model" in ml_models,
        "model_class": "TabICL (SOTA)"
    }

@app.post("/predict")
def predict(payload: PredictionInput):
    if "regression_model" not in ml_models:
        raise HTTPException(status_code=500, detail="Modele non charge sur le serveur.")

    try:
        input_data = payload.data
        if isinstance(input_data, dict):
            input_data = [input_data]

        df = pd.DataFrame(input_data)
        model = ml_models["regression_model"]

        predictions = model.predict(df)
        response = {"predictions": predictions.tolist()}

        if hasattr(model, "predict_proba"):
            try:
                probabilities = model.predict_proba(df)
                response["probabilities"] = probabilities.tolist()
            except Exception as prob_err:
                response["probabilities_error"] = str(prob_err)

        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'inference: {str(e)}")

@app.post("/explain")
def explain(payload: PredictionInput):
    if "regression_model" not in ml_models:
        raise HTTPException(status_code=500, detail="Modele non charge sur le serveur.")

    try:
        input_data = payload.data
        if isinstance(input_data, dict):
            input_data = [input_data]

        df_instance = pd.DataFrame(input_data)
        model = ml_models["regression_model"]

        if "x_train_sample" not in ml_models:
            raise ValueError("Echantillon d'entrainement non disponible pour LIME.")

        X_train_sample = ml_models["x_train_sample"]

        # Isolation preprocessing/estimator
        preprocessing_step = None
        final_estimator = model

        if hasattr(model, "steps"):
            for step_name, step_obj in model.steps:
                if step_name in ['preprocessing_full', 'preprocessor']:
                    preprocessing_step = step_obj
                else:
                    final_estimator = step_obj

            if preprocessing_step is not None:
                X_train_prep = preprocessing_step.transform(X_train_sample)
                instance_prep = preprocessing_step.transform(df_instance)
            else:
                X_train_prep = X_train_sample.values
                instance_prep = df_instance.values
        else:
            X_train_prep = X_train_sample.values
            instance_prep = df_instance.values
            final_estimator = model

        from sklearn.preprocessing import StandardScaler
        from sklearn.linear_model import Ridge

        scaler = StandardScaler()
        X_train_scaled = scaler.fit_transform(X_train_prep)
        instance_scaled = scaler.transform(instance_prep)[0]

        num_perturbations = 1000
        perturbations_scaled = np.random.normal(0, 0.4, size=(num_perturbations, X_train_prep.shape[1])) + instance_scaled
        perturbations_prep = scaler.inverse_transform(perturbations_scaled)

        is_classification = "classification" == "classification"
        if is_classification and hasattr(final_estimator, "predict_proba"):
            pred_probs = final_estimator.predict_proba(instance_prep)[0]
            pred_class = int(np.argmax(pred_probs))
            y_perturbed = final_estimator.predict_proba(perturbations_prep)[:, pred_class]
        else:
            pred_class = 0
            y_perturbed = final_estimator.predict(perturbations_prep)

        distances = np.sqrt(np.sum((perturbations_scaled - instance_scaled) ** 2, axis=1))
        kernel_width = np.sqrt(X_train_prep.shape[1]) * 0.75
        weights = np.exp(-(distances ** 2) / (kernel_width ** 2))

        local_model = Ridge(alpha=1.0)
        local_model.fit(perturbations_scaled, y_perturbed, sample_weight=weights)
        coefficients = local_model.coef_

        if hasattr(model, "steps") and preprocessing_step is not None:
            if hasattr(preprocessing_step, "get_feature_names_out"):
                try:
                    feature_names = list(preprocessing_step.get_feature_names_out())
                except Exception:
                    feature_names = [f"col_{i}" for i in range(X_train_prep.shape[1])]
            else:
                feature_names = [f"col_{i}" for i in range(X_train_prep.shape[1])]
        else:
            feature_names = list(X_train_sample.columns)

        contributions = []
        for i, name in enumerate(feature_names):
            contributions.append({
                "feature": name,
                "coefficient": float(coefficients[i])
            })

        contributions = sorted(contributions, key=lambda x: abs(x["coefficient"]), reverse=True)

        return {
            "status": "success",
            "predicted_class": pred_class if is_classification else None,
            "contributions": contributions[:10]
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'explication: {str(e)}")