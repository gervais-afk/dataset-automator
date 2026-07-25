// === SECTION 1 : CONTRAINTES & INDEX ===
CREATE CONSTRAINT concept_name_uniq IF NOT EXISTS FOR (c:Concept) REQUIRE c.name IS UNIQUE;
CREATE CONSTRAINT tool_name_uniq IF NOT EXISTS FOR (t:Tool) REQUIRE t.name IS UNIQUE;
CREATE CONSTRAINT proc_title_uniq IF NOT EXISTS FOR (p:Procedure) REQUIRE p.title IS UNIQUE;
CREATE CONSTRAINT dt_id_uniq IF NOT EXISTS FOR (d:DecisionTree) REQUIRE d.id IS UNIQUE;

CREATE INDEX concept_category_idx IF NOT EXISTS FOR (c:Concept) ON (c.category);
CREATE INDEX tool_category_idx IF NOT EXISTS FOR (t:Tool) ON (t.category);
CREATE INDEX proc_domain_idx IF NOT EXISTS FOR (p:Procedure) ON (p.domain);
CREATE INDEX dt_context_idx IF NOT EXISTS FOR (d:DecisionTree) ON (d.context);

// === SECTION 2 : DOMAINES ===
MERGE (d1:Domain {name: 'time_series'})
MERGE (d2:Domain {name: 'mlops'})
MERGE (d3:Domain {name: 'data_engineering'})
MERGE (d4:Domain {name: 'supervised_learning'})
MERGE (d5:Domain {name: 'clustering'})
MERGE (d6:Domain {name: 'agentic_ai'})
MERGE (d7:Domain {name: 'dev_tools'})
MERGE (d8:Domain {name: 'validation'})
MERGE (d9:Domain {name: 'feature_engineering'})
MERGE (d10:Domain {name: 'modeling'})
MERGE (d11:Domain {name: 'finance'})
MERGE (d12:Domain {name: 'ecommerce'})
MERGE (d13:Domain {name: 'medical'});

// === SECTION 3 : CONCEPTS & TOOLS ===
MERGE (c1:Concept {name: 'Stationnarite'}) SET c1 += {category: 'time_series', definition: 'Propriete d\'une serie temporelle dont les caracteristiques statistiques restent constantes.', token_estimate: 25}
MERGE (c2:Concept {name: 'Decomposition STL'}) SET c2 += {category: 'time_series', definition: 'Methode de separation d\'une serie temporelle en composants de tendance, saisonniers et residuels.', token_estimate: 30}
MERGE (c3:Concept {name: 'Concept Drift'}) SET c3 += {category: 'mlops', definition: 'Changement imprevu des proprietes statistiques de la variable cible au fil du temps.', token_estimate: 28}
MERGE (c4:Concept {name: 'Lagged Features'}) SET c4 += {category: 'time_series', definition: 'Variables creees en utilisant les valeurs passees d\'une serie temporelle.', token_estimate: 22}
MERGE (c5:Concept {name: 'SplineTransformer'}) SET c5 += {category: 'time_series', definition: 'Ingenierie de caracteristiques utilisant des fonctions splines pour modeliser des modeles cycliques.', token_estimate: 35}
MERGE (c6:Concept {name: 'TimeSeriesSplit'}) SET c6 += {category: 'time_series', definition: 'Strategie de validation croisee par fenetre glissante respectant la chronologie.', token_estimate: 26}
MERGE (c7:Concept {name: 'Model Registry'}) SET c7 += {category: 'mlops', definition: 'Referentiel centralise pour stocker, versionner et gerer le cycle de vie des modeles.', token_estimate: 24}
MERGE (c8:Concept {name: 'Feature Store'}) SET c8 += {category: 'mlops', definition: 'Couche de gestion des donnees centralisant la definition et le stockage des caracteristiques ML.', token_estimate: 27}
MERGE (c9:Concept {name: 'Deploiement Canary'}) SET c9 += {category: 'mlops', definition: 'Strategie de deploiement progressif ou une fraction du trafic est routee vers le nouveau modele.', token_estimate: 29}
MERGE (c10:Concept {name: 'Deploiement Blue-Green'}) SET c10 += {category: 'mlops', definition: 'Modele s\'appuyant sur deux environnements identiques permettant de basculer le trafic instantanement.', token_estimate: 31}
MERGE (c11:Concept {name: 'Winsorisation'}) SET c11 += {category: 'data_engineering', definition: 'Transformation visant a limiter l\'effet des valeurs aberrantes en plafonnant les extremums.', token_estimate: 28}
MERGE (c12:Concept {name: 'Retrieval-Augmented Generation (RAG)'}) SET c12 += {category: 'agentic_ai', definition: 'Architecture fournissant un contexte recupere via recherche vectorielle aux LLM.', token_estimate: 32}
MERGE (c13:Concept {name: 'K-Means'}) SET c13 += {category: 'clustering', definition: 'Algorithme de partitionnement non supervise regroupant les donnees autour de centroides.', token_estimate: 24}
MERGE (c14:Concept {name: 'Score de Silhouette'}) SET c14 += {category: 'clustering', definition: 'Metrique evaluant la qualite du clustering en mesurant l\'etancheite intra-cluster.', token_estimate: 26}
MERGE (c15:Concept {name: 'DBSCAN'}) SET c15 += {category: 'clustering', definition: 'Algorithme de clustering spatial base sur la densite pour detecter des formes complexes.', token_estimate: 27}
MERGE (c16:Concept {name: 'UMAP'}) SET c16 += {category: 'clustering', definition: 'Technique de reduction de dimensionnalite preservant les topologies locales et globales.', token_estimate: 25}
MERGE (c17:Concept {name: 'Stacking'}) SET c17 += {category: 'supervised_learning', definition: 'Methode d\'apprentissage d\'ensemble entrainant un meta-modele a partir de predictions d\'autres modeles.', token_estimate: 30}
MERGE (c18:Concept {name: 'Pseudo-etiquetage'}) SET c18 += {category: 'supervised_learning', definition: 'Technique semi-supervisee utilisant les predictions souples d\'un modele initial.', token_estimate: 26}
MERGE (c19:Concept {name: 'Isolation Forest'}) SET c19 += {category: 'clustering', definition: 'Algorithme utilise pour la detection d\'anomalies en isolant les valeurs atypiques.', token_estimate: 24}
MERGE (c20:Concept {name: 'PCA'}) SET c20 += {category: 'data_engineering', definition: 'Technique de reduction dimensionnelle lineaire vers des directions de variance maximale.', token_estimate: 22}
MERGE (c21:Concept {name: 'Orchestration par graphes'}) SET c21 += {category: 'agentic_ai', definition: 'Modele controlant le flux d\'agents via un graphe oriente explicite.', token_estimate: 25}
MERGE (c22:Concept {name: 'Model Context Protocol (MCP)'}) SET c22 += {category: 'agentic_ai', definition: 'Standard de communication open-source pour l\'integration securisee de donnees.', token_estimate: 26}
MERGE (c23:Concept {name: 'Differencing'}) SET c23 += {category: 'time_series', definition: 'Methode pour rendre une serie temporelle stationnaire en soustrayant des valeurs passees.', token_estimate: 23}
MERGE (c24:Concept {name: 'Data Validation'}) SET c24 += {category: 'data_engineering', definition: 'Processus d\'application de contrats de donnees pour eviter la corruption.', token_estimate: 24}
MERGE (c25:Concept {name: 'Environment Consistency'}) SET c25 += {category: 'mlops', definition: 'Reproductibilite de l\'environnement d\'execution du developpement a la production.', token_estimate: 25}
MERGE (c26:Concept {name: 'Notebook-Driven Development (NDD)'}) SET c26 += {category: 'dev_tools', definition: 'Methodologie pronant l\'utilisation des notebooks comme composants de premiere classe.', token_estimate: 28}
MERGE (c27:Concept {name: 'End-to-End MLOps Pipeline'}) SET c27 += {category: 'mlops', definition: 'Architecture complete automatisant le cycle de vie d\'un modele ML.', token_estimate: 25}
MERGE (c28:Concept {name: 'Data Leakage'}) SET c28 += {category: 'validation', definition: 'Information du futur ou du test se retrouvant accidentellement dans le set d\'entrainement.', token_estimate: 24}
MERGE (c29:Concept {name: 'Cyclical Feature Encoding'}) SET c29 += {category: 'feature_engineering', definition: 'Transformation de caracteristiques temporelles via sinus et cosinus.', token_estimate: 22}
MERGE (c30:Concept {name: 'Marketing Mix Modeling (MMM)'}) SET c30 += {category: 'modeling', definition: 'Analyse quantifiant l\'impact des canaux marketing sur les ventes via des modeles ML.', token_estimate: 26}
MERGE (c31:Concept {name: 'Architecture Agentique à 3 Couches'}) SET c31 += {category: 'agentic_ai', definition: 'Modèle d\'architecture d\'entreprise divisant les systèmes en Couche d\'Orchestration, Cognitive et Outils.', token_estimate: 25}
MERGE (c32:Concept {name: 'Société d\'Agents'}) SET c32 += {category: 'agentic_ai', definition: 'Réseau d\'agents hautement spécialisés coordonnés par un orchestrateur.', token_estimate: 22}
MERGE (c33:Concept {name: 'Agentic TCO'}) SET c33 += {category: 'mlops', definition: 'Évaluation du Coût Total de Possession incluant l\'inférence continue et la valeur composée.', token_estimate: 24}


MERGE (t1:Tool {name: 'MLflow'}) SET t1 += {category: 'mlops', definition: 'Plateforme open-source standardisant la gestion du cycle de vie des modeles.', token_estimate: 20}
MERGE (t2:Tool {name: 'DVC'}) SET t2 += {category: 'mlops', definition: 'Systeme de controle de version pour gerer les grands ensembles de donnees et modeles ML.', token_estimate: 22}
MERGE (t3:Tool {name: 'Feast'}) SET t3 += {category: 'mlops', definition: 'Magasin de caracteristiques open source garantissant la coherence hors-ligne et en ligne.', token_estimate: 24}
MERGE (t4:Tool {name: 'Docker'}) SET t4 += {category: 'mlops', definition: 'Plateforme de conteneurisation assurant la consistance environnementale.', token_estimate: 18}
MERGE (t5:Tool {name: 'FastAPI'}) SET t5 += {category: 'mlops', definition: 'Framework Python asynchrone pour exposer les modeles ML via des API RESTful.', token_estimate: 21}
MERGE (t6:Tool {name: 'Seldon Core'}) SET t6 += {category: 'mlops', definition: 'Plateforme Kubernetes native pour le deploiement de modeles ML a grande echelle.', token_estimate: 22}
MERGE (t7:Tool {name: 'Papermill'}) SET t7 += {category: 'data_engineering', definition: 'Outil pour executer et parametrer des notebooks Jupyter comme des jobs automatises.', token_estimate: 23}
MERGE (t8:Tool {name: 'Jupytext'}) SET t8 += {category: 'data_engineering', definition: 'Outil synchronisant les notebooks avec des scripts de texte pur pour le versionnement.', token_estimate: 24}
MERGE (t9:Tool {name: 'Marimo'}) SET t9 += {category: 'data_engineering', definition: 'Environnement de notebook Python reactif et reproductible sans etat cache.', token_estimate: 25}
MERGE (t10:Tool {name: 'Quarto'}) SET t10 += {category: 'data_engineering', definition: 'Systeme de publication scientifique multi-langages base sur Pandoc.', token_estimate: 21}
MERGE (t11:Tool {name: 'Apache Airflow'}) SET t11 += {category: 'data_engineering', definition: 'Plateforme pour definir, planifier et monitorer des workflows et pipelines.', token_estimate: 23}
MERGE (t12:Tool {name: 'dbt'}) SET t12 += {category: 'data_engineering', definition: 'Framework de transformation de donnees appliquant des principes d\'ingenierie logicielle au SQL.', token_estimate: 25}
MERGE (t13:Tool {name: 'Polars'}) SET t13 += {category: 'data_engineering', definition: 'Bibliotheque DataFrame optimisee pour un traitement ultra-rapide et multi-thread.', token_estimate: 24}
MERGE (t14:Tool {name: 'Pandera'}) SET t14 += {category: 'data_engineering', definition: 'Bibliotheque de validation de donnees orientee schemas pour DataFrames.', token_estimate: 22}
MERGE (t15:Tool {name: 'Great Expectations'}) SET t15 += {category: 'data_engineering', definition: 'Framework declaratif pour valider, tester et documenter la qualite des donnees.', token_estimate: 24}
MERGE (t16:Tool {name: 'pointblank'}) SET t16 += {category: 'data_engineering', definition: 'Package pour comprendre et valider la qualite des donnees tabulaires.', token_estimate: 21}
MERGE (t17:Tool {name: 'XGBoost'}) SET t17 += {category: 'supervised_learning', definition: 'Implementation d\'arbres de decision a gradient booste hautement optimisee.', token_estimate: 22}
MERGE (t18:Tool {name: 'Optuna'}) SET t18 += {category: 'supervised_learning', definition: 'Framework d\'optimisation automatique des hyperparametres avec elagage dynamique.', token_estimate: 23}
MERGE (t19:Tool {name: 'LangGraph'}) SET t19 += {category: 'agentic_ai', definition: 'Framework orchestrant des workflows agentiques complexes et controlables via DAG.', token_estimate: 26}
MERGE (t20:Tool {name: 'CrewAI'}) SET t20 += {category: 'agentic_ai', definition: 'Framework facilitant la creation de systemes multi-agents attribuant des roles specifiques.', token_estimate: 24}
MERGE (t21:Tool {name: 'AutoGen'}) SET t21 += {category: 'agentic_ai', definition: 'Framework base sur un modele de conversation multi-agents pilote par les evenements.', token_estimate: 23}
MERGE (t22:Tool {name: 'Semantic Kernel'}) SET t22 += {category: 'agentic_ai', definition: 'SDK d\'orchestration enterprise integrant les capacites des LLMs aux applications existantes.', token_estimate: 25}
MERGE (t23:Tool {name: 'Haystack'}) SET t23 += {category: 'agentic_ai', definition: 'Framework oriente pipeline specialise dans le RAG natif et le traitement NLP.', token_estimate: 24}
MERGE (t24:Tool {name: 'Smolagents'}) SET t24 += {category: 'agentic_ai', definition: 'Framework minimaliste utilisant des LLMs pour generer et executer dynamiquement du code.', token_estimate: 26}
MERGE (t25:Tool {name: 'Mastra'}) SET t25 += {category: 'agentic_ai', definition: 'Framework TypeScript-first integrant des workflows en graphe et un routage multi-agents.', token_estimate: 24}

// === SECTION 4 : RELATIONS CAUSALES ===
MATCH (a:Concept {name: 'Differencing'}), (b:Concept {name: 'Stationnarite'}) MERGE (a)-[:ENABLES {strength: 0.95, evidence: 'Most real-world series lack stationarity and need differencing'}]->(b);
MATCH (a:Tool {name: 'MLflow'}), (b:Concept {name: 'Model Registry'}) MERGE (a)-[:IMPLEMENTS {strength: 0.90, evidence: 'MLflow standardise le registre de modeles centralise'}]->(b);
MATCH (a:Tool {name: 'Docker'}), (b:Concept {name: 'Environment Consistency'}) MERGE (a)-[:ENABLES {strength: 0.95, evidence: 'Docker ensures the same environment avoiding works on my machine'}]->(b);
MATCH (a:Tool {name: 'Feast'}), (b:Concept {name: 'Concept Drift'}) MERGE (a)-[:PREVENTS {strength: 0.85, evidence: 'Feast prevent training-serving skew'}]->(b);
MATCH (a:Tool {name: 'Great Expectations'}), (b:Concept {name: 'Data Validation'}) MERGE (a)-[:ENABLES {strength: 0.90, evidence: 'Great Expectations is an open-source tool for data quality testing'}]->(b);
MATCH (a:Tool {name: 'CrewAI'}), (b:Tool {name: 'AutoGen'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.85, evidence: 'CrewAI assigns fixed roles, AutoGen let agents communicate conversationally'}]->(b);
MATCH (a:Tool {name: 'LangGraph'}), (b:Concept {name: 'Orchestration par graphes'}) MERGE (a)-[:IMPLEMENTS {strength: 0.95, evidence: 'LangGraph provides fine-grained control via DAGs'}]->(b);
MATCH (a:Tool {name: 'Semantic Kernel'}), (b:Tool {name: 'AutoGen'}) MERGE (a)-[:PART_OF {strength: 1.0, evidence: 'Microsoft merged AutoGen with Semantic Kernel into Microsoft Agent Framework'}]->(b);
MATCH (a:Tool {name: 'Haystack'}), (b:Concept {name: 'Retrieval-Augmented Generation (RAG)'}) MERGE (a)-[:ENABLES {strength: 0.95, evidence: 'Haystack builds everything around RAG'}]->(b);
MATCH (a:Tool {name: 'Smolagents'}), (b:Tool {name: 'LangGraph'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.85, evidence: 'Smolagents is for single-agent minimal setup, LangGraph for complex branching'}]->(b);
MATCH (a:Concept {name: 'SplineTransformer'}), (b:Concept {name: 'Lagged Features'}) MERGE (a)-[:COMPLEMENTS {strength: 0.80, evidence: 'Spline features can be combined with lagged features for robust TS modeling'}]->(b);
MATCH (a:Tool {name: 'Pandera'}), (b:Concept {name: 'Data Validation'}) MERGE (a)-[:ENABLES {strength: 0.95, evidence: 'Pandera is a framework for data validation on dataframe-like objects'}]->(b);
MATCH (a:Tool {name: 'Jupytext'}), (b:Concept {name: 'Environment Consistency'}) MERGE (a)-[:ENABLES {strength: 0.80, evidence: 'Jupytext convert notebooks to text formats for version control'}]->(b);
MATCH (a:Concept {name: 'PCA'}), (b:Concept {name: 'K-Means'}) MERGE (a)-[:ENABLES {strength: 0.85, evidence: 'PCA decrit les directions de variance maximale ou les centroides s\'alignent'}]->(b);
MATCH (a:Tool {name: 'XGBoost'}), (b:Concept {name: 'Stacking'}) MERGE (a)-[:PART_OF {strength: 0.90, evidence: 'XGBoost is often used as a base model in stacking architectures'}]->(b);
MATCH (a:Concept {name: 'Winsorisation'}), (b:Concept {name: 'Isolation Forest'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.85, evidence: 'Winsorization cap values, while Isolation Forest removes or isolates anomalies'}]->(b);
MATCH (a:Tool {name: 'dbt'}), (b:Concept {name: 'Data Validation'}) MERGE (a)-[:IMPLEMENTS {strength: 0.85, evidence: 'dbt brings software engineering testing to data models'}]->(b);
MATCH (a:Tool {name: 'Polars'}), (b:Concept {name: 'Lagged Features'}) MERGE (a)-[:ENABLES {strength: 0.90, evidence: 'Polars automatically caches subexpressions like shift() for fast lag features'}]->(b);
MATCH (a:Concept {name: 'Score de Silhouette'}), (b:Concept {name: 'K-Means'}) MERGE (a)-[:EVALUATES {strength: 0.95, evidence: 'Silhouette scores are used to select the optimal number of clusters in KMeans'}]->(b);
MATCH (a:Tool {name: 'FastAPI'}), (b:Concept {name: 'Model Registry'}) MERGE (a)-[:INTEGRATES_WITH {strength: 0.85, evidence: 'FastAPI serves the best model stored in the MLflow Model Registry'}]->(b);
MATCH (a:Concept {name: 'Pseudo-etiquetage'}), (b:Tool {name: 'XGBoost'}) MERGE (a)-[:USES {strength: 0.80, evidence: 'Pseudo labels act as regularization for strong gradient boosting models'}]->(b);
MATCH (a:Concept {name: 'TimeSeriesSplit'}), (b:Concept {name: 'Lagged Features'}) MERGE (a)-[:EVALUATES {strength: 0.95, evidence: 'Walk-forward validation evaluates models using lagged features without leakage'}]->(b);
MATCH (a:Tool {name: 'Mastra'}), (b:Concept {name: 'Orchestration par graphes'}) MERGE (a)-[:IMPLEMENTS {strength: 0.90, evidence: 'Mastra provides .then() and .branch() primitives for graph execution'}]->(b);
MATCH (a:Concept {name: 'Model Context Protocol (MCP)'}), (b:Concept {name: 'Retrieval-Augmented Generation (RAG)'}) MERGE (a)-[:ENABLES {strength: 0.85, evidence: 'MCP connects AI models to secure data sources natively'}]->(b);

MATCH (a:Concept {name: 'Deploiement Canary'}), (b:Tool {name: 'Seldon Core'}) MERGE (a)-[:IMPLEMENTED_BY {strength: 0.90, evidence: 'Seldon Core provides native Kubernetes routing for Canary deployments'}]->(b);
MATCH (a:Concept {name: 'Deploiement Blue-Green'}), (b:Tool {name: 'Seldon Core'}) MERGE (a)-[:IMPLEMENTED_BY {strength: 0.90, evidence: 'Seldon Core supports Blue-Green shadow deployments'}]->(b);
MATCH (a:Tool {name: 'Docker'}), (b:Tool {name: 'FastAPI'}) MERGE (a)-[:PACKAGES {strength: 0.95, evidence: 'Docker containerizes the FastAPI serving code and environment'}]->(b);
MATCH (a:Tool {name: 'Papermill'}), (b:Tool {name: 'Apache Airflow'}) MERGE (a)-[:ORCHESTRATED_BY {strength: 0.85, evidence: 'Papermill notebooks can be scheduled as DAGs in Airflow'}]->(b);
MATCH (a:Tool {name: 'Marimo'}), (b:Tool {name: 'Jupytext'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.95, evidence: 'Marimo solves the versioning issue natively without Jupytext syncing'}]->(b);
MATCH (a:Concept {name: 'DBSCAN'}), (b:Concept {name: 'K-Means'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.90, evidence: 'DBSCAN handles arbitrary shapes, K-Means assumes spherical clusters'}]->(b);
MATCH (a:Concept {name: 'UMAP'}), (b:Concept {name: 'PCA'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.85, evidence: 'UMAP preserves non-linear local topology unlike linear PCA'}]->(b);
MATCH (a:Tool {name: 'Optuna'}), (b:Tool {name: 'XGBoost'}) MERGE (a)-[:OPTIMIZES {strength: 0.95, evidence: 'Optuna performs hyperparameter search for XGBoost parameters'}]->(b);
MATCH (a:Tool {name: 'DVC'}), (b:Tool {name: 'MLflow'}) MERGE (a)-[:COMPLEMENTS {strength: 0.90, evidence: 'DVC versions data, MLflow versions model artifacts and metrics'}]->(b);
MATCH (a:Concept {name: 'Inertie'}), (b:Concept {name: 'K-Means'}) MERGE (a)-[:EVALUATES {strength: 0.90, evidence: 'Inertia (WCSS) creates the elbow method plot for K-Means'}]->(b);
MATCH (a:Tool {name: 'Quarto'}), (b:Tool {name: 'Jupytext'}) MERGE (a)-[:COMPLEMENTS {strength: 0.80, evidence: 'Quarto publishes documents rendered from scripts or notebooks'}]->(b);
MATCH (a:Concept {name: 'Stacking'}), (b:Tool {name: 'XGBoost'}) MERGE (a)-[:USES {strength: 0.90, evidence: 'XGBoost is used as a highly optimized base or meta model in stacking'}]->(b);
MATCH (a:Concept {name: 'Concept Drift'}), (b:Concept {name: 'Data Validation'}) MERGE (a)-[:DETECTED_BY {strength: 0.85, evidence: 'Continuous data validation catches drift distributions'}]->(b);
MATCH (a:Tool {name: 'LangGraph'}), (b:Tool {name: 'CrewAI'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.90, evidence: 'LangGraph gives explicit graph control, CrewAI offers fast role-based setup'}]->(b);
MATCH (a:Tool {name: 'pointblank'}), (b:Tool {name: 'Pandera'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.80, evidence: 'Both perform dataframe testing but in different ecosystems'}]->(b);
MATCH (a:Tool {name: 'dbt'}), (b:Tool {name: 'Polars'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.70, evidence: 'dbt transforms in warehouse, Polars transforms in-memory'}]->(b);
MATCH (a:Concept {name: 'Pseudo-etiquetage'}), (b:Concept {name: 'Stacking'}) MERGE (a)-[:COMPLEMENTS {strength: 0.85, evidence: 'Both techniques improve model robustness in Kaggle pipelines'}]->(b);
MATCH (a:Concept {name: 'Stationnarite'}), (b:Concept {name: 'Lagged Features'}) MERGE (a)-[:COMPLEMENTS {strength: 0.80, evidence: 'Stationarity improves the stability of lagged feature correlations'}]->(b);
MATCH (a:Tool {name: 'Smolagents'}), (b:Tool {name: 'CrewAI'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.85, evidence: 'Smolagents is code-first single agent, CrewAI is multi-agent role-based'}]->(b);
MATCH (a:Concept {name: 'Isolation Forest'}), (b:Concept {name: 'DBSCAN'}) MERGE (a)-[:COMPLEMENTS {strength: 0.80, evidence: 'Both isolate noise, but DBSCAN is spatial and Isolation Forest uses trees'}]->(b);
MATCH (a:Tool {name: 'Haystack'}), (b:Tool {name: 'Semantic Kernel'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.85, evidence: 'Haystack is document-pipeline focused, Semantic Kernel is enterprise SDK focused'}]->(b);
MATCH (a:Concept {name: 'Deploiement Canary'}), (b:Concept {name: 'Deploiement Blue-Green'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.90, evidence: 'Canary ramps up traffic percentage, Blue-Green cuts over instantly'}]->(b);
MATCH (a:Concept {name: 'Feature Store'}), (b:Concept {name: 'Model Registry'}) MERGE (a)-[:COMPLEMENTS {strength: 0.95, evidence: 'Feature store serves data, Model registry serves the ML artifacts'}]->(b);
MATCH (a:Tool {name: 'Apache Airflow'}), (b:Tool {name: 'dbt'}) MERGE (a)-[:ORCHESTRATES {strength: 0.90, evidence: 'Airflow DAGs trigger dbt transformations in the data warehouse'}]->(b);
MATCH (a:Concept {name: 'Notebook-Driven Development (NDD)'}), (b:Tool {name: 'Jupytext'}) MERGE (a)-[:REQUIRES {strength: 0.95, evidence: 'Le NDD necessite Jupytext pour versionner correctement.'}]->(b);
MATCH (a:Concept {name: 'End-to-End MLOps Pipeline'}), (b:Tool {name: 'MLflow'}) MERGE (a)-[:REQUIRES {strength: 1.0, evidence: 'MLflow est au coeur des pipelines MLOps.'}]->(b);
MATCH (a:Concept {name: 'Data Leakage'}), (b:Concept {name: 'TimeSeriesSplit'}) MERGE (a)-[:PREVENTED_BY {strength: 0.90, evidence: 'Le split chronologique empeche le data leakage.'}]->(b);
MATCH (a:Concept {name: 'Cyclical Feature Encoding'}), (b:Concept {name: 'SplineTransformer'}) MERGE (a)-[:ALTERNATIVE_TO {strength: 0.85, evidence: 'Alternative mathematique simple aux splines.'}]->(b);
MATCH (a:Concept {name: 'Marketing Mix Modeling (MMM)'}), (b:Concept {name: 'Lagged Features'}) MERGE (a)-[:REQUIRES {strength: 0.95, evidence: 'Le MMM a besoin de features retardees pour capter l\'adstock.'}]->(b);
MATCH (a:Concept {name: 'Architecture Agentique à 3 Couches'}), (b:Concept {name: 'Model Context Protocol (MCP)'}) MERGE (a)-[:REQUIRES {strength: 0.95, evidence: 'Le MCP sert de protocole pour la couche Outils.'}]->(b);
MATCH (a:Concept {name: 'Société d\'Agents'}), (b:Tool {name: 'CrewAI'}) MERGE (a)-[:IMPLEMENTED_BY {strength: 0.90, evidence: 'CrewAI implémente la société d\'agents avec rôles fixes.'}]->(b);
MATCH (a:Concept {name: 'Société d\'Agents'}), (b:Tool {name: 'LangGraph'}) MERGE (a)-[:IMPLEMENTED_BY {strength: 0.90, evidence: 'LangGraph coordonne la société d\'agents via graphes d\'état.'}]->(b);
MATCH (a:Concept {name: 'Agentic TCO'}), (b:Tool {name: 'MLflow'}) MERGE (a)-[:EVALUATES {strength: 0.85, evidence: 'TCO nécessite suivi MLOps.'}]->(b);

// === SECTION 5 : PROCEDURES & STEPS ===
MERGE (p1:Procedure {title: 'Detect and Achieve Stationarity'}) SET p1 += {domain: 'time_series', objective: 'Transformer une serie non-stationnaire en stationnaire pour la modelisation'}
MERGE (s1_1:Step {order: 1, action: 'Visualiser l\'autocorrelation (ACF/PACF)', code_snippet: 'plot_acf(df[\'value\'])'})
MERGE (s1_2:Step {order: 2, action: 'Effectuer tests ADF/KPSS', code_snippet: 'adfuller(df[\'value\'])'})
MERGE (s1_3:Step {order: 3, action: 'Appliquer la differenciation', code_snippet: 'df[\'value\'].diff()'})
MATCH (p:Procedure {title: 'Detect and Achieve Stationarity'}), (s:Step {order: 1, action: 'Visualiser l\'autocorrelation (ACF/PACF)'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Detect and Achieve Stationarity'}), (s:Step {order: 2, action: 'Effectuer tests ADF/KPSS'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Detect and Achieve Stationarity'}), (s:Step {order: 3, action: 'Appliquer la differenciation'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p2:Procedure {title: 'Setup MLflow Tracking Server'}) SET p2 += {domain: 'mlops', objective: 'Configurer un serveur MLflow avec Model Registry'}
MERGE (s2_1:Step {order: 1, action: 'Demarrer serveur avec backend DB', code_snippet: 'mlflow server --backend-store-uri sqlite:///mlflow.db'})
MERGE (s2_2:Step {order: 2, action: 'Logger parametres et modele', code_snippet: 'mlflow.log_param(\'param\', 1)'})
MERGE (s2_3:Step {order: 3, action: 'Enregistrer modele avec alias', code_snippet: 'client.set_registered_model_alias(\'Model\', \'champion\', 1)'})
MATCH (p:Procedure {title: 'Setup MLflow Tracking Server'}), (s:Step {order: 1, action: 'Demarrer serveur avec backend DB'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Setup MLflow Tracking Server'}), (s:Step {order: 2, action: 'Logger parametres et modele'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Setup MLflow Tracking Server'}), (s:Step {order: 3, action: 'Enregistrer modele avec alias'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p3:Procedure {title: 'Setup Data Validation with Pandera'}) SET p3 += {domain: 'data_engineering', objective: 'Definir et appliquer des schemas sur DataFrames'}
MERGE (s3_1:Step {order: 1, action: 'Definir un schema base sur les classes', code_snippet: 'class Schema(pa.DataFrameModel): ...'})
MERGE (s3_2:Step {order: 2, action: 'Integrer dans Pytest', code_snippet: '@pa.check_types def process(): ...'})
MERGE (s3_3:Step {order: 3, action: 'Valider paresseusement en production', code_snippet: 'Schema.validate(df, lazy=True)'})
MATCH (p:Procedure {title: 'Setup Data Validation with Pandera'}), (s:Step {order: 1, action: 'Definir un schema base sur les classes'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Setup Data Validation with Pandera'}), (s:Step {order: 2, action: 'Integrer dans Pytest'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Setup Data Validation with Pandera'}), (s:Step {order: 3, action: 'Valider paresseusement en production'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p4:Procedure {title: 'Build Stateful Agent Workflow'}) SET p4 += {domain: 'agentic_ai', objective: 'Orchestrer un workflow avec LangGraph'}
MERGE (s4_1:Step {order: 1, action: 'Definir le graphe d\'etats', code_snippet: 'workflow = StateGraph(State)'})
MERGE (s4_2:Step {order: 2, action: 'Configurer routage conditionnel', code_snippet: 'workflow.add_conditional_edges(...)'})
MERGE (s4_3:Step {order: 3, action: 'Ajouter controle humain', code_snippet: 'app = workflow.compile(checkpointer=memory)'})
MATCH (p:Procedure {title: 'Build Stateful Agent Workflow'}), (s:Step {order: 1, action: 'Definir le graphe d\'etats'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Build Stateful Agent Workflow'}), (s:Step {order: 2, action: 'Configurer routage conditionnel'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Build Stateful Agent Workflow'}), (s:Step {order: 3, action: 'Ajouter controle humain'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p5:Procedure {title: 'Optimal K-Means Clustering'}) SET p5 += {domain: 'clustering', objective: 'Determiner le nombre optimal de clusters'}
MERGE (s5_1:Step {order: 1, action: 'Normaliser les donnees', code_snippet: 'scaler.fit_transform(X)'})
MERGE (s5_2:Step {order: 2, action: 'Tester differents k', code_snippet: 'KMeans(n_clusters=k).fit(X)'})
MERGE (s5_3:Step {order: 3, action: 'Calculer Silhouette Score', code_snippet: 'silhouette_score(X, labels)'})
MATCH (p:Procedure {title: 'Optimal K-Means Clustering'}), (s:Step {order: 1, action: 'Normaliser les donnees'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Optimal K-Means Clustering'}), (s:Step {order: 2, action: 'Tester differents k'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Optimal K-Means Clustering'}), (s:Step {order: 3, action: 'Calculer Silhouette Score'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p6:Procedure {title: 'Implement Stacking Ensemble'}) SET p6 += {domain: 'supervised_learning', objective: 'Combiner plusieurs modeles via un meta-modele'}
MERGE (s6_1:Step {order: 1, action: 'Entrainer modeles de base', code_snippet: 'cross_val_predict(model, X, y)'})
MERGE (s6_2:Step {order: 2, action: 'Generer OOF features', code_snippet: 'np.column_stack(preds)'})
MERGE (s6_3:Step {order: 3, action: 'Entrainer meta-modele', code_snippet: 'meta_model.fit(meta_features, y)'})
MATCH (p:Procedure {title: 'Implement Stacking Ensemble'}), (s:Step {order: 1, action: 'Entrainer modeles de base'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Implement Stacking Ensemble'}), (s:Step {order: 2, action: 'Generer OOF features'}) MERGE (p)-[:HAS_STEP]->(s);
MATCH (p:Procedure {title: 'Implement Stacking Ensemble'}), (s:Step {order: 3, action: 'Entrainer meta-modele'}) MERGE (p)-[:HAS_STEP]->(s);

// === SECTION 6 : DECISION TREES & BRANCHES ===
MERGE (dt1:DecisionTree {id: 'ts-model-selection'}) SET dt1 += {question: 'Quel modele pour une serie temporelle ?', context: 'time_series'}
MERGE (b1_1:DecisionBranch {order: 1, condition: 'Serie propre sans complexite'}) SET b1_1 += {action: 'Utiliser modeles classiques (ARIMA)', confidence: 0.90}
MERGE (b1_2:DecisionBranch {order: 2, condition: 'Non-linearites et caracteristiques riches'}) SET b1_2 += {action: 'Utiliser ML base sur les arbres (XGBoost)', confidence: 0.85}
MATCH (dt:DecisionTree {id: 'ts-model-selection'}), (b:DecisionBranch {order: 1, condition: 'Serie propre sans complexite'}) MERGE (dt)-[:HAS_BRANCH]->(b);
MATCH (dt:DecisionTree {id: 'ts-model-selection'}), (b:DecisionBranch {order: 2, condition: 'Non-linearites et caracteristiques riches'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt2:DecisionTree {id: 'agentic-framework-selection'}) SET dt2 += {question: 'Quel framework d\'agents IA choisir ?', context: 'agentic_ai'}
MERGE (b2_1:DecisionBranch {order: 1, condition: 'Controle d\'etat et validation humaine'}) SET b2_1 += {action: 'Utiliser LangGraph', confidence: 0.95}
MERGE (b2_2:DecisionBranch {order: 2, condition: 'Workflows business et roles'}) SET b2_2 += {action: 'Utiliser CrewAI', confidence: 0.85}
MERGE (b2_3:DecisionBranch {order: 3, condition: 'Extraction de documents et RAG'}) SET b2_3 += {action: 'Utiliser Haystack', confidence: 0.90}
MATCH (dt:DecisionTree {id: 'agentic-framework-selection'}), (b:DecisionBranch {order: 1, condition: 'Controle d\'etat et validation humaine'}) MERGE (dt)-[:HAS_BRANCH]->(b);
MATCH (dt:DecisionTree {id: 'agentic-framework-selection'}), (b:DecisionBranch {order: 2, condition: 'Workflows business et roles'}) MERGE (dt)-[:HAS_BRANCH]->(b);
MATCH (dt:DecisionTree {id: 'agentic-framework-selection'}), (b:DecisionBranch {order: 3, condition: 'Extraction de documents et RAG'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt3:DecisionTree {id: 'mlops-infrastructure'}) SET dt3 += {question: 'Services Cloud Manages ou Open-Source heberge ?', context: 'mlops'}
MERGE (b3_1:DecisionBranch {order: 1, condition: 'Equipe novice et besoin de rapidite'}) SET b3_1 += {action: 'AWS SageMaker, Azure ML', confidence: 0.90}
MERGE (b3_2:DecisionBranch {order: 2, condition: 'Refus du vendor lock-in et maturite'}) SET b3_2 += {action: 'Kubeflow, MLflow local', confidence: 0.95}
MATCH (dt:DecisionTree {id: 'mlops-infrastructure'}), (b:DecisionBranch {order: 1, condition: 'Equipe novice et besoin de rapidite'}) MERGE (dt)-[:HAS_BRANCH]->(b);
MATCH (dt:DecisionTree {id: 'mlops-infrastructure'}), (b:DecisionBranch {order: 2, condition: 'Refus du vendor lock-in et maturite'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt4:DecisionTree {id: 'clustering-selection'}) SET dt4 += {question: 'Quel algorithme de clustering utiliser ?', context: 'clustering'}
MERGE (b4_1:DecisionBranch {order: 1, condition: 'Clusters spheriques et de tailles egales'}) SET b4_1 += {action: 'Utiliser K-Means', confidence: 0.95}
MERGE (b4_2:DecisionBranch {order: 2, condition: 'Formes arbitraires ou presence d\'outliers'}) SET b4_2 += {action: 'Utiliser DBSCAN', confidence: 0.90}
MATCH (dt:DecisionTree {id: 'clustering-selection'}), (b:DecisionBranch {order: 1, condition: 'Clusters spheriques et de tailles egales'}) MERGE (dt)-[:HAS_BRANCH]->(b);
MATCH (dt:DecisionTree {id: 'clustering-selection'}), (b:DecisionBranch {order: 2, condition: 'Formes arbitraires ou presence d\'outliers'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt5:DecisionTree {id: 'notebook-vs-script'}) SET dt5 += {question: 'Notebook Jupyter ou Script Python ?', context: 'data_engineering'}
MERGE (b5_1:DecisionBranch {order: 1, condition: 'Exploration, EDA et prototypage'}) SET b5_1 += {action: 'Utiliser Jupyter Notebooks', confidence: 0.90}
MERGE (b5_2:DecisionBranch {order: 2, condition: 'Environnement de production'}) SET b5_2 += {action: 'Utiliser scripts .py', confidence: 0.95}
MATCH (dt:DecisionTree {id: 'notebook-vs-script'}), (b:DecisionBranch {order: 1, condition: 'Exploration, EDA et prototypage'}) MERGE (dt)-[:HAS_BRANCH]->(b);
MATCH (dt:DecisionTree {id: 'notebook-vs-script'}), (b:DecisionBranch {order: 2, condition: 'Environnement de production'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt6:DecisionTree {id: 'agentic-human-supervision'}) SET dt6 += {question: 'Quel niveau d\'intervention humaine est requis pour cette action de l\'agent ?', context: 'agentic_ai'}
MERGE (b6_1:DecisionBranch {order: 1, condition: 'Action automatisée à faible risque et réversible'}) SET b6_1 += {action: 'Niveau 1 : Exécution automatisée', confidence: 0.95}
MERGE (b6_2:DecisionBranch {order: 2, condition: 'Action modérée nécessitant un contrôle qualité'}) SET b6_2 += {action: 'Niveau 2 : Supervision avec fenêtre de révision', confidence: 0.90}
MERGE (b6_3:DecisionBranch {order: 3, condition: 'Action irréversible ou à forts enjeux'}) SET b6_3 += {action: 'Niveau 3 : Approbation stricte obligatoire', confidence: 0.99}
MATCH (dt:DecisionTree {id: 'agentic-human-supervision'}), (b:DecisionBranch {order: 1, condition: 'Action automatisée à faible risque et réversible'}) MERGE (dt)-[:HAS_BRANCH]->(b);
MATCH (dt:DecisionTree {id: 'agentic-human-supervision'}), (b:DecisionBranch {order: 2, condition: 'Action modérée nécessitant un contrôle qualité'}) MERGE (dt)-[:HAS_BRANCH]->(b);
MATCH (dt:DecisionTree {id: 'agentic-human-supervision'}), (b:DecisionBranch {order: 3, condition: 'Action irréversible ou à forts enjeux'}) MERGE (dt)-[:HAS_BRANCH]->(b);

// === SECTION 7 : LIENS DOMAINES <-> CONCEPTS ===
MATCH (d:Domain {name: 'time_series'}), (c:Concept {category: 'time_series'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'time_series'}), (t:Tool {category: 'time_series'}) MERGE (t)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'time_series'}), (p:Procedure {domain: 'time_series'}) MERGE (p)-[:BELONGS_TO]->(d);

MATCH (d:Domain {name: 'mlops'}), (c:Concept {category: 'mlops'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'mlops'}), (t:Tool {category: 'mlops'}) MERGE (t)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'mlops'}), (p:Procedure {domain: 'mlops'}) MERGE (p)-[:BELONGS_TO]->(d);

MATCH (d:Domain {name: 'data_engineering'}), (c:Concept {category: 'data_engineering'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'data_engineering'}), (t:Tool {category: 'data_engineering'}) MERGE (t)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'data_engineering'}), (p:Procedure {domain: 'data_engineering'}) MERGE (p)-[:BELONGS_TO]->(d);

MATCH (d:Domain {name: 'supervised_learning'}), (c:Concept {category: 'supervised_learning'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'supervised_learning'}), (t:Tool {category: 'supervised_learning'}) MERGE (t)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'supervised_learning'}), (p:Procedure {domain: 'supervised_learning'}) MERGE (p)-[:BELONGS_TO]->(d);

MATCH (d:Domain {name: 'clustering'}), (c:Concept {category: 'clustering'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'clustering'}), (t:Tool {category: 'clustering'}) MERGE (t)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'clustering'}), (p:Procedure {domain: 'clustering'}) MERGE (p)-[:BELONGS_TO]->(d);

MATCH (d:Domain {name: 'agentic_ai'}), (c:Concept {category: 'agentic_ai'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'agentic_ai'}), (t:Tool {category: 'agentic_ai'}) MERGE (t)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'agentic_ai'}), (p:Procedure {domain: 'agentic_ai'}) MERGE (p)-[:BELONGS_TO]->(d);

MATCH (d:Domain {name: 'dev_tools'}), (c:Concept {category: 'dev_tools'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'validation'}), (c:Concept {category: 'validation'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'feature_engineering'}), (c:Concept {category: 'feature_engineering'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'modeling'}), (c:Concept {category: 'modeling'}) MERGE (c)-[:BELONGS_TO]->(d);


// === SECTION 8 : ENRICHISSEMENT DES DOMAINES EXPERTS ===

// --- FINANCE ---
MERGE (cfin1:Concept {name: "Credit Scoring"}) SET cfin1 += {category: "finance", definition: "Évaluation du risque de défaut d'un emprunteur", token_estimate: 24}
MERGE (cfin2:Concept {name: "Look-Ahead Bias"}) SET cfin2 += {category: "finance", definition: "Biais d'utilisation d'informations futures non disponibles au moment de la prédiction", token_estimate: 28}
MERGE (cfin3:Concept {name: "Sharpe Ratio"}) SET cfin3 += {category: "finance", definition: "Mesure de la rentabilité d'un actif par rapport à sa volatilité", token_estimate: 22}
MERGE (tfin1:Tool {name: "SHAP"}) SET tfin1 += {category: "supervised_learning", definition: "Outil d'explicabilité basé sur la théorie des jeux pour attribuer des importances aux features.", token_estimate: 25}

MERGE (pfin1:Procedure {title: "Train Interpretable Credit Scorecard"}) SET pfin1 += {domain: "finance", objective: "Créer une grille de scoring interprétable pour l'octroi de crédit"}
MERGE (sfin1_1:Step {order: 1, action: "Nettoyer les variables financières", code_snippet: "df_clean = df.dropna()"})
MERGE (sfin1_2:Step {order: 2, action: "Appliquer une Régression Logistique", code_snippet: "model = LogisticRegression().fit(X, y)"})
MERGE (sfin1_3:Step {order: 3, action: "Extraire les coefficients et les traduire en grille de points score", code_snippet: "coefficients = model.coef_"})
MERGE (pfin1)-[:HAS_STEP]->(sfin1_1)
MERGE (pfin1)-[:HAS_STEP]->(sfin1_2)
MERGE (pfin1)-[:HAS_STEP]->(sfin1_3)

MERGE (pfin2:Procedure {title: "Stationnariser serie financiere"}) SET pfin2 += {domain: "finance", objective: "Retirer la non-stationnarité d'une série temporelle financière"}
MERGE (sfin2_1:Step {order: 1, action: "Appliquer le test ADF", code_snippet: "adfuller(df['price'])"})
MERGE (sfin2_2:Step {order: 2, action: "Si non stationnaire, calculer les rendements log", code_snippet: "df['returns'] = np.log(df['price']).diff()"})
MERGE (pfin2)-[:HAS_STEP]->(sfin2_1)
MERGE (pfin2)-[:HAS_STEP]->(sfin2_2)

MERGE (dtfin:DecisionTree {id: "finance-model-selection"}) SET dtfin += {question: "Comment modéliser le risque financier ?", context: "finance"}
MERGE (bfin_1:DecisionBranch {order: 1, condition: "Réglementation stricte demandant explications simples"}) SET bfin_1 += {action: "Utiliser Régression Logistique avec Scorecard", confidence: 0.95}
MERGE (bfin_2:DecisionBranch {order: 2, condition: "Performance maximale avec explication locale via attribution"}) SET bfin_2 += {action: "Utiliser XGBoost + SHAP", confidence: 0.90}
MERGE (dtfin)-[:HAS_BRANCH]->(bfin_1)
MERGE (dtfin)-[:HAS_BRANCH]->(bfin_2)

// Relations Finance
MERGE (p1:Procedure {title: "Train Interpretable Credit Scorecard"}) MERGE (c1:Concept {name: "Credit Scoring"}) MERGE (t1:Tool {name: "SHAP"})
MERGE (p1)-[:REQUIRES]->(c1)
MERGE (p1)-[:USES_TOOL]->(t1)
MERGE (p2:Procedure {title: "Stationnariser serie financiere"}) MERGE (c2:Concept {name: "Look-Ahead Bias"}) MERGE (t2:Tool {name: "statsmodels"}) SET t2.category = "time_series"
MERGE (p2)-[:AVOIDS]->(c2)
MERGE (p2)-[:USES_TOOL]->(t2)

// --- E-COMMERCE ---
MERGE (ceco1:Concept {name: "Modèle RFM"}) SET ceco1 += {category: "ecommerce", definition: "Segmentation basée sur la Récence, Fréquence et Montant d'achat", token_estimate: 25}
MERGE (ceco2:Concept {name: "Churn Client"}) SET ceco2 += {category: "ecommerce", definition: "Prédiction du taux d'attrition des utilisateurs", token_estimate: 24}

MERGE (peco1:Procedure {title: "Segmenter avec le modele RFM"}) SET peco1 += {domain: "ecommerce", objective: "Segmenter les clients d'une boutique en ligne"}
MERGE (seco1_1:Step {order: 1, action: "Calculer Recency, Frequency et Monetary par client", code_snippet: "rfm = df.groupby('CustomerID').agg(...)"})
MERGE (seco1_2:Step {order: 2, action: "Normaliser les colonnes", code_snippet: "StandardScaler().fit_transform(rfm)"})
MERGE (seco1_3:Step {order: 3, action: "Appliquer KMeans pour segmenter", code_snippet: "KMeans(n_clusters=4).fit(rfm_scaled)"})
MERGE (peco1)-[:HAS_STEP]->(seco1_1)
MERGE (peco1)-[:HAS_STEP]->(seco1_2)
MERGE (peco1)-[:HAS_STEP]->(seco1_3)

MERGE (peco2:Procedure {title: "Entrainer un modele de Churn"}) SET peco2 += {domain: "ecommerce", objective: "Prédire le départ des utilisateurs"}
MERGE (seco2_1:Step {order: 1, action: "Définir la période d'inactivité", code_snippet: "df['churn'] = (df['days_inactive'] > 90).astype(int)"})
MERGE (seco2_2:Step {order: 2, action: "Gérer le déséquilibre des classes", code_snippet: "scale_pos_weight = count_neg / count_pos"})
MERGE (seco2_3:Step {order: 3, action: "Entraîner un classifieur de type Gradient Boosting", code_snippet: "XGBClassifier().fit(X, y)"})
MERGE (peco2)-[:HAS_STEP]->(seco2_1)
MERGE (peco2)-[:HAS_STEP]->(seco2_2)
MERGE (peco2)-[:HAS_STEP]->(seco2_3)

MERGE (dteco:DecisionTree {id: "ecommerce-pricing-strategy"}) SET dteco += {question: "Comment optimiser les prix en E-commerce ?", context: "ecommerce"}
MERGE (beco_1:DecisionBranch {order: 1, condition: "Faible historique ou nouveautés"}) SET beco_1 += {action: "Règles expertes métier basées sur les coûts", confidence: 0.80}
MERGE (beco_2:DecisionBranch {order: 2, condition: "Historique transactionnel complet"}) SET beco_2 += {action: "Estimer l'élasticité-prix de la demande par régression log-log", confidence: 0.90}
MERGE (dteco)-[:HAS_BRANCH]->(beco_1)
MERGE (dteco)-[:HAS_BRANCH]->(beco_2)

// Relations E-commerce
MERGE (p3:Procedure {title: "Segmenter avec le modele RFM"}) MERGE (c3:Concept {name: "Modèle RFM"}) MERGE (t3:Tool {name: "scikit-learn"}) SET t3.category = "supervised_learning"
MERGE (p3)-[:REQUIRES]->(c3)
MERGE (p3)-[:USES_TOOL]->(t3)
MERGE (p4:Procedure {title: "Entrainer un modele de Churn"}) MERGE (c4:Concept {name: "Churn Client"}) MERGE (t4:Tool {name: "XGBoost"})
MERGE (p4)-[:REQUIRES]->(c4)
MERGE (p4)-[:USES_TOOL]->(t4)

// --- MEDICAL ---
MERGE (cmed1:Concept {name: "Données censurées"}) SET cmed1 += {category: "medical", definition: "Données où l'événement d'intérêt (ex: décès, récidive) n'a pas été observé pendant l'étude", token_estimate: 27}
MERGE (cmed2:Concept {name: "Recall Médical"}) SET cmed2 += {category: "medical", definition: "Priorité clinique donnée au fait de ne rater aucun malade (minimiser les faux négatifs)", token_estimate: 25}

MERGE (tmed1:Tool {name: "lifelines"}) SET tmed1 += {category: "survival", definition: "Bibliothèque Python pour l'analyse de survie et les modèles de risques proportionnels de Cox.", token_estimate: 24}

MERGE (pmed1:Procedure {title: "Kaplan-Meier Survival Estimation"}) SET pmed1 += {domain: "medical", objective: "Estimer la fonction de survie sur des données censurées"}
MERGE (smed1_1:Step {order: 1, action: "Charger données avec colonnes Temps et Événement", code_snippet: "T = df['time']; E = df['event']"})
MERGE (smed1_2:Step {order: 2, action: "Instancier KaplanMeierFitter", code_snippet: "kmf = KaplanMeierFitter()"})
MERGE (smed1_3:Step {order: 3, action: "Ajuster et tracer la courbe de survie", code_snippet: "kmf.fit(T, E).plot_survival_function()"})
MERGE (pmed1)-[:HAS_STEP]->(smed1_1)
MERGE (pmed1)-[:HAS_STEP]->(smed1_2)
MERGE (pmed1)-[:HAS_STEP]->(smed1_3)

MERGE (pmed2:Procedure {title: "Ajuster un modele de Cox"}) SET pmed2 += {domain: "medical", objective: "Ajuster un modèle de régression de Cox pour l'analyse de survie"}
MERGE (smed2_1:Step {order: 1, action: "Encoder les variables catégorielles", code_snippet: "pd.get_dummies(df)"})
MERGE (smed2_2:Step {order: 2, action: "Instancier CoxPHFitter", code_snippet: "cph = CoxPHFitter()"})
MERGE (smed2_3:Step {order: 3, action: "Ajuster et analyser les hazard ratios", code_snippet: "cph.fit(df, duration_col='T', event_col='E')"})
MERGE (pmed2)-[:HAS_STEP]->(smed2_1)
MERGE (pmed2)-[:HAS_STEP]->(smed2_2)
MERGE (pmed2)-[:HAS_STEP]->(smed2_3)

MERGE (dtmed:DecisionTree {id: "medical-metric-selection"}) SET dtmed += {question: "Quelle métrique de performance pour le diagnostic médical ?", context: "medical"}
MERGE (bmed_1:DecisionBranch {order: 1, condition: "Maladie grave (taux de survie lié à la détection)"}) SET bmed_1 += {action: "Maximiser le Recall / Sensibilité", confidence: 0.95}
MERGE (bmed_2:DecisionBranch {order: 2, condition: "Diagnostic screening global"}) SET bmed_2 += {action: "Optimiser ROC-AUC ou F1-weighted", confidence: 0.90}
MERGE (dtmed)-[:HAS_BRANCH]->(bmed_1)
MERGE (dtmed)-[:HAS_BRANCH]->(bmed_2)

// Relations Medical
MERGE (p5:Procedure {title: "Kaplan-Meier Survival Estimation"}) MERGE (c5:Concept {name: "Données censurées"}) MERGE (t5:Tool {name: "lifelines"})
MERGE (p5)-[:REQUIRES]->(c5)
MERGE (p5)-[:USES_TOOL]->(t5)
MERGE (p6:Procedure {title: "Ajuster un modele de Cox"}) MERGE (c6:Concept {name: "Données censurées"}) MERGE (t6:Tool {name: "lifelines"})
MERGE (p6)-[:REQUIRES]->(c6)
MERGE (p6)-[:USES_TOOL]->(t6)


// === SECTION 9 : LIENS DOMAINES <-> ENRICHISSEMENT ===
MATCH (d:Domain {name: 'finance'}), (c:Concept {category: 'finance'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'finance'}), (p:Procedure {domain: 'finance'}) MERGE (p)-[:BELONGS_TO]->(d);

MATCH (d:Domain {name: 'ecommerce'}), (c:Concept {category: 'ecommerce'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'ecommerce'}), (p:Procedure {domain: 'ecommerce'}) MERGE (p)-[:BELONGS_TO]->(d);

MATCH (d:Domain {name: 'medical'}), (c:Concept {category: 'medical'}) MERGE (c)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'medical'}), (p:Procedure {domain: 'medical'}) MERGE (p)-[:BELONGS_TO]->(d);
MATCH (d:Domain {name: 'medical'}), (t:Tool {category: 'survival'}) MERGE (t)-[:BELONGS_TO]->(d);


// === SECTION 10 : NOUVELLES CONTRAINTES DE L'EXPANSION ===
CREATE CONSTRAINT run_id_uniq IF NOT EXISTS FOR (r:Run) REQUIRE r.id IS UNIQUE;
CREATE CONSTRAINT model_name_uniq IF NOT EXISTS FOR (m:Model) REQUIRE m.name IS UNIQUE;
CREATE CONSTRAINT sc_name_uniq IF NOT EXISTS FOR (s:SemanticConcept) REQUIRE s.name IS UNIQUE;
CREATE CONSTRAINT remedy_name_uniq IF NOT EXISTS FOR (rem:Remedy) REQUIRE rem.name IS UNIQUE;

// === SECTION 11 : FEATURE STORE SÉMANTIQUE ===
MERGE (sc1:SemanticConcept {name: 'Identifier'}) SET sc1 += {definition: 'Colonne d\'identification unique à haute cardinalité (ex: ID client, ID commande)'}
MERGE (sc2:SemanticConcept {name: 'MonetaryValue'}) SET sc2 += {definition: 'Donnée numérique représentant des transactions financières, des prix ou des coûts'}
MERGE (sc3:SemanticConcept {name: 'TemporalCycle'}) SET sc3 += {definition: 'Donnée temporelle ou cyclique (ex: mois de l\'année, jour de la semaine)'}
MERGE (sc4:SemanticConcept {name: 'HighCardinalityCategorical'}) SET sc4 += {definition: 'Variable catégorielle avec un grand nombre de modalités uniques'}
MERGE (sc5:SemanticConcept {name: 'CameroonianPhoneNumber'}) SET sc5 += {definition: 'Numéro de téléphone portable camerounais commençant par +237, 237 ou 6'}
MERGE (sc6:SemanticConcept {name: 'CameroonianGeography'}) SET sc6 += {definition: 'Département, ville ou région administrative du Cameroun'}
MERGE (sc7:SemanticConcept {name: 'AfricanCurrency'}) SET sc7 += {definition: 'Montant monétaire libellé en Franc CFA (XAF/XOF)'}
MERGE (sc8:SemanticConcept {name: 'MobileMoneyTransaction'}) SET sc8 += {definition: 'Détail de transaction de paiement électronique (MTN Mobile Money ou Orange Money)'}

MERGE (act1:Action {name: 'drop'})
MERGE (act2:Action {name: 'winsorize'})
MERGE (act3:Action {name: 'scale'})
MERGE (act4:Action {name: 'encode'})
MERGE (act5:Action {name: 'sanitize_phone'})
MERGE (act6:Action {name: 'normalize_cam_geo'})
MERGE (act7:Action {name: 'clean_fcfa'})
MERGE (act8:Action {name: 'parse_momo'})

MERGE (sc1)-[:RECOMMENDS_ACTION]->(act1)
MERGE (sc2)-[:RECOMMENDS_ACTION]->(act2)
MERGE (sc3)-[:RECOMMENDS_ACTION]->(act3)
MERGE (sc4)-[:RECOMMENDS_ACTION]->(act4)
MERGE (sc5)-[:RECOMMENDS_ACTION]->(act5)
MERGE (sc6)-[:RECOMMENDS_ACTION]->(act6)
MERGE (sc7)-[:RECOMMENDS_ACTION]->(act7)
MERGE (sc8)-[:RECOMMENDS_ACTION]->(act8);

// Mappings historiques de colonnes connues
MATCH (sc1:SemanticConcept {name: 'Identifier'})
MATCH (sc2:SemanticConcept {name: 'MonetaryValue'})
MATCH (sc3:SemanticConcept {name: 'TemporalCycle'})
MERGE (col1:ColumnMapping {name: 'order_id'})-[:MAPS_TO]->(sc1)
MERGE (col2:ColumnMapping {name: 'customer_id'})-[:MAPS_TO]->(sc1)
MERGE (col3:ColumnMapping {name: 'product_id'})-[:MAPS_TO]->(sc1)
MERGE (col4:ColumnMapping {name: 'total_amount'})-[:MAPS_TO]->(sc2)
MERGE (col5:ColumnMapping {name: 'profit_margin'})-[:MAPS_TO]->(sc2)
MERGE (col6:ColumnMapping {name: 'Date'})-[:MAPS_TO]->(sc3)
MERGE (col7:ColumnMapping {name: 'days_inactive'})-[:MAPS_TO]->(sc3);

// Mappings historiques de colonnes connues (formats locaux)
MATCH (sc5:SemanticConcept {name: 'CameroonianPhoneNumber'}),
      (sc6:SemanticConcept {name: 'CameroonianGeography'}),
      (sc7:SemanticConcept {name: 'AfricanCurrency'}),
      (sc8:SemanticConcept {name: 'MobileMoneyTransaction'})
MERGE (col8:ColumnMapping {name: 'tel'})-[:MAPS_TO]->(sc5)
MERGE (col9:ColumnMapping {name: 'telephone'})-[:MAPS_TO]->(sc5)
MERGE (col10:ColumnMapping {name: 'phone_number'})-[:MAPS_TO]->(sc5)
MERGE (col11:ColumnMapping {name: 'num_tel'})-[:MAPS_TO]->(sc5)
MERGE (col12:ColumnMapping {name: 'ville'})-[:MAPS_TO]->(sc6)
MERGE (col13:ColumnMapping {name: 'region'})-[:MAPS_TO]->(sc6)
MERGE (col14:ColumnMapping {name: 'departement'})-[:MAPS_TO]->(sc6)
MERGE (col15:ColumnMapping {name: 'commune'})-[:MAPS_TO]->(sc6)
MERGE (col16:ColumnMapping {name: 'montant_fcfa'})-[:MAPS_TO]->(sc7)
MERGE (col17:ColumnMapping {name: 'prix_xaf'})-[:MAPS_TO]->(sc7)
MERGE (col18:ColumnMapping {name: 'fcfa'})-[:MAPS_TO]->(sc7)
MERGE (col19:ColumnMapping {name: 'solde'})-[:MAPS_TO]->(sc7)
MERGE (col20:ColumnMapping {name: 'transaction_momo'})-[:MAPS_TO]->(sc8)
MERGE (col21:ColumnMapping {name: 'ref_payment'})-[:MAPS_TO]->(sc8)
MERGE (col22:ColumnMapping {name: 'mode_paiement'})-[:MAPS_TO]->(sc8);

// === SECTION 12 : REMÈDES DE SELF-HEALING & GUARDRAILS ===
MERGE (rem1:Remedy {name: 'Overfitting'}) SET rem1 += {
  description: 'Le modèle est en sur-apprentissage (différence importante de performance entre train et test).',
  action: 'Augmenter l\'élagage (pruning) d\'Optuna ou ajouter de la régularisation L2 / n_estimators réduit.',
  code_snippet: 'params = {"max_depth": trial.suggest_int("max_depth", 3, 7), "learning_rate": trial.suggest_float("learning_rate", 0.01, 0.1)}'
}
MERGE (rem2:Remedy {name: 'Data Drift'}) SET rem2 += {
  description: 'Une dérive statistique temporelle a été détectée sur des variables clés.',
  action: 'Supprimer les variables fortement dérivées (comme les identifiants temporels) ou utiliser TimeSeriesSplit.',
  code_snippet: 'tscv = TimeSeriesSplit(n_splits=5)'
}
MERGE (rem3:Remedy {name: 'Class Imbalance'}) SET rem3 += {
  description: 'Le jeu de données présente un déséquilibre fort entre les classes de la cible.',
  action: 'Utiliser scale_pos_weight pour XGBoost/LightGBM ou class_weight="balanced" pour RandomForest.',
  code_snippet: 'class_weight="balanced"'
}
MERGE (rem4:Remedy {name: 'CalibrationError'}) SET rem4 += {
  description: 'Erreur de paramètre cv="prefit" sur CalibratedClassifierCV avec les versions récentes de scikit-learn (>= 1.6).',
  action: 'Utiliser FrozenEstimator pour envelopper le modèle et passer une liste de split unique cv=[(np.arange(len(X_test)), np.arange(len(X_test)))] pour figer la calibration.',
  code_snippet: 'calibrated_model = CalibratedClassifierCV(FrozenEstimator(best_model), method="isotonic", cv=[(np.arange(len(X)), np.arange(len(X)))])'
}
MERGE (rem5:Remedy {name: 'SHAPStackingClassifierError'}) SET rem5 += {
  description: 'Erreur d\'explicabilité SHAP sur les modèles StackingClassifier (non appelables).',
  action: 'Extraire un estimateur de base d\'arbre du modèle Stacking (comme RandomForest ou LightGBM) ou passer sa fonction predict_proba à l\'Explainer général.',
  code_snippet: 'model_to_explain = best_model.named_estimators_["rf"] if hasattr(best_model, "named_estimators_") else best_model.predict_proba'
};

// === SECTION 13 : HISTORIQUE ET EXPÉRIENCE DES RUNS (MÉMOIRE ÉPISODIQUE) ===

// Run 1: BTC-USD
MERGE (ds1:Dataset {name: 'BTC-USD (2014-2024)'})
MERGE (dom1:Domain {name: 'time_series'})
MERGE (ds1)-[:BELONGS_TO]->(dom1)
MERGE (m1:Model {name: 'LightGBM Regressor'})
MERGE (run1:Run {id: 'run-btc-usd-seed'}) SET run1 += {
  timestamp: 1718872000,
  taskType: 'timeseries',
  metrics: '{"r2": 0.8465, "mape": 18.47}',
  strategy: '{"target": "Volume", "steps": [{"column": "Volume", "action": "scale"}, {"column": "Date", "action": "scale"}]}'
}
MERGE (ds1)-[:HAS_RUN]->(run1)
MERGE (run1)-[:CHAMPION_MODEL]->(m1);

// Run 2: ecommerce_sales_34500
MERGE (ds2:Dataset {name: 'ecommerce_sales_34500'})
MERGE (dom2:Domain {name: 'ecommerce'})
MERGE (ds2)-[:BELONGS_TO]->(dom2)
MERGE (m2:Model {name: 'Hierarchical Clustering'})
MERGE (run2:Run {id: 'run-ecommerce-seed'}) SET run2 += {
  timestamp: 1718873000,
  taskType: 'clustering',
  metrics: '{"silhouette": 0.53}',
  strategy: '{"target": "None", "steps": [{"column": "order_id", "action": "drop"}, {"column": "customer_id", "action": "drop"}, {"column": "product_id", "action": "drop"}, {"column": "total_amount", "action": "winsorize"}, {"column": "profit_margin", "action": "scale"}]}'
}
MERGE (ds2)-[:HAS_RUN]->(run2)
MERGE (run2)-[:CHAMPION_MODEL]->(m2);

// Run 3: diabetes_data_upload
MERGE (ds3:Dataset {name: 'diabetes_data_upload'})
MERGE (dom3:Domain {name: 'medical'})
MERGE (ds3)-[:BELONGS_TO]->(dom3)
MERGE (m3:Model {name: 'RandomForest Classifier'})
MERGE (run3:Run {id: 'run-diabetes-seed'}) SET run3 += {
  timestamp: 1718874000,
  taskType: 'classification',
  metrics: '{"accuracy": 0.99, "f1_score": 0.99}',
  strategy: '{"target": "class", "steps": [{"column": "Age", "action": "scale"}, {"column": "all_categorical", "action": "encode"}]}'
}
MERGE (ds3)-[:HAS_RUN]->(run3)
MERGE (run3)-[:CHAMPION_MODEL]->(m3);

// Run 4: ObesityDataSet
MERGE (ds4:Dataset {name: 'ObesityDataSet_raw_and_data_sinthetic'})
MERGE (ds4)-[:BELONGS_TO]->(dom3)
MERGE (m4:Model {name: 'LightGBM Classifier'})
MERGE (run4:Run {id: 'run-obesity-seed'}) SET run4 += {
  timestamp: 1718875000,
  taskType: 'classification',
  metrics: '{"accuracy": 0.798, "f1_score": 0.76}',
  strategy: '{"target": "NObeyesdad", "steps": [{"column": "all_numerical", "action": "scale"}, {"column": "all_categorical", "action": "encode"}]}'
}
MERGE (ds4)-[:HAS_RUN]->(run4)
MERGE (run4)-[:CHAMPION_MODEL]->(m4);

// === SECTION 14 : TOPOLOGIE MULTI-AGENTS ===
MERGE (ag1:Agent {name: 'Orchestrator'}) SET ag1 += {role: 'Orchestre les flux du pipeline, gère l\'état global et la gouvernance.'}
MERGE (ag2:Agent {name: 'AdversarialValidator'}) SET ag2 += {role: 'Détecte les dérives statistiques temporelles (data drift).'}
MERGE (ag3:Agent {name: 'StrategyGenerator'}) SET ag3 += {role: 'Génère la stratégie de nettoyage de données optimale par Graph RAG.'}
MERGE (ag4:Agent {name: 'ChartInterpreter'}) SET ag4 += {role: 'Valide visuellement les courbes de performance (matrice de confusion, résidus).'}
MERGE (ag5:Agent {name: 'ExplainabilityAuditor'}) SET ag5 += {role: 'Calcule l\'explicabilité globale et locale du modèle (SHAP).'}

MERGE (ag1)-[:DELEGATES_TO]->(ag2)
MERGE (ag1)-[:DELEGATES_TO]->(ag3)
MERGE (ag1)-[:DELEGATES_TO]->(ag4)
MERGE (ag1)-[:DELEGATES_TO]->(ag5);


