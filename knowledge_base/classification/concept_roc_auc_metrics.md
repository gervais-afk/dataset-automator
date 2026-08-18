---
type: concept
title: Métriques Avancées (ROC-AUC & Precision-Recall)
domain: classification
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Métriques Avancées (ROC-AUC & Precision-Recall)

**Definition**: Métriques robustes au déséquilibre. L'Accuracy est trompeuse si 99% du dataset est de la classe 0 (prédire 0 donne 99% d'accuracy). 
Le F1-Macro donne un poids égal à chaque classe. La courbe Precision-Recall (PR-AUC) est la métrique ultime pour les classes ultra-minoritaires (ex: fraude).

**Related Tools**: scikit-learn

**Quand l'utiliser** :
- Systématiquement en classification déséquilibrée pour évaluer la qualité du modèle de façon objective.

**Code Snippet** :
```python
from sklearn.metrics import roc_auc_score, f1_score, average_precision_score

y_pred = model.predict(X_test)
y_proba = model.predict_proba(X_test)[:, 1] # Probabilité de la classe positive

macro_f1 = f1_score(y_test, y_pred, average='macro')
roc_auc = roc_auc_score(y_test, y_proba)
pr_auc = average_precision_score(y_test, y_proba)
```
