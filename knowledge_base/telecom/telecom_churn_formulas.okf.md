---
type: okf
title: Formules Métiers Télécom & Analyse de Churn (OKF)
description: Formules analytiques certifiées pour la prédiction d'attrition client (churn), la valeur vie client et les métriques de consommation télécom.
domain: telecom
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-15T10:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-15T11:00:00Z" }
status: stable
stale_after: 2027-08-15
---

# Formules Métiers Télécom & Analyse de Churn (OKF)

Ce document OKF formalise les variables calculées standards de l'industrie des télécommunications et des abonnements SaaS.

## 🧮 Formules Métiers Certifiées

### 1. Revenu Moyen par Utilisateur (Average Revenue Per User - ARPU)
*   **Définition** : Revenu mensuel moyen généré par un abonné sur sa durée d'engagement.
*   **Formule** : `total_charges / (tenure_months + 1.0)`
*   **Interprétation Métier** :
    *   Permet d'identifier les segments de clients à haute valeur ajoutée (*High Value Customers*).
    *   Un ARPU élevé combiné à des réclamations récentes signale un risque critique de perte de revenu.
*   **Contrainte Guardrail** : Borne `[0.0, 5000.0]`.

### 2. Ratio Facturation Récente sur Historique (Charge Shock Ratio - CSR)
*   **Définition** : Détecte une augmentation brutale de la facture mensuelle par rapport à la moyenne historique (cause fréquente de désabonnement).
*   **Formule** : `monthly_charges / (total_charges / (tenure_months + 1.0))`
*   **Interprétation Métier** :
    *   `CSR > 1.30` : Facturation anormale (+30% par rapport à la moyenne) $\rightarrow$ Risque de churn multiplié par 3.

### 3. Valeur Vie Client Estimée (Customer Lifetime Value - CLV)
*   **Définition** : Estimation de la valeur financière totale apportée par le client avant son désengagement.
*   **Formule** : `monthly_charges * expected_tenure_months * margin_rate`
*   **Interprétation Métier** :
    *   Sert de multiplicateur dans la matrice des coûts pour calibrer le seuil d'intervention commerciale préventive.
