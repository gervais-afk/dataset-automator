# ⏳ Étape 3 — Analyse de Survie (Kaplan-Meier & Cox PH)

Objectif : Modéliser le temps écoulé avant la survenue d'un événement (ex: désabonnement, panne) en prenant en compte les données censurées.

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from lifelines import KaplanMeierFitter, CoxPHFitter
from lifelines.statistics import logrank_test
import os
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("⏳ ANALYSE DE SURVIE (Kaplan-Meier & Cox PH)")
print("=" * 60)

# Détection automatique ou repli sur des colonnes de survie
# (duree_col doit contenir le temps écoulé, event_col doit être binaire 1/0)
duree_col = globals().get('DATE_COL') or 'duree_jours'
event_col = globals().get('TARGET_COL') or 'evenement'

# Vérification de l'existence des colonnes
if duree_col not in df.columns:
    # Recherche heuristique d'une colonne de durée
    durations = [c for c in df.columns if any(k in c.lower() for k in ['duree', 'duration', 'time', 'days', 'mois'])]
    duree_col = durations[0] if durations else df.select_dtypes(include=np.number).columns[0]

if event_col not in df.columns:
    events = [c for c in df.columns if any(k in c.lower() for k in ['churn', 'panpe', 'mort', 'death', 'event'])]
    event_col = events[0] if events else df.select_dtypes(include=[np.int64, np.int32, bool]).columns[0]

print(f"📊 Variables utilisées : Durée = '{duree_col}' | Événement = '{event_col}'")

# ── 1. Estimation Non-Paramétrique (Kaplan-Meier) ─────────────────────
kmf = KaplanMeierFitter()
kmf.fit(df[duree_col], event_observed=df[event_col], label="Population Globale")

plt.figure(figsize=(10, 6))
kmf.plot_survival_function(color='teal')
plt.title("Courbe de Rétention Globale (Kaplan-Meier)")
plt.xlabel("Temps")
plt.ylabel("Probabilité de Rétention / Survie")
plt.grid(True, alpha=0.3)
plt.savefig(os.path.join(OUTPUT_DIR, '03_survival_kaplan_meier.png'), dpi=150)
plt.show()

print(f"🥇 Temps médian de survie : {kmf.median_survival_time_} unités de temps")
```

### Modélisation Multi-variée de Cox (Hazard Ratios)

```python
# Sélection des caractéristiques numériques auxiliaires
num_feats = df.select_dtypes(include=np.number).columns.drop([duree_col, event_col], errors='ignore').tolist()
df_cox = df[num_feats + [duree_col, event_col]].dropna()

print(f"\n🔬 Ajustement du modèle de Cox PH sur {len(df_cox)} observations...")
cph = CoxPHFitter()
cph.fit(df_cox, duration_col=duree_col, event_col=event_col)
cph.print_summary()

plt.figure(figsize=(10, 5))
cph.plot()
plt.title("Ratios de Risque (Hazard Ratios) des Variables explicatives")
plt.axvline(1, color='red', linestyle='--')
plt.savefig(os.path.join(OUTPUT_DIR, '03_survival_cox_coefficients.png'), dpi=150)
plt.show()

# Enregistrement pour l'orchestrateur
best_name = "Cox Proportional Hazards"
best_model = cph
results = {best_name: {"score": float(cph.log_likelihood_), "model": cph}}
```
