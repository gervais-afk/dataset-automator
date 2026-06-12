---
title: supervised-ml-selection
domain: machine_learning
type: decision_tree
---

# Decision: Quel algorithme d'apprentissage supervisé choisir ?

**Root Consideration**: Format des données, taille et besoin d'interprétabilité

**Branches**:
- IF Tabular data, < 100 k rows, need fast results THEN Utiliser Random Forest ou XGBoost
- IF Need a probability + interpretability THEN Utiliser Logistic Regression (L2/L1)
- IF High-dimensional text / sparse features THEN Utiliser Naive Bayes ou Logistic Regression + TF-IDF
- IF Small dataset (< 5 k rows), non-linear boundary THEN Utiliser SVM (RBF kernel)
- IF Image / audio / video THEN Utiliser Pre-trained CNN ou ViT (fine-tune)
