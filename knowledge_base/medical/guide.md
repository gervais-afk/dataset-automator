---
type: concept
title: Guide d'Analyse de Données Cliniques & Médicales
domain: medical
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Guide d'Analyse de Données Cliniques & Médicales

Ce guide définit les contraintes et règles méthodologiques obligatoires lors de la manipulation de jeux de données médicaux ou cliniques.

## 🏥 La Priorité Absolue : Zéro Faux Négatifs (Recall élevé)
En médecine, les erreurs d'algorithmes ont des conséquences cliniques asymétriques :
*   **Faux Positif (FP)** : Déclarer un patient sain comme malade.
    *   *Conséquence* : Examens complémentaires de contrôle (anxiété, coût mineur).
*   **Faux Négatif (FN)** : Rater une pathologie grave.
    *   *Conséquence* : Retard de soin, risque de complications majeures, voire décès.
*   **Stratégie** : Optimiser les modèles en utilisant le **Recall (Sensibilité)** comme métrique principale, quitte à dégrader légèrement la Précision.

## 🔒 Confidentialité & Éthique (RGPD Santé, HIPAA)
*   **Anonymisation obligatoire** : Supprimer systématiquement les identifiants directs (Noms, Numéro de Sécurité Sociale, adresses exactes).
*   **Agrégation** : Transformer les dates de naissance exactes en tranches d'âge.

## 📊 Gestion du déséquilibre de classes extrêmes
Les pathologies cibles sont souvent minoritaires dans la population (ex: 1% de cas positifs).
*   Utiliser la validation croisée stratifiée (`StratifiedKFold`) pour conserver le ratio de classes dans chaque pli.
*   Envisager des techniques comme SMOTE ou le sur-échantillonnage, tout en gardant à l'esprit que l'ajustement du seuil de classification (`predict_proba`) est souvent plus robuste cliniquement.
