import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union

app = FastAPI(
    title="API de Prédiction - BTC-USD (2014-2024)",
    description="API FastAPI générée automatiquement pour servir le modèle champion LightGBM Regressor.",
    version="1.1.0"
)

# Résolution et chargement du modèle
# Résolution et chargement du modèle
model_file_local = "model.joblib"
model = None

try:
    # Chemin local dans le conteneur / api/
    local_path = os.path.join(os.path.dirname(__file__), model_file_local)
    if os.path.exists(local_path):
        model = joblib.load(local_path)
        print(f"Modèle chargé depuis le dossier local de l'API: {local_path}")
    else:
        # Fallback chemin absolu
        model_path = "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors/outputs/BTC-USD (2014-2024)/models/pipeline_BTC-USD (2014-2024)_20260708_1158.joblib"
        if os.path.exists(model_path):
            model = joblib.load(model_path)
        else:
            # Essai de chemin relatif si le chemin absolu n'est plus valide (ex: déplacement du projet)
            rel_path = os.path.join(os.path.dirname(__file__), "..", "models", "pipeline_BTC-USD (2014-2024)_20260708_1158.joblib")
            if os.path.exists(rel_path):
                model = joblib.load(rel_path)
                print(f"Modèle chargé via chemin relatif: {rel_path}")
except Exception as e:
    print(f"Erreur critique lors du chargement du modèle : {e}")

class TimeSeriesInput(BaseModel):
    # L'API s'attend à recevoir l'historique récent (minimum 30 points) pour calculer les caractéristiques temporelles
    history: List[Dict[str, Any]]

@app.get("/")
def read_root():
    return {
        "status": "online",
        "project": "BTC-USD (2014-2024)",
        "model_loaded": model is not None,
        "model_class": "LightGBM Regressor"
    }

@app.post("/predict")
def predict(payload: TimeSeriesInput):
    if model is None:
        raise HTTPException(status_code=500, detail="Modèle non chargé sur le serveur.")

    try:
        # 1. Convertir l'historique en DataFrame
        df = pd.DataFrame(payload.history)

        # Trouver la colonne temporelle
        date_col = None
        for col in df.columns:
            if any(kw in col.lower() for kw in ['date', 'time', 'timestamp']):
                df[col] = pd.to_datetime(df[col])
                df = df.sort_values(col).set_index(col)
                date_col = col
                break

        if not date_col:
            df.index = pd.date_range(start="2024-01-01", periods=len(df), freq="D")

        # 2. Calculer le feature engineering causal en direct (anti-leakage)
        for w in [7, 14, 30]:
            df['Volume_lag_' + str(w)] = df['Volume'].shift(w)
            df['Volume_roll_mean_' + str(w)] = df['Volume'].rolling(window=w).mean()
            df['Volume_ewm_' + str(w)] = df['Volume'].ewm(span=w, adjust=False).mean()

        df['month_sin'] = np.sin(2 * np.pi * df.index.month / 12)
        df['month_cos'] = np.cos(2 * np.pi * df.index.month / 12)
        df['day_sin']   = np.sin(2 * np.pi * df.index.dayofweek / 7)
        df['day_cos']   = np.cos(2 * np.pi * df.index.dayofweek / 7)

        df_clean = df.dropna()
        if df_clean.empty:
            raise ValueError("Historique trop court pour calculer les caractéristiques (min 30 observations requises)")

        # Sélectionner les colonnes de features
        features = [c for c in df_clean.columns if c != 'Volume']

        # Prédire le point le plus récent
        predictions = model.predict(df_clean[features])

        return {
            "prediction": float(predictions[-1]),
            "timestamp": str(df_clean.index[-1]),
            "status": "success"
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'inférence: {str(e)}")