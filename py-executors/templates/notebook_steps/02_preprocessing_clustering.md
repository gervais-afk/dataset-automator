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
X_train_inp = X_train_clean if 'X_train_clean' in globals() else X_train
X_test_inp  = X_test_clean if 'X_test_clean' in globals() else X_test

num_cols = X_train_inp.select_dtypes(include=np.number).columns.tolist()
X_num    = X_train_inp[num_cols].fillna(X_train_inp[num_cols].median())

scaler = RobustScaler()
X_train_prep = scaler.fit_transform(X_num)
X_scaled = pd.DataFrame(X_train_prep, columns=num_cols)

# Préparation du test set si disponible
if 'X_test_inp' in globals() and X_test_inp is not None:
    X_test_num = X_test_inp[num_cols].fillna(X_train_inp[num_cols].median())
    X_test_prep = scaler.transform(X_test_num)
else:
    X_test_prep = X_train_prep

print(f"✅ Données d'entraînement prêtes : {X_train_prep.shape}")
print(f"✅ Données de test prêtes : {X_test_prep.shape}")

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
