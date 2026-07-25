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
    print("✨ Reconstruction de benchmark_results à partir des modèles entraînés...")
    benchmark_results = []
    if 'results' in dir() and results:
        from sklearn.metrics import silhouette_score
        for name, res in results.items():
            model = res["model"]
            try:
                if hasattr(model, "predict"):
                    labels = model.predict(X_test_prep)
                else:
                    labels = model.fit_predict(X_test_prep)
                
                n_uniq = len(np.unique(labels))
                if 1 < n_uniq < len(X_test_prep):
                    if len(X_test_prep) > 10000:
                        indices = np.random.RandomState(42).choice(len(X_test_prep), 10000, replace=False)
                        sil = silhouette_score(X_test_prep[indices], labels[indices])
                    else:
                        sil = silhouette_score(X_test_prep, labels)
                else:
                    sil = -1.0
                benchmark_results.append({
                    "Algo": name,
                    "Silhouette": sil,
                    "labels": labels,
                    "model": model
                })
                # Mettre à jour le score de silhouette dans le dictionnaire results global
                results[name]["score"] = sil
            except Exception as e:
                print(f"⚠️ Erreur silhouette pour {name} : {e}")

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
    best_model  = benchmark_results[best_idx].get("model", None)
    best_name   = best_algo  # Définir le modèle champion pour le rapport final
    print(f"🥇 Meilleur : {best_algo} (Silhouette={best_sil:.4f})")
else:
    best_algo, best_labels, best_sil, best_model = "N/A", np.array([]), 0.0, None
    best_name   = "N/A"

# Projection PCA du test set pour l'affichage (évite les erreurs de dimension si len(best_labels) != len(X_pca))
if 'pca_2d' in globals() and 'X_test_prep' in globals():
    X_pca_plot = pca_2d.transform(X_test_prep)
else:
    X_pca_plot = X_pca if 'X_pca' in globals() else None

if X_pca_plot is not None and len(best_labels) > 0:
    # ── Calcul du t-SNE pour comparaison non-linéaire ─────────────────────
    X_tsne = None
    try:
        from sklearn.manifold import TSNE
        print("⏳ Calcul du t-SNE (échantillon de 2000 points max)...")
        sample_size = min(2000, len(X_test_prep))
        indices_tsne = np.random.RandomState(42).choice(len(X_test_prep), sample_size, replace=False)
        X_tsne_sample = X_test_prep[indices_tsne]
        labels_tsne_sample = best_labels[indices_tsne]
        
        tsne = TSNE(n_components=2, perplexity=min(30, sample_size - 1), random_state=42)
        X_tsne = tsne.fit_transform(X_tsne_sample)
    except Exception as e_tsne:
        print(f"⚠️ Impossible de calculer le t-SNE : {e_tsne}")

    # Tracé des graphiques de partitionnement
    n_cols = 3 if X_tsne is not None else 2
    fig, axes = plt.subplots(1, n_cols, figsize=(6 * n_cols, 5.5))
    
    # 1. PCA 2D
    sc = axes[0].scatter(X_pca_plot[:, 0], X_pca_plot[:, 1],
                         c=best_labels, cmap='viridis', s=35, alpha=0.7)
    axes[0].set_title(f"PCA 2D — {best_algo}")
    axes[0].set_xlabel("PC1")
    axes[0].set_ylabel("PC2")
    fig.colorbar(sc, ax=axes[0], label='Cluster')
    
    # 2. t-SNE 2D (si disponible)
    if X_tsne is not None:
        sc2 = axes[1].scatter(X_tsne[:, 0], X_tsne[:, 1],
                              c=labels_tsne_sample, cmap='viridis', s=35, alpha=0.7)
        axes[1].set_title("t-SNE 2D (Visualisation non-linéaire)")
        axes[1].set_xlabel("t-SNE 1")
        axes[1].set_ylabel("t-SNE 2")
        fig.colorbar(sc2, ax=axes[1], label='Cluster')
        
    # 3. Barplot de répartition
    vals, cnts = np.unique(best_labels, return_counts=True)
    ax_bar = axes[-1]
    ax_bar.bar([str(v) for v in vals], cnts, color='steelblue', edgecolor='black', alpha=0.8)
    ax_bar.set_title("Répartition des Clusters")
    ax_bar.set_xlabel("Cluster")
    ax_bar.set_ylabel("Nombre d'individus")
    
    plt.tight_layout()
    plt.savefig(os.path.join(OUTPUT_DIR, "04_evaluation_clustering.png"), dpi=120, bbox_inches="tight")
    plt.show()
```

### Profilage des Clusters

> 💡 **Guide d'Interprétation du Graphique Radar & Centroïdes** :
> 1. **Tableau des caractéristiques moyennes** : Il montre la moyenne réelle de chaque variable pour chaque cluster. Les dégradés de couleur mettent en valeur les variables dominantes de chaque segment.
> 2. **Graphique Radar (Radar Chart)** : 
>    * Chaque branche représente une caractéristique (ex: *price*, *quantity*, *customer_age*).
>    * Les valeurs sont normalisées entre 0 (centre = valeur minimale du dataset) et 1 (bord extérieur = valeur maximale du dataset) pour comparer des unités différentes.
>    * **Lecture pratique** : Si le trait d'un cluster s'étire vers le bord extérieur d'un axe, cela montre que ce groupe de clients a une valeur très élevée pour cette caractéristique. S'il reste proche du centre, elle est faible. Par exemple, un cluster étiré sur *price* et *total_amount* représentera le segment des *"Acheteurs VIP"*.
>    * Cela vous permet d'identifier l'identité de chaque groupe et de définir des actions marketing ciblées.

```python
if 'X_test' in dir() and len(best_labels) > 0:
    try:
        X_profil = pd.DataFrame(X_test) if not isinstance(X_test, pd.DataFrame) else X_test.copy()
        X_profil['Cluster'] = best_labels
        cluster_profile = X_profil.groupby('Cluster').mean(numeric_only=True)
        print("\n📊 Caractéristiques moyennes par cluster (Jeu d'évaluation) :")
        display(cluster_profile.round(3).style.background_gradient(cmap='YlGnBu'))
        
        # ── Graphique Radar des Centroïdes (Profilage) ────────────────────────
        # On restreint aux 6 variables numériques les plus intéressantes pour la lisibilité
        num_cols = [c for c in cluster_profile.columns if not c.startswith('log_') and not c.startswith('feat_')]
        features_to_plot = num_cols[:6] if len(num_cols) >= 3 else list(cluster_profile.columns[:6])
        
        if len(features_to_plot) >= 3:
            print("\n🎯 Tracé du Profil Multidimensionnel des Clusters...")
            # Normalisation MinMax pour l'échelle du graphique radar
            c_min = cluster_profile[features_to_plot].min()
            c_max = cluster_profile[features_to_plot].max()
            profile_norm = (cluster_profile[features_to_plot] - c_min) / (c_max - c_min + 1e-6)
            
            labels_radar = list(features_to_plot)
            num_vars = len(labels_radar)
            angles = np.linspace(0, 2 * np.pi, num_vars, endpoint=False).tolist()
            angles += angles[:1] # Boucler la ligne
            
            fig, ax = plt.subplots(figsize=(7, 7), subplot_kw=dict(polar=True))
            for cluster_id in profile_norm.index:
                values = profile_norm.loc[cluster_id].tolist()
                values += values[:1]
                ax.plot(angles, values, linewidth=1.5, linestyle='solid', label=f'Cluster {cluster_id}')
                ax.fill(angles, values, alpha=0.1)
                
            ax.set_theta_offset(np.pi / 2)
            ax.set_theta_direction(-1)
            ax.set_thetagrids(np.degrees(angles[:-1]), labels_radar)
            plt.title("🎯 Profil Multidimensionnel des Clusters (Radar Chart)", y=1.1, fontsize=12)
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.1))
            plt.savefig(os.path.join(OUTPUT_DIR, "04_cluster_radar.png"), dpi=120, bbox_inches="tight")
            plt.show()
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

# ── 4.5 Diagnostics du Data Scientist Senior (Automatisés)
print("\n" + "=" * 60)
print("🧠 DIAGNOSTICS DE ROBUSTESSE (SENIOR DATA SCIENCE AUDIT)")
print("=" * 60)
print(f"✅ Silhouette Score : {best_sil:.4f} | Algorithme Champion : {best_algo}")
if best_sil < 0.25:
    print("   🚨 ALERTE COHÉRENCE : Le score de silhouette est faible (< 0.25).")
    print("   → Les clusters se chevauchent fortement et la segmentation n'est pas nette.")
    print("   → Recommandation : Essayer de réduire les dimensions (PCA/UMAP) ou réévaluer le nombre de clusters.")
else:
    print("   ✅ Robustesse : Les clusters ont une bonne séparation structurelle.")

print("\n✅ ANALYSE CLUSTERING TERMINÉE")
```

## Rapport d'évaluation visuelle

{EVAL_PLOT}

## 🧠 Rapport d'Interprétation Qualitatif RAG (Agent IA Senior)

{LLM_INTERPRETATION}

