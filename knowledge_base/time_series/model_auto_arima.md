---
title: Auto-ARIMA (pmdarima)
domain: time_series
type: model
---

# Auto-ARIMA (Modèles Classiques)

**Definition**: Algorithme qui automatise la recherche des paramètres optimaux (p, d, q) et saisonniers (P, D, Q, s) pour un modèle ARIMA/SARIMA, en minimisant un critère d'information (AIC ou BIC).

**Related Tools**: pmdarima, statsmodels

**Quand l'utiliser** :
- Pour des séries temporelles courtes à moyennes, relativement stables et bien comprises.
- Comme modèle de base (Baseline) robuste avant de tester des algorithmes de Machine Learning plus complexes.
- Lorsque l'explicabilité mathématique linéaire est exigée.

**Code Snippet** :
```python
from pmdarima import auto_arima

# Trouver le meilleur modèle automatiquement
model = auto_arima(df['Target'], 
                   seasonal=True, 
                   m=12, # Période saisonnière (ex: 12 mois)
                   trace=True,
                   error_action='ignore',  
                   suppress_warnings=True, 
                   stepwise=True)

print(model.summary())

# Prédiction
forecast = model.predict(n_periods=10)
```
