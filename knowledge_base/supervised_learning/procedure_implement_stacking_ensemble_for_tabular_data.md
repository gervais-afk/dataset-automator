---
type: procedure
title: Implement Stacking Ensemble for Tabular Data
domain: supervised_learning
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Procedure: Implement Stacking Ensemble for Tabular Data

**Objective**: Combiner les prédictions de plusieurs modèles de base hétérogènes (linéaires, arbres, réseaux de neurones) via un méta-modèle (Stage 2) pour extraire plus de signal.

## Steps
### Step 1: Entraîner des modèles de base diversifiés de manière croisée
```python
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from lightgbm import LGBMClassifier

base_models = [
    ('rf', RandomForestClassifier(n_estimators=500)),
    ('xgb', XGBClassifier(tree_method='gpu_hist')),
    ('lgbm', LGBMClassifier(device='gpu'))
]
```
**Tools**: scikit-learn, XGBoost, LightGBM

### Step 2: Générer les caractéristiques OOF (Out-Of-Fold) ou les résidus
```python
from sklearn.model_selection import cross_val_predict
meta_features = np.column_stack([
    cross_val_predict(model, X_train, y_train, cv=5, method='predict_proba')
    for name, model in base_models
])
```
**Tools**: N/A

### Step 3: Entraîner le méta-modèle de second niveau
```python
from sklearn.linear_model import LogisticRegression
meta_model = LogisticRegression()
meta_model.fit(meta_features, y_train)
```
**Tools**: scikit-learn, cuML

**Validation/Pitfalls**: 
