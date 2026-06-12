// ==========================================
// 1. CREATE CONSTRAINT + CREATE INDEX
// ==========================================
// Note : La création d'index accélère considérablement l'opération MERGE.
CREATE INDEX concept_name_idx IF NOT EXISTS FOR (c:Concept) ON (c.name);
CREATE INDEX tool_name_idx IF NOT EXISTS FOR (t:Tool) ON (t.name);
CREATE INDEX procedure_title_idx IF NOT EXISTS FOR (p:Procedure) ON (p.title);

// Recommandation : dans un environnement de production, on utiliserait des contraintes d'unicité
// CREATE CONSTRAINT concept_unique IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE;


// ==========================================
// 2. Section: Concepts (time_series)
// Source: "7 Steps to Mastering Time Series Analysis with Python - KDnuggets"
// Source: "Lagged features for time series forecasting - Scikit-learn"
// ==========================================
MERGE (c1:Concept {name: "Stationnarité"})
  ON CREATE SET c1.category = "time_series", c1.definition = "Propriété statistique constante dans le temps"
MERGE (c2:Concept {name: "Décomposition STL"})
  ON CREATE SET c2.category = "time_series"
MERGE (c3:Concept {name: "Lagged Features"})
  ON CREATE SET c3.category = "time_series"
MERGE (c4:Concept {name: "TimeSeriesSplit"})
  ON CREATE SET c4.category = "time_series", c4.definition = "Validation croisée temporelle sans data leakage"
MERGE (m1:Method {name: "Différenciation"})
  ON CREATE SET m1.category = "time_series"


// ==========================================
// 3. Section: Concepts (mlops)
// Source: "MLOps in Practice — Jupyter to Production ML Pipeline 2026 - EITT"
// Source: "Build Your First MLOps Pipeline in 90 Minutes - KodeKloud"
// ==========================================
MERGE (m2:Concept {name: "Concept Drift"})
  ON CREATE SET m2.category = "mlops"
MERGE (m3:Concept {name: "Model Reproducibility"})
  ON CREATE SET m3.category = "mlops"
MERGE (m4:Concept {name: "Model Registry"})
  ON CREATE SET m4.category = "mlops"
MERGE (m5:Concept {name: "Feature Store"})
  ON CREATE SET m5.category = "mlops"
MERGE (m6:Concept {name: "Canary Deployment"})
  ON CREATE SET m6.category = "mlops"
MERGE (req1:Requirement {name: "Database Backend"})


// ==========================================
// 4. Section: Tools
// Source: Ensemble des 45 sources, notamment les comparatifs Agentic AI et MLOps
// ==========================================
MERGE (t1:Tool {name: "MLflow"}) ON CREATE SET t1.category = "mlops"
MERGE (t2:Tool {name: "DVC"}) ON CREATE SET t2.category = "mlops"
MERGE (t3:Tool {name: "Feast"}) ON CREATE SET t3.category = "mlops"
MERGE (t4:Tool {name: "Docker"}) ON CREATE SET t4.category = "mlops"
MERGE (t5:Tool {name: "LangGraph"}) ON CREATE SET t5.category = "agentic_ai"
MERGE (t6:Tool {name: "CrewAI"}) ON CREATE SET t6.category = "agentic_ai"
MERGE (t7:Tool {name: "AutoGen"}) ON CREATE SET t7.category = "agentic_ai"
MERGE (t8:Tool {name: "LangChain"}) ON CREATE SET t8.category = "agentic_ai"
MERGE (t9:Tool {name: "Pandera"}) ON CREATE SET t9.category = "data_engineering"
MERGE (t10:Tool {name: "statsmodels"}) ON CREATE SET t10.category = "time_series"
MERGE (t11:Tool {name: "scikit-learn"}) ON CREATE SET t11.category = "machine_learning"
MERGE (t12:Tool {name: "XGBoost"}) ON CREATE SET t12.category = "machine_learning"


// ==========================================
// 5. Section: Procedures
// Source: Extractions procédurales (KDnuggets, KodeKloud, Firecrawl)
// ==========================================
MERGE (p1:Procedure {title: "Detect and Achieve Stationarity"})
  ON CREATE SET p1.domain = "time_series",
                p1.steps = "[\"Visualiser l'autocorrélation (ACF/PACF)\", \"Effectuer tests ADF/KPSS\", \"Appliquer la différenciation si non-stationnaire\"]"

MERGE (p2:Procedure {title: "Setup MLflow Tracking Server with Model Registry"})
  ON CREATE SET p2.domain = "mlops",
                p2.steps = "[\"Démarrer serveur avec backend DB\", \"Logger l'expérience avec paramètres\", \"Enregistrer le modèle avec alias (ex: @champion)\"]"

MERGE (p3:Procedure {title: "Setup Data Validation with Pandera Schemas"})
  ON CREATE SET p3.domain = "data_engineering",
                p3.steps = "[\"Définir un schéma basé sur les classes\", \"Intégrer dans les tests Pytest\", \"Valider paresseusement (lazy=True) en production\"]"

MERGE (p4:Procedure {title: "Build Stateful Agent Workflow with LangGraph"})
  ON CREATE SET p4.domain = "agentic_ai",
                p4.steps = "[\"Définir le graphe d'états (DAG)\", \"Configurer le routage\", \"Intégrer la mémoire LangChain\", \"Ajouter un point de contrôle humain\"]"


// ==========================================
// 6. Section: Decision Trees
// Source: "CrewAI vs AutoGen vs Microsoft Agent Framework", "The Kaggle Grandmasters Playbook"
// ==========================================
MERGE (d1:Decision {id: "ts-model-selection"})
  ON CREATE SET d1.question = "Quel modèle pour une série temporelle ?",
                d1.context = "time_series",
                d1.decision_tree = "{\"root\": \"Caractéristiques de la série\", \"branches\": [{\"condition\": \"Série classique bien comprise\", \"action\": \"Utiliser ARIMA\"}, {\"condition\": \"Variables non-linéaires complexes\", \"action\": \"Utiliser XGBoost/LightGBM\"}]}"

MERGE (d2:Decision {id: "agentic-framework-selection"})
  ON CREATE SET d2.question = "Quel framework d'agents IA choisir ?",
                d2.context = "agentic_ai",
                d2.decision_tree = "{\"root\": \"Exigences du projet\", \"branches\": [{\"condition\": \"Besoin de contrôle d'état et validation humaine\", \"action\": \"Utiliser LangGraph\"}, {\"condition\": \"Workflows business déterministes basés sur des rôles\", \"action\": \"Utiliser CrewAI\"}, {\"condition\": \"Extraction de documents et RAG\", \"action\": \"Utiliser Haystack\"}]}"

MERGE (d3:Decision {id: "mlops-infrastructure"})
  ON CREATE SET d3.question = "Services Cloud Managés ou Open-Source hébergé ?",
                d3.context = "mlops",
                d3.decision_tree = "{\"root\": \"Maturité de l'organisation\", \"branches\": [{\"condition\": \"Équipe novice et besoin de rapidité\", \"action\": \"AWS SageMaker, Azure ML\"}, {\"condition\": \"Équipe mature refusant le vendor lock-in\", \"action\": \"Kubeflow, MLflow local\"}]}"


// ==========================================
// 7. Section: Relations
// Source: Analyse des dépendances et de l'orchestration des outils
// ==========================================
// Relations Conceptuelles et Outils
MATCH (diff:Method {name: "Différenciation"}), (stat:Concept {name: "Stationnarité"})
MERGE (diff)-[r1:ENABLES]->(stat)
  ON CREATE SET r1.strength = 0.9, r1.evidence = "Appliquer la différenciation rend la série stationnaire"

MATCH (docker:Tool {name: "Docker"}), (repro:Concept {name: "Model Reproducibility"})
MERGE (docker)-[r2:ENABLES]->(repro)
  ON CREATE SET r2.strength = 0.85

MATCH (mlflow:Tool {name: "MLflow"}), (db_backend:Requirement {name: "Database Backend"})
MERGE (mlflow)-[r3:REQUIRES]->(db_backend)
  ON CREATE SET r3.strength = 1.0, r3.evidence = "MLflow's model registry requires a database backend"

MATCH (feast:Tool {name: "Feast"}), (repro:Concept {name: "Model Reproducibility"})
MERGE (feast)-[r4:ENABLES]->(repro)
  ON CREATE SET r4.evidence = "Garantit la cohérence des features entre l'entraînement et l'inférence"

MATCH (langgraph:Tool {name: "LangGraph"}), (langchain:Tool {name: "LangChain"})
MERGE (langgraph)-[r5:REQUIRES]->(langchain)
  ON CREATE SET r5.evidence = "LangGraph supports memory through LangChain integration"

MATCH (crewai:Tool {name: "CrewAI"}), (autogen:Tool {name: "AutoGen"})
MERGE (crewai)-[r6:ALTERNATIVE_TO]->(autogen)
  ON CREATE SET r6.context = "Rôles fixes vs Événementiel conversationnel", r6.strength = 0.8

// Relations Procédures -> Concepts/Outils
MATCH (proc1:Procedure {title: "Detect and Achieve Stationarity"}), (stat:Concept {name: "Stationnarité"}), (sm:Tool {name: "statsmodels"})
MERGE (proc1)-[:REQUIRES]->(stat)
MERGE (proc1)-[:USES_TOOL]->(sm)

MATCH (proc2:Procedure {title: "Setup MLflow Tracking Server with Model Registry"}), (mlflow:Tool {name: "MLflow"}), (db_backend:Requirement {name: "Database Backend"})
MERGE (proc2)-[:USES_TOOL]->(mlflow)
MERGE (proc2)-[:REQUIRES]->(db_backend)

MATCH (proc3:Procedure {title: "Setup Data Validation with Pandera Schemas"}), (pandera:Tool {name: "Pandera"}), (repro:Concept {name: "Model Reproducibility"})
MERGE (proc3)-[:USES_TOOL]->(pandera)
MERGE (proc3)-[:ENABLES]->(repro)

MATCH (proc4:Procedure {title: "Build Stateful Agent Workflow with LangGraph"}), (langgraph:Tool {name: "LangGraph"})
MERGE (proc4)-[:USES_TOOL]->(langgraph)


// ==========================================
// 8. Section: NLP Domain
// ==========================================
MERGE (cnlp1:Concept {name: "TF-IDF"})
  ON CREATE SET cnlp1.category = "nlp", cnlp1.definition = "Term Frequency-Inverse Document Frequency, méthode de vectorisation de texte"
MERGE (cnlp2:Concept {name: "Tokenization"})
  ON CREATE SET cnlp2.category = "nlp", cnlp2.definition = "Découpage de texte en unités lexicales (tokens)"
MERGE (tnlp1:Tool {name: "nltk"}) ON CREATE SET tnlp1.category = "nlp"
MERGE (pnlp1:Procedure {title: "Apply TF-IDF vectorization for text classification"})
  ON CREATE SET pnlp1.domain = "nlp",
                pnlp1.steps = "[\"Tokeniser le texte brut\", \"Supprimer les stopwords\", \"Instancier TfidfVectorizer\", \"Ajuster et transformer sur le train\", \"Transformer le test\"]"
MERGE (dnlp1:Decision {id: "nlp-model-selection"})
  ON CREATE SET dnlp1.question = "Quelle stratégie de vectorisation textuelle ?",
                dnlp1.context = "nlp",
                dnlp1.decision_tree = "{\"root\": \"Type de texte\", \"branches\": [{\"condition\": \"Texte court et vocabulaire simple\", \"action\": \"Utiliser TF-IDF (TfidfVectorizer)\"}, {\"condition\": \"Relations sémantiques complexes\", \"action\": \"Utiliser Transformers (BERT, CamemBERT)\"}]}"

// Relations NLP
MATCH (tok:Concept {name: "Tokenization"}), (tfidf:Concept {name: "TF-IDF"})
MERGE (tok)-[:ENABLES]->(tfidf)
MATCH (pnlp:Procedure {title: "Apply TF-IDF vectorization for text classification"}), (tfidf:Concept {name: "TF-IDF"}), (sk:Tool {name: "scikit-learn"})
MERGE (pnlp)-[:REQUIRES]->(tfidf)
MERGE (pnlp)-[:USES_TOOL]->(sk)


// ==========================================
// 9. Section: Geospatial Domain
// ==========================================
MERGE (cgeo1:Concept {name: "Haversine Distance"})
  ON CREATE SET cgeo1.category = "geospatial", cgeo1.definition = "Distance sur une sphère à partir de coordonnées latitude/longitude"
MERGE (cgeo2:Concept {name: "Système de coordonnées"})
  ON CREATE SET cgeo2.category = "geospatial", cgeo2.definition = "Référentiel cartographique spatial (ex: EPSG:4326)"
MERGE (tgeo1:Tool {name: "geopandas"}) ON CREATE SET tgeo1.category = "geospatial"
MERGE (pgeo1:Procedure {title: "Calculate Haversine Distance between points"})
  ON CREATE SET pgeo1.domain = "geospatial",
                pgeo1.steps = "[\"Convertir latitudes/longitudes en radians\", \"Calculer les deltas lat/lon\", \"Appliquer la formule trigonométrique\", \"Multiplier par le rayon de la Terre (6371 km)\"]"
MERGE (dgeo1:Decision {id: "geospatial-anomalies"})
  ON CREATE SET dgeo1.question = "Comment traiter les anomalies géographiques ?",
                dgeo1.context = "geospatial",
                dgeo1.decision_tree = "{\"root\": \"Type d'anomalie\", \"branches\": [{\"condition\": \"Latitude/Longitude hors limites (-90/90, -180/180)\", \"action\": \"Imputer par la médiane ou supprimer la ligne\"}, {\"condition\": \"Points aberrants (ex: en mer pour une adresse terrestre)\", \"action\": \"Filtrer avec un polygone de masque terrestre via geopandas\"}]}"

// Relations Geospatial
MATCH (pgeo:Procedure {title: "Calculate Haversine Distance between points"}), (hav:Concept {name: "Haversine Distance"}), (gpd:Tool {name: "geopandas"})
MERGE (pgeo)-[:REQUIRES]->(hav)
MERGE (pgeo)-[:USES_TOOL]->(gpd)

