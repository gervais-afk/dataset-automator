# 🚀 Guide de Lancement Rapide — Dataset Automator v4.0

Ce document regroupe les instructions pour lancer et piloter la plateforme **Dataset Automator**, soit en **1 clic automatisé**, soit via les terminaux modulaires.

---

## ⚡ Option 1 : Lancement Automatisé en 1 Clic (Recommandé)

Pour lancer automatiquement **tous les services** dans des fenêtres de terminal dédiées (afin de conserver une visibilité totale sur les logs et traces en temps réel) :

Faites simplement un double-clic sur :
👉 **`launch_all.bat`** (situé à la racine du projet).

Ou en ligne de commande PowerShell :
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory"
.\launch_all.bat
```

### 🌐 Interfaces Web Ouvertes Automatiquement :
* **Dashboard Streamlit (Interface Métier & Canvas Spatial) :** [http://localhost:8501](http://localhost:8501)
* **MLflow UI (Tracking, Modèles & Artefacts) :** [http://localhost:5000](http://localhost:5000)
* **Genkit UI (Traces & Raisonnement Multi-Agents) :** [http://localhost:4000](http://localhost:4000)
* **Neo4j Web Browser (Graphe de Connaissances OKF) :** [http://localhost:7474](http://localhost:7474)

---

## 🛠️ Prérequis Système

1. **Docker Desktop** : Assurez-vous que Docker est démarré. (Le conteneur Neo4j `neo4j:latest` tourne sur `bolt://127.0.0.1:7687` avec mot de passe `password123`).
2. **Environnement Python (`.venv`)** : Installé automatiquement via `uv sync` dans `py-executors/`.

---

## 🖥️ Rôle des 5 Terminaux Dédiés (Lancement Modulaire Manuel)

Si vous préférez lancer chaque composant individuellement :

### ⬛ Terminal 1 : Firebase Emulator (Base locale & Gestion d'état des Jobs)
*Utilité : Gère l'authentification et l'état asynchrone des tâches (`jobId`) dans Firestore.*
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator"
firebase emulators:start
```

---

### ⬛ Terminal 2 : Serveur MLflow (Tracking & Métriques)
*Utilité : Enregistrement des runs d'expériences, métriques de cross-validation et sérialisation SKOPS.*
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator\workspace"
..\py-executors\.venv\Scripts\mlflow.exe ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root file:///mlruns --port 5000
```

---

### ⬛ Terminal 3 : Genkit Developer UI (Traces & Observabilité)
*Utilité : Visualisation des traces d'exécution de l'orchestrateur, des prompts et des appels d'outils FastMCP.*
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator\ts-orchestrator"
npx genkit start
```

---

### ⬛ Terminal 4 : L'Orchestrateur TypeScript (Cerveau du Pipeline)
*Utilité : Moteur décisionnel principal orchestrant les 7 phases du cycle CRISP-ML(Q).*
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator\ts-orchestrator"
npm run dev
```

---

### ⬛ Terminal 5 : Dashboard Streamlit Central (Control Center)
*Utilité : Interface utilisateur complète (Canvas Spatial SVG, Copilot chatbot, PAIR What-If Tool, Google Model Card, Red Teamer, et Validateur de Notebooks 100/100).*
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator\py-executors"
& ".venv\Scripts\streamlit.exe" run src/app_dashboard.py
```

---

## 🔬 Nouveaux Outils & Scripts d'Audit Autonomes

### 📊 1. Générateur de Rapport HTML MLOps Visuel & Interactif
*Utilité : Produit un rapport web autonome incluant la galerie des figures, le journal d'auto-correction et le reçu cryptographique.*
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator\py-executors"
& ".venv\Scripts\python.exe" src/visual_report_generator.py
```

### 🛡️ 2. Validateur Forensic de Notebooks CRISP-ML (Score 100/100)
*Utilité : Audit statique et dynamique du notebook Jupyter généré pour certifier l'absence de fuite de données.*
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator\py-executors"
& ".venv\Scripts\python.exe" src/notebook_validator.py
```

### 🚨 3. Détecteur de Data Drift (KS-Test & PSI)
*Utilité : Vérification de la stabilité temporelle des distributions et alertes de dérive.*
```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator\py-executors"
& ".venv\Scripts\python.exe" src/drift_monitor.py
```

---

## ☁️ Option 2 : Déploiement Production en 1 Clic sur Google Cloud Run

Pour déployer l'application complète sur **Google Cloud Run** et fournir une URL HTTPS publique accessible en direct par le jury Devpost :

```powershell
cd "c:\Users\HP\Desktop\Notebooks factory\dataset_automator"
.\scripts\deploy_cloud_run.ps1
```

*Ce script effectue automatiquement :*
1. L'activation des APIs Google Cloud (`run`, `cloudbuild`, `aiplatform`, `bigquery`).
2. La création du compte de service IAM sécurisé `dataset-automator-runner`.
3. L'attribution des rôles Vertex AI & BigQuery.
4. La compilation de l'image Docker et le déploiement Cloud Run managé avec autoscaling (0 à 5 instances).
5. L'affichage de l'URL publique HTTPS prête pour le jury du Hackathon !
