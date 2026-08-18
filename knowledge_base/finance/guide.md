---
type: concept
title: Guide de Modélisation Financière & Risque
domain: finance
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Guide de Modélisation Financière & Risque

Ce guide présente les bonnes pratiques pour concevoir des modèles de Machine Learning robustes appliqués aux marchés financiers et à l'analyse de risque.

## ⚠️ Le Fléau du Data Leakage Temporel (Look-Ahead Bias)
En finance, la variable temporelle est structurante. La fuite d'informations futures vers le passé est l'erreur la plus fréquente :
*   **Ne jamais utiliser de validation croisée standard (K-Fold)** : Elle brise l'ordre chronologique. Utilisez toujours `TimeSeriesSplit` ou un split temporel fixe (Train = passé, Test = futur).
*   **Attention aux variables calculées sur tout le dataset** : La moyenne globale ou l'encodage de cible (Target Encoding) calculés sur l'ensemble des données introduisent un biais de futur.
*   **Retards (Lagging)** : Assurez-vous que toutes les variables exogènes sont décalées d'au moins un pas de temps (t-1) avant de prédire t.

## 📊 Métriques Financières Métier
Les métriques standard de régression (MSE, R²) ne reflètent pas le gain financier. Intégrez des métriques métier :
*   **Sharpe Ratio** : Évaluation du rendement par rapport au risque (volatilité).
*   **Maximum Drawdown** : La perte maximale historique d'un portefeuille.
*   **Value at Risk (VaR)** : Perte maximale potentielle avec un niveau de confiance donné (ex: 95%).

## 🛠️ Stationnarisation des Séries Temporelles
La plupart des modèles ML assument la stationnarité (statistiques stables dans le temps).
*   Utiliser le test ADF (Augmented Dickey-Fuller) pour tester la stationnarité.
*   Si non stationnaire, appliquer la différenciation (`diff()`) ou passer aux rendements logarithmiques (`log(price).diff()`).
