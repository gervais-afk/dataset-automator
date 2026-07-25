# Model Card — Dataset Automator

## Informations Générales
- **Nom du Dataset** : ecommerce_sales_34500
- **Type de Tâche** : clustering
- **Variable Cible (Target)** : None
- **Date d'Entraînement** : 2026-07-12 17:50:53
- **Pipeline de Production** : Scikit-Learn Pipeline (preprocessing + modèle)

## Modèle Champion Élu
- **Algorithme Élu** : RandomForest/AutoARIMA
- **Statut de la Gate de Déploiement** : **APPROVED**

## Performances Clés
- **shap_surrogate_fidelity** : 0.9200


## Explicabilité & Gouvernance (SHAP / LIME)
- Explications globales (SHAP) et locales (LIME) générées et stockées sous forme de graphiques dans le répertoire du run.
- **Rappel Causalité** : Les contributions indiquent la force d'association locale/globale avec la prédiction du modèle. Elles ne décrivent pas des relations de causalité absolue.

## Limites & Recommandations
- Le modèle doit être utilisé avec prudence sur des données hors-distribution (données dont les variables dépassent les limites observées dans le dataset d'entraînement).
- **Recalibrage** : Recommandé périodiquement (ex: tous les mois ou si un drift significatif est détecté).
