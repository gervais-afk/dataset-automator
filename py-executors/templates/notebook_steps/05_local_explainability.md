# 🔍 Explicabilité Locale de Prédiction Individuelle (LIME)

Objectif : Expliquer une décision unitaire (par exemple, le cas spécifique d'un client) pour éviter l'effet "boîte noire". Nous appliquons la méthode LIME (Local Interpretable Model-agnostic Explanations) en simulant des profils alternatifs autour de notre instance cible pour identifier l'influence exacte de chaque caractéristique sur sa prédiction.

```python
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler
import warnings
warnings.filterwarnings("ignore")

print("=" * 60)
print("🔬 EXPLICATION LOCALE D'UNE PRÉDICTION AVEC LIME")
print("=" * 60)

# index de la ligne à expliquer (vous pouvez modifier cet index !)
row_index = 0

if row_index >= len(X_test):
    print(f"⚠️ Index {row_index} hors limites. Sélection de la première ligne de test (index 0).")
    row_index = 0

# 1. Sélectionner l'instance cible dans les données de test
target_instance = X_test.iloc[row_index]
instance_df = pd.DataFrame([target_instance])
print(f"🎯 Explication du profil à l'index de test {row_index} :")
display(instance_df)

# Extraction du prétraitement du pipeline si présent, sinon fallback sur full_pipeline
preprocessing_step = None
final_estimator = best_model
if hasattr(best_model, "steps"):
    final_estimator = best_model.steps[-1][1]
    from sklearn.pipeline import Pipeline
    preprocessing_step = Pipeline(best_model.steps[:-1])
elif 'full_pipeline' in globals():
    preprocessing_step = full_pipeline

if preprocessing_step is not None:
    X_train_prep = preprocessing_step.transform(X_train)
    instance_prep = preprocessing_step.transform(instance_df)
else:
    X_train_prep = X_train.values if isinstance(X_train, pd.DataFrame) else X_train
    instance_prep = instance_df.values

# 2. Prédire la valeur/classe pour ce profil (en gérant si best_model est un pipeline ou un estimateur brut)
pred_input = instance_df if hasattr(best_model, "steps") else instance_prep

if '{TACHE_ML}' == 'classification':
    pred_probs = best_model.predict_proba(pred_input)[0]
    pred_class = int(np.argmax(pred_probs))
    print(f"🔮 Classe prédite par le champion : {pred_class} (Probabilité : {pred_probs[pred_class]:.4f})")
else:
    pred_val = best_model.predict(pred_input)[0]
    print(f"🔮 Valeur prédite par le champion : {pred_val:.4f}")

# 3. Standardisation locale pour le calcul de distance
scaler = StandardScaler()
X_train_scaled = scaler.fit_transform(X_train_prep)
instance_scaled = scaler.transform(instance_prep)[0]

# 4. Générer des perturbations locales (1000 exemples légèrement bruités)
num_perturbations = 1000
perturbations_scaled = np.random.normal(0, 0.4, size=(num_perturbations, X_train_prep.shape[1])) + instance_scaled
perturbations_prep = scaler.inverse_transform(perturbations_scaled)

# 5. Prédire les perturbations avec le modèle final
if '{TACHE_ML}' == 'classification' and hasattr(final_estimator, "predict_proba"):
    y_perturbed = final_estimator.predict_proba(perturbations_prep)[:, pred_class]
else:
    y_perturbed = final_estimator.predict(perturbations_prep)

# 6. Calculer les distances et les poids
distances = np.sqrt(np.sum((perturbations_scaled - instance_scaled) ** 2, axis=1))
kernel_width = np.sqrt(X_train_prep.shape[1]) * 0.75
weights = np.exp(-(distances ** 2) / (kernel_width ** 2))

# 7. Ajuster la régression Ridge locale
local_model = Ridge(alpha=1.0)
local_model.fit(perturbations_scaled, y_perturbed, sample_weight=weights)
coefficients = local_model.coef_

# 8. Récupérer les noms des caractéristiques après prétraitement
if preprocessing_step is not None:
    if hasattr(preprocessing_step, "get_feature_names_out"):
        try:
            features = list(preprocessing_step.get_feature_names_out())
        except Exception:
            features = [f"col_{i}" for i in range(X_train_prep.shape[1])]
    else:
        # Essayer de prendre la dernière étape du préprocesseur
        last_prep = preprocessing_step.steps[-1][1]
        if hasattr(last_prep, "get_feature_names_out"):
            try:
                features = list(last_prep.get_feature_names_out())
            except Exception:
                features = [f"col_{i}" for i in range(X_train_prep.shape[1])]
        else:
            features = [f"col_{i}" for i in range(X_train_prep.shape[1])]
else:
    features = X_train.columns.tolist()

sorted_indices = np.argsort(np.abs(coefficients))

plt.figure(figsize=(10, 6))
colors = ['#2ca02c' if coef >= 0 else '#d62728' for coef in coefficients[sorted_indices]]
plt.barh([features[i] for i in sorted_indices], coefficients[sorted_indices], color=colors)
plt.axvline(x=0, color='black', linestyle='--')
plt.title(f"Explication Locale LIME - Profil Index {row_index}\n(Barres vertes = favorisent la prédiction | Barres rouges = la défavorisent)")
plt.xlabel("Force de contribution locale (standardisée)")
plt.grid(axis='x', linestyle=':', alpha=0.6)
plt.show()

# 9. Afficher les règles de décision textuelles
print("\n📝 Détails des contributions locales :")
for i in reversed(sorted_indices):
    direction = "favorise" if coefficients[i] >= 0 else "défavorise"
    print(f"   • {features[i]:<25} : {coefficients[i]:+.4f} ({direction} la prédiction)")
```
