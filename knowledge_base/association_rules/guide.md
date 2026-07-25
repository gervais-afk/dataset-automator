---
title: Guide pour les Règles d'Association (Market Basket Analysis)
domain: association_rules
type: concept
---

# Guide pour les Règles d'Association (Market Basket Analysis)

**Definition**: Identifier des motifs d'achat fréquents (co-occurrences) dans un ensemble de transactions (ex: "ceux qui achètent des couches achètent aussi de la bière").

**Related Tools**: association_rules_tools

## Description de la tâche
Identifier des motifs d'achat fréquents (co-occurrences) dans un ensemble de transactions (ex: "ceux qui achètent des couches achètent aussi de la bière").

## Algorithmes recommandés
- **Apriori** (via `mlxtend`) : Filtre les itemsets fréquents en calculant le support.
- **Règles d'Association** : Calcule la confiance (probabilité conditionnelle) et le **Lift** (force d'association). Un Lift > 1.0 indique une association supérieure au hasard.
