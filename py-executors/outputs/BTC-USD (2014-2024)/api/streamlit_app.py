import streamlit as st
import requests
import pandas as pd
import numpy as np

st.set_page_config(
    page_title="Inference BTC-USD (2014-2024) - MLOps", 
    page_icon="📈", 
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/artificial-intelligence.png", width=100)
    st.title("Gouvernance MLOps")
    st.write("**Dataset** : BTC-USD (2014-2024)")
    st.write("**Tache** : PREDICTION SÉRIE TEMPORELLE")
    st.write("**Modele** : LightGBM Regressor")
    st.write("---")
    st.info("Cette interface communique avec l'API FastAPI locale pour executer des predictions de series temporelles.")

st.title("📊 Interface de Prédiction Temporelle — BTC-USD (2014-2024)")
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
            payload = {"history": history_list}
            
            with st.spinner("Prevision en cours..."):
                backend_url = "http://localhost:8000/predict"
                response = requests.post(backend_url, json=payload, timeout=10)
                
                if response.status_code == 200:
                    res_json = response.json()
                    pred_val = res_json["prediction"]
                    timestamp = res_json.get("timestamp", "Date inconnue")
                    
                    st.success(f"🎯 **Prevision pour la prochaine date ({timestamp}):** {pred_val:.4f}")
                else:
                    st.error(f"❌ Erreur du serveur FastAPI (code {response.status_code}) : {response.text}")
    except Exception as e:
        st.error(f"❌ Erreur lors de la lecture ou de l'envoi de l'historique : {e}")