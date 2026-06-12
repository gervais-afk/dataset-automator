# 🌟 Dataset Automator: Platform Agentic End-to-End MLOps

`Dataset Automator` est une plateforme industrielle d'**IA Agentique appliquée au MLOps (CRISP-ML(Q))**. Elle orchestre de multiples agents intelligents spécialisés pour profiler, nettoyer, optimiser, auditer et documenter n'importe quel jeu de données tabulaires de manière déterministe et sécurisée.

Ce projet démontre comment allier la puissance de l'IA générative (LLM locaux/cloud) avec la rigueur de l'ingénierie logicielle traditionnelle (Bases de graphes Neo4j, validation Zod, Guardrails mathématiques et vision par ordinateur).

---

## 🏛️ Architecture Globale (Cerveau & Muscles)

L'application est conçue selon un modèle de **découplage asynchrone** complet :

```
                        +----------------------------+
                        |   Orchestrateur TS (Flow)  | <---+ (Zod / State)
                        +----------------------------+
                                      |
                       (Spawn asynchrone + Heartbeat)
                                      v
                        +----------------------------+
                        |    Workers Python (MCP)    | <---+ (Pandas / Sklearn)
                        +----------------------------+
```

*   **Le Cerveau (TS Orchestrator)** : Écrit en **TypeScript (Node.js)** avec **Google Genkit**. Il gère la logique de flux (Flows), maintient l'état, interroge le graphe de connaissances Neo4j, gère la gouvernance humaine (Human-in-the-Loop) et contrôle les cycles d'auto-correction (Self-Healing).
*   **Les Muscles (Python Workers)** : Un serveur **FastMCP** en **Python** qui exécute les tâches lourdes de science des données (Pandas, Scikit-Learn, Optuna, MLflow, CrewAI) et expose des outils à l'orchestrateur.

---

## 🚀 Fonctionnalités & Agents Experts

### 1. 🕵️‍♂️ Agent Adversarial Validator (Détection de Drift)
Avant d'établir une stratégie, cet agent cherche à détecter du **Data Drift** (dérive statistique) ou du **Target Leakage** :
*   Il sépare chronologiquement le dataset en 80% (passé) et 20% (futur).
*   Il entraîne un classifieur (`RandomForest`) pour distinguer le passé du futur.
*   Si le modèle y parvient avec un score **AUC > 0.6**, un drift est identifié. L'agent extrait les 5 caractéristiques responsables de la dérive et les injecte dans le contexte du LLM Stratège pour adapter la stratégie de nettoyage.

### 2. 🧠 Stratégie Assistée par Graph RAG (Neo4j)
L'orchestrateur extrait les concepts théoriques et les règles expertes métiers depuis une base de graphe **Neo4j** (ex: *"Dans une série temporelle, privilégier l'imputation par interpolation ou médiane plutôt que la moyenne"*). Ces règles alimentent le prompt du LLM.

### 🔄 Boucle de "Self-Healing" (Auto-Correction)
Les LLM locaux peuvent parfois échouer à formater leurs sorties. L'orchestrateur utilise des schémas **Zod** stricts. Si l'IA renvoie un schéma invalide :
*   L'erreur Zod est interceptée.
*   Elle est réinjectée dans le prompt du LLM comme feedback correctif.
*   L'orchestrateur réessaie (jusqu'à 3 fois) avec un délai d'attente progressif (backoff exponentiel).

### 3. 🚦 Double Guardrail (Mathématique & Visuel)
*   **Guardrail Mathématique** : Vérification des métriques de performance du modèle (sur-apprentissage/overfitting, recall nul sur des classes majoritaires).
*   **Guardrail Visuel (Chart Interpreter)** : L'image de la matrice de confusion ou des résidus est analysée par un agent de vision (VLM) pour détecter visuellement des anomalies graphiques (ex: effondrement de classe) que les chiffres n'auraient pas détectées.

### 4. ⚖️ Agent Explainability Auditor (SHAP Audit)
Avant la livraison du modèle, cet agent calcule les valeurs **SHAP** (teinte de la théorie des jeux coopératifs) pour :
*   Profiler l'attribution des variables dans la décision du modèle.
*   Calculer un **Score de Risque** (si une feature pèse >80% à elle seule, alerte de fuite de données ou de proxy biaisé).
*   Générer un graphique d'importance globale (`shap_summary.png`) et pousser les métriques brutes sur **Firestore**.

### 5. 🛡️ Heartbeat & Résilience Python
Pour éviter qu'un script Python ne gèle le serveur TS (ex: saturation RAM pendant Optuna) :
*   Un thread d'arrière-plan envoie un signal de vie (heartbeat) toutes les 10 secondes dans **Firestore**.
*   L'orchestrateur TypeScript monitore ce signal de manière non bloquante et applique un **SIGKILL** si le worker ne répond plus pendant 60 secondes, libérant proprement les ressources système.

---

## 🛠️ Stack Technique

*   **Backend TS** : Node.js, Google Genkit, TypeScript, Zod, Pino (logging).
*   **Calcul ML** : Python, Pandas, Scikit-Learn, SHAP, Optuna, CrewAI, Matplotlib, Seaborn.
*   **Bases de Données** : Neo4j (Graph RAG), Firebase Local Emulator (Firestore & Cloud Storage pour le découplage asynchrone).

---

## 📋 Livrables du Pipeline

Chaque exécution génère un dossier contenant :
1.  **Le Dataset Nettoyé** (`.csv`) après application de la stratégie.
2.  **Le Rapport SHAP** (`shap_summary.png`) d'explicabilité.
3.  **Le Notebook MLOps Final** (`.ipynb`) : Un rapport Jupyter complet structuré selon le standard CRISP-ML(Q), contenant le code de nettoyage, l'entraînement optimal (paramètres d'auto-tuning Optuna intégrés), et les évaluations MLflow.
