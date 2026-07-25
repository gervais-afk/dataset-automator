import os
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union
import sys

# Definition requise pour la désérialisation joblib du pipeline de prétraitement
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

# Gestionnaire de cycle de vie (Lifespan) pour charger le modèle une fois en mémoire
ml_models = {}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage : Chargement du modèle
    try:
        model_file_local = "model.joblib"
        local_path = os.path.join(os.path.dirname(__file__), model_file_local)
        if os.path.exists(local_path):
            ml_models["regression_model"] = joblib.load(local_path)
            print(f"Modèle chargé depuis le dossier local : {local_path}")
        else:
            model_path = "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/ecommerce_sales_34500/outputs/ecommerce_sales_34500/models/pipeline_ecommerce_sales_34500_20260708_1518.joblib"
            if os.path.exists(model_path):
                ml_models["regression_model"] = joblib.load(model_path)
            else:
                rel_path = os.path.join(os.path.dirname(__file__), "..", "models", "pipeline_ecommerce_sales_34500_20260708_1518.joblib")
                ml_models["regression_model"] = joblib.load(rel_path)
                print(f"Modèle chargé via chemin relatif: {rel_path}")
    except Exception as e:
        print(f"Erreur critique lors du chargement du modèle : {e}")
    yield
    # Extinction : Libération de la mémoire
    ml_models.clear()

app = FastAPI(
    title="API de Prédiction - ecommerce_sales_34500",
    description="API FastAPI générée automatiquement avec lifespan pour servir le modèle Baseline (K-Means).",
    version="1.2.0",
    lifespan=lifespan
)

class PredictionInput(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any]]

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "ecommerce_sales_34500",
        "model_loaded": "regression_model" in ml_models,
        "model_class": "Baseline (K-Means)"
    }

# Fonction d'inférence synchrone (def) pour éviter de bloquer la boucle asynchrone (CPU-bound task)
@app.post("/predict")
def predict(payload: PredictionInput):
    if "regression_model" not in ml_models:
        raise HTTPException(status_code=500, detail="Modèle non chargé sur le serveur.")

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
        raise HTTPException(status_code=400, detail=f"Erreur d'inférence: {str(e)}")