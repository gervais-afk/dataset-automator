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

# Détection automatique du preprocessing (full_pipeline pour supervisé, scaler pour clustering)
if 'full_pipeline' in globals():
    preprocessing_obj = full_pipeline
elif 'scaler' in globals():
    preprocessing_obj = scaler
else:
    preprocessing_obj = None

is_tabicl = "TabICL" in type(best_model).__name__

# Connexion au run actif de MLflow pour la traçabilité
import mlflow
import mlflow.pyfunc
import mlflow.sklearn

run = mlflow.active_run()

if is_tabicl:
    model_filename = f"pipeline_{NOM_BASE}_{datetime.now().strftime('%Y%m%d_%H%M')}.sav"
    model_path = os.path.join(MODELS_DIR, model_filename)
    best_model.save(model_path, save_model_weights=False, save_training_data=True, save_kv_cache=True)
    print(f"✅ Pipeline TabICL exporté avec succès via .save() : {model_path}")
    print(f"💡 Pour l'utiliser : from tabicl import TabICLClassifier; model = TabICLClassifier.load('{model_filename}')")
    
    if run:
        mlflow.log_artifact(model_path, artifact_path="model")
        try:
            # Création d'un wrapper PyFunc pour enregistrer le modèle TabICL dans le Model Registry MLflow
            class TabICLWrapper(mlflow.pyfunc.PythonModel):
                def load_context(self, context):
                    from tabicl import TabICLClassifier
                    import os
                    self.model = TabICLClassifier.load(context.artifacts["model_file"])
                def predict(self, context, model_input):
                    return self.model.predict(model_input)
            
            mlflow.pyfunc.log_model(
                artifact_path="model_tabicl",
                python_model=TabICLWrapper(),
                artifacts={"model_file": model_path},
                registered_model_name=f"model_{NOM_BASE}"
            )
            print(f"✅ Modèle TabICL enregistré dans le Model Registry MLflow sous : model_{NOM_BASE}")
        except Exception as e_reg:
            print(f"⚠️ Impossible d'enregistrer le modèle TabICL dans le Model Registry : {e_reg}")
else:
    if preprocessing_obj is not None:
        inference_pipeline = Pipeline([
            ('preprocessing_full', preprocessing_obj),
            ('champion_model', best_model)
        ])
    else:
        inference_pipeline = best_model

    model_filename = f"pipeline_{NOM_BASE}_{datetime.now().strftime('%Y%m%d_%H%M')}.joblib"
    model_path = os.path.join(MODELS_DIR, model_filename)

    # Correction pour le pickling des fonctions personnalisées dans __main__ sous exec/headless
    import sys
    if 'engineering_func' in globals():
        sys.modules['__main__'].engineering_func = globals()['engineering_func']

    # Essayer de sauvegarder au format skops sécurisé (Règle de robustesse)
    try:
        import skops.io as sio
        skops_path = model_path.replace('.joblib', '.skops')
        sio.dump(inference_pipeline, skops_path)
        print(f"✅ Pipeline exporté au format sécurisé skops : {skops_path}")
    except Exception as e_skops:
        print(f"⚠️ skops non disponible pour l'export sécurisé, utilisation de joblib ({e_skops})")
        
    joblib.dump(inference_pipeline, model_path)
    print(f"✅ Pipeline exporté avec succès : {model_path}")
    print(f"💡 Pour l'utiliser : model = joblib.load('{model_filename}')")

    if run:
        try:
            mlflow.sklearn.log_model(
                sk_model=inference_pipeline,
                artifact_path="model",
                registered_model_name=f"model_{NOM_BASE}"
            )
            print(f"✅ Modèle sklearn enregistré dans le Model Registry MLflow sous : model_{NOM_BASE}")
        except Exception as e_reg:
            print(f"⚠️ Impossible d'enregistrer le modèle dans le Model Registry : {e_reg}")
```

## 5.2 Anticipation de la Dérive (Drift Detection)

```python
print("\n📡 Configuration du Monitoring de Dérive (Théorique)")
print("-" * 60)

# Un senior met en place des outils comme EvidentlyAI ou Alibi-Detect.
# Voici une implémentation simplifiée de détection de dérive sur la cible (ou les features en clustering).

def detect_drift(new_data_stream, reference_mean, threshold=0.2):
    current_mean = np.mean(new_data_stream)
    drift_score = abs(current_mean - reference_mean) / (abs(reference_mean) + 1e-8)
    if drift_score > threshold:
        return True, drift_score
    return False, drift_score

# Trajectoire supervisée vs non-supervisée pour la dérive
if TYPE_TACHE == "unsupervised" or 'y_train' not in globals() or y_train is None:
    # Non-supervisé : Drift mesuré sur la première composante PCA ou feature
    if 'X_train_prep' in globals() and X_train_prep is not None:
        ref_mean = X_train_prep[:, 0].mean() if isinstance(X_train_prep, np.ndarray) else X_train_prep.iloc[:, 0].mean()
        print(f"📊 Moyenne de référence (Feature 0, Training) : {ref_mean:.4f}")
        test_stream = X_test_prep[:, 0] if isinstance(X_test_prep, np.ndarray) else X_test_prep.iloc[:, 0]
        has_drift, score = detect_drift(test_stream, ref_mean)
    else:
        ref_mean = 0.0
        has_drift, score = False, 0.0
else:
    ref_mean = y_train.mean()
    print(f"📊 Moyenne de référence (Target, Training) : {ref_mean:.4f}")
    has_drift, score = detect_drift(y_test, ref_mean)

if has_drift:
    print(f"🚨 ALERTE DRIFT : Dérive de {score:.1%} détectée !")
    print("👉 Action : Déclencher un ré-entraînement sur les nouvelles données.")
else:
    print(f"✅ Flux stable : Dérive de {score:.1%} (sous le seuil de 20%).")

print("\n🚀 SYSTÈME PRÊT POUR LE DÉPLOIEMENT (MLOps Ready)")
```
