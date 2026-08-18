---
type: concept
title: Analyse en Composantes Principales (PCA)
domain: preprocessing
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# PCA (Réduction de Dimensionnalité)

**Definition**: Technique mathématique qui transforme des variables corrélées en de nouvelles variables non corrélées (les composantes principales), triées par la variance qu'elles expliquent.

**Related Tools**: scikit-learn

**Quand l'utiliser** :
- Le profil montre un très grand nombre de colonnes numériques (`total_columns > 50`).
- Risque de malédiction de la dimensionnalité ou surapprentissage.
- **Attention** : Les données doivent ABSOLUMENT être standardisées (StandardScaler) avant d'appliquer la PCA.

**Code Snippet** :
```python
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# 1. Standardisation
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_train)

# 2. PCA pour garder 95% de la variance expliquée
pca = PCA(n_components=0.95, random_state=42)
X_pca = pca.fit_transform(X_scaled)
```
