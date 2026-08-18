---
type: concept
title: Guide d'Analyse de Survie (Survival Analysis)
domain: survival
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Guide d'Analyse de Survie (Survival Analysis)

**Definition**: L'analyse de survie modélise le temps écoulé avant la survenue d'un événement (départ client, panne, décès). Sa particularité est la gestion des données censurées (les clients qui n'ont pas encore résilié à la fin de l'étude).

**Related Tools**: survival_tools

## Description de la tâche
L'analyse de survie modélise le temps écoulé avant la survenue d'un événement (départ client, panne, décès). Sa particularité est la gestion des données censurées (les clients qui n'ont pas encore résilié à la fin de l'étude).

## Modèles recommandés
- **Kaplan-Meier** : Estimateur non-paramétrique pour tracer la courbe de survie globale ou par segments.
- **Modèle de Cox (Proportional Hazards)** : Modélise les taux de risques à l'aide de plusieurs variables explicatives (calcul des Hazard Ratios).
