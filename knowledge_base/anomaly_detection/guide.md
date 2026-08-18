---
type: concept
title: Guide de Détection d'Anomalies (Anomaly Detection)
domain: anomaly_detection
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Guide de Détection d'Anomalies (Anomaly Detection)

**Definition**: La détection d'anomalies consiste à identifier les observations aberrantes ou suspectes dans un jeu de données non étiqueté ou déséquilibré.

**Related Tools**: anomaly_detection_tools

## Description de la tâche
La détection d'anomalies consiste à identifier les observations aberrantes ou suspectes dans un jeu de données non étiqueté ou déséquilibré.

## Méthodes recommandées
1. **Isolation Forest** (Standard industriel) : Fonctionne par partitionnement récurrent. Les points faciles à isoler (faible profondeur) sont étiquetés comme des anomalies.
2. **Local Outlier Factor (LOF)** : Basé sur la densité locale par rapport aux voisins les plus proches.

## Preprocessing critique
- Un **scaling des variables** (StandardScaler ou RobustScaler) est obligatoire pour éviter que les variables à grande échelle ne dominent la détection.
- La réduction de dimension par **PCA** est très utile pour projeter les anomalies en 2D pour inspection visuelle humaine.
