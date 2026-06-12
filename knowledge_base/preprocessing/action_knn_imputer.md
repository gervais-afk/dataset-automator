---
title: Imputation Avancée (KNN Imputer)
domain: preprocessing
type: action
---

# KNN Imputer & Iterative Imputer

**Definition**: Algorithmes remplaçant les valeurs manquantes (NaN) en se basant sur les autres colonnes. KNN cherche les K lignes les plus similaires pour déduire la valeur. IterativeImputer (MICE) utilise un modèle de régression itératif.

**Related Tools**: scikit-learn

**Quand l'utiliser** :
- Le dataset a de nombreuses valeurs manquantes (`missing_percentage > 5%`).
- Le `dropna()` supprimerait plus de 10% des lignes.
- La simple moyenne/médiane détruirait la variance de la colonne.

**Code Snippet** :
```python
from sklearn.impute import KNNImputer

# Ne fonctionne que sur des données numériques, encoder d'abord si besoin
imputer = KNNImputer(n_neighbors=5, weights='distance')
df_imputed = pd.DataFrame(imputer.fit_transform(df_numeric), columns=df_numeric.columns)
```
