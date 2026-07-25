---
title: Adversarial Validation
domain: validation
type: concept
---

# Adversarial Validation

**Definition**: L'Adversarial Validation est une technique avancée pour détecter la dérive de données (Data Drift) entre deux ensembles (ex: train vs test, ou historique vs récent). Elle consiste à entraîner un classificateur binaire (comme un RandomForestClassifier) pour tenter de distinguer l'origine des échantillons (classe 0 pour le train, classe 1 pour le test). Si l'AUC de ce modèle adversaire dépasse 0.6, cela prouve que le modèle distingue facilement les deux ensembles, confirmant ainsi une dérive temporelle ou structurelle.

**Related Tools**: scikit-learn, RandomForestClassifier

**Quand l'utiliser** :
- Lors de l'ingestion de nouveaux lots de données pour détecter un glissement de distribution (Phase 1.5).
- Pour identifier précisément les variables (features) responsables du drift à travers l'importance des variables du modèle adversaire.

**Code Snippet** :
```python
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import roc_auc_score

# Assigner les labels d'origine (0 pour train, 1 pour test)
df_train['is_test'] = 0
df_test['is_test'] = 1

combined = pd.concat([df_train, df_test])
X = combined.drop('is_test', axis=1)
y = combined['is_test']

# Classificateur adversaire
model = RandomForestClassifier(n_estimators=50, random_state=42)
model.fit(X, y)

# Calcul du score de détection (AUC)
auc = roc_auc_score(y, model.predict_proba(X)[:, 1])
if auc > 0.60:
    # Drift détecté : extraire les variables suspectes
    importances = model.feature_importances_
```
