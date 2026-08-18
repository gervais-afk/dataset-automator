---
type: concept
title: Analyse de Survie (Survival Analysis)
domain: medical
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Concept : Analyse de Survie (Survival Analysis)

L'analyse de survie s'intéresse à la durée s'écoulant avant la survenue d'un événement donné (ex: décès, récidive, rechute, panne de machine).

## 🩺 Le Défi des Données Censurées (Censoring)
On dit qu'une donnée est **censurée** si l'événement d'intérêt n'est pas survenu durant la période de l'étude (ex: le patient est toujours vivant à la fin de l'étude ou a quitté le protocole).
*   **Ne pas supprimer ces patients** : C'est un biais de sélection majeur qui fausse les résultats.
*   **Ne pas traiter comme régression standard** : Les modèles de régression classique ne gèrent pas la censure.

## 🛠️ Modèles Recommandés
*   **Estimateur de Kaplan-Meier** : Pour visualiser la courbe de survie globale de la population.
*   **Modèle des Risques Proportionnels de Cox (Cox Proportional Hazards)** : Pour évaluer l'effet de covariables (âge, dose de médicament, groupe témoin) sur le taux de risque.
*   **Random Survival Forests (RSF)** : Extension non-linéaire du modèle de Cox avec des forêts d'arbres décisionnels.
*   **Métrique d'évaluation** : **Concordance Index (C-index)** au lieu du R² ou RMSE. Un C-index de 0.5 correspond au hasard, 1.0 est une prédiction parfaite de l'ordre de survenue de l'événement.
