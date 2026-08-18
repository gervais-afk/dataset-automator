---
type: decision_tree
title: clustering-selection
domain: clustering
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Decision: Quel algorithme de clustering utiliser ?

**Root Consideration**: Forme attendue des clusters et présence d'outliers

**Branches**:
- IF Clusters are expected to be spherical, of equal size, and data lacks severe outliers THEN Utiliser K-Means
- IF Clusters have arbitrary/uneven shapes, or need to isolate noise/outliers THEN Utiliser DBSCAN
