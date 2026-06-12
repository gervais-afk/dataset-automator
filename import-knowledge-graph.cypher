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
MERGE (d10:Domain {name: 'modeling'});

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
MATCH (p:Procedure {title: 'Detect and Achieve Stationarity'}), (s:Step {order: 1, action: 'Visualiser l\'autocorrelation (ACF/PACF)'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Detect and Achieve Stationarity'}), (s:Step {order: 2, action: 'Effectuer tests ADF/KPSS'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Detect and Achieve Stationarity'}), (s:Step {order: 3, action: 'Appliquer la differenciation'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p2:Procedure {title: 'Setup MLflow Tracking Server'}) SET p2 += {domain: 'mlops', objective: 'Configurer un serveur MLflow avec Model Registry'}
MERGE (s2_1:Step {order: 1, action: 'Demarrer serveur avec backend DB', code_snippet: 'mlflow server --backend-store-uri sqlite:///mlflow.db'})
MERGE (s2_2:Step {order: 2, action: 'Logger parametres et modele', code_snippet: 'mlflow.log_param(\'param\', 1)'})
MERGE (s2_3:Step {order: 3, action: 'Enregistrer modele avec alias', code_snippet: 'client.set_registered_model_alias(\'Model\', \'champion\', 1)'})
MATCH (p:Procedure {title: 'Setup MLflow Tracking Server'}), (s:Step {order: 1, action: 'Demarrer serveur avec backend DB'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Setup MLflow Tracking Server'}), (s:Step {order: 2, action: 'Logger parametres et modele'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Setup MLflow Tracking Server'}), (s:Step {order: 3, action: 'Enregistrer modele avec alias'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p3:Procedure {title: 'Setup Data Validation with Pandera'}) SET p3 += {domain: 'data_engineering', objective: 'Definir et appliquer des schemas sur DataFrames'}
MERGE (s3_1:Step {order: 1, action: 'Definir un schema base sur les classes', code_snippet: 'class Schema(pa.DataFrameModel): ...'})
MERGE (s3_2:Step {order: 2, action: 'Integrer dans Pytest', code_snippet: '@pa.check_types def process(): ...'})
MERGE (s3_3:Step {order: 3, action: 'Valider paresseusement en production', code_snippet: 'Schema.validate(df, lazy=True)'})
MATCH (p:Procedure {title: 'Setup Data Validation with Pandera'}), (s:Step {order: 1, action: 'Definir un schema base sur les classes'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Setup Data Validation with Pandera'}), (s:Step {order: 2, action: 'Integrer dans Pytest'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Setup Data Validation with Pandera'}), (s:Step {order: 3, action: 'Valider paresseusement en production'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p4:Procedure {title: 'Build Stateful Agent Workflow'}) SET p4 += {domain: 'agentic_ai', objective: 'Orchestrer un workflow avec LangGraph'}
MERGE (s4_1:Step {order: 1, action: 'Definir le graphe d\'etats', code_snippet: 'workflow = StateGraph(State)'})
MERGE (s4_2:Step {order: 2, action: 'Configurer routage conditionnel', code_snippet: 'workflow.add_conditional_edges(...)'})
MERGE (s4_3:Step {order: 3, action: 'Ajouter controle humain', code_snippet: 'app = workflow.compile(checkpointer=memory)'})
MATCH (p:Procedure {title: 'Build Stateful Agent Workflow'}), (s:Step {order: 1, action: 'Definir le graphe d\'etats'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Build Stateful Agent Workflow'}), (s:Step {order: 2, action: 'Configurer routage conditionnel'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Build Stateful Agent Workflow'}), (s:Step {order: 3, action: 'Ajouter controle humain'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p5:Procedure {title: 'Optimal K-Means Clustering'}) SET p5 += {domain: 'clustering', objective: 'Determiner le nombre optimal de clusters'}
MERGE (s5_1:Step {order: 1, action: 'Normaliser les donnees', code_snippet: 'scaler.fit_transform(X)'})
MERGE (s5_2:Step {order: 2, action: 'Tester differents k', code_snippet: 'KMeans(n_clusters=k).fit(X)'})
MERGE (s5_3:Step {order: 3, action: 'Calculer Silhouette Score', code_snippet: 'silhouette_score(X, labels)'})
MATCH (p:Procedure {title: 'Optimal K-Means Clustering'}), (s:Step {order: 1, action: 'Normaliser les donnees'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Optimal K-Means Clustering'}), (s:Step {order: 2, action: 'Tester differents k'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Optimal K-Means Clustering'}), (s:Step {order: 3, action: 'Calculer Silhouette Score'}) MERGE (p)-[:HAS_STEP]->(s);

MERGE (p6:Procedure {title: 'Implement Stacking Ensemble'}) SET p6 += {domain: 'supervised_learning', objective: 'Combiner plusieurs modeles via un meta-modele'}
MERGE (s6_1:Step {order: 1, action: 'Entrainer modeles de base', code_snippet: 'cross_val_predict(model, X, y)'})
MERGE (s6_2:Step {order: 2, action: 'Generer OOF features', code_snippet: 'np.column_stack(preds)'})
MERGE (s6_3:Step {order: 3, action: 'Entrainer meta-modele', code_snippet: 'meta_model.fit(meta_features, y)'})
MATCH (p:Procedure {title: 'Implement Stacking Ensemble'}), (s:Step {order: 1, action: 'Entrainer modeles de base'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Implement Stacking Ensemble'}), (s:Step {order: 2, action: 'Generer OOF features'}) MERGE (p)-[:HAS_STEP]->(s)
MATCH (p:Procedure {title: 'Implement Stacking Ensemble'}), (s:Step {order: 3, action: 'Entrainer meta-modele'}) MERGE (p)-[:HAS_STEP]->(s);

// === SECTION 6 : DECISION TREES & BRANCHES ===
MERGE (dt1:DecisionTree {id: 'ts-model-selection'}) SET dt1 += {question: 'Quel modele pour une serie temporelle ?', context: 'time_series'}
MERGE (b1_1:DecisionBranch {order: 1, condition: 'Serie propre sans complexite'}) SET b1_1 += {action: 'Utiliser modeles classiques (ARIMA)', confidence: 0.90}
MERGE (b1_2:DecisionBranch {order: 2, condition: 'Non-linearites et caracteristiques riches'}) SET b1_2 += {action: 'Utiliser ML base sur les arbres (XGBoost)', confidence: 0.85}
MATCH (dt:DecisionTree {id: 'ts-model-selection'}), (b:DecisionBranch {order: 1, condition: 'Serie propre sans complexite'}) MERGE (dt)-[:HAS_BRANCH]->(b)
MATCH (dt:DecisionTree {id: 'ts-model-selection'}), (b:DecisionBranch {order: 2, condition: 'Non-linearites et caracteristiques riches'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt2:DecisionTree {id: 'agentic-framework-selection'}) SET dt2 += {question: 'Quel framework d\'agents IA choisir ?', context: 'agentic_ai'}
MERGE (b2_1:DecisionBranch {order: 1, condition: 'Controle d\'etat et validation humaine'}) SET b2_1 += {action: 'Utiliser LangGraph', confidence: 0.95}
MERGE (b2_2:DecisionBranch {order: 2, condition: 'Workflows business et roles'}) SET b2_2 += {action: 'Utiliser CrewAI', confidence: 0.85}
MERGE (b2_3:DecisionBranch {order: 3, condition: 'Extraction de documents et RAG'}) SET b2_3 += {action: 'Utiliser Haystack', confidence: 0.90}
MATCH (dt:DecisionTree {id: 'agentic-framework-selection'}), (b:DecisionBranch {order: 1, condition: 'Controle d\'etat et validation humaine'}) MERGE (dt)-[:HAS_BRANCH]->(b)
MATCH (dt:DecisionTree {id: 'agentic-framework-selection'}), (b:DecisionBranch {order: 2, condition: 'Workflows business et roles'}) MERGE (dt)-[:HAS_BRANCH]->(b)
MATCH (dt:DecisionTree {id: 'agentic-framework-selection'}), (b:DecisionBranch {order: 3, condition: 'Extraction de documents et RAG'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt3:DecisionTree {id: 'mlops-infrastructure'}) SET dt3 += {question: 'Services Cloud Manages ou Open-Source heberge ?', context: 'mlops'}
MERGE (b3_1:DecisionBranch {order: 1, condition: 'Equipe novice et besoin de rapidite'}) SET b3_1 += {action: 'AWS SageMaker, Azure ML', confidence: 0.90}
MERGE (b3_2:DecisionBranch {order: 2, condition: 'Refus du vendor lock-in et maturite'}) SET b3_2 += {action: 'Kubeflow, MLflow local', confidence: 0.95}
MATCH (dt:DecisionTree {id: 'mlops-infrastructure'}), (b:DecisionBranch {order: 1, condition: 'Equipe novice et besoin de rapidite'}) MERGE (dt)-[:HAS_BRANCH]->(b)
MATCH (dt:DecisionTree {id: 'mlops-infrastructure'}), (b:DecisionBranch {order: 2, condition: 'Refus du vendor lock-in et maturite'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt4:DecisionTree {id: 'clustering-selection'}) SET dt4 += {question: 'Quel algorithme de clustering utiliser ?', context: 'clustering'}
MERGE (b4_1:DecisionBranch {order: 1, condition: 'Clusters spheriques et de tailles egales'}) SET b4_1 += {action: 'Utiliser K-Means', confidence: 0.95}
MERGE (b4_2:DecisionBranch {order: 2, condition: 'Formes arbitraires ou presence d\'outliers'}) SET b4_2 += {action: 'Utiliser DBSCAN', confidence: 0.90}
MATCH (dt:DecisionTree {id: 'clustering-selection'}), (b:DecisionBranch {order: 1, condition: 'Clusters spheriques et de tailles egales'}) MERGE (dt)-[:HAS_BRANCH]->(b)
MATCH (dt:DecisionTree {id: 'clustering-selection'}), (b:DecisionBranch {order: 2, condition: 'Formes arbitraires ou presence d\'outliers'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt5:DecisionTree {id: 'notebook-vs-script'}) SET dt5 += {question: 'Notebook Jupyter ou Script Python ?', context: 'data_engineering'}
MERGE (b5_1:DecisionBranch {order: 1, condition: 'Exploration, EDA et prototypage'}) SET b5_1 += {action: 'Utiliser Jupyter Notebooks', confidence: 0.90}
MERGE (b5_2:DecisionBranch {order: 2, condition: 'Environnement de production'}) SET b5_2 += {action: 'Utiliser scripts .py', confidence: 0.95}
MATCH (dt:DecisionTree {id: 'notebook-vs-script'}), (b:DecisionBranch {order: 1, condition: 'Exploration, EDA et prototypage'}) MERGE (dt)-[:HAS_BRANCH]->(b)
MATCH (dt:DecisionTree {id: 'notebook-vs-script'}), (b:DecisionBranch {order: 2, condition: 'Environnement de production'}) MERGE (dt)-[:HAS_BRANCH]->(b);

MERGE (dt6:DecisionTree {id: 'agentic-human-supervision'}) SET dt6 += {question: 'Quel niveau d\'intervention humaine est requis pour cette action de l\'agent ?', context: 'agentic_ai'}
MERGE (b6_1:DecisionBranch {order: 1, condition: 'Action automatisée à faible risque et réversible'}) SET b6_1 += {action: 'Niveau 1 : Exécution automatisée', confidence: 0.95}
MERGE (b6_2:DecisionBranch {order: 2, condition: 'Action modérée nécessitant un contrôle qualité'}) SET b6_2 += {action: 'Niveau 2 : Supervision avec fenêtre de révision', confidence: 0.90}
MERGE (b6_3:DecisionBranch {order: 3, condition: 'Action irréversible ou à forts enjeux'}) SET b6_3 += {action: 'Niveau 3 : Approbation stricte obligatoire', confidence: 0.99}
MATCH (dt:DecisionTree {id: 'agentic-human-supervision'}), (b:DecisionBranch {order: 1, condition: 'Action automatisée à faible risque et réversible'}) MERGE (dt)-[:HAS_BRANCH]->(b)
MATCH (dt:DecisionTree {id: 'agentic-human-supervision'}), (b:DecisionBranch {order: 2, condition: 'Action modérée nécessitant un contrôle qualité'}) MERGE (dt)-[:HAS_BRANCH]->(b)
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
