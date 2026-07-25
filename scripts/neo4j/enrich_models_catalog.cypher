// ================================================================
// enrich_models_catalog.cypher
// Catalogue complet des modèles ML — aligné avec server.py
// Ajoute les nœuds :Model manquants et normalise les noms
// ================================================================

// ── CLASSIFICATION ───────────────────────────────────────────────

MERGE (m:Model {name: 'XGBoost Classifier'})
SET m += {
  task_type: 'classification',
  python_class: 'XGBClassifier',
  library: 'xgboost',
  strengths: 'Gradient boosting rapide, robuste aux outliers, supporte les données manquantes',
  weaknesses: 'Sensible au surapprentissage si mal régularisé',
  hyperparams: 'n_estimators, max_depth, learning_rate, subsample, colsample_bytree',
  registered: true
};

MERGE (m:Model {name: 'LightGBM Classifier'})
SET m += {
  task_type: 'classification',
  python_class: 'LGBMClassifier',
  library: 'lightgbm',
  strengths: 'Très rapide sur grands datasets, gère nativement les catégorielles',
  weaknesses: 'Peut overfit sur petits datasets',
  hyperparams: 'n_estimators, max_depth, learning_rate, num_leaves',
  registered: true
};

MERGE (m:Model {name: 'RandomForest Classifier'})
SET m += {
  task_type: 'classification',
  python_class: 'RandomForestClassifier',
  library: 'sklearn',
  strengths: 'Robuste, peu d hyperparamètres critiques, importances de features fiables',
  weaknesses: 'Lent à prédire sur très grand nombre d arbres',
  hyperparams: 'n_estimators, max_depth, min_samples_split',
  registered: true
};

MERGE (m:Model {name: 'CatBoost Classifier'})
SET m += {
  task_type: 'classification',
  python_class: 'CatBoostClassifier',
  library: 'catboost',
  strengths: 'Natif pour catégorielles, peu de preprocessing, robuste',
  weaknesses: 'Plus lent à entraîner que XGBoost/LightGBM',
  hyperparams: 'iterations, depth, learning_rate, l2_leaf_reg',
  registered: true
};

MERGE (m:Model {name: 'TabICL Classifier'})
SET m += {
  task_type: 'classification',
  python_class: 'TabICLClassifier',
  library: 'tabicl',
  strengths: 'SOTA pour données tabulaires, in-context learning, pas de feature engineering',
  weaknesses: 'Lent, nécessite GPU recommandé, peu interprétable',
  hyperparams: 'Aucun (in-context learning)',
  registered: true
};

MERGE (m:Model {name: 'Logistic Regression'})
SET m += {
  task_type: 'classification',
  python_class: 'LogisticRegression',
  library: 'sklearn',
  strengths: 'Interprétable, baseline solide, rapide',
  weaknesses: 'Limité aux relations linéaires',
  hyperparams: 'C, solver, max_iter',
  registered: false
};

MERGE (m:Model {name: 'SVM Classifier'})
SET m += {
  task_type: 'classification',
  python_class: 'SVC',
  library: 'sklearn',
  strengths: 'Efficace en haute dimension, kernel trick',
  weaknesses: 'Lent sur grands datasets, sensible aux échelles',
  hyperparams: 'C, kernel, gamma',
  registered: false
};

// ── REGRESSION ───────────────────────────────────────────────────

MERGE (m:Model {name: 'XGBoost Regressor'})
SET m += {
  task_type: 'regression',
  python_class: 'XGBRegressor',
  library: 'xgboost',
  strengths: 'Gradient boosting rapide, gère non-linéarités',
  weaknesses: 'Sensible aux outliers en target',
  hyperparams: 'n_estimators, max_depth, learning_rate, subsample',
  registered: true
};

MERGE (m:Model {name: 'LightGBM Regressor'})
SET m += {
  task_type: 'regression',
  python_class: 'LGBMRegressor',
  library: 'lightgbm',
  strengths: 'Rapide, scalable',
  weaknesses: 'Peut extrapoler de façon instable',
  hyperparams: 'n_estimators, max_depth, learning_rate, num_leaves',
  registered: true
};

MERGE (m:Model {name: 'RandomForest Regressor'})
SET m += {
  task_type: 'regression',
  python_class: 'RandomForestRegressor',
  library: 'sklearn',
  strengths: 'Stable, résistant au bruit',
  weaknesses: 'Ne peut pas extrapoler au delà des valeurs d entraînement',
  hyperparams: 'n_estimators, max_depth, min_samples_split',
  registered: true
};

MERGE (m:Model {name: 'CatBoost Regressor'})
SET m += {
  task_type: 'regression',
  python_class: 'CatBoostRegressor',
  library: 'catboost',
  strengths: 'Natif catégorielles, robuste',
  weaknesses: 'Plus lent à entraîner',
  hyperparams: 'iterations, depth, learning_rate',
  registered: true
};

MERGE (m:Model {name: 'TabICL Regressor'})
SET m += {
  task_type: 'regression',
  python_class: 'TabICLRegressor',
  library: 'tabicl',
  strengths: 'SOTA tabulaire, in-context learning',
  weaknesses: 'Lent, GPU recommandé',
  hyperparams: 'Aucun',
  registered: true
};

MERGE (m:Model {name: 'Ridge Regression'})
SET m += {
  task_type: 'regression',
  python_class: 'Ridge',
  library: 'sklearn',
  strengths: 'Baseline rapide, gère multicollinéarité via L2',
  weaknesses: 'Limité aux relations linéaires',
  hyperparams: 'alpha',
  registered: false
};

// ── CLUSTERING ───────────────────────────────────────────────────

MERGE (m:Model {name: 'KMeans'})
SET m += {
  task_type: 'clustering',
  python_class: 'KMeans',
  library: 'sklearn',
  strengths: 'Simple, rapide, interprétable',
  weaknesses: 'Suppose clusters sphériques, sensible aux outliers, nécessite k fixe',
  hyperparams: 'n_clusters, init, max_iter',
  registered: true
};

MERGE (m:Model {name: 'DBSCAN'})
SET m += {
  task_type: 'clustering',
  python_class: 'DBSCAN',
  library: 'sklearn',
  strengths: 'Détecte les formes arbitraires, identifie les outliers automatiquement',
  weaknesses: 'Difficile à paramétrer (eps, min_samples), lent sur gros datasets',
  hyperparams: 'eps, min_samples, metric',
  registered: true
};

MERGE (m:Model {name: 'Hierarchical Clustering'})
SET m += {
  task_type: 'clustering',
  python_class: 'AgglomerativeClustering',
  library: 'sklearn',
  strengths: 'Pas besoin de k fixe, dendrogramme interprétable',
  weaknesses: 'O(n²) en mémoire, lent sur grands datasets',
  hyperparams: 'n_clusters, linkage, affinity',
  registered: true
};

MERGE (m:Model {name: 'Gaussian Mixture Model'})
SET m += {
  task_type: 'clustering',
  python_class: 'GaussianMixture',
  library: 'sklearn',
  strengths: 'Soft clustering, probabilités d appartenance',
  weaknesses: 'Suppose distribution gaussienne',
  hyperparams: 'n_components, covariance_type',
  registered: false
};

// ── SÉRIES TEMPORELLES ───────────────────────────────────────────

MERGE (m:Model {name: 'Prophet'})
SET m += {
  task_type: 'timeseries',
  python_class: 'Prophet',
  library: 'prophet',
  strengths: 'Gère saisonnalité multiple et jours fériés, robuste aux données manquantes',
  weaknesses: 'Pas idéal pour séries très courtes ou très bruitées',
  hyperparams: 'changepoint_prior_scale, seasonality_mode, yearly/weekly/daily_seasonality',
  registered: true
};

MERGE (m:Model {name: 'AutoARIMA'})
SET m += {
  task_type: 'timeseries',
  python_class: 'auto_arima',
  library: 'pmdarima',
  strengths: 'Sélection automatique des ordres p,d,q, modèle statistiquement fondé',
  weaknesses: 'Lent sur longues séries, univarié uniquement',
  hyperparams: 'p, d, q, P, D, Q, seasonal',
  registered: true
};

MERGE (m:Model {name: 'RandomForest Timeseries'})
SET m += {
  task_type: 'timeseries',
  python_class: 'RandomForestRegressor',
  library: 'sklearn',
  strengths: 'Baseline ML solide sur features lag, robuste',
  weaknesses: 'Ne peut pas extrapoler, nécessite feature engineering temporel',
  hyperparams: 'n_estimators, max_depth, lags',
  registered: true
};

MERGE (m:Model {name: 'LSTM'})
SET m += {
  task_type: 'timeseries',
  python_class: 'LSTM',
  library: 'tensorflow/keras',
  strengths: 'Capture dépendances long terme, multivarié',
  weaknesses: 'Nécessite GPU, long à entraîner, difficile à interpréter',
  hyperparams: 'units, layers, dropout, look_back',
  registered: false
};

// ── NORMALISATION : lier les nœuds Model au bon Task Type ────────

MERGE (t_cls:Concept {name: 'Classification'})
MERGE (t_reg:Concept {name: 'Regression'})
MERGE (t_clu:Concept {name: 'Clustering'})
MERGE (t_ts:Concept {name: 'TimeSeries'});

MATCH (m:Model {task_type: 'classification'}), (t:Concept {name: 'Classification'})
MERGE (m)-[:USED_FOR]->(t);

MATCH (m:Model {task_type: 'regression'}), (t:Concept {name: 'Regression'})
MERGE (m)-[:USED_FOR]->(t);

MATCH (m:Model {task_type: 'clustering'}), (t:Concept {name: 'Clustering'})
MERGE (m)-[:USED_FOR]->(t);

MATCH (m:Model {task_type: 'timeseries'}), (t:Concept {name: 'TimeSeries'})
MERGE (m)-[:USED_FOR]->(t);

// ── SUPPRIMER L'AMBIGUÏTÉ : renommer le nœud "XGBoost" générique ─
// Le nœud :Model {name: 'XGBoost'} sans task_type est ambigu.
// On lui ajoute un alias pour éviter la confusion avec XGBoost Classifier.

MATCH (m:Model {name: 'XGBoost'})
WHERE m.task_type IS NULL
SET m.name = 'XGBoost Classifier', m.task_type = 'classification',
    m.python_class = 'XGBClassifier', m.library = 'xgboost';

// ── IDEM pour "LightGBM" générique ───────────────────────────────
MATCH (m:Model {name: 'LightGBM'})
WHERE m.task_type IS NULL
SET m.name = 'LightGBM Classifier', m.task_type = 'classification',
    m.python_class = 'LGBMClassifier', m.library = 'lightgbm';

// ── IDEM pour "RandomForest" générique ───────────────────────────
MATCH (m:Model {name: 'RandomForest'})
WHERE m.task_type IS NULL
SET m.name = 'RandomForest Classifier', m.task_type = 'classification',
    m.python_class = 'RandomForestClassifier', m.library = 'sklearn';
