from typing import Dict, Any
from pathlib import Path

# Templates métiers par domaine + type de tâche pour alignement CRISP-ML(Q)
DOMAIN_CONTEXTS: Dict[str, Dict[str, Any]] = {
    "finance": {
        "timeseries": {
            "business_objective": "Prévision de cours, gestion de risque (VaR), optimisation de portefeuille ou détection de régimes de marché.",
            "economic_matrix": "| Résultat | Action Métier | Impact Financier |\n|---|---|---|\n| **TP** | Position correcte / Hedge activé | + Rendement / - Perte évitée |\n| **FP** | Sur-trading / Fausse alerte | - Frais de transaction / Slippage |\n| **FN** | Opportunité manquée / Risque non couvert | - Perte sèche / Dépassement VaR |\n| **TN** | Inaction justifiée | 0€ (Stabilité préservée) |",
            "success_metrics": "sMAPE < 5%, RMSE normalisé, Sharpe Ratio > 1.2, Backtest hors-échantillon stable.",
            "constraints": ["Non-stationnarité structurelle", "Latence d'inférence < 100ms", "Features exogènes (macro, news)"],
            "regulatory": "Bâle III/IV, MiFID II, auditabilité des signaux, interdiction du look-ahead bias.",
            "pitfalls": "Fuites temporelles (data leakage), sur-optimisation (curve fitting), non-gestion des chocs exogènes (black swan)."
        },
        "classification": {
            "business_objective": "Scoring de crédit, détection de fraude, segmentation risque/client.",
            "economic_matrix": "| Résultat | Action Métier | Impact Financier |\n|---|---|---|\n| **TP** | Fraude détectée / Dossier bloqué | + Économie directe de la perte |\n| **FP** | Blocage légitime / Faux positif | - Perte client / Coût de vérification manuelle |\n| **FN** | Fraude manquée / Défaut non détecté | - Perte sèche du montant fraudé / Provision risque |\n| **TN** | Flux normal autorisé | 0€ (Traitement automatique fluide) |",
            "success_metrics": "Precision @ Top K, ROC-AUC > 0.85, Coût moyen par erreur < seuil métier, F1-Weighted.",
            "constraints": ["Déséquilibre extrême des classes (ex: 1:1000)", "Interprétabilité obligatoire des scores", "Décision en temps réel (< 50ms)"],
            "regulatory": "RGPD, droit à l'explication, conformité anti-blanchiment (AML/KYC), biais algorithmique.",
            "pitfalls": "Métriques trompeuses (Accuracy > 99% trompeur), variables corrélées au futur (data leakage), dérive rapide de la distribution des fraudes."
        },
        "default": {
            "business_objective": "Analyse financière, modélisation de tendances ou évaluation quantitative d'actifs.",
            "economic_matrix": "| Résultat | Action Métier | Impact Financier |\n|---|---|---|\n| **TP** / **TN** | Décision correcte basée sur les données | + Optimisation de marge / + Sécurité |\n| **FP** / **FN** | Erreur d'analyse | - Coût opérationnel / - Perte d'opportunité |",
            "success_metrics": "Stabilité temporelle des prévisions, alignement avec les objectifs de rentabilité.",
            "constraints": ["Qualité des flux de données historiques", "Audits de conformité réguliers"],
            "regulatory": "Normes comptables internationales (IFRS), conformité réglementaire locale.",
            "pitfalls": "Non-prise en compte de la saisonnalité financière et des chocs de volatilité."
        }
    },
    "medical": {
        "classification": {
            "business_objective": "Aide au diagnostic précoce, prédiction de récidive, triage patient ou optimisation des ressources hospitalières.",
            "economic_matrix": "| Résultat | Action Médicale | Impact Clinique |\n|---|---|---|\n| **TP** | Traitement initié à temps | + Sauvetage de vie / Réduction de la durée de séjour |\n| **FP** | Examens complémentaires inutiles | - Coût d'imagerie additionnel / Anxiété du patient |\n| **FN** | Diagnostic manqué / Retard de soin | - Aggravation clinique majeure / Risque vital engagé |\n| **TN** | Suivi standard ou sortie | 0€ (Parcours nominal préservé) |",
            "success_metrics": "Sensibilité (Recall) > 0.90, Valeur Prédictive Négative (VPN) élevée, Concordance Index (survie).",
            "constraints": ["Données fortement déséquilibrées", "Interprétabilité clinique obligatoire (SHAP/LIME)", "Biais de sélection des centres"],
            "regulatory": "RGPD santé, validation ANSM/FDA, éthique de l'IA médicale, traçabilité décisionnelle stricte.",
            "pitfalls": "Faux négatifs inacceptables cliniquement, données de survie censurées mal traitées, sur-apprentissage sur un centre unique."
        },
        "default": {
            "business_objective": "Recherche clinique, analyse épidémiologique ou optimisation de protocoles de soins.",
            "economic_matrix": "| Résultat | Action Médicale | Impact |\n|---|---|---|\n| **Correct** | Protocole adapté | + Amélioration de la santé publique / + Efficacité |\n| **Incorrect** | Mauvaise allocation de soin | - Coût de traitement inefficace / Effets secondaires |",
            "success_metrics": "Significativité statistique, reproductibilité des résultats cliniques.",
            "constraints": ["Données hautement sensibles et anonymisées", "Rareté des cas d'études"],
            "regulatory": "Réglementations de bioéthique, RGPD, certification des dispositifs médicaux.",
            "pitfalls": "Biais de confusion (confounding bias), confusion entre corrélation et causalité clinique."
        }
    },
    "ecommerce": {
        "classification": {
            "business_objective": "Prédiction de churn (désabonnement), scoring de propension d'achat, détection de fraude transactionnelle.",
            "economic_matrix": "| Résultat | Action Marketing/Opérationnelle | Impact |\n|---|---|---|\n| **TP** | Rétention ciblée / Code promo | + Customer Lifetime Value (CLV) préservée / + Chiffre d'Affaires |\n| **FP** | Promo inutile / Relance intrusive | - Marge (effet d'aubaine) / - Score de satisfaction (NPS) |\n| **FN** | Perte client silencieuse / Fraude acceptée | - Perte irréversible du client / - Marge sur transaction |\n| **TN** | Aucun contact publicitaire | 0€ (Économie de ressources marketing) |",
            "success_metrics": "F1-Score > 0.75, Uplift réel > 3%, ROI de campagne marketing > 150%, Precision @ Top K.",
            "constraints": ["Problème du Cold Start (nouveaux utilisateurs)", "Fraîcheur des features < 24h", "Scalabilité lors des pics saisonniers (Black Friday)"],
            "regulatory": "RGPD (consentement cookies), loyauté algorithmique, transparence des prix et recommandations.",
            "pitfalls": "Data leakage (features post-achat), bulle de filtrage limitant la découverte, saisonnalité non modélisée."
        },
        "regression": {
            "business_objective": "Prévision de panier moyen, estimation de lifetime value (CLV), pricing dynamique.",
            "economic_matrix": "| Résultat | Action Opérationnelle | Impact |\n|---|---|---|\n| **Sur-estimation** | Approvisionnement excédentaire | - Coût de stockage / Risque de démarque et dépréciation |\n| **Sous-estimation** | Rupture de stock | - Manque à gagner (perte directe de chiffre d'affaires) |\n| **Estimation correcte** | Flux tendus optimisés | + Rotation de stock maximale / + Marge opérationnelle |",
            "success_metrics": "R² > 0.70, MAPE < 10%, RMSE pondéré par la marge produit.",
            "constraints": ["Relations non-linéaires fortes", "Variables catégorielles à haute cardinalité (codes SKU)", "Biais de retour produit"],
            "regulatory": "Législation sur la concurrence déloyale, interdiction du pricing discriminatoire abusif.",
            "pitfalls": "Outliers de promotions non traités, variables corrélées au prix induisant des biais causaux."
        },
        "default": {
            "business_objective": "Segmentation client, ciblage publicitaire ou recommandation personnalisée.",
            "economic_matrix": "| Résultat | Action Marketing | Impact |\n|---|---|---|\n| **Recommandation utile** | Achat déclenché | + Panier moyen / + Fidélité |\n| **Recommandation inutile** | Spam / Rejet | - Engagement / Fatigue de l'utilisateur |",
            "success_metrics": "Taux de clics (CTR), taux de conversion, couverture du catalogue.",
            "constraints": ["Calcul en temps réel des recommandations", "Volume de données volumineux"],
            "regulatory": "Réglementations e-privacy, consentement au ciblage comportemental.",
            "pitfalls": "Sur-recommandation de produits déjà achetés, non-gestion de la diversité."
        }
    },
    "energy": {
        "timeseries": {
            "business_objective": "Prévision de charge électrique/thermique, optimisation de production renouvelable, détection d'anomalies réseau.",
            "economic_matrix": "| Résultat | Action Réseau | Impact Opérationnel |\n|---|---|---|\n| **TP** | Ajustement production / Stockage activé | + Équilibre offre/demande / - Coût de congestion |\n| **FP** | Activation de réserve inutile | - Coût de démarrage de centrale thermique / Pertes d'énergie |\n| **FN** | Délestage réseau / Sous-production | - Risque de blackout / Pénalités RTE astronomiques |\n| **TN** | Réseau stable sans intervention | 0€ (Stabilité nominale) |",
            "success_metrics": "sMAPE < 3%, MAE < 1% de la charge globale du réseau, disponibilité système > 99.9%.",
            "constraints": ["Haute fréquence de données (15min-1h)", "Dépendance critique aux variables météo", "Contraintes physiques de transport"],
            "regulatory": "Normes ISO 50001 (management de l'énergie), réglementations RTE/Enedis, reporting carbone.",
            "pitfalls": "Dérive progressive des capteurs physiques, saisonnalités croisées (horaires, météo, congés), non-gestion des extrêmes météo."
        },
        "default": {
            "business_objective": "Maintenance prédictive de turbines, prédiction de pannes de réseaux ou optimisation de coûts.",
            "economic_matrix": "| Résultat | Action | Impact |\n|---|---|---|\n| **TP** | Maintenance planifiée à l'avance | + Économie sur réparation d'urgence / + Durée de vie |\n| **FP** | Maintenance inutile | - Coût de main-d'œuvre et pièces pour rien |\n| **FN** | Panne catastrophique | - Arrêt de production / Dégâts matériels majeurs |\n| **TN** | Fonctionnement normal | 0€ |",
            "success_metrics": "F1-Score sur les alertes de pannes, réduction du taux d'indisponibilité.",
            "constraints": ["Données de capteurs industriels bruitées", "Événements de pannes rares"],
            "regulatory": "Normes de sécurité industrielle, directives environnementales.",
            "pitfalls": "Retard d'alarme supérieur au temps de rupture physique, sur-réaction au bruit."
        }
    },
    "general": {
        "default": {
            "business_objective": "Exploration de données, identification de patterns structurels et modélisation prédictive de baseline.",
            "economic_matrix": "| Résultat | Action Métier | Impact |\n|---|---|---|\n| **Correct** | Décision alignée | + Efficacité opérationnelle |\n| **Erreur** | Mauvais alignement | - Perte de temps / Coût d'opportunité |",
            "success_metrics": "Robustesse statistique, scores supérieurs au benchmark aléatoire.",
            "constraints": ["Données structurées", "Interprétabilité de base"],
            "regulatory": "RGPD (anonymisation et sécurité des données).",
            "pitfalls": "Sur-apprentissage sur les données historiques, non-validation sur données hors-échantillon (OOD)."
        }
    }
}

# Alias pour mapper les synonymes ou domaines détectés vers notre dictionnaire
DOMAIN_ALIASES = {
    "healthcare": "medical",
    "health": "medical",
    "environment": "energy",
    "environmental": "energy",
}

def get_business_header(domain: str, task_type: str, dataset_name: str, target_col: str = "", business_costs: dict = None, df = None) -> str:
    """Génère le markdown CRISP-ML(Q) adapté au domaine + tâche."""
    normalized_domain = domain.lower().strip()
    # Résolution des alias
    resolved_domain = DOMAIN_ALIASES.get(normalized_domain, normalized_domain)
    
    # Récupération du domaine, fallback sur general
    domain_data = DOMAIN_CONTEXTS.get(resolved_domain, DOMAIN_CONTEXTS["general"])
    
    # Récupération de la tâche, fallback sur default
    normalized_task = task_type.lower().replace("_", "").strip()
    
    # Mapper timeseries ou time_series vers la même clé
    if "time" in normalized_task:
        task_key = "timeseries"
    elif "class" in normalized_task:
        task_key = "classification"
    elif "regress" in normalized_task:
        task_key = "regression"
    else:
        task_key = normalized_task

    task_data = domain_data.get(task_key, domain_data.get("default", DOMAIN_CONTEXTS["general"]["default"]))
    
    # Si le domaine spécifique n'a pas cette tâche, utiliser le fallback de "general"
    if not task_data and task_key in DOMAIN_CONTEXTS["general"]:
        task_data = DOMAIN_CONTEXTS["general"][task_key]
    elif not task_data:
        task_data = DOMAIN_CONTEXTS["general"]["default"]

    # Duplication pour éviter de modifier la configuration globale
    task_data = dict(task_data)

    # Calcul dynamique de la matrice économique si des coûts réels sont fournis OU calculés depuis df
    if df is not None and not df.empty and target_col in df.columns:
        import numpy as np
        # Calculer le prix moyen si colonne close présente, sinon 1.0
        avg_price = df['Close'].mean() if 'Close' in df.columns else 1.0
        
        # Si c'est le volume financier
        if target_col.lower() == 'volume':
            avg_volume = df[target_col].mean()
            std_volume = df[target_col].std()
            estimated_mae = std_volume * 0.15 # Une estimation raisonnable de l'erreur MAE (15%)
            
            # Application de la stratégie dynamique
            cost_fp = int(estimated_mae * 0.001 * avg_price) # 0.1% du volume d'erreur * prix
            cost_fn = int(estimated_mae * 0.01 * avg_price)  # 1% du volume d'erreur (opportunité manquée)
            gain_tp = int(avg_volume * 0.0005 * avg_price)   # 0.05% du volume moyen sécurisé
            
            currency = "USD" if avg_price > 10 else "FCFA"
            if currency == "FCFA":
                # Convertir USD fictif en FCFA (par exemple 600 FCFA = 1 USD)
                cost_fp = int(cost_fp * 600)
                cost_fn = int(cost_fn * 600)
                gain_tp = int(gain_tp * 600)
                
            task_data['economic_matrix'] = f"""Pour transformer les scores ML en décisions métiers réelles, les coûts et gains opérationnels suivants ont été calculés dynamiquement à partir des statistiques de la cible `{target_col}` (Prix moyen: {avg_price:,.2f}$, Volume moyen: {avg_volume:,.0f}) :

| Résultat Modèle | Action Métier | Impact Financier (Calculé sur Données) |
| :--- | :--- | :--- |
| **Vrai Positif (TP)** | Transaction réussie | **+ {gain_tp:,} {currency}** (0.05% du volume moyen sécurisé) |
| **Faux Positif (FP)** | Fausse alerte (Slippage) | **- {cost_fp:,} {currency}** (0.1% d'erreur volume sur frais de transaction) |
| **Faux Négatif (FN)** | Opportunité manquée | **- {cost_fn:,} {currency}** (1% d'erreur volume sur transaction perdue) |
| **Vrai Négatif (TN)** | Statut quo | **0 {currency}** (Aucune action requise) |"""

    elif business_costs and 'cost_FP' in business_costs and 'cost_FN' in business_costs:
        currency = business_costs.get('currency', 'FCFA')
        cost_fp = business_costs.get('cost_FP')
        cost_fn = business_costs.get('cost_FN')
        gain_tp = business_costs.get('gain_TP', 2 * cost_fp)
        
        task_data['economic_matrix'] = f"""Pour transformer les scores ML en décisions métiers réelles, les coûts et gains opérationnels suivants ont été configurés ou calculés statistiquement à partir du dataset :

| Résultat Modèle | Action Métier | Impact Financier (Estimation) |
| :--- | :--- | :--- |
| **Vrai Positif (TP)** | Intervention réussie | **+ {gain_tp:,} {currency}** (ex: gain net ou perte évitée) |
| **Faux Positif (FP)** | Fausse alerte | **- {cost_fp:,} {currency}** (ex: coût d'audit opérationnel ou de contact inutile) |
| **Faux Négatif (FN)** | Opportunité manquée | **- {cost_fn:,} {currency}** (ex: perte brute de la transaction ou churn client) |
| **Vrai Négatif (TN)** | Statut quo | **0€** (Aucune action requise) |"""

    return f"""# ── 0️⃣ COMPRÉHENSION MÉTIER — {task_type.upper()} ({resolved_domain.upper()} - CRISP-ML(Q)) ──

## 0.1 Objectif Métier (Business Understanding)
> **Alignement MLOps** : Cette cellule présente les exigences de l'étape 1 de la méthodologie **CRISP-ML(Q)** pour le dataset `{dataset_name}`.

### 🎯 Objectif Business
{task_data['business_objective']}

### 💰 Matrice d'Impact Économique (Coûts & Gains)
{task_data['economic_matrix']}

### 📊 Métriques de Succès Métier
{task_data['success_metrics']}

## 0.2 Contraintes, Réglementation & Risques
*   **⚙️ Contraintes Techniques** : {', '.join(task_data['constraints'])}
*   **⚖️ Cadre Réglementaire & Éthique** : {task_data['regulatory']}
*   **⚠️ Pièges Fréquents à Éviter** : {task_data['pitfalls']}

---
> 📌 *La colonne cible validée pour cette modélisation est : `{target_col or 'Non spécifiée (Clustering/Anomalie)'}`.*
> 🔒 *Les seuils d'alertes et coûts associés sont paramétrables dans `config/metrics.yaml`.*
"""

