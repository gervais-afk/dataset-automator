---
title: clustering-selection
domain: clustering
type: decision_tree
---

# Decision: Quel algorithme de clustering utiliser ?

**Root Consideration**: Forme attendue des clusters et présence d'outliers

**Branches**:
- IF Clusters are expected to be spherical, of equal size, and data lacks severe outliers THEN Utiliser K-Means
- IF Clusters have arbitrary/uneven shapes, or need to isolate noise/outliers THEN Utiliser DBSCAN
