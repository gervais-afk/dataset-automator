# 📊 Évaluation Comparative et Synthèse Clustering

```python
# ── Tableau Récapitulatif ─────────────────────────────────────────
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import glob, os
from IPython.display import display, Markdown

OUTPUT_DIR   = r"{OUTPUT_DIR}"
DATASET_NAME = "{DATASET_NAME}"
os.makedirs(OUTPUT_DIR, exist_ok=True)

if 'benchmark_results' not in dir() or not benchmark_results:
    print("⚠️  benchmark_results vide")
    benchmark_results = []

if benchmark_results:
    df_bench = pd.DataFrame([
        {"Algo": r["Algo"], "Silhouette": r["Silhouette"]}
        for r in benchmark_results
    ])
    print("\n📋 CLUSTERING BENCHMARK :")
    print(df_bench.sort_values("Silhouette", ascending=False).to_string(index=False))
```

### Visualisation du meilleur partitionnement

```python
if benchmark_results:
    best_idx    = int(np.argmax([r["Silhouette"] for r in benchmark_results]))
    best_algo   = benchmark_results[best_idx]["Algo"]
    best_labels = benchmark_results[best_idx]["labels"]
    best_sil    = float(benchmark_results[best_idx]["Silhouette"])
    print(f"🥇 Meilleur : {best_algo} (Silhouette={best_sil:.4f})")
else:
    best_algo, best_labels, best_sil = "N/A", np.array([]), 0.0

if 'X_pca' in dir() and len(best_labels) > 0:
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    sc = axes[0].scatter(X_pca[:, 0], X_pca[:, 1],
                         c=best_labels, cmap='viridis', s=40, alpha=0.7)
    axes[0].set_title(f"PCA 2D — {best_algo}")
    plt.colorbar(sc, ax=axes[0], label='Cluster')

    vals, cnts = np.unique(best_labels, return_counts=True)
    axes[1].bar([str(v) for v in vals], cnts, color='steelblue')
    axes[1].set_title("Répartition des Clusters")
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "04_evaluation_clustering.png"), dpi=120, bbox_inches="tight")
    plt.show()
```

### Profilage des Clusters

```python
if 'X_train' in dir() and len(best_labels) > 0:
    try:
        X_profil = pd.DataFrame(X_train) if not isinstance(X_train, pd.DataFrame) else X_train.copy()
        X_profil['Cluster'] = best_labels[:len(X_profil)]
        cluster_profile = X_profil.groupby('Cluster').mean(numeric_only=True)
        print("\n📊 Caractéristiques moyennes par cluster :")
        display(cluster_profile.round(3).style.background_gradient(cmap='YlGnBu'))
    except Exception as e:
        print(f"⚠️  Profilage : {e}")
```

## 📝 Synthèse Clustering

```python
n_clusters = len(np.unique(best_labels)) if len(best_labels) > 0 else "?"
qualite = (
    "🟢 Excellent" if best_sil > 0.50 else
    "🟡 Acceptable" if best_sil > 0.25 else
    "🔴 Faible"
)

# NOM_BASE injecté à la génération → devient une chaîne littérale dans le notebook
titre_dataset = "{NOM_BASE}"

rapport_lines = [
    f"## 📊 Rapport Clustering — {titre_dataset}",
    "",
    "| Critère | Valeur |",
    "|---------|--------|",
    f"| Meilleur algorithme | **{best_algo}** |",
    f"| Silhouette Score | **{best_sil:.4f}** — {qualite} |",
    f"| Nombre de clusters | **{n_clusters}** |",
    "",
    "### 🔧 Recommandations",
    "1. Valider la signification métier de chaque cluster",
    "2. Nommer les segments (ex: Utilisateur actif, Profil à risque)",
    "3. Appliquer au dataset complet pour la segmentation",
]
display(Markdown("\n".join(rapport_lines)))

figures = sorted(glob.glob(os.path.join(OUTPUT_DIR, "*.png")))
if figures:
    print(f"\n📊 {len(figures)} figure(s) :")
    for f in figures:
        print(f"   🖼️  {os.path.basename(f)}")

print("\n✅ ANALYSE CLUSTERING TERMINÉE")
```

## Rapport d'évaluation visuelle

{EVAL_PLOT}

