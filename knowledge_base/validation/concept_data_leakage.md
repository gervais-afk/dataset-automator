---
title: Data Leakage (Fuite de données)
domain: validation
type: concept
---

# Data Leakage (Fuite de données)

## 1. Graph Context (Metadonnées pour Agents)
- **Concept Name**: Data Leakage
- **Category**: validation
- **Is_A**: Antipattern / Risque de modélisation
- **Requires**: []
- **Solves**: [Surapprentissage illusoire, Performances irréalistes en production]
- **Related_Concepts**: [TimeSeriesSplit, Validation Croisée, Target Encoding]

## 2. Definition
Problème critique survenant lorsqu'une information de l'ensemble de test ou du futur (pour les séries temporelles) se retrouve accidentellement dans l'ensemble d'entraînement. Cela conduit à un modèle qui semble parfait lors de la validation (métriques artificiellement élevées) mais qui échouera complètement en production.

## 3. Propriétés & Pièges courants
- **Leakage temporel** : Utiliser des données futures pour prédire le passé (ex: moyenner sur l'année entière avant de faire le split train/test).
- **Leakage de preprocessing** : Appliquer un `StandardScaler` ou un `PCA` sur l'ensemble complet avant de séparer le `X_train` et `X_test`. Le scaler a "vu" la distribution du test.

## 4. Implémentation & Résolution (Comment l'éviter)
1. **Pipeline stricte** : Toujours utiliser des objets `Pipeline` de scikit-learn. Le fit du scaler ne doit se faire que sur le `train_fold`.
2. **Pour les Séries Temporelles** : Utiliser impérativement `TimeSeriesSplit` au lieu du KFold classique pour respecter la chronologie.
