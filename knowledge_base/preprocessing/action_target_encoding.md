---
title: Target Encoding (Haute Cardinalité)
domain: preprocessing
type: action
---

# Target Encoding

**Definition**: Encodeur catégoriel qui remplace une modalité par la moyenne de la variable cible (Target) pour cette modalité. 

**Related Tools**: category_encoders

**Quand l'utiliser** :
- Le profil du dataset montre une colonne catégorielle avec une cardinalité extrême (`cardinality > 50`).
- Un One-Hot Encoding classique (get_dummies) créerait des centaines de colonnes vides et détruirait le modèle (Malédiction de la dimensionnalité).
- Ne pas oublier de lisser (Smoothing) pour éviter l'overfitting sur les petites catégories.

**Code Snippet** :
```python
import category_encoders as ce

# S'applique après le split Train/Test pour éviter la fuite de données (Data Leakage)
encoder = ce.TargetEncoder(cols=['Colonne_Haute_Cardinalite'], smoothing=10)

X_train_encoded = encoder.fit_transform(X_train, y_train)
X_test_encoded = encoder.transform(X_test)
```
