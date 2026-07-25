---
title: Prédiction de l'Attrition Client (Churn Prediction)
domain: ecommerce
type: concept
---

# Concept : Prédiction de l'Attrition Client (Churn Prediction)

La prédiction de churn vise à identifier les clients risquant de quitter ou de cesser d'acheter sur une plateforme.

## ⚙️ Stratégie ML
*   **Définition de la Cible** : Dans les services contractuels (SaaS), le churn est net (désabonnement). Dans le retail transactionnel, il faut définir un seuil d'inactivité (ex: aucun achat depuis 90 jours).
*   **Déséquilibre des classes (Imbalanced Data)** : Le taux de churn est généralement faible (1% à 5%). L'accuracy globale sera artificiellement élevée. Utiliser le **F1-Score** ou l'**Uplift** pour évaluer la pertinence des campagnes de rétention.
*   **Modèles phares** : Gradient Boosting (XGBoost, CatBoost) car ils gèrent nativement les variables catégorielles et les données tabulaires complexes.

## 💰 Optimisation Marketing (Matrice de Coûts)
L'action métier consiste à proposer une incitation (code promo, réduction) pour retenir les clients à risque :
*   **Vrai Positif (TP)** : Client à risque ciblé -> Rétention réussie -> Gain de la LTV (Lifetime Value).
*   **Faux Positif (FP)** : Client stable ciblé -> Promo inutile -> Perte de marge (effet d'aubaine).
*   **Faux Négatif (FN)** : Client à risque non ciblé -> Churn silencieux -> Perte de la LTV.
