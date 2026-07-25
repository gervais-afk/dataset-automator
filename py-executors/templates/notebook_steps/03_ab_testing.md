# 🧪 Étape 3 — Tests A/B & Design Expérimental

Objectif : Comparer scientifiquement deux versions (A et B) pour valider une différence significative sur une métrique clé (conversion, panier moyen).

```python
import pandas as pd
import numpy as np
import os
from scipy import stats
import statsmodels.api as sm
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("🧪 TESTS A/B STATISTIQUES")
print("=" * 60)

# Détection des groupes et de la métrique
group_col = 'group'
metric_col = globals().get('TARGET_COL') or 'conversion'

if group_col not in df.columns:
    group_col = [c for c in df.columns if any(k in c.lower() for k in ['group', 'variant', 'version', 'test'])][0]
    
if metric_col not in df.columns:
    metric_col = [c for c in df.columns if any(k in c.lower() for k in ['convert', 'conv', 'valeur', 'click', 'revenue'])][0]

print(f"📊 Variables utilisées : Groupe = '{group_col}' | Métrique = '{metric_col}'")

# ── 1. Statistiques Descriptives & Intervalles de Confiance ───────────
print("\n📊 1. Statistiques par Groupe :")
group_stats = df.groupby(group_col)[metric_col].agg(['mean', 'std', 'count', 'sum'])
group_stats['erreur_std'] = group_stats['std'] / np.sqrt(group_stats['count'])
# Marge d'erreur à 95%
group_stats['marge_95'] = 1.96 * group_stats['erreur_std']
display(group_stats)

# ── 2. Test d'Hypothèse Statistique ──────────────────────────────────
val_A = df[df[group_col] == 'A'][metric_col] if 'A' in df[group_col].unique() else df[df[group_col] == df[group_col].unique()[0]][metric_col]
val_B = df[df[group_col] == 'B'][metric_col] if 'B' in df[group_col].unique() else df[df[group_col] == df[group_col].unique()[1]][metric_col]

is_binary = df[metric_col].nunique() <= 2

if is_binary:
    # Z-Test pour Proportions
    from statsmodels.stats.proportion import proportions_ztest
    stat, p_val = proportions_ztest([val_A.sum(), val_B.sum()], [len(val_A), len(val_B)])
    test_name = "Z-test (Proportions)"
else:
    # T-Test indépendant de Welch (variances inégales)
    stat, p_val = stats.ttest_ind(val_A, val_B, equal_var=False)
    test_name = "T-test (Moyennes de Welch)"

print(f"\n🔬 2. Analyse Statistique :")
print(f"   - Test appliqué : {test_name}")
print(f"   - Statistique   : {stat:.4f}")
print(f"   - p-value       : {p_val:.6f}")

# ── 3. Taille d'Effet (Cohen's d) ────────────────────────────────────
pooled_std = np.sqrt(((len(val_A) - 1) * val_A.var() + (len(val_B) - 1) * val_B.var()) / (len(val_A) + len(val_B) - 2))
cohens_d = (val_B.mean() - val_A.mean()) / pooled_std
print(f"   - Taille de l'effet (Cohen's d) : {cohens_d:.4f} (0.2=faible, 0.5=moyen, 0.8=fort)")

# Enregistrement pour l'orchestrateur
best_name = "A/B Hypothesis Test"
results = {best_name: {"score": -p_val, "model": stat}}
```

### Visualisation des Différences de Performance

```python
plt.figure(figsize=(10, 6))
sns.barplot(data=df, x=group_col, y=metric_col, ci=95, capsize=0.1, palette='Set2')
plt.title(f"Comparaison de la Métrique par Groupe (p-value = {p_val:.4f})")
plt.ylabel(f"Moyenne de {metric_col} (avec IC 95%)")
plt.savefig(os.path.join(OUTPUT_DIR, '03_ab_test_comparison.png'), dpi=150)
plt.show()

# Conclusion
alpha = 0.05
if p_val < alpha:
    print(f"✅ RÉSULTAT SIGNIFICATIF : Il y a moins de {alpha*100}% de chances que cette différence soit due au hasard.")
else:
    print("❌ RÉSULTAT NON SIGNIFICATIF : Aucune différence statistiquement prouvable.")
```
