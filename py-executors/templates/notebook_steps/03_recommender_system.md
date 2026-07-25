# 🎯 Étape 3 — Système de Recommandation (SVD Matrix Factorization)

Objectif : Prédire les préférences des utilisateurs pour des items non consommés à l'aide de la décomposition en valeurs singulières (SVD).

```python
import pandas as pd
import numpy as np
import os
from surprise import Dataset, Reader, SVD, accuracy
from surprise.model_selection import cross_validate, train_test_split
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🎯 RECOMMANDATION PERSONNALISÉE (SVD)")
print("=" * 60)

# Détection heuristique des colonnes de notations
# Colonnes attendues : user_id, item_id, rating
user_col = 'user_id'
item_col = 'item_id'
rating_col = globals().get('TARGET_COL') or 'rating'

# Fallback si colonnes absentes
if user_col not in df.columns:
    user_col = [c for c in df.columns if 'user' in c.lower() or 'client' in c.lower()][0]
if item_col not in df.columns:
    item_col = [c for c in df.columns if 'item' in c.lower() or 'product' in c.lower() or 'film' in c.lower() or 'article' in c.lower()][0]
if rating_col not in df.columns:
    rating_col = [c for c in df.columns if 'rate' in c.lower() or 'note' in c.lower() or 'score' in c.lower()][0]

print(f"📊 Mapping des colonnes : User = '{user_col}' | Item = '{item_col}' | Note = '{rating_col}'")

# ── 1. Préparation Surprise ───────────────────────────────────────────
reader = Reader(rating_scale=(df[rating_col].min(), df[rating_col].max()))
data = Dataset.load_from_df(df[[user_col, item_col, rating_col]], reader)

trainset, testset = train_test_split(data, test_size=0.2, random_state=42)

# ── 2. Entraînement SVD ────────────────────────────────────────────────
print("\n⏳ Entraînement de la Factorisation de Matrice SVD...")
algo = SVD(n_factors=50, n_epochs=20, lr_all=0.005, reg_all=0.02, random_state=42)
algo.fit(trainset)

# ── 3. Évaluation ─────────────────────────────────────────────────────
predictions = algo.test(testset)
rmse = accuracy.rmse(predictions)
mae = accuracy.mae(predictions)

print(f"\n📊 Métriques d'évaluation :")
print(f"   - RMSE : {rmse:.4f}")
print(f"   - MAE  : {mae:.4f}")

# Enregistrement pour l'orchestrateur
best_name = "SVD Matrix Factorization"
best_model = algo
results = {best_name: {"score": -rmse, "model": algo}}
y_pred = [p.est for p in predictions]
y_test = [p.r_ui for p in predictions]
```

### Recommandations Personnalisées (Test)

```python
# Sélection d'un utilisateur au hasard dans le test set
sample_user = predictions[0].uid
print(f"\n🔝 Génération de recommandations pour l'utilisateur : {sample_user}")

# Items déjà consommés
items_deja_vus = set(df[df[user_col] == sample_user][item_col])
tous_les_items = set(df[item_col])
candidates = tous_les_items - items_deja_vus

# Prédiction pour les items candidats
user_recs = []
for iid in list(candidates)[:200]: # Limiter à 200 candidats pour la rapidité
    pred_val = algo.predict(sample_user, iid).est
    user_recs.append((iid, pred_val))

recs_df = pd.DataFrame(user_recs, columns=[item_col, 'rating_pred']).sort_values('rating_pred', ascending=False)
display(recs_df.head(5))
```
