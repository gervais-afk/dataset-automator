---
type: concept
title: End-to-End MLOps Pipeline
domain: mlops
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# End-to-End MLOps Pipeline

## 1. Graph Context (Metadonnées pour Agents)
- **Concept Name**: End-to-End MLOps Pipeline
- **Category**: mlops
- **Is_A**: Architecture système
- **Requires**: [MLflow, FastAPI, Docker, DVC]
- **Solves**: [Dette technique du ML, Déploiement manuel, Manque de traçabilité des modèles]
- **Related_Concepts**: [Notebook-Driven Development, Feature Store, Model Registry]

## 2. Definition
Architecture complète et automatisée gérant l'intégralité du cycle de vie d'un modèle d'apprentissage automatique : de l'ingestion et versionnement des données à l'entraînement, le suivi (tracking), le registre de modèles, jusqu'à l'exposition via une API REST conteneurisée.

## 3. Composants typiques d'un pipeline complet
- **Tracking & Registre** : `MLflow` pour enregistrer les paramètres, métriques, et versions du modèle.
- **Déploiement API** : `FastAPI` pour créer des endpoints RESTful servant les prédictions.
- **Conteneurisation** : `Docker` pour empaqueter l'API, les dépendances et le modèle afin d'assurer l'isomorphisme entre les environnements.
- **Modélisation** : Frameworks performants comme `XGBoost`.

## 4. Pipeline d'Exécution Typique
1. Extraction des caractéristiques (Feature Engineering) et versionnement (DVC).
2. Entraînement du modèle et enregistrement dans MLflow (Logging).
3. Promotion du modèle (Staging -> Production) dans le Model Registry.
4. Construction de l'image Docker contenant le modèle et l'API FastAPI.
5. Déploiement (Canary ou Blue-Green) sur Kubernetes.
