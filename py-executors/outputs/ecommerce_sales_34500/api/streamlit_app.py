import streamlit as st
import requests
import pandas as pd

st.set_page_config(page_title="Inférence ecommerce_sales_34500", layout="wide")
st.title("📊 Interface de Prédiction Interactrice — ecommerce_sales_34500")
st.write("Saisissez les caractéristiques ci-dessous pour obtenir une prédiction immédiate du modèle.")

# Formulaire de saisie dynamique des variables explicatives
st.subheader("⚙️ Variables d'Entrée")

# Extraction des caractéristiques attendues (fallback par défaut si vide)
num_cols = []
features_input = {}

cols = st.columns(min(3, max(1, len(num_cols))))
for i, col_name in enumerate(num_cols):
    col_ui = cols[i % len(cols)]
    features_input[col_name] = col_ui.number_input(f"{col_name}", value=0.0)

if st.button("🚀 Lancer la Prédiction", type="primary"):
    payload = {"data": features_input}
    try:
        # Envoie de la requête à l'API FastAPI (DNS interne si conteneurisé)
        backend_url = "http://localhost:8000/predict"
        response = requests.post(backend_url, json=payload)

        if response.status_code == 200:
            res_json = response.json()
            pred = res_json["predictions"][0]
            st.success(f"🎯 **Valeur Prédite par le Modèle :** {pred:.4f}")

            # Probabilités pour la classification
            if "probabilities" in res_json:
                st.info(f"⚖️ **Probabilités associées :** {res_json['probabilities'][0]}")
        else:
            st.error(f"❌ Erreur du serveur FastAPI (code {response.status_code}) : {response.text}")
    except Exception as e:
        st.error(f"❌ Impossible de joindre l'API FastAPI : {e}")