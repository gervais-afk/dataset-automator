---
type: concept
title: Credit Scoring (Scoring de Crédit)
domain: finance
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Concept : Credit Scoring (Scoring de Crédit)

Le Credit Scoring consiste à estimer la probabilité de défaut (Probability of Default - PD) d'un emprunteur.

## ⚙️ Contraintes Réglementaires & Métiers
*   **Interprétabilité stricte (Bâle III / IV, RGPD)** : L'emprunteur a un "droit à l'explication". Les modèles boîte noire pure (Deep Learning complexe) sont souvent interdits sans cadre d'explication.
*   **Modèles préférés** : 
    *   **Régression Logistique** avec scorecard (facile à traduire en points).
    *   **XGBoost / LightGBM** associés à **SHAP (SHapley Additive exPlanations)** pour expliquer chaque refus de crédit individuel.

## 💰 Matrice des Coûts
Dans le scoring de crédit, les erreurs sont asymétriques :
*   **Faux Positif (Prêter à un client qui va faire défaut)** : Perte financière très élevée (perte du capital prêté).
*   **Faux Négatif (Refuser un client solvable)** : Perte d'opportunité d'intérêt mineure.
*   **Action** : Optimiser le seuil de décision en pénalisant fortement les Faux Positifs dans la fonction de coût ou en calibrant les probabilités de manière stricte.
