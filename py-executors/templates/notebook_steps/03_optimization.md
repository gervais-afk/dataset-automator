# 📐 Étape 3 — Optimisation sous Contraintes (Recherche Opérationnelle)

Objectif : Allouer au mieux des ressources limitées (budget, temps, personnel) pour maximiser le profit ou minimiser le coût en résolvant un programme linéaire.

```python
import pulp
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("📐 OPTIMISATION DES RESSOURCES (PuLP)")
print("=" * 60)

# ── 1. Formalisation du Problème ──────────────────────────────────────
# Exemple : Allocation budget marketing sur 3 canaux
canaux = ['SEO', 'Google_Ads', 'Social_Media']
roi_estim = [2.5, 1.8, 3.2] # ROI par canal (ex: 1€ investi rapporte 2.50€)
min_spends = [1000, 500, 200] # Limite inférieure de dépenses
max_spends = [5000, 3000, 4000] # Limite supérieure de dépenses
budget_total = 8000 # Contrainte de budget global

print("📋 Paramètres d'optimisation :")
print(f"   - Canaux : {canaux}")
print(f"   - Budget total disponible : {budget_total} €")

# Problème de maximisation
prob = pulp.LpProblem("Maximisation_ROI_Marketing", pulp.LpMaximize)

# ── 2. Définition des Variables de Décision ───────────────────────────
x = {}
for i, c in enumerate(canaux):
    x[c] = pulp.LpVariable(c, lowBound=min_spends[i], upBound=max_spends[i], cat='Continuous')

# ── 3. Fonction Objectif (ROI à maximiser) ────────────────────────────
prob += pulp.lpSum([roi_estim[i] * x[c] for i, c in enumerate(canaux)]), "ROI_Total"

# ── 4. Contraintes ────────────────────────────────────────────────────
prob += pulp.lpSum([x[c] for c in canaux]) <= budget_total, "Budget_Global"

# ── 5. Résolution ─────────────────────────────────────────────────────
print("\n⏳ Résolution du programme linéaire...")
status = prob.solve()
print(f"   - Statut de la solution : {pulp.LpStatus[status]}")

# Affichage des résultats
for c in canaux:
    print(f"   👉 Budget optimal alloué à {c} : {x[c].varValue:,.2f} €")
print(f"🥇 ROI Total attendu : {pulp.value(prob.objective):,.2f} €")

# Enregistrement pour l'orchestrateur
best_name = "PuLP Optimization Solver"
results = {best_name: {"score": pulp.value(prob.objective), "model": prob}}
```

### Analyse de Sensibilité & Coûts Marginaux

```python
# Sensibilité des contraintes (Shadow Price / Prix d'ombre)
print("\n🔬 Analyse de sensibilité (Shadow Prices) :")
sensitivity_data = []
for name, c in prob.constraints.items():
    print(f"   - Contrainte '{name}' | Shadow Price : {c.pi:.3f} | Slack : {c.slack:.1f}")
    sensitivity_data.append({"Contrainte": name, "Shadow Price": c.pi, "Slack": c.slack})

# Graphique de l'allocation optimale
allocs = {c: x[c].varValue for c in canaux}
plt.figure(figsize=(8, 5))
plt.bar(allocs.keys(), allocs.values(), color='teal', edgecolor='black', alpha=0.8)
plt.ylabel("Budget Alloué (€)")
plt.title(f"Allocation optimale du Budget (Gain = {pulp.value(prob.objective):,.2f} €)")
plt.savefig(os.path.join(OUTPUT_DIR, '03_pulp_allocation.png'), dpi=150)
plt.show()
```
