---
title: Guide pour les Systèmes de Recommandation (Recommender Systems)
domain: recommendation
type: concept
---

# Guide pour les Systèmes de Recommandation (Recommender Systems)

**Definition**: Prédire les préférences des utilisateurs sur des items (produits, films, articles) en se basant sur les historiques de notations ou d'achats.

**Related Tools**: recommendation_tools

## Description de la tâche
Prédire les préférences des utilisateurs sur des items (produits, films, articles) en se basant sur les historiques de notations ou d'achats.

## Modèles recommandés
- **SVD (Singular Value Decomposition)** : Factorisation matricielle de la librairie `surprise` pour projeter les utilisateurs et les items dans un espace latent.
- **Filtrage collaboratif basé sur les items / utilisateurs**.

## Évaluation
- Métriques standard : **RMSE** et **MAE** de prédiction de note, et **Précision@K** pour le classement.
