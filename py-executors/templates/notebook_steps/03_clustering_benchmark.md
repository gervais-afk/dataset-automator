# 🏆 Benchmarking Non-Supervisé (Clustering) & Sélection de l'Optimal K

Conformément aux standards Senior, nous déterminons d'abord le nombre optimal de clusters ($K$) avant d'entraîner et de comparer les algorithmes de clustering.

## 🔍 1. Recherche du K Optimal (Elbow Method & Silhouette Analysis)

Nous évaluons les performances de K-Means pour des valeurs de $K$ allant de 2 à 8 en mesurant l'Inertie (Méthode de l'Elbow) et le Score de Silhouette.

```python
import time
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

print("🔍 Analyse de la structure géométrique du dataset...")
inertias = []
silhouettes = []
k_range = range(2, 9)

# Échantillonnage si le dataset est grand pour éviter des lenteurs de calcul de la silhouette
if X_train_prep.shape[0] > 10000:
    indices = np.random.RandomState(42).choice(X_train_prep.shape[0], 10000, replace=False)
    X_search = X_train_prep[indices]
else:
    X_search = X_train_prep

for k in k_range:
    km = KMeans(n_clusters=k, n_init=10, random_state=42)
    labels = km.fit_predict(X_search)
    inertias.append(km.inertia_)
    silhouettes.append(silhouette_score(X_search, labels))

# Sélection du meilleur K
best_k = int(k_range[np.argmax(silhouettes)])
print(f"🎯 Nombre optimal de clusters suggéré (max Silhouette) : K = {best_k}")

# Sauvegarde globale
best_k_global = best_k

# Tracé des graphiques d'analyse
fig, ax = plt.subplots(1, 2, figsize=(16, 5))

# Courbe d'Elbow
ax[0].plot(k_range, inertias, 'o-', color='steelblue', linewidth=2)
ax[0].set_title("Méthode de l'Elbow (Inertie Intra-classe)")
ax[0].set_xlabel("Nombre de clusters (K)")
ax[0].set_ylabel("Inertie")
ax[0].grid(True, alpha=0.3)
ax[0].axvline(best_k, color='red', linestyle='--', label=f'Optimal K = {best_k}')
ax[0].legend()

# Score de Silhouette
ax[1].plot(k_range, silhouettes, 'o-', color='forestgreen', linewidth=2)
ax[1].set_title("Score de Silhouette moyen")
ax[1].set_xlabel("Nombre de clusters (K)")
ax[1].set_ylabel("Score de Silhouette")
ax[1].grid(True, alpha=0.3)
ax[1].axvline(best_k, color='red', linestyle='--', label=f'Optimal K = {best_k}')
ax[1].legend()

plt.tight_layout()
plt.show()
```

## 🏆 2. Benchmarking des Modèles de Clustering (avec K optimal)

Nous comparons trois familles d'algorithmes de partitionnement configurés avec le nombre optimal de clusters déterminé ci-dessus :
1. **K-Means (Partitionnement)** : Basé sur les distances euclidiennes par rapport aux centroïdes.
2. **Clustering Hiérarchique (Connectivité)** : Approche agglomérative (Ward).
3. **GMM (Modèles de Mélange Gaussien - Probabiliste)** : Ajustement de distributions normales.

```python
from sklearn.cluster import AgglomerativeClustering
from sklearn.mixture import GaussianMixture

opt_k = best_k_global
print(f"🚀 Initialisation des modèles avec K = {opt_k}")

MODELES = {
    f"Baseline (K-Means)": KMeans(n_clusters=opt_k, n_init=10, random_state=42),
    "Hiérarchique"      : AgglomerativeClustering(n_clusters=opt_k),
    "GMM (Probabiliste)": GaussianMixture(n_components=opt_k, random_state=42),
}

results = {}
metric = "silhouette"

for name, model in MODELES.items():
    t0 = time.time()
    try:
        # Éviter la lenteur du clustering hiérarchique sur les grands datasets
        if name == "Hiérarchique" and X_train_prep.shape[0] > 10000:
            print(f"      ⚠️ Taille importante ({X_train_prep.shape[0]} lignes). Échantillonnage à 10 000 pour l'algorithme Hiérarchique.")
            indices = np.random.RandomState(42).choice(X_train_prep.shape[0], 10000, replace=False)
            model.fit(X_train_prep[indices])
        else:
            model.fit(X_train_prep)
            
        dt = (time.time() - t0) * 1000 # ms
        results[name] = {"score": 0.0, "time_ms": dt, "model": model} # score sera calculé lors de l'évaluation sur test set
        print(f"✅ {name:<20} entraîné avec succès | Latence: {dt:.1f}ms")
    except Exception as e:
        print(f"❌ {name:<20} | Erreur: {str(e)[:50]}")
```

## Comparatif Multi-dimensionnel

| Dimension | K-Means | Hiérarchique | GMM |
| :--- | :--- | :--- | :--- |
| **Type de Frontières** | Linéaires / Voronoï | Rigides / Arborescentes | Souples / Ellipsoïdales |
| **Sensibilité au Bruit** | Élevée (déplace les centroïdes) | Moyenne | Faible (géré par covariance) |
| **Complexité Temporelle** | Linéaire $O(N \cdot K)$ | Haute $O(N^2 \log N)$ | Moyenne (via EM) |
