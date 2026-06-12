---
title: Notebook-Driven Development (NDD)
domain: dev_tools
type: concept
---

# Notebook-Driven Development (NDD)

## 1. Graph Context (Metadonnées pour Agents)
- **Concept Name**: Notebook-Driven Development (NDD)
- **Category**: dev_tools
- **Is_A**: Méthodologie de développement
- **Requires**: [Jupyter, Marimo, Jupytext, Papermill]
- **Solves**: [Friction de passage du POC à la Production, Reproductibilité, Silos entre Data Scientists et Data Engineers]
- **Related_Concepts**: [End-to-End MLOps Pipeline, Data Engineering]

## 2. Definition
Méthodologie prônant l'utilisation des notebooks comme composants de première classe dans les pipelines de production ML et Data Engineering. Au lieu de réécrire systématiquement le code exploratoire des notebooks en scripts Python purs, le NDD utilise des outils pour versionner, paramétrer, tester et orchestrer directement les notebooks.

## 3. Propriétés & Avantages
- **Agilité** : Maintient l'aspect exploratoire tout en appliquant les standards de l'ingénierie logicielle.
- **Transparence** : Les résultats (graphiques, tables) sont enregistrés avec le code, ce qui facilite l'audit.

## 4. Implémentation & Pipeline (Comment l'utiliser)
Pour appliquer le NDD dans un pipeline :
1. **Versionnement** : Utiliser `Jupytext` pour synchroniser le notebook avec un fichier texte pur (.py ou .md) afin d'utiliser Git proprement.
2. **Paramétrage** : Injecter des variables dynamiques à l'exécution avec des tags (ex: via `Papermill`).
3. **Orchestration** : Utiliser un orchestrateur (comme Apache Airflow) pour lancer le notebook avec différents paramètres selon les données du jour.
