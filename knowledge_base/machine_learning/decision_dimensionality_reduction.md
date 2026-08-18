---
type: decision_tree
title: dimensionality-reduction
domain: machine_learning
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Decision: Comment réduire la dimensionnalité (> 50 features) ?

**Root Consideration**: Objectif de la transformation

**Branches**:
- IF Besoin d'une transformation linéaire, rapide et réversible THEN Utiliser PCA
- IF Besoin de préserver la topologie locale et globale (non-linéaire) THEN Utiliser UMAP ou t-SNE
