---
type: decision_tree
title: ts-model-selection
domain: time_series
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Decision: Quel modèle utiliser pour la prévision de séries temporelles ?

**Root Consideration**: Caractéristiques de la série temporelle

**Branches**:
- IF Clean, well-understood series sans complexité majeure THEN Utiliser des modèles statistiques classiques (ARIMA, Exponential Smoothing) comme base
- IF Complex non-linearities, rich feature sets, and calendar variables THEN Utiliser des modèles de Machine Learning basés sur les arbres (LightGBM, XGBoost)
