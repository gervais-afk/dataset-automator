---
type: concept
title: SMOTE & ADASYN (Imbalanced Data)
domain: classification
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# SMOTE & ADASYN (Déséquilibre de Classes)

**Definition**: Techniques de sur-échantillonnage synthétique. Au lieu de dupliquer bêtement les données de la classe minoritaire, SMOTE crée de nouveaux exemples synthétiques en interpolant entre les points minoritaires existants.

**Related Tools**: imbalanced-learn (imblearn)

**Quand l'utiliser** :
- Le profil indique un fort déséquilibre de classes (ex: 95% classe 0, 5% classe 1).
- Le Guardrail rejette le pipeline car le `recall` de la classe minoritaire est à 0.0.
- **Attention :** SMOTE ne doit s'appliquer QUE sur le jeu d'entraînement (`X_train`), JAMAIS sur le jeu de test.

**Code Snippet** :
```python
from imblearn.over_sampling import SMOTE

# X_train et y_train doivent être préalablement encodés et sans valeurs manquantes
smote = SMOTE(random_state=42)
X_train_resampled, y_train_resampled = smote.fit_resample(X_train, y_train)
```
