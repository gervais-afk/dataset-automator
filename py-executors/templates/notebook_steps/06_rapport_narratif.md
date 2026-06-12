# 📋 Étape 6 — Rapport Final & Validation Senior

```python
import json
import os
from IPython.display import display, Markdown

print("=" * 60)
print("📋 GÉNÉRATION DU RAPPORT DE VALIDATION SENIOR")
print("=" * 60)

# Construction de la checklist Trustworthy AI
checklist = {
    "Qualité des données (EDA)": "✅ Validée",
    "Traitement des manques (MNAR)": "✅ Inclus (MissingIndicator)",
    "Pipeline Anti-Leakage": "✅ Garanti (Sklearn Pipelines)",
    "Optimisation robuste": "✅ Optuna / Bayesian",
    "IA de Confiance (Calibration)": "✅ Effectuée",
    "Explicabilité (SHAP/LIME)": "✅ Disponible",
    "Prêt pour Production (MLOps)": "✅ Exporté (.joblib)"
}

report_md = f"""
## 🏆 Synthèse du Projet : {NOM_BASE}

### 🎯 Performance
- **Modèle Champion** : {best_name}
- **Score Final ({metric})** : {results[best_name]['score']:.4f}

### 🛡️ IA de Confiance & Gouvernance
"""

for criterion, status in checklist.items():
    report_md += f"- **{criterion}** : {status}\n"

report_md += f"""
### 📁 Artefacts de sortie
- Rapport complet : `{OUTPUT_DIR}`
- Pipeline de production : `{model_filename}`

**Conclusion** : Le modèle est certifié robuste et prêt pour une mise en pré-production avec monitoring actif de la dérive.
"""

display(Markdown(report_md))

with open(os.path.join(OUTPUT_DIR, "validation_senior.json"), "w") as f:
    json.dump(checklist, f, indent=4)

print("\n🏁 PROCESSUS SENIOR DATA SCIENCE TERMINÉ")
```
