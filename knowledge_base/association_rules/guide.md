---
type: concept
title: Guide pour les Règles d'Association (Market Basket Analysis)
domain: association_rules
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Guide pour les Règles d'Association (Market Basket Analysis)

**Definition**: Identifier des motifs d'achat fréquents (co-occurrences) dans un ensemble de transactions (ex: "ceux qui achètent des couches achètent aussi de la bière").

**Related Tools**: association_rules_tools

## Description de la tâche
Identifier des motifs d'achat fréquents (co-occurrences) dans un ensemble de transactions (ex: "ceux qui achètent des couches achètent aussi de la bière").

## Algorithmes recommandés
- **Apriori** (via `mlxtend`) : Filtre les itemsets fréquents en calculant le support.
- **Règles d'Association** : Calcule la confiance (probabilité conditionnelle) et le **Lift** (force d'association). Un Lift > 1.0 indique une association supérieure au hasard.
