# 🧺 Étape 3 — Analyse des Règles d'Association (Market Basket Analysis)

Objectif : Découvrir des associations d'achat récurrentes (ex: "les clients qui achètent A achètent aussi B") pour guider le placement de produits ou les promotions.

```python
import pandas as pd
import numpy as np
import os
from mlxtend.frequent_patterns import apriori, association_rules
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🧺 ANALYSE DU PANIER D'ACHATS (Apriori)")
print("=" * 60)

# Détection des colonnes transaction et item
tx_col = 'transaction_id'
item_col = 'item'

if tx_col not in df.columns:
    tx_col = [c for c in df.columns if any(k in c.lower() for k in ['tx', 'trans', 'id', 'panier', 'basket'])][0]
if item_col not in df.columns:
    item_col = [c for c in df.columns if any(k in c.lower() for k in ['item', 'product', 'produit', 'article'])][0]

print(f"📊 Columns utilisées : Transaction ID = '{tx_col}' | Item = '{item_col}'")

# ── 1. Transformation en Format Binaire ───────────────────────────────
print("\n⏳ Conversion des transactions en matrice d'encodage binaire...")
basket = df.groupby([tx_col, item_col])[item_col].count().unstack().fillna(0)
basket = basket.applymap(lambda x: 1 if x > 0 else 0)

print(f"   - Paniers analysés : {basket.shape[0]}")
print(f"   - Produits distincts : {basket.shape[1]}")

# ── 2. Algorithme Apriori (Extraction itemsets) ───────────────────────
min_supp = 0.03
print(f"\n⏳ Application de l'algorithme Apriori (Support minimal = {min_supp*100}%)...")
frequent_itemsets = apriori(basket, min_support=min_supp, use_colnames=True)
print(f"   ✅ {len(frequent_itemsets)} itemsets fréquents trouvés.")

# ── 3. Génération des règles d'association ────────────────────────────
min_conf = 0.5
print(f"⏳ Génération des règles (Confiance minimale = {min_conf*100}%)...")
rules = association_rules(frequent_itemsets, metric="confidence", min_threshold=min_conf)
rules = rules.sort_values('lift', ascending=False)

print(f"   ✅ {len(rules)} règles générées.")
display(rules[['antecedents', 'consequents', 'support', 'confidence', 'lift']].head(10))

# Enregistrement pour l'orchestrateur
best_name = "Apriori Association Rules"
results = {best_name: {"score": float(rules['lift'].max()) if not rules.empty else 0.0, "model": rules}}
```

### Cartographie des Règles (Support vs Confiance)

```python
if not rules.empty:
    plt.figure(figsize=(10, 6))
    sc = plt.scatter(rules['support'], rules['confidence'], c=rules['lift'], cmap='coolwarm', alpha=0.8, s=50)
    plt.colorbar(sc, label='Lift')
    plt.xlabel('Support (Fréquence relative)')
    plt.ylabel('Confiance (Force de la règle)')
    plt.title("Cartographie des Règles d'Association")
    plt.grid(True, alpha=0.3)
    plt.savefig(os.path.join(OUTPUT_DIR, '03_association_rules_map.png'), dpi=150)
    plt.show()
else:
    print("⚠️ Aucune règle générée pour tracer le graphique.")
```
