# 🚀 Guide de Lancement Rapide — Dataset Automator

Ce document regroupe les instructions pour lancer et piloter l'application complète **Dataset Automator**, soit en **1 clic automatisé**, soit via les terminaux modulaires.

---

## ⚡ Option 1 : Lancement Automatisé en 1 Clic (Recommandé)

Pour lancer automatiquement **tous les services** dans des fenêtres de terminal dédiées (afin de conserver une visibilité totale sur les logs et erreurs en temps réel) :

Faites simplement un double-clic sur :
👉 **`launch_all.bat`** (situé à la racine du projet).

Ou en ligne de commande PowerShell :
```powershell
cd "C:\Users\HP\cam_data_sov_solutions newversion"
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
cd "C:\Users\HP\cam_data_sov_solutions newversion\dataset_automator"
firebase emulators:start
```

---

### ⬛ Terminal 2 : MLflow UI (Tracking & Métriques)
*Utilité : Interface Web pour voir les courbes de performances, Optuna et les artefacts MLOps.*
```powershell
cd "C:\Users\HP\cam_data_sov_solutions newversion\dataset_automator\workspace"
..\py-executors\.venv\Scripts\mlflow.exe ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root file:///mlruns
```
*(Note : Si une erreur de schéma MLflow apparaît après mise à jour, supprimez simplement le fichier `mlflow.db` dans `workspace` pour réinitialiser le schéma).*

---

### ⬛ Terminal 3 : Genkit Developer UI (Traces & Raisonnement LLM)
*Utilité : Permet de visualiser en temps réel les prompts, les appels d'outils (`replInterpreter`, `graphRAGReasoner`) et les erreurs LLM.*
```powershell
cd "C:\Users\HP\cam_data_sov_solutions newversion\dataset_automator\ts-orchestrator"
npx genkit start
```

---

### ⬛ Terminal 4 : L'Orchestrateur TypeScript (Cerveau du Pipeline)
*Utilité : Cerveau principal qui exécute les 7 phases du workflow MLOps.*
```powershell
cd "C:\Users\HP\cam_data_sov_solutions newversion\dataset_automator\ts-orchestrator"
npm run dev
```
👉 **Attente de votre saisie :** Dès le démarrage, le terminal affiche la liste des datasets disponibles. Tapez le numéro du choix (ex: **`7`** pour `test_cameroun_business.csv`) et appuyez sur **Entrée** pour démarrer l'exécution.

---

### ⬛ Terminal 5 : Dashboard Web Streamlit Central
*Utilité : Interface utilisateur pour déposer un CSV, suivre la progression, consulter SHAP, explorer le Knowledge Graph et télécharger le Notebook MLOps `.ipynb`.*
```powershell
cd "C:\Users\HP\cam_data_sov_solutions newversion\dataset_automator\py-executors"
& ".venv\Scripts\streamlit.exe" run src/app_dashboard.py
```

---

## 🛠️ Nouveaux Outils & Scripts Spécialisés

### 🚨 1. Détecteur de Data Drift & Surveillance Statistique
*Utilité : Compare un dataset d'entraînement avec un dataset de production pour détecter les dérives (KS-test / PSI).*
```powershell
cd "C:\Users\HP\cam_data_sov_solutions newversion\dataset_automator\py-executors"
& ".venv\Scripts\python.exe" src/tools/data_drift_detector.py --ref "data/reference.csv" --curr "data/production.csv"
```
*(En cas de dérive majeure > 30%, une alerte `(:Alert)` est automatiquement enregistrée dans Neo4j).*

---

### 🕸️ 2. Visualisateur de Graphe Neo4j (HTML Interactif)
*Utilité : Exporte la vue HTML 2D/3D dynamique du Knowledge Graph Neo4j.*
```powershell
cd "C:\Users\HP\cam_data_sov_solutions newversion\dataset_automator\py-executors"
& ".venv\Scripts\python.exe" ..\workspace\visualize_graph.py
```
*(Génère `dataset_automator/workspace/knowledge_graph_view.html` consultable directement dans le Dashboard Streamlit).*
