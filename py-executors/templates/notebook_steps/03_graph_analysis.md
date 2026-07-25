# 🕸️ Étape 3 — Analyse de Graphes et de Réseaux (Network Analysis)

Objectif : Modéliser les données sous forme de nœuds et de relations, mesurer les centralités (influence) et partitionner les communautés connexes (détection de structures/fraudes).

```python
import pandas as pd
import numpy as np
import os
import networkx as nx
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🕸️ ANALYSE DE RÉSEAUX & GRAPHES (NetworkX)")
print("=" * 60)

# Détection des colonnes Source / Target
src_col = 'source'
tgt_col = 'target'
weight_col = 'weight'

# Auto-détection
if src_col not in df.columns:
    src_col = [c for c in df.columns if any(k in c.lower() for k in ['src', 'source', 'from', 'node_1'])][0]
if tgt_col not in df.columns:
    tgt_col = [c for c in df.columns if any(k in c.lower() for k in ['tgt', 'target', 'to', 'node_2', 'dest'])][0]

has_weight = weight_col in df.columns or any('weight' in c.lower() for c in df.columns)
if has_weight and weight_col not in df.columns:
    weight_col = [c for c in df.columns if 'weight' in c.lower()][0]

print(f"📊 Variables : Nœud Source = '{src_col}' | Nœud Cible = '{tgt_col}' | Poids = '{weight_col if has_weight else 'Aucun'}'")

# ── 1. Construction du Graphe ─────────────────────────────────────────
if has_weight:
    G = nx.from_pandas_edgelist(df, source=src_col, target=tgt_col, edge_attr=weight_col)
else:
    G = nx.from_pandas_edgelist(df, source=src_col, target=tgt_col)

print(f"\n📈 Métriques structurelles globales :")
print(f"   - Nombre total de nœuds : {G.number_of_nodes()}")
print(f"   - Nombre total de liens : {G.number_of_edges()}")
print(f"   - Densité du réseau     : {nx.density(G):.4f}")
print(f"   - Coefficient de clustering moyen : {nx.average_clustering(G):.4f}")

# ── 2. Analyse des Centralités (Importance des Nœuds) ─────────────────
# Centralité d'intermédiarité (Betweenness Centrality - utile pour détecter les passerelles)
betweenness = nx.betweenness_centrality(G)
# PageRank (influence globale)
pagerank = nx.pagerank(G, weight=weight_col if has_weight else None)

top_influencers = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:5]
print("\n🔝 Top 5 des nœuds les plus influents (PageRank) :")
for node, score in top_influencers:
    print(f"   - Nœud '{node}' | Score : {score:.4f}")

# Enregistrement pour l'orchestrateur
best_name = "Network Graph Analysis"
best_model = G
results = {best_name: {"score": nx.density(G), "model": G}}
```

### Détection de Communautés & Visualisation

```python
# Essayer d'importer la communauté Louvain
try:
    import community as community_louvain
    partition = community_louvain.best_partition(G)
    n_communities = len(set(partition.values()))
    print(f"\n👥 Détection de Communautés (Algorithme de Louvain) :")
    print(f"   - Nombre de communautés détectées : {n_communities}")
    
    # Couleur des nœuds selon la communauté
    node_colors = [partition[n] for n in G.nodes()]
    has_communities = True
except ImportError:
    print("\n⚠️ 'python-louvain' non installé. Détection de communautés désactivée.")
    node_colors = 'teal'
    has_communities = False

# Tracé du Graphe
plt.figure(figsize=(12, 10))
pos = nx.spring_layout(G, seed=42)

nx.draw_networkx_nodes(
    G, pos,
    node_size=40,
    node_color=node_colors,
    cmap=plt.cm.tab20 if has_communities else None
)
nx.draw_networkx_edges(G, pos, alpha=0.2, edge_color='gray')
plt.title("Représentation Spatiale du Graphe (Réseau de connexions)")
plt.axis('off')
plt.savefig(os.path.join(OUTPUT_DIR, '03_network_graph.png'), dpi=150)
plt.show()
```
