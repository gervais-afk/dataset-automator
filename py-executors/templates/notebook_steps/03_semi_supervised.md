# 🤖 Étape 3 — Apprentissage Semi-Supervisé (Label Spreading)

Objectif : Exploiter des données non étiquetées (marquées par la valeur -1) pour augmenter le jeu de données d'apprentissage grâce à la propagation de labels.

```python
import pandas as pd
import numpy as np
import os
from sklearn.semi_supervised import LabelSpreading
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import classification_report
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🤖 APPRENTISSAGE SEMI-SUPERVISÉ (Label Spreading)")
print("=" * 60)

# Détection de la cible
target_col = globals().get('TARGET_COL') or 'label'
if target_col not in df.columns:
    target_col = [c for c in df.columns if any(k in c.lower() for k in ['label', 'target', 'class'])][0]

X = df.drop(columns=[target_col])
y = df[target_col].values

# Diagnostic des étiquettes
n_labeled = np.sum(y != -1)
n_unlabeled = np.sum(y == -1)
print(f"📊 Données : Étiquetées = {n_labeled} | Non étiquetées (-1) = {n_unlabeled}")

# ── 1. Scaling des Caractéristiques ───────────────────────────────────
num_cols = X.select_dtypes(include=np.number).columns.tolist()
X_num = X[num_cols].fillna(X[num_cols].median())

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X_num)

# ── 2. Entraînement du Modèle Label Spreading ──────────────────────────
print("\n⏳ Lancement de l'algorithme de propagation des labels...")
model = LabelSpreading(kernel='knn', n_neighbors=7, alpha=0.2)
model.fit(X_scaled, y)

# Récupération des étiquettes finales
y_pred = model.transduction_
df['label_predit'] = y_pred

# ── 3. Évaluation sur les données initialement étiquetées ─────────────
print("\n📋 Évaluation de la propagation sur les étiquettes initialement connues :")
known_mask = y != -1
print(classification_report(y[known_mask], y_pred[known_mask]))

# Enregistrement pour l'orchestrateur
best_name = "Label Spreading"
best_model = model
results = {best_name: {"score": float(np.mean(y == y_pred)), "model": model}}
X_test_prep = X_scaled
y_test = y
```

### Visualisation de la Confiance de Propagation

```python
# Extraction des distributions de probabilité
probs = model.label_distributions_
confidences = probs.max(axis=1)

df_unlabeled_preds = pd.DataFrame({
    'prediction': y_pred[y == -1],
    'confiance': confidences[y == -1]
})

plt.figure(figsize=(10, 5))
df_unlabeled_preds['confiance'].hist(bins=30, color='teal', edgecolor='white')
plt.axvline(0.7, color='crimson', linestyle='--', label='Seuil de confiance minimum (70%)')
plt.title("Distribution de la Confiance de Propagation (Données Non Étiquetées)")
plt.xlabel("Confiance de prédiction")
plt.ylabel("Fréquence")
plt.legend()
plt.savefig(os.path.join(OUTPUT_DIR, '03_semi_supervised_confidence.png'), dpi=150)
plt.show()

# Proposer des candidats sûrs
print(f"💡 Nombre de nouveaux exemples sûrs (confiance > 90%) : {len(df_unlabeled_preds[df_unlabeled_preds['confiance'] > 0.9])}")
```
