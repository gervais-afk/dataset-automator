# 🚀 Entraînement Avancé (Stacking & Pseudo-Labeling)

Pour maximiser les performances de nos modèles de {TYPE_TACHE}, nous allons utiliser des techniques avancées issues des meilleures pratiques (ex: compétitions Kaggle).

## 1. Stacking Ensemble

Le *Stacking* consiste à entraîner plusieurs modèles de base (Random Forest, XGBoost, LightGBM) et à utiliser un **méta-modèle** (généralement une régression linéaire/logistique) pour apprendre à combiner intelligemment leurs prédictions.

```python
from sklearn.ensemble import StackingClassifier, StackingRegressor, RandomForestClassifier, RandomForestRegressor
from xgboost import XGBClassifier, XGBRegressor
from lightgbm import LGBMClassifier, LGBMRegressor
from sklearn.linear_model import LogisticRegression, RidgeCV
import time

print("🏗️ Initialisation du Stacking Ensemble...")

# Définition des modèles de base performants
if TYPE_TACHE == "classification":
    base_models = [
        ('rf', RandomForestClassifier(n_estimators=200, max_depth=10, random_state=42)),
        ('xgb', XGBClassifier(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42, eval_metric='logloss')),
        ('lgb', LGBMClassifier(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42, verbose=-1))
    ]
    meta_model = LogisticRegression()
    stacking_model = StackingClassifier(estimators=base_models, final_estimator=meta_model, cv=5)
    
elif TYPE_TACHE == "regression" or TYPE_TACHE == "timeseries":
    base_models = [
        ('rf', RandomForestRegressor(n_estimators=200, max_depth=10, random_state=42)),
        ('xgb', XGBRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42)),
        ('lgb', LGBMRegressor(n_estimators=200, learning_rate=0.05, max_depth=6, random_state=42, verbose=-1))
    ]
    meta_model = RidgeCV()
    stacking_model = StackingRegressor(estimators=base_models, final_estimator=meta_model, cv=5)

# Entraînement
t0 = time.time()
try:
    if TYPE_TACHE != "unsupervised":
        stacking_model.fit(X_train_prep, y_train)
        score_stacking = stacking_model.score(X_test_prep, y_test)
        print(f"✅ Stacking Model Score ({metric}) : {score_stacking:.4f} | Temps : {time.time()-t0:.2f}s")
    else:
        print("⏭️ Stacking ignoré pour le clustering.")
except Exception as e:
    print(f"❌ Erreur lors du stacking : {e}")
```

## 2. Pseudo-Labeling (Semi-Supervised)

Le *Pseudo-Labeling* consiste à utiliser notre meilleur modèle pour prédire des labels sur des données "non étiquetées", puis à ré-entraîner le modèle sur ces nouvelles données combinées aux données d'origine pour améliorer sa robustesse.

> *Note : Dans ce bloc, nous simulons des données non étiquetées en générant des variations bruitées du jeu de test (Data Augmentation) ou en utilisant des données d'un domaine connexe.*

```python
import numpy as np

if TYPE_TACHE in ["classification", "regression"]:
    print("🔄 Application du Pseudo-Labeling...")
    
    try:
        # 1. Sélection du modèle de confiance (ici, le Stacking model s'il a réussi, sinon on utilise 'best_name' du benchmark)
        conf_model = stacking_model
        
        # 2. Simulation de données non étiquetées (ex: ajout de bruit gaussien sur X_test)
        noise = np.random.normal(0, 0.01, X_test_prep.shape)
        X_unlabeled = X_test_prep + noise
        
        # 3. Prédiction des Pseudo-Labels
        pseudo_labels = conf_model.predict(X_unlabeled)
        
        # 4. Fusion des datasets
        if isinstance(X_train_prep, pd.DataFrame):
            X_combined = pd.concat([X_train_prep, pd.DataFrame(X_unlabeled, columns=X_train_prep.columns)])
            y_combined = pd.concat([y_train, pd.Series(pseudo_labels)])
        else:
            X_combined = np.vstack((X_train_prep, X_unlabeled))
            y_combined = np.concatenate((y_train, pseudo_labels))
            
        # 5. Ré-entraînement du modèle final sur les données augmentées
        final_model = conf_model
        final_model.fit(X_combined, y_combined)
        
        score_final = final_model.score(X_test_prep, y_test)
        print(f"✅ Score après Pseudo-Labeling ({metric}) : {score_final:.4f}")
        
    except Exception as e:
        print(f"⚠️ Pseudo-Labeling ignoré/Erreur : {e}")
```
