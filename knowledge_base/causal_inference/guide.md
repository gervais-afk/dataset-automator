---
type: concept
title: Guide d'Inférence Causale et Uplift Modeling
domain: causal_inference
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Guide d'Inférence Causale et Uplift Modeling

**Definition**: L'inférence causale évalue l'effet réel (incrémental) d'un traitement en le séparant du hasard ou du biais de sélection. L'uplift modeling identifie les clients sensibles uniquement s'ils sont ciblés.

**Related Tools**: causal_inference_tools

## Description de la tâche
L'inférence causale évalue l'effet réel (incrémental) d'un traitement en le séparant du hasard ou du biais de sélection. L'uplift modeling identifie les clients sensibles uniquement s'ils sont ciblés.

## Modèles recommandés
- **Uplift Random Forest** (de la bibliothèque `causalml`).
- **T-Learner** (deux modèles séparés pour le traitement et le contrôle).

## Évaluation
- Tracé de la courbe de gain cumulatif (**Qini curve**) pour valider la pertinence du ciblage incrémental par rapport à l'aléatoire.
