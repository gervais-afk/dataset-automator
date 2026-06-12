---
title: Isolation Forest (Outliers)
domain: preprocessing
type: concept
---

# Isolation Forest (Valeurs Aberrantes)

**Definition**: Algorithme de détection d'anomalies non supervisé basé sur les Random Forests. Il isole les observations en divisant aléatoirement l'espace. Les anomalies, étant rares et différentes, nécessitent moins de divisions pour être isolées.

**Related Tools**: scikit-learn

**Quand l'utiliser** :
- Sur des datasets non nettoyés avec des valeurs aberrantes suspectées.
- Avant un modèle de Régression Linéaire ou K-Means (qui sont très sensibles aux outliers).
- Plus performant que le Z-Score car il détecte les anomalies multidimensionnelles.

**Code Snippet** :
```python
from sklearn.ensemble import IsolationForest

# L'entraînement se fait sans la target
iso = IsolationForest(contamination=0.05, random_state=42)
yhat = iso.fit_predict(X_train)

# Filtrer pour ne garder que les inliers (1 = inlier, -1 = outlier)
mask = yhat != -1
X_train_clean, y_train_clean = X_train[mask], y_train[mask]
```
