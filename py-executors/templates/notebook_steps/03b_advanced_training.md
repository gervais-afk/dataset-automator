# 🚀 Entraînement Avancé (Stacking & Pseudo-Labeling)

Pour maximiser les performances de nos modèles de {TYPE_TACHE}, nous allons utiliser des techniques avancées issues des meilleures pratiques (ex: compétitions Kaggle) en optimisant d'abord nos modèles via recherche bayésienne, puis en les assemblant.

## 1. Optimisation des Hyperparamètres (Optuna)

Nous utilisons `Optuna` pour chercher automatiquement la meilleure configuration d'hyperparamètres (taux d'apprentissage, profondeur, etc.) pour notre classifieur/régresseur champion (XGBoost) par validation croisée.

```python
# Installation de Optuna si absent
try:
    import optuna
except ImportError:
    print("⏳ Installation de optuna...")
    !pip install -q optuna
    import optuna

import optuna
from xgboost import XGBClassifier, XGBRegressor
from sklearn.model_selection import cross_val_score

# Désactiver les logs trop verbeux d'Optuna
optuna.logging.set_verbosity(optuna.logging.WARNING)

print("=" * 60)
print("🔬 OPTIMISATION DES HYPERPARAMÈTRES AVEC OPTUNA")
print("=" * 60)

def objective(trial):
    # Espace de recherche bayésien avec régulation de la complexité
    n_estimators = trial.suggest_int("n_estimators", 50, 150)
    max_depth = trial.suggest_int("max_depth", 3, 9)
    learning_rate = trial.suggest_float("learning_rate", 0.01, 0.2, log=True)
    
    # Intégration des concepts RAG : Régularisation L1 (alpha), L2 (lambda) et Élagage (min_child_weight)
    reg_alpha = trial.suggest_float("reg_alpha", 1e-8, 10.0, log=True)
    reg_lambda = trial.suggest_float("reg_lambda", 1e-8, 10.0, log=True)
    min_child_weight = trial.suggest_int("min_child_weight", 1, 10)
    
    if TYPE_TACHE == "classification":
        model = XGBClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            reg_alpha=reg_alpha,
            reg_lambda=reg_lambda,
            min_child_weight=min_child_weight,
            random_state=42,
            eval_metric='logloss',
            n_jobs=-1
        )
        scoring_metric = "accuracy"
    else:
        model = XGBRegressor(
            n_estimators=n_estimators,
            max_depth=max_depth,
            learning_rate=learning_rate,
            reg_alpha=reg_alpha,
            reg_lambda=reg_lambda,
            min_child_weight=min_child_weight,
            random_state=42,
            n_jobs=-1
        )
        scoring_metric = "r2"
        
    # Détermination de la stratégie de CV
    if TYPE_TACHE == "timeseries":
        from sklearn.model_selection import TimeSeriesSplit
        cv_strategy = TimeSeriesSplit(n_splits=3)
    elif TYPE_TACHE == "classification":
        from sklearn.model_selection import StratifiedKFold
        cv_strategy = StratifiedKFold(n_splits=3, shuffle=True, random_state=42)
    else:
        from sklearn.model_selection import KFold
        cv_strategy = KFold(n_splits=3, shuffle=True, random_state=42)
        
    # Évaluation par validation croisée
    score = cross_val_score(model, X_train_prep, y_train, cv=cv_strategy, scoring=scoring_metric).mean()
    return score

try:
    # Lancement de l'optimisation bayésienne (15 trials rapides) avec sampler déterministe
    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="maximize", sampler=sampler)
    print("⏳ Recherche des meilleurs hyperparamètres (15 trials)...")
    study.optimize(objective, n_trials=15)
    
    best_params = study.best_params
    print("   ✅ Recherche terminée !")
    print("   🎯 Meilleurs paramètres :", best_params)
    print(f"   🎯 Meilleur Score ({'Accuracy' if TYPE_TACHE=='classification' else 'R²'}) : {study.best_value:.4f}")
except Exception as e_opt:
    print(f"   ⚠️ Échec d'Optuna : {e_opt}. Utilisation des paramètres par défaut.")
    best_params = {"n_estimators": 200, "max_depth": 6, "learning_rate": 0.05}
```

## 2. Stacking Ensemble

Le *Stacking* consiste à entraîner plusieurs modèles de base (Random Forest, XGBoost, LightGBM) et à utiliser un **méta-modèle** (généralement une régression linéaire/logistique) pour combiner intelligemment leurs prédictions. Nous injectons ici le modèle XGBoost optimisé par Optuna.

```python
from sklearn.ensemble import StackingClassifier, StackingRegressor, RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.linear_model import LogisticRegression, RidgeCV
from sklearn.model_selection import TimeSeriesSplit
import time
import mlflow
try:
    from catboost import CatBoostClassifier, CatBoostRegressor
    HAS_CATBOOST = True
except ImportError:
    HAS_CATBOOST = False

print("🏗️ Initialisation du Stacking Ensemble...")

# Définition des modèles de base performants (XGBoost utilise best_params d'Optuna)
if TYPE_TACHE == "classification":
    base_models = [
        ('rf', RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)),
        ('xgb', XGBClassifier(
            n_estimators=best_params.get("n_estimators", 200),
            max_depth=best_params.get("max_depth", 6),
            learning_rate=best_params.get("learning_rate", 0.05),
            random_state=42,
            eval_metric='logloss',
            n_jobs=-1
        )),
        ('lgb', LGBMClassifier(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42, verbose=-1, n_jobs=-1))
    ]
    if HAS_CATBOOST:
        base_models.append(('cat', CatBoostClassifier(iterations=200, learning_rate=0.05, depth=6, verbose=0, random_state=42)))
    meta_model = LogisticRegression()
    stacking_model = StackingClassifier(estimators=base_models, final_estimator=meta_model, cv=5, n_jobs=-1)
    
elif TYPE_TACHE == "regression" or TYPE_TACHE == "timeseries":
    base_models = [
        ('rf', RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42, n_jobs=-1)),
        ('xgb', XGBRegressor(
            n_estimators=best_params.get("n_estimators", 200),
            max_depth=best_params.get("max_depth", 6),
            learning_rate=best_params.get("learning_rate", 0.05),
            random_state=42,
            n_jobs=-1
        )),
        ('lgb', LGBMRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42, verbose=-1, n_jobs=-1))
    ]
    if HAS_CATBOOST:
        base_models.append(('cat', CatBoostRegressor(iterations=200, learning_rate=0.05, depth=6, verbose=0, random_state=42)))
    meta_model = RidgeCV()
    if TYPE_TACHE == "timeseries":
        # TimeSeriesSplit ne forme pas de partition et fait échouer cross_val_predict dans StackingRegressor.
        # On utilise 5-fold pour générer les méta-features en toute sécurité.
        cv_split = 5
        print("⏳ Utilisation de cv=5 pour le Stacking (évite l'erreur de partition)...")
    else:
        cv_split = 5
    stacking_model = StackingRegressor(estimators=base_models, final_estimator=meta_model, cv=cv_split, n_jobs=-1)

# Entraînement
t0 = time.time()
try:
    if TYPE_TACHE != "unsupervised":
        with mlflow.start_run(run_name="Stacking_Ensemble", nested=True):
            stacking_model.fit(X_train_prep, y_train)
            score_stacking = stacking_model.score(X_test_prep, y_test)
            elapsed = time.time() - t0
            print(f"✅ Stacking Model Score ({metric}) : {score_stacking:.4f} | Temps : {elapsed:.2f}s")
            
            # Tracking MLflow
            mlflow.log_metric("stacking_score", score_stacking)
            mlflow.sklearn.log_model(stacking_model, "model_stacking")
    else:
        print("⏭️ Stacking ignoré pour le clustering.")
except Exception as e:
    print(f"❌ Erreur lors du stacking : {e}")
    if 'stacking_model' in globals():
        del stacking_model

```

## 2. Pseudo-Labeling Sécurisé (Cellule 12)

```python
log_section("12 - PSEUDO-LABELING DU JEU D'ENTRAÎNEMENT")

# Pour éviter la fuite de données, on n'utilise jamais le jeu d'évaluation !
# Nous appliquons un bruit contrôlé uniquement sur une copie bruitée de la base de Train.
try:
    if TYPE_TACHE != "unsupervised" and 'stacking_model' in globals():
        conf_model = stacking_model
        noise = np.random.normal(0, 0.01, X_train_prep.shape)
        X_train_unlabeled = X_train_prep + noise
        
        pseudo_labels = conf_model.predict(X_train_unlabeled)
        
        X_combined = np.vstack((X_train_prep, X_train_unlabeled))
        y_combined = np.concatenate((y_train, pseudo_labels))
        
        final_model = conf_model
        final_model.fit(X_combined, y_combined)
        
        score_final = final_model.score(X_test_prep, y_test)
        print(f"✅ Score R² final après Pseudo-Labeling légitime : {score_final:.4f}")
    else:
        print("⏭️ Pseudo-labeling non applicable ou ignoré.")
        final_model = stacking_model if 'stacking_model' in globals() else None
except Exception as e:
    print(f"⚠️ Pseudo-Labeling non-exécuté / Erreur : {e}")
    final_model = stacking_model if 'stacking_model' in globals() else None
```
