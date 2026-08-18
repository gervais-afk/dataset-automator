---
type: decision_tree
title: supervised-ml-selection
domain: machine_learning
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Decision: Quel algorithme d'apprentissage supervisé choisir ?

**Root Consideration**: Format des données, taille et besoin d'interprétabilité

**Branches**:
- IF Tabular data, < 100 k rows, need fast results THEN Utiliser Random Forest ou XGBoost
- IF Need a probability + interpretability THEN Utiliser Logistic Regression (L2/L1)
- IF High-dimensional text / sparse features THEN Utiliser Naive Bayes ou Logistic Regression + TF-IDF
- IF Small dataset (< 5 k rows), non-linear boundary THEN Utiliser SVM (RBF kernel)
- IF Image / audio / video THEN Utiliser Pre-trained CNN ou ViT (fine-tune)
