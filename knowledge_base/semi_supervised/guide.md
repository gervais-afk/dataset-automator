---
title: Guide de l'Apprentissage Semi-Supervisé (Semi-Supervised)
domain: semi_supervised
type: concept
---

# Guide de l'Apprentissage Semi-Supervisé (Semi-Supervised)

**Definition**: Exploiter un grand volume de données non étiquetées (étiquettes notées `-1`) à l'aide d'un petit volume de données étiquetées initialement, réduisant le coût d'annotation manuelle.

**Related Tools**: semi_supervised_tools

## Description de la tâche
Exploiter un grand volume de données non étiquetées (étiquettes notées `-1`) à l'aide d'un petit volume de données étiquetées initialement, réduisant le coût d'annotation manuelle.

## Modèles recommandés
- **Label Spreading** (scikit-learn) : Utilise une structure de graphe KNN pour propager les étiquettes existantes vers les voisins proches de manière itérative.
- **Label Propagation**.

## Évaluation
- Analyse de la distribution des probabilités/confiances pour sélectionner les instances les plus sûres (Active Learning).
