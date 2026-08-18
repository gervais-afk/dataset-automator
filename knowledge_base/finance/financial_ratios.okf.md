---
type: okf
title: Ratios Financiers & Scoring de Solvabilité (OKF)
description: Ratios financiers standards pour l'évaluation du risque de crédit, solvabilité et capacité de remboursement.
domain: finance
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-15T10:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-15T11:00:00Z" }
status: stable
stale_after: 2027-08-15
---

# Ratios Financiers & Scoring de Solvabilité (OKF)

Ce document OKF (Open Knowledge Format) formalise les règles de calcul arithmétique et les contraintes réglementaires (Bâle III / Bâle IV) pour les modèles de risque de crédit.

## 🧮 Formules Métiers Certifiées

### 1. Ratio Dette sur Revenu (Debt-to-Income Ratio - DTI)
*   **Définition** : Mesure la part des revenus mensuels consacrée au remboursement des dettes.
*   **Formule** : `total_debt_payments / monthly_income`
*   **Interprétation Métier** :
    *   `DTI < 0.36` : Risque faible (Profil solvable).
    *   `0.36 <= DTI <= 0.43` : Risque modéré (Seuil d'alerte).
    *   `DTI > 0.43` : Risque élevé (Rejet automatique ou surprime).
*   **Contrainte Guardrail** : Borne stricte `[0.0, 5.0]` (filtrage des dénominateurs nuls).

### 2. Taux d'Utilisation du Crédit (Credit Utilization Rate - CUR)
*   **Définition** : Proportion de la ligne de crédit renouvelable actuellement utilisée par l'emprunteur.
*   **Formule** : `revolving_balance / credit_limit`
*   **Interprétation Métier** :
    *   `CUR < 0.30` : Excellente gestion du crédit.
    *   `CUR > 0.75` : Dépendance excessive au crédit (Signal avant-coureur de défaut).
*   **Contrainte Guardrail** : Borne `[0.0, 1.5]`.

### 3. Ratio de Couverture du Service de la Dette (Debt Service Coverage Ratio - DSCR)
*   **Définition** : Capacité d'un emprunteur ou d'une entreprise à couvrir ses échéances de prêt avec son flux de trésorerie net.
*   **Formule** : `net_operating_income / total_debt_service`
*   **Interprétation Métier** :
    *   `DSCR > 1.25` : Capacité de remboursement confortable.
    *   `DSCR < 1.00` : Flux de trésorerie négatif (Défaut imminent).
