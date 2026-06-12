# Preprocessing pour le Clustering

Dans cette étape, nous préparons les données en sélectionnant uniquement les variables numériques et en appliquant un scaling robuste.

```python
# ── Sélection et Nettoyage ─────────────────────────────────
import numpy  as np
import pandas as pd
from sklearn.preprocessing import RobustScaler
from sklearn.decomposition import PCA
import matplotlib.pyplot   as plt

print("⚙️  Extraction des colonnes numériques...")
num_cols = X_train.select_dtypes(include=np.number).columns.tolist()
X_num    = X_train[num_cols].fillna(X_num.median()) if 'X_num' in locals() else X_train[num_cols].fillna(X_train[num_cols].median())

scaler = RobustScaler()
X_scaled = pd.DataFrame(scaler.fit_transform(X_num), columns=num_cols)
print(f"✅ Données prêtes : {X_scaled.shape}")
```

### Visualisation Initiale (PCA)
Nous projetons les données en 2D pour voir s'il existe des groupes naturels.

```python
# ── Projection PCA 2D ─────────────────────────────────────
pca_2d = PCA(n_components=2, random_state=42)
X_pca  = pca_2d.fit_transform(X_scaled)
var_exp = pca_2d.explained_variance_ratio_.sum() * 100

plt.figure(figsize=(8, 6))
plt.scatter(X_pca[:, 0], X_pca[:, 1], alpha=0.5, s=20, c="#3498db")
plt.title(f"Projection PCA 2D — Avant Clustering\n(Variance expliquée : {var_exp:.1f}%)")
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.grid(True, alpha=0.3)
plt.show()
```
