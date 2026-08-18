---
type: procedure
title: Tune XGBoost Hyperparameters and Extra Training
domain: supervised_learning
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Procedure: Tune XGBoost Hyperparameters and Extra Training

**Objective**: Optimiser les paramètres des modèles basés sur les arbres.

## Steps
### Step 1: Ajuster les hyperparamètres clés de XGBoost
```python
xgb_params = {'learning_rate': 0.05, 'max_depth': 6, 'n_estimators': 1000}
```
**Tools**: N/A

### Step 2: S'entraîner avec différents Random Seeds
```python
preds = []
for seed in range(10):
    model = XGBClassifier(random_state=seed, **xgb_params)
    model.fit(X_train, y_train)
    preds.append(model.predict_proba(X_test))
final_preds = np.mean(preds, axis=0)
```
**Tools**: N/A

### Step 3: Réentraîner le modèle final sur 100% des données
```python
final_model = XGBClassifier(**best_params)
final_model.fit(X_full, y_full)
```
**Tools**: N/A

**Validation/Pitfalls**: 
