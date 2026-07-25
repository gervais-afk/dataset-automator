# 🚀 Guide de Lancement Rapide — Dataset Automator

Ce document regroupe les instructions pour lancer et piloter l'application complète **Dataset Automator**, soit en **1 clic automatisé**, soit via les terminaux modulaires.

---

## ⚡ Option 1 : Lancement Automatisé en 1 Clic (Recommandé)

Pour lancer automatiquement **tous les services** dans des fenêtres de terminal dédiées (afin de conserver une visibilité totale sur les logs et erreurs en temps réel) :

Faites simplement un double-clic sur :
👉 **`launch_all.bat`** (situé à la racine du dépôt).

Ou en ligne de commande PowerShell :
```powershell
cd "c:\Users\HP\cam_data_sov_solutions newversion\dataset_automator"
.\launch_all.bat
```

### 🌐 Interfaces Web Ouvertes Automatiquement :
*   **Dashboard Streamlit (Interface Métier) :** [http://localhost:8501](http://localhost:8501)
*   **MLflow UI (Tracking & Modèles) :** [http://localhost:5000](http://localhost:5000)
*   **Genkit UI (Traces & Logs IA) :** [http://localhost:4000](http://localhost:4000)
*   **Neo4j Web Browser (Knowledge Graph) :** [http://localhost:7474](http://localhost:7474)

---

## 🛠️ Prérequis (Logiciels de bureau à lancer)
1. **Docker Desktop** : Assurez-vous que Docker est démarré. (Le conteneur Neo4j `neo4j:latest` tourne sur `bolt://127.0.0.1:7687`).
2. **LM Studio** : Lancez l'application, chargez le modèle `google/gemma-4-12b` et démarrez le serveur local API (port `1234`).

---

## 🖥️ Rôle des 5 Terminaux Dédiés (Lancement Manuel ou Automatisé)

### ⬛ Terminal 1 : Firebase Emulator (Base de données locale & Auth)
*Utilité : Gère l'authentification et l'état des tâches (`jobId`) dans Firestore.*
```powershell
cd dataset_automator
firebase emulators:start
```

---

### ⬛ Terminal 2 : MLflow UI (Tracking & Métriques)
*Utilité : Interface Web pour voir les courbes de performances, Optuna et les artefacts MLOps.*
```powershell
cd dataset_automator\workspace
..\py-executors\.venv\Scripts\mlflow.exe ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root file:///mlruns
```

---

### ⬛ Terminal 3 : Genkit Developer UI (Traces & Observabilité Agentique)
*Utilité : Inspection visuelle des appels LLM et des traces de réflexion de Genkit.*
```powershell
cd dataset_automator\ts-orchestrator
npx genkit start
```

---

### ⬛ Terminal 4 : Dashboard Streamlit (Interface Web Utilisateur)
*Utilité : Permet à l'utilisateur de charger un dataset, de lancer l'analyse autonome et de visualiser les résultats.*
```powershell
cd dataset_automator\py-executors
.venv\Scripts\streamlit.exe run src/app_dashboard.py
```

---

### ⬛ Terminal 5 : TS Orchestrator (Cerveau du Pipeline RAG)
*Utilité : Écoute les requêtes Firestore, consulte le Graph RAG Neo4j et coordonne les générateurs Python.*
```powershell
cd dataset_automator\ts-orchestrator
npm run dev
```

---

## 📊 Modules & Capacités Réalisés
1. **RAG Hybride Vectoriel & Ontologique Neo4j** (Catalogues de modèles MLOps, règles d'interprétation, coûts métier).
2. **Support Multimodal Gemma 4 12B QAT / LM Studio** (Raisonnement RAG, génération de code, validation visuelle de graphiques & matrices de confusion).
3. **Pipeline Multi-Domaine Extensible** (Classification, Régression, Time Series / SARIMA, Clustering, Détection d'anomalies, NLP, Computer Vision, Graphes, Causal Inference, Reinforcement Learning, Portfolio Risk Evaluation).
4. **Auto-Correction & Self-Healing** des Notebooks Python avec boucle d'itération sandboxée.
5. **Dashboard Streamlit Interactif** avec monitoring MLOps (MLflow) et validation de contrats de données (Great Expectations / Data Contracts).
