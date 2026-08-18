---
type: concept
title: Marketing Mix Modeling (MMM)
domain: modeling
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Marketing Mix Modeling (MMM)

## 1. Graph Context (Metadonnées pour Agents)
- **Concept Name**: Marketing Mix Modeling (MMM)
- **Category**: modeling, time_series
- **Is_A**: Cas d'usage d'analyse temporelle
- **Requires**: [Régression, Time Series, MLflow]
- **Solves**: [Attribution marketing, Optimisation du ROI publicitaire sans cookies]
- **Related_Concepts**: [Lagged Features, Décomposition STL]

## 2. Definition
Technique d'analyse statistique et Machine Learning visant à quantifier l'impact historique de différentes activités marketing (TV, Digital, Radio) sur les ventes ou conversions. Historiquement basée sur la régression linéaire (OLS), elle intègre désormais massivement le ML (ex: XGBoost avec variables retardées) pour capter les effets non linéaires et de rémanence (carry-over effects).

## 3. Propriétés & Pièges
- **Adstock Effect** : La publicité a un effet retardé. L'utilisation de *Lagged Features* est indispensable.
- **Diminishing Returns** : Effet de saturation (dépenser 10x plus ne rapporte pas 10x plus). Nécessite des transformations non linéaires.

## 4. Stratégie d'implémentation
1. **Feature Engineering** : Créer des features d'Adstock (decaying lags) et de saturation (log ou racine carrée) pour les dépenses.
2. **Contrôle** : Intégrer les facteurs externes (météo, jours fériés, macro-économie).
3. **Modélisation** : Entraîner des modèles explicables (Ridge, Bayesian Regression ou ML enrichi via SHAP values).
