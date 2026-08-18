---
type: concept
title: Guide d'Optimisation sous Contraintes (Recherche Opérationnelle)
domain: optimization
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Guide d'Optimisation sous Contraintes (Recherche Opérationnelle)

**Definition**: Maximiser ou minimiser une fonction objectif (ex: ROI publicitaire, profit, temps de transport) en respectant un ensemble de limites de ressources (budget, capacité).

**Related Tools**: optimization_tools

## Description de la tâche
Maximiser ou minimiser une fonction objectif (ex: ROI publicitaire, profit, temps de transport) en respectant un ensemble de limites de ressources (budget, capacité).

## Outils recommandés
- **PuLP** : Bibliothèque Python pour modéliser et résoudre des problèmes d'optimisation linéaire de manière déclarative.

## Analyses de sensibilité
- **Shadow Prices** : Déterminer la valeur marginale d'une unité supplémentaire d'une ressource contrainte.
- **Slacks** : Connaître la marge inutilisée pour chaque contrainte.
