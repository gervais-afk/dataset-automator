---
title: SHAP Multiclass Handling
domain: machine_learning
type: concept
---

# SHAP Multiclass Handling

**Definition**: SHAP (SHapley Additive exPlanations) est une méthode d'explicabilité locale. Pour les modèles de classification multiclasse (nombre de classes cibles > 2), TreeExplainer retourne soit une liste de matrices 2D (une par classe), soit un tableau numpy 3D de dimension `(samples, features, classes)`. Traiter ces valeurs directement comme un tableau 2D sans agréger la dimension des classes lève une exception `TypeError: only 0-dimensional arrays can be converted to Python scalars` lors des calculs d'importance scalaire.

**Related Tools**: SHAP, scikit-learn

**Quand l'utiliser** :
- Pour auditer l'explicabilité des modèles de classification multiclasse de manière robuste.
- Pour calculer l'importance globale d'une variable (mean absolute SHAP) en moyennant sur l'axe des échantillons et l'axe des classes.

**Code Snippet** :
```python
import numpy as np
import shap

# Calcul des valeurs SHAP
explainer = shap.TreeExplainer(model)
shap_values = explainer.shap_values(X_sample)

# Agrégation robuste de l'importance absolue globale
if isinstance(shap_values, list):
    # Moyenne sur les échantillons (axe 0) puis sur les classes (liste)
    mean_abs_shap = np.mean([np.abs(val).mean(axis=0) for val in shap_values], axis=0)
elif isinstance(shap_values, np.ndarray) and shap_values.ndim == 3:
    # Moyenne sur les échantillons (axe 0) et les classes (axe 2)
    mean_abs_shap = np.abs(shap_values).mean(axis=(0, 2))
else:
    # Cas standard 2D (régression ou classification binaire)
    mean_abs_shap = np.abs(shap_values).mean(axis=0)
```
