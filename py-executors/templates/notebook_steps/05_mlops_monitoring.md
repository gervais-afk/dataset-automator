# 🚀 Étape 5 — MLOps : Mise en Production & Monitoring

Objectif : Préparer le modèle pour le monde réel et anticiper sa dégradation.

## 5.1 Packaging & Exportation du Pipeline

```python
import joblib
import os
from datetime import datetime
from sklearn.pipeline import Pipeline

# Création de l'artefact complet (Preprocessing + Modèle)
print("📦 Création de l'artefact de production...")

# On encapsule tout dans un pipeline final pour l'inférence simple
inference_pipeline = Pipeline([
    ('preprocessing_full', full_pipeline),
    ('champion_model', best_model)
])

model_filename = f"pipeline_{NOM_BASE}_{datetime.now().strftime('%Y%m%d_%H%M')}.joblib"
model_path = os.path.join(MODELS_DIR, model_filename)

joblib.dump(inference_pipeline, model_path)

print(f"✅ Pipeline exporté avec succès : {model_path}")
print(f"💡 Pour l'utiliser : model = joblib.load('{model_filename}')")
```

## 5.2 Anticipation de la Dérive (Drift Detection)

```python
print("\n📡 Configuration du Monitoring de Dérive (Théorique)")
print("-" * 60)

# Un senior met en place des outils comme EvidentlyAI ou Alibi-Detect.
# Voici une implémentation simplifiée de détection de dérive sur la cible.

def detect_drift(new_data_stream, reference_mean, threshold=0.2):
    current_mean = np.mean(new_data_stream)
    drift_score = abs(current_mean - reference_mean) / reference_mean
    if drift_score > threshold:
        return True, drift_score
    return False, drift_score

ref_mean = y_train.mean()
print(f"📊 Moyenne de référence (Training) : {ref_mean:.4f}")

# Simulation d'un nouveau flux (le test set)
has_drift, score = detect_drift(y_test, ref_mean)

if has_drift:
    print(f"🚨 ALERTE DRIFT : Dérive de {score:.1%} détectée sur la cible !")
    print("👉 Action : Déclencher un ré-entraînement sur les nouvelles données.")
else:
    print(f"✅ Flux stable : Dérive de {score:.1%} (sous le seuil de 20%).")

print("\n🚀 SYSTÈME PRÊT POUR LE DÉPLOIEMENT (MLOps Ready)")
```
