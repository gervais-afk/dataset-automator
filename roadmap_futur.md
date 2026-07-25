# 🗺️ Feuille de Route & Évolutions Futures - Dataset Automator

Ce document récapitule les fonctionnalités de niveau production à ajouter au pipeline lors des prochaines itérations.

---

## 🗹 1. Intégration de CatBoost au Benchmark
* **Objectif** : Améliorer les performances prédictives sur les jeux de données riches en catégories et textes courts.
* **Tâches** :
  * [ ] Installer `catboost` dans le `requirements.txt` des exécuteurs Python.
  * [ ] Importer `CatBoostClassifier` et `CatBoostRegressor` au sein de `server.py`.
  * [ ] Ajouter CatBoost à la liste des modèles évalués dans le benchmark initial de la Phase 3.5.
  * [ ] Configurer la grille de recherche d'hyperparamètres dans l'optimiseur Optuna (`optimize_hyperparameters`).

---

## 🗹 2. Audit d'Équité & Détection des Biais (Fairness)
* **Objectif** : Empêcher le déploiement de modèles biaisés ou discriminatoires sur des caractéristiques sensibles (Genre, Âge, Ethnie, etc.).
* **Tâches** :
  * [ ] Définir une liste de variables sensibles à surveiller (ex: `Gender`, `Age`).
  * [ ] Calculer l'**Impact Disparate (Disparate Impact Ratio)** lors de la phase d'évaluation.
  * [ ] Configurer un seuil d'équité strict (règle standard des 80% / 1.25) dans Neo4j.
  * [ ] Bloquer le pipeline ou lever une alerte de gouvernance en cas de non-respect du seuil d'équité.

---

## 🗹 3. Feature Engineering & Contextes Métiers via le format OKF (AutoFE)
* **Objectif** : Permettre à l'Agent Stratège de concevoir des variables dérivées validées (ex: IMC) en extrayant des formules mathématiques de référence stockées localement en format OKF (.okf.md) et synchronisées dans Neo4j.
* **Tâches** :
  * [ ] Créer le premier fichier de contexte OKF (ex: `medical_context.okf.md` pour l'obésité/diabète) définissant les métadonnées, formules de calcul (IMC), coûts métiers et seuils de performance.
  * [ ] Développer l'outil de parsing `okfReader.ts` pour lire et structurer les métadonnées et le markdown des fichiers OKF au démarrage de l'Orchestrateur.
  * [ ] Ajouter un attribut `formula` sur les nœuds de label `Concept` dans Neo4j (ex: `(:Concept {name: 'IMC', formula: 'Weight / (Height ** 2)'})`).
  * [ ] Lier ces concepts de formules aux nœuds `Domain` via la relation `BELONGS_TO` (ex: `(IMC)-[:BELONGS_TO]->(medical)`).
  * [ ] Modifier l'Orchestrateur TypeScript pour interroger les concepts de formules associés au domaine du dataset (ou lire le fichier local OKF correspondant).
  * [ ] Injecter ces formules récupérées dans le contexte (prompt utilisateur) envoyé à l'Agent Stratège.
  * [ ] Étendre le schéma JSON de la stratégie pour supporter l'action `"formula"`.
  * [ ] Développer un parseur d'expressions mathématiques sécurisé dans l'exécuteur Python (`server.py`) pour injecter et évaluer dynamiquement la formule dans le DataFrame Pandas.

---

## 🗹 4. Publication dans le Registre de Modèles MLflow (Model Registry)
* **Objectif** : Suivre le cycle de vie des modèles (Champion, Staging, Production) directement depuis l'interface MLflow.
* **Tâches** :
  * [ ] Activer le registre de modèles MLflow connecté à la base SQLite locale.
  * [ ] Ajouter une fonction d'enregistrement post-évaluation dans `server.py` via `mlflow.register_model()`.
  * [ ] Associer des tags automatiques au modèle (ex: `Dataset: Obesity`, `Accuracy: 0.84`, `Status: Champion`).
