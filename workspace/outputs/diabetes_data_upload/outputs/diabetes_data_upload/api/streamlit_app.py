import streamlit as st
import requests
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Inference diabetes_data_upload - MLOps", 
    page_icon="🎯", 
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main {
        background-color: #0e1117;
        color: #ffffff;
    }
    .stButton>button {
        background: linear-gradient(135deg, #00c6ff 0%, #0072ff 100%);
        color: white;
        border: none;
        padding: 10px 24px;
        border-radius: 8px;
        font-weight: bold;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 15px rgba(0, 114, 255, 0.4);
    }
    .metric-card {
        background-color: #1e222b;
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid #0072ff;
        margin-bottom: 20px;
    }
    .metric-title {
        font-size: 14px;
        color: #8a909d;
        text-transform: uppercase;
        margin-bottom: 5px;
    }
    .metric-value {
        font-size: 28px;
        font-weight: bold;
        color: #ffffff;
    }
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.image("https://img.icons8.com/clouds/200/artificial-intelligence.png", width=100)
    st.title("Gouvernance MLOps")
    st.write("**Dataset** : diabetes_data_upload")
    st.write("**Tache** : CLASSIFICATION")
    st.write("**Modele** : TabICL (SOTA)")
    st.write("---")
    st.info("Cette interface communique avec l'API FastAPI locale pour executer des predictions et calculer des explications locales via LIME.")

st.title("🎯 Diagnostic & Inference Interactive")
st.write("Saisissez les caracteristiques ci-dessous pour obtenir une prediction immediate accompagnee de sa justification locale.")

st.subheader("⚙️ Saisie des variables d'entree")

num_cols = ['Age']
cat_cols = ['Gender', 'Polyuria', 'Polydipsia', 'sudden weight loss', 'weakness', 'Polyphagia', 'Genital thrush', 'visual blurring', 'Itching', 'Irritability', 'delayed healing', 'partial paresis', 'muscle stiffness', 'Alopecia', 'Obesity', 'class']
features_input = {}

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
        if col_name == "class": continue
        col_ui = cols_num[i % len(cols_num)]
        features_input[col_name] = col_ui.number_input(f"{col_name}", value=0.0, step=0.1)

if cat_cols:
    st.markdown("---")
    st.markdown("##### 🔠 Variables Categorielles")
    cols_cat = st.columns(min(3, max(1, len(cat_cols))))
    for i, col_name in enumerate(cat_cols):
        if col_name == "class": continue
        col_ui = cols_cat[i % len(cols_cat)]
        
        # Recuperer les categories uniques depuis l'echantillon si disponible
        options = []
        if df_sample is not None and col_name in df_sample.columns:
            options = list(df_sample[col_name].dropna().unique())
        
        if options:
            features_input[col_name] = col_ui.selectbox(f"{col_name}", options=options)
        else:
            features_input[col_name] = col_ui.text_input(f"{col_name}", value="")

st.markdown("---")

if st.button("🚀 Calculer la Prediction & Explication", type="primary"):
    payload = {"data": features_input}

    with st.spinner("Inference en cours..."):
        try:
            backend_url = "http://localhost:8000/predict"
            response = requests.post(backend_url, json=payload, timeout=10)

            if response.status_code == 200:
                res_json = response.json()
                pred = res_json["predictions"][0]

                col_m1, col_m2 = st.columns(2)
                is_classif = "probabilities" in res_json or "classification" == "classification"

                with col_m1:
                    if is_classif:
                        decision_color = "#2ca02c" if pred == 0 else "#d62728"
                        st.markdown(f'''
                        <div class="metric-card" style="border-left-color: {decision_color};">
                            <div class="metric-title">Decision Modele</div>
                            <div class="metric-value" style="color: {decision_color};">Classe {int(pred)}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                    else:
                        st.markdown(f'''
                        <div class="metric-card">
                            <div class="metric-title">Valeur Predite</div>
                            <div class="metric-value">{pred:.4f}</div>
                        </div>
                        ''', unsafe_allow_html=True)

                with col_m2:
                    if is_classif and "probabilities" in res_json:
                        probs = res_json["probabilities"][0]
                        confidence = probs[int(pred)] * 100
                        st.markdown(f'''
                        <div class="metric-card" style="border-left-color: #0072ff;">
                            <div class="metric-title">Confiance (Probabilite)</div>
                            <div class="metric-value">{confidence:.2f}%</div>
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
                st.error(f"❌ Erreur du serveur FastAPI (code {response.status_code}) : {response.text}")
                st.stop()
        except Exception as e:
            st.error(f"❌ Impossible de joindre l'API FastAPI sur /predict : {e}")
            st.stop()

    if "classification" != "timeseries":
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
                                st.markdown(f"• **{c['feature']}** : `{c['coefficient']:+.4f}` (:{color_text}[{direction}] la prediction)")
                    else:
                        st.warning("Aucune contribution significative calculee par LIME.")
                else:
                    st.warning(f"⚠️ L'API n'a pas pu calculer d'explications LIME (code {exp_response.status_code})")
            except Exception as e:
                st.warning(f"⚠️ Le calcul LIME a echoue ou l'echantillon de train n'est pas disponible : {e}")