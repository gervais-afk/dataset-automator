---
title: ts-model-selection
domain: time_series
type: decision_tree
---

# Decision: Quel modèle utiliser pour la prévision de séries temporelles ?

**Root Consideration**: Caractéristiques de la série temporelle

**Branches**:
- IF Clean, well-understood series sans complexité majeure THEN Utiliser des modèles statistiques classiques (ARIMA, Exponential Smoothing) comme base
- IF Complex non-linearities, rich feature sets, and calendar variables THEN Utiliser des modèles de Machine Learning basés sur les arbres (LightGBM, XGBoost)
