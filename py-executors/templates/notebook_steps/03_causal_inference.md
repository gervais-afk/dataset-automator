# 🔗 Étape 3 — Inférence Causale & Uplift Modeling

Objectif : Estimer l'effet incrémental d'un traitement (marketing, incitation) sur le comportement individuel (achat, churn) pour optimiser le retour sur investissement.

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from sklearn.model_selection import train_test_split
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🔗 INFÉRENCE CAUSALE & UPLIFT MODELING")
print("=" * 60)

# Détection des colonnes clés
# treatment_col: 1 si traité (a reçu l'offre), 0 sinon
# outcome_col: variable de résultat binaire ou continue (ex: conversion)
treatment_col = 'treatment'
outcome_col = globals().get('TARGET_COL') or 'conversion'

# Auto-détection
if treatment_col not in df.columns:
    treatment_col = [c for c in df.columns if any(k in c.lower() for k in ['treat', 'email', 'promo', 'offre', 'groupe'])][0]

if outcome_col not in df.columns:
    outcome_col = [c for c in df.columns if any(k in c.lower() for k in ['convert', 'conv', 'achat', 'clic', 'target'])][0]

feature_cols = [c for c in df.columns if c not in [treatment_col, outcome_col]]
print(f"📊 Variables : Traitement = '{treatment_col}' | Résultat = '{outcome_col}'")

# ── 1. Diagnostic d'équilibrage des groupes ───────────────────────────
print("\n⚖️ Équilibre des groupes d'étude (Moyennes des variables) :")
balance_df = df.groupby(treatment_col)[feature_cols[:4]].mean().T
display(balance_df)

# ── 2. Entraînement du modèle d'Uplift ────────────────────────────────
# Nous utilisons un Uplift Classifier (Uplift Random Forest ou T-Learner)
try:
    from causalml.inference.tree import UpliftRandomForestClassifier
    HAS_CAUSALML = True
except ImportError:
    HAS_CAUSALML = False
    print("⚠️ 'causalml' non installé. Utilisation d'un estimateur double de secours (T-Learner).")

# Split Train/Test
df_train, df_test = train_test_split(df, test_size=0.3, random_state=42)

X_tr = df_train[feature_cols].values
t_tr = df_train[treatment_col].values
y_tr = df_train[outcome_col].values

X_te = df_test[feature_cols].values
t_te = df_test[treatment_col].values
y_te = df_test[outcome_col].values

if HAS_CAUSALML:
    model = UpliftRandomForestClassifier(n_estimators=40, max_depth=5, random_state=42)
    model.fit(X_tr, treatment=t_tr, y=y_tr)
    uplift_te = model.predict(X_te)
    # causalml renvoie une matrice contenant les effets marginaux par rapport à chaque traitement
    if uplift_te.ndim > 1:
        uplift_te = uplift_te.flatten()
else:
    # Fallback T-Learner maison avec 2 modèles de forêt aléatoire
    from sklearn.ensemble import RandomForestClassifier
    m0 = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    m1 = RandomForestClassifier(n_estimators=50, max_depth=5, random_state=42)
    
    # Entraîner m0 sur le groupe de contrôle, m1 sur le groupe traité
    m0.fit(X_tr[t_tr == 0], y_tr[t_tr == 0])
    m1.fit(X_tr[t_tr == 1], y_tr[t_tr == 1])
    
    uplift_te = m1.predict_proba(X_te)[:, 1] - m0.predict_proba(X_te)[:, 1]
    model = (m0, m1)

df_test['uplift_score'] = uplift_te
print("\n✅ Modèle entraîné avec succès.")

# Enregistrement pour l'orchestrateur
best_name = "Uplift Model"
best_model = model
results = {best_name: {"score": float(np.mean(uplift_te)), "model": model}}
y_pred = uplift_te
y_test = y_te
```

### Évaluation par Gain Cumulatif (Qini)

```python
# Trier par score d'uplift décroissant
df_eval = df_test.sort_values('uplift_score', ascending=False).reset_index(drop=True)
df_eval['cum_treated'] = df_eval[treatment_col].cumsum()
df_eval['cum_untreated'] = (1 - df_eval[treatment_col]).cumsum()
df_eval['cum_y_treated'] = (df_eval[outcome_col] * df_eval[treatment_col]).cumsum()
df_eval['cum_y_untreated'] = (df_eval[outcome_col] * (1 - df_eval[treatment_col])).cumsum()

# Calcul du Qini index
df_eval['qini'] = df_eval['cum_y_treated'] - df_eval['cum_y_untreated'] * (df_eval['cum_treated'] / (df_eval['cum_untreated'] + 1e-6))

plt.figure(figsize=(10, 6))
plt.plot(df_eval['qini'].values, label="Modèle Uplift (Ciblage incrémental)", color="teal", lw=2)
# Ligne aléatoire
plt.plot([0, len(df_eval)], [0, df_eval['qini'].iloc[-1]], label="Aléatoire", linestyle="--", color="gray")
plt.title("Courbe de Gain Incremental (Qini)")
plt.xlabel("Nombre de clients ciblés (Triés par score)")
plt.ylabel("Achat incrémental cumulé")
plt.legend()
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(OUTPUT_DIR, '03_causal_qini_curve.png'), dpi=150)
plt.show()
```
