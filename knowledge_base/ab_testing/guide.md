---
title: Guide de Test A/B et Design Expérimental
domain: ab_testing
type: concept
---

# Guide de Test A/B et Design Expérimental

**Definition**: Comparer scientifiquement et valider si les performances d'une version A diffèrent significativement d'une version B.

**Related Tools**: ab_testing_tools

## Description de la tâche
Comparer scientifiquement et valider si les performances d'une version A diffèrent significativement d'une version B.

## Tests statistiques recommandés
- **Proportions Z-Test** : Pour les variables binaires (taux de conversion).
- **Welch T-Test** : Pour les variables continues (panier moyen, temps de session).

## Métriques requises
- **p-value** (seuil $\alpha = 0.05$).
- **Taille de l'effet** (Cohen's d) pour évaluer la signification pratique de la différence.
- **Intervalles de confiance** (à 95%) pour estimer la plage de gain probable.
