# 🚀 Étape 7 — Déploiement : Génération automatique de l'API FastAPI

Objectif : Exposer le modèle champion sous forme d'API REST locale pour permettre aux applications tierces de consommer les prédictions en temps réel.

## 7.1 Génération des scripts de l'API (app.py et requirements.txt)

```python
import os

api_dir = os.path.join(OUTPUT_DIR, "api")
os.makedirs(api_dir, exist_ok=True)

# Résoudre le nom exact du fichier de modèle exporté à la phase 5
model_file = model_filename if 'model_filename' in globals() else f"pipeline_{NOM_BASE}.joblib"
model_abs_path = os.path.join(MODELS_DIR, model_file).replace('\\', '/')

if TYPE_TACHE == "timeseries":
    app_py_content = f"""import os
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import joblib
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Union

app = FastAPI(
    title="API de Prédiction - {NOM_BASE}",
    description="API FastAPI générée automatiquement pour servir le modèle champion {best_name}.",
    version="1.1.0"
)

# Résolution et chargement du modèle
model_file_local = "{model_file}"
model = None

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

try:
    # Chemin local dans le conteneur / api/
    local_path = os.path.join(os.path.dirname(__file__), model_file_local)
    if os.path.exists(local_path):
        model = load_model(local_path)
        print(f"Modèle chargé depuis le dossier local de l'API: {{local_path}}")
    else:
        # Fallback chemin absolu
        model_path = "{model_abs_path}"
        if os.path.exists(model_path):
            model = load_model(model_path)
        else:
            # Essai de chemin relatif si le chemin absolu n'est plus valide (ex: déplacement du projet)
            rel_path = os.path.join(os.path.dirname(__file__), "..", "models", "{model_file}")
            if os.path.exists(rel_path):
                model = load_model(rel_path)
                print(f"Modèle chargé via chemin relatif: {{rel_path}}")
except Exception as e:
    print(f"Erreur critique lors du chargement du modèle : {{e}}")

class TimeSeriesInput(BaseModel):
    # L'API s'attend à recevoir l'historique récent (minimum 30 points) pour calculer les caractéristiques temporelles
    history: List[Dict[str, Any]]

@app.get("/")
def read_root():
    return {{
        "status": "online",
        "project": "{NOM_BASE}",
        "model_loaded": model is not None,
        "model_class": "{best_name}"
    }}

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
            df['{TARGET_COL}_lag_' + str(w)] = df['{TARGET_COL}'].shift(w)
            df['{TARGET_COL}_roll_mean_' + str(w)] = df['{TARGET_COL}'].shift(1).rolling(window=w).mean()
            df['{TARGET_COL}_ewm_' + str(w)] = df['{TARGET_COL}'].shift(1).ewm(span=w, adjust=False).mean()
            
        df['month_sin'] = np.sin(2 * np.pi * df.index.month / 12)
        df['month_cos'] = np.cos(2 * np.pi * df.index.month / 12)
        df['day_sin']   = np.sin(2 * np.pi * df.index.dayofweek / 7)
        df['day_cos']   = np.cos(2 * np.pi * df.index.dayofweek / 7)
        
        df_clean = df.dropna()
        if df_clean.empty:
            raise ValueError("Historique trop court pour calculer les caractéristiques (min 30 observations requises)")
            
        # Sélectionner les colonnes de features
        features = [c for c in df_clean.columns if c != '{TARGET_COL}']
        
        # Prédire le point le plus récent
        predictions = model.predict(df_clean[features])
        
        return {{
            "prediction": float(predictions[-1]),
            "timestamp": str(df_clean.index[-1]),
            "status": "success"
        }}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
"""
else:
    app_py_content = f"""import os
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
            X_out[f'log_{{col}}'] = np.log1p(X_out[col].clip(lower=0))
            
    return X_out

sys.modules['__main__'].engineering_func = engineering_func

# Gestionnaire de cycle de vie (Lifespan) pour charger le modele une fois en memoire
ml_models = {{}}

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Demarrage : Chargement du modele
    try:
        model_file_local = "{model_file}"
        
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
            print(f"Modele charge depuis le dossier local : {{local_path}}")
        else:
            model_path = "{model_abs_path}"
            if os.path.exists(model_path):
                ml_models["regression_model"] = load_model(model_path)
            else:
                rel_path = os.path.join(os.path.dirname(__file__), "..", "models", "{model_file}")
                ml_models["regression_model"] = load_model(rel_path)
                print(f"Modele charge via chemin relatif: {{rel_path}}")
                
        # Charger l'echantillon de train pour LIME si disponible
        sample_path = os.path.join(os.path.dirname(__file__), "x_train_sample.csv")
        if os.path.exists(sample_path):
            ml_models["x_train_sample"] = pd.read_csv(sample_path)
            print("Echantillon d'entrainement charge pour les explications LIME.")
            
    except Exception as e:
        print(f"Erreur critique lors du chargement du modele : {{e}}")
    yield
    # Extinction : Liberation de la memoire
    ml_models.clear()

app = FastAPI(
    title="API de Prediction - {NOM_BASE}",
    description="API FastAPI generee automatiquement avec lifespan pour servir le modele {best_name}.",
    version="1.2.0",
    lifespan=lifespan
)

class PredictionInput(BaseModel):
    data: Union[List[Dict[str, Any]], Dict[str, Any]]

@app.get("/")
def read_root():
    return {{
        "status": "online",
        "project": "{NOM_BASE}",
        "model_loaded": "regression_model" in ml_models,
        "model_class": "{best_name}"
    }}

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
        response = {{"predictions": predictions.tolist()}}
        
        if hasattr(model, "predict_proba"):
            try:
                probabilities = model.predict_proba(df)
                response["probabilities"] = probabilities.tolist()
            except Exception as prob_err:
                response["probabilities_error"] = str(prob_err)
                
        return response
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'inference: {{str(e)}}")

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
        
        is_classification = "{TYPE_TACHE}" == "classification"
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
            contributions.append({{
                "feature": name,
                "coefficient": float(coefficients[i])
            }})
            
        contributions = sorted(contributions, key=lambda x: abs(x["coefficient"]), reverse=True)
        
        return {{
            "status": "success",
            "predicted_class": pred_class if is_classification else None,
            "contributions": contributions[:10]
        }}
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Erreur d'explication: {{str(e)}}")
"""

# Ecriture de l'application FastAPI
app_path = os.path.join(api_dir, "app.py")
with open(app_path, "w", encoding="utf-8") as f:
    f.write(app_py_content.strip())

# Generation de l'interface utilisateur Streamlit
if TYPE_TACHE == "timeseries":
    streamlit_app_content = f"""import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Inference {NOM_BASE} - MLOps", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/artificial-intelligence.png", width=100)
    st.title("Gouvernance MLOps")
    st.write("**Dataset** : {NOM_BASE}")
    st.write("**Tache** : PREDICTION SÉRIE TEMPORELLE")
    st.write("**Modele** : {best_name}")
    st.write("---")
    st.info("Cette interface communique avec l'API FastAPI locale pour executer des predictions de series temporelles.")

st.title("📊 Interface de Prédiction Temporelle — {NOM_BASE}")
st.write("Pour prevoir la valeur future, veuillez charger un fichier CSV contenant l'historique recent des prix/volumes.")

# Uploadeur de fichier
uploaded_file = st.file_uploader("📂 Charger l'historique recent (CSV avec au moins 30 observations)", type=["csv"])

# Option pour charger un echantillon de demo
if st.checkbox("💡 Utiliser un echantillon de test demo"):
    import os
    demo_path = os.path.join(os.path.dirname(__file__), "demo_history.csv")
    if os.path.exists(demo_path):
        uploaded_file = demo_path
        st.info("Echantillon de demo charge avec succes !")

if uploaded_file is not None:
    try:
        if isinstance(uploaded_file, str):
            df_history = pd.read_csv(uploaded_file)
        else:
            df_history = pd.read_csv(uploaded_file)
            
        st.write("### 🔍 Extrait de l'historique charge :")
        st.dataframe(df_history.tail(10))
        
        if st.button("🚀 Lancer la Prevision", type="primary"):
            # Convertir les donnees en JSON pour le payload
            history_list = df_history.to_dict(orient="records")
            payload = {{"history": history_list}}
            
            with st.spinner("Prevision en cours..."):
                backend_url = "http://localhost:8000/predict"
                response = requests.post(backend_url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    res_json = response.json()
                    pred_val = res_json["prediction"]
                    timestamp = res_json.get("timestamp", "Date inconnue")
                    
                    st.success(f"🎯 **Prevision pour la prochaine date ({{timestamp}}):** {{pred_val:.4f}}")
                else:
                    st.error(f"❌ Erreur du serveur FastAPI (code {{response.status_code}}) : {{response.text}}")
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture ou de l'envoi de l'historique : {{e}}")
"""
else:
    streamlit_app_content = f"""import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Inference {NOM_BASE} - MLOps", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(\"\"\"
<style>
    .main {{
        background-color: #0e1117;
        color: #ffffff;
    }}
    .stButton>button {{
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }}
    .stButton>button:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
    }}
    .metric-card {{
        background-color: #1e222b;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #0072ff;
        margin-bottom: 20px;
    }}
    .metric-title {{
        font-size: 14px;
        color: #8a909d;
        text-transform: uppercase;
        margin-bottom: 5px;
    }}
    .metric-value {{
        font-size: 28px;
        font-weight: bold;
        color: #ffffff;
    }}
</style>
\"\"\", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/artificial-intelligence.png", width=100)
    st.title("Gouvernance MLOps")
    st.write("**Dataset** : {NOM_BASE}")
    st.write("**Tache** : {TYPE_TACHE.upper()}")
    st.write("**Modele** : {best_name}")
    st.write("---")
    st.info("Cette interface communique avec l'API FastAPI locale pour executer des predictions et calculer des explications locales via LIME.")

st.title("🎯 Diagnostic & Inference Interactive")
st.write("Saisissez les caracteristiques ci-dessous pour obtenir une prediction immediate accompagnee de sa justification locale.")

st.subheader("⚙️ Saisie des variables d'entree")

num_cols = {NUM_COLS_LIST}
cat_cols = {CAT_COLS_LIST}
features_input = {{}}

# Charger x_train_sample pour connaitre les valeurs possibles des variables categorielles
import os
sample_path = os.path.join(os.path.dirname(__file__), "x_train_sample.csv")
df_sample = None
if os.path.exists(sample_path):
    df_sample = pd.read_csv(sample_path)

if num_cols:
    st.markdown("##### 🔢 Variables Numeriques")
    cols_num = st.columns(min(3, max(1, len(num_cols))))
    for i, col_name in enumerate(num_cols):
        if col_name == "{TARGET_COL}": continue
        col_ui = cols_num[i % len(cols_num)]
        features_input[col_name] = col_ui.number_input(f"{{col_name}}", value=0.0, step=0.1)

if cat_cols:
    st.markdown("---")
    st.markdown("##### 🔠 Variables Categorielles")
    cols_cat = st.columns(min(3, max(1, len(cat_cols))))
    for i, col_name in enumerate(cat_cols):
        if col_name == "{TARGET_COL}": continue
        col_ui = cols_cat[i % len(cols_cat)]
        
        # Recuperer les categories uniques depuis l'echantillon si disponible
        options = []
        if df_sample is not None and col_name in df_sample.columns:
            options = list(df_sample[col_name].dropna().unique())
        
        if options:
            features_input[col_name] = col_ui.selectbox(f"{{col_name}}", options=options)
        else:
            features_input[col_name] = col_ui.text_input(f"{{col_name}}", value="")

st.markdown("---")

if st.button("🚀 Calculer la Prediction & Explication", type="primary"):
    payload = {{"data": features_input}}
    
    with st.spinner("Inference en cours..."):
        try:
            backend_url = "http://localhost:8000/predict"
            response = requests.post(backend_url, json=payload, timeout=10)
            
            if response.status_code == 200:
                res_json = response.json()
                pred = res_json["predictions"][0]
                
                col_m1, col_m2 = st.columns(2)
                is_classif = "probabilities" in res_json or "{TYPE_TACHE}" == "classification"
                
                with col_m1:
                    if is_classif:
                        decision_color = "#2ca02c" if pred == 0 else "#d62728"
                        st.markdown(f'''
                        <div class="metric-card" style="border-left-color: {{decision_color}};">
                            <div class="metric-title">Decision Modele</div>
                            <div class="metric-value" style="color: {{decision_color}};">Classe {{int(pred)}}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''
                        <div class="metric-card">
                            <div class="metric-title">Valeur Predite</div>
                            <div class="metric-value">{{pred:.4f}}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                        
                with col_m2:
                    if is_classif and "probabilities" in res_json:
                        probs = res_json["probabilities"][0]
                        confidence = probs[int(pred)] * 100
                        st.markdown(f'''
                        <div class="metric-card" style="border-left-color: #0072ff;">
                            <div class="metric-title">Confiance (Probabilite)</div>
                            <div class="metric-value">{{confidence:.2f}}%</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''
                        <div class="metric-card" style="border-left-color: #0072ff;">
                            <div class="metric-title">Statut Inference</div>
                            <div class="metric-value" style="color: #2ca02c;">Succes</div>
                        </div>
                        ''', unsafe_allow_html=True)
            else:
                st.error(f"❌ Erreur du serveur FastAPI (code {{response.status_code}}) : {{response.text}}")
                st.stop()
        except Exception as e:
            st.error(f"❌ Impossible de joindre l'API FastAPI sur /predict : {{e}}")
            st.stop()

    if "{TYPE_TACHE}" != "timeseries":
        with st.spinner("Calcul de la justification locale LIME (1000 perturbations)..."):
            try:
                explain_url = "http://localhost:8000/explain"
                exp_response = requests.post(explain_url, json=payload, timeout=15)
                
                if exp_response.status_code == 200:
                    exp_json = exp_response.json()
                    contributions = exp_json.get("contributions", [])
                    
                    st.subheader("🔬 Justification locale du resultat (LIME)")
                    st.write("Ce graphique montre comment chaque variable a influence la decision du modele pour cet individu :")
                    
                    if contributions:
                        features = [c["feature"] for c in contributions]
                        coefficients = [c["coefficient"] for c in contributions]
                        
                        fig, ax = plt.subplots(figsize=(8, 4.5))
                        fig.patch.set_facecolor('#1e222b')
                        ax.set_facecolor('#1e222b')
                        
                        colors = ['#2ca02c' if coef >= 0 else '#d62728' for coef in coefficients]
                        y_pos = np.arange(len(features))
                        ax.barh(y_pos, coefficients[::-1], color=colors[::-1], edgecolor='none', height=0.6)
                        ax.set_yticks(y_pos)
                        ax.set_yticklabels(features[::-1], color='#ffffff', fontsize=10)
                        
                        ax.axvline(x=0, color='#8a909d', linestyle='--', linewidth=1)
                        ax.tick_params(colors='#ffffff')
                        ax.spines['top'].set_visible(False)
                        ax.spines['right'].set_visible(False)
                        ax.spines['left'].set_color('#8a909d')
                        ax.spines['bottom'].set_color('#8a909d')
                        
                        ax.set_title("Contributions Variables (LIME)", color='#ffffff', fontsize=12, pad=15)
                        ax.set_xlabel("Poids (Vert = favorise | Rouge = defavorise)", color='#ffffff', fontsize=9)
                        ax.grid(axis='x', linestyle=':', color='#3a3f4b', alpha=0.5)
                        
                        st.pyplot(fig)
                        
                        with st.expander("📝 Details des contributions"):
                            for c in contributions:
                                direction = "favorise" if c["coefficient"] >= 0 else "defavorise"
                                color_text = "green" if c["coefficient"] >= 0 else "red"
                                st.markdown(f"• **{{c['feature']}}** : `{{c['coefficient']:+.4f}}` (:{{color_text}}[{{direction}}] la prediction)")
                    else:
                        st.warning("Aucune contribution significative calculee par LIME.")
                else:
                    st.warning(f"⚠️ L'API n'a pas pu calculer d'explications LIME (code {{exp_response.status_code}})")
            except Exception as e:
                st.warning(f"⚠️ Le calcul LIME a echoue ou l'echantillon de train n'est pas disponible : {{e}}")
"""

streamlit_path = os.path.join(api_dir, "streamlit_app.py")
with open(streamlit_path, "w", encoding="utf-8") as f:
    f.write(streamlit_app_content.strip())

# Ecriture des dependances requises (incluant streamlit)
requirements_content = """
fastapi>=0.100.0
uvicorn>=0.22.0
pydantic>=2.0.0
joblib>=1.3.0
pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.2.0
xgboost>=1.7.0
streamlit>=1.22.0
requests>=2.30.0
matplotlib>=3.5.0
"""

requirements_path = os.path.join(api_dir, "requirements.txt")
with open(requirements_path, "w", encoding="utf-8") as f:
    f.write(requirements_content.strip())

# Copie physique du modele et sauvegarde de l'echantillon X_train pour LIME
import shutil
try:
    src_model = os.path.join(MODELS_DIR, model_file)
    dst_model = os.path.join(api_dir, "model.joblib")
    shutil.copy2(src_model, dst_model)
    print(f"✅ Modele exporte copie dans le dossier API pour isolation : {dst_model}")
    
    # Echantillon X_train pour LIME
    if 'X_train' in globals() and X_train is not None:
        sample_path = os.path.join(api_dir, "x_train_sample.csv")
        X_train.head(100).to_csv(sample_path, index=False)
        print(f"✅ Echantillon de données d'entrainement exporte pour LIME : {sample_path}")
        
    # Echantillon de demo pour les series temporelles (X_test ou df)
    if TYPE_TACHE == "timeseries" and 'df' in globals() and df is not None:
        demo_path = os.path.join(api_dir, "demo_history.csv")
        df.tail(60).to_csv(demo_path, index=False)
        print(f"✅ Echantillon de demo pour series temporelles exporte : {demo_path}")
except Exception as e:
    print(f"⚠️ Impossible d'exporter le modele ou l'echantillon LIME : {e}")

# Écriture du Dockerfile de production (Build multi-étapes multi-stage et sécurité non-root)
dockerfile_content = """
# ==========================================
# ÉTAPE 1 : BUILDER (Compilation)
# ==========================================
FROM python:3.10-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ==========================================
# ÉTAPE 2 : RUNNER (Image de production finale)
# ==========================================
FROM python:3.10-slim AS runner

WORKDIR /app

# Création et configuration d'un utilisateur système non-root sécurisé
RUN useradd -m appuser
USER appuser

# Récupération des dépendances compilées
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copie du code de l'API et du modèle
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser model.joblib .
COPY --chown=appuser:appuser streamlit_app.py .
COPY --chown=appuser:appuser x_train_sample.csv .

EXPOSE 8000
EXPOSE 8501

# Lancement par défaut du backend FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
"""

dockerfile_path = os.path.join(api_dir, "Dockerfile")
with open(dockerfile_path, "w", encoding="utf-8") as f:
    f.write(dockerfile_content.strip())

print("=" * 60)
print(f"✅ API FastAPI générée avec succès dans : {api_dir}")
print(f"✅ Application Streamlit générée dans : {streamlit_path}")
print(f"✅ Dockerfile de production multi-stage créé : {dockerfile_path}")
print("Pour exécuter localement :")
print(f"  1. Démarrez l'API  : uvicorn app:app --port 8000")
print(f"  2. Démarrez l'UI   : streamlit run streamlit_app.py")
print("=" * 60)
```
