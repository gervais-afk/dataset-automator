# 🕵️ Étape 3 — Détection d'Anomalies (Isolation Forest)

Objectif : Identifier les observations aberrantes ou suspectes dans le dataset en combinant Isolation Forest et réduction de dimension (PCA).

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
import os
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🕵️ DÉTECTION D'ANOMALIES (Isolation Forest)")
print("=" * 60)

# ── 1. Préparation & Normalisation ────────────────────────────────────
# Extraction des variables numériques pour la détection de distance/densité
num_cols = X_train.select_dtypes(include=np.number).columns.tolist()
X_train_num = X_train[num_cols].fillna(X_train[num_cols].median())
X_test_num = X_test[num_cols].fillna(X_train[num_cols].median())

scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_num)
X_test_scaled = scaler.transform(X_test_num)

# ── 2. Entraînement de l'Isolation Forest ──────────────────────────────
# Taux de contamination attendu (ex: 5%)
contamination_rate = 0.05
print(f"⏳ Entraînement du modèle (Contamination estimée : {contamination_rate*100}%)")

clf = IsolationForest(contamination=contamination_rate, random_state=42, n_estimators=100)
clf.fit(X_train_scaled)

# Scores de décision et labels (1 = normal, -1 = anomalie)
train_scores = clf.decision_function(X_train_scaled)
train_labels = clf.predict(X_train_scaled)

test_scores = clf.decision_function(X_test_scaled)
test_labels = clf.predict(X_test_scaled)

# ── 3. Analyse des Anomalies Détectées ────────────────────────────────
n_anomalies_test = (test_labels == -1).sum()
print(f"\n📊 Résumés des résultats (Test Set) :")
print(f"   - Total observations : {len(X_test)}")
print(f"   - Anomalies détectées : {n_anomalies_test} ({n_anomalies_test/len(X_test)*100:.2f}%)")

# Enregistrement pour l'orchestrateur
best_name = "Isolation Forest"
best_model = clf
results = {best_name: {"score": -float(n_anomalies_test), "model": clf}}
X_test_prep = X_test_scaled
y_pred = test_labels
```

### Visualisation PCA 2D des Anomalies

```python
# Projection 2D pour inspection visuelle
pca = PCA(n_components=2, random_state=42)
X_test_pca = pca.fit_transform(X_test_scaled)

plt.figure(figsize=(10, 7))
sns.scatterplot(
    x=X_test_pca[:, 0], y=X_test_pca[:, 1],
    hue=pd.Series(test_labels).map({1: 'Normal', -1: 'Anomalie'}),
    palette={'Normal': 'teal', 'Anomalie': 'crimson'},
    alpha=0.7, s=60
)
plt.title("Visualisation PCA des Anomalies Détectées (Test Set)")
plt.xlabel("PC1")
plt.ylabel("PC2")
plt.legend(title="Statut")
plt.grid(True, alpha=0.3)

# Sauvegarde
plt.savefig(os.path.join(OUTPUT_DIR, '03_anomaly_pca.png'), dpi=150, bbox_inches='tight')
plt.show()
```
