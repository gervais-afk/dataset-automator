---
title: dimensionality-reduction
domain: machine_learning
type: decision_tree
---

# Decision: Comment réduire la dimensionnalité (> 50 features) ?

**Root Consideration**: Objectif de la transformation

**Branches**:
- IF Besoin d'une transformation linéaire, rapide et réversible THEN Utiliser PCA
- IF Besoin de préserver la topologie locale et globale (non-linéaire) THEN Utiliser UMAP ou t-SNE
