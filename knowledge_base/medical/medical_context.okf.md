---
title: Contexte Métier Médical & Formules (OKF)
domain: medical
type: okf
formulas:
  - name: IMC
    formula: "Weight / (Height ** 2)"
    description: "Indice de Masse Corporelle (Body Mass Index) calculé à partir du poids (Weight) et de la taille (Height)."
    target_column: IMC
  - name: MAP
    formula: "(SysBP + 2 * DiaBP) / 3"
    description: "Pression Artérielle Moyenne (Mean Arterial Pressure) calculée à partir de la pression systolique (SysBP) et diastolique (DiaBP)."
    target_column: MAP
business_rules:
  recall_priority: true
  sensitive_attributes:
    - Gender
    - Age
performance_thresholds:
  min_f1_score: 0.80
  min_recall: 0.85
---

# Contexte Métier Médical & Formules (OKF)

Ce document de contexte au format OKF (Open Knowledge Format) définit les concepts cliniques clés, les formules arithmétiques standards et les exigences de performance pour le traitement automatisé des datasets médicaux.

## 🧮 Formules Métiers
Les formules déclarées ci-dessus dans le bloc de métadonnées doivent être injectées automatiquement par l'Agent Stratège sous forme d'étapes d'ingénierie de caractéristiques (AutoFE) et exécutées de façon sécurisée par l'exécuteur.

1. **Indice de Masse Corporelle (IMC)** : Permet d'évaluer la corpulence d'un individu et de catégoriser l'obésité ou la dénutrition.
2. **Pression Artérielle Moyenne (MAP)** : Indicateur de perfusion des organes vitaux utilisé en cardiologie et soins intensifs.
