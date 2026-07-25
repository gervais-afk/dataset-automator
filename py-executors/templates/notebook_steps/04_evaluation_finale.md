# ✅ Étape 4 — Évaluation Finale & IA de Confiance

Objectif : Prouver la robustesse, la fiabilité et l'explicabilité du modèle.

```python
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.metrics import (confusion_matrix, classification_report, accuracy_score, 
                             r2_score, mean_absolute_error, mean_squared_error, silhouette_score)

print("=" * 60)
print(f"✅ ÉVALUATION FINALE — {best_name}")
print("=" * 60)

# Sélection du modèle à évaluer : final_model si entraîné, sinon stacking_model s'il est là, sinon best_model
if 'final_model' in globals():
    best_model = final_model
    print("Using final_model (Pseudo-Labeling) for evaluation")
elif 'stacking_model' in globals():
    best_model = stacking_model
    print("Using stacking_model for evaluation")
else:
    best_model = results[best_name]["model"]

# Check if model is fitted, if not, fit it
if TYPE_TACHE in ["classification", "regression"]:
    from sklearn.utils.validation import check_is_fitted
    from sklearn.exceptions import NotFittedError
    try:
        check_is_fitted(best_model)
    except NotFittedError:
        print(f"⏳ Fitting model on X_train_prep...")
        best_model.fit(X_train_prep, y_train)

# Gestion hybride predict / fit_predict
if hasattr(best_model, "predict"):
    y_pred = best_model.predict(X_test_prep)
else:
    y_pred = best_model.fit_predict(X_test_prep)

# ── 4.1 Trajectoire : CLASSIFICATION ──────────────────────────────────
if TYPE_TACHE == "classification":
    from sklearn.calibration import CalibratedClassifierCV, CalibrationDisplay
    print("\n📊 Calibration des Probabilités...")
    try:
        try:
            # Essayer d'importer FrozenEstimator (scikit-learn >= 1.6)
            from sklearn.calibration import FrozenEstimator
            # Utilisation de FrozenEstimator avec un split unique sur le jeu de test complet
            cv_custom = [(np.arange(len(X_test_prep)), np.arange(len(X_test_prep)))]
            calibrated_model = CalibratedClassifierCV(FrozenEstimator(best_model), method='isotonic', cv=cv_custom)
            calibrated_model.fit(X_test_prep, y_test)
        except ImportError:
            # Fallback pour scikit-learn < 1.6
            calibrated_model = CalibratedClassifierCV(best_model, method='isotonic', cv='prefit')
            calibrated_model.fit(X_test_prep, y_test)
            
        fig, ax = plt.subplots(figsize=(8, 6))
        try:
            CalibrationDisplay.from_estimator(best_model, X_test_prep, y_test, name=best_name, ax=ax)
            plt.title("📈 Courbe de Calibration (Fiabilité)")
            plt.show()
        except Exception as plot_err:
            plt.close(fig)
            raise plot_err
    except Exception as e:
        print(f"⚠️ Calibration non supportée : {e}")

    # ── Confusion Matrix (Heatmap) & ROC/PR Curves ───────────────────
    print("\n📊 Graphiques d'Évaluation de la Classification...")
    try:
        from sklearn.metrics import confusion_matrix, roc_curve, auc, precision_recall_curve
        classes = np.unique(y_test)
        is_binary = len(classes) == 2
        n_plots = 3 if is_binary else 2
        fig, axes = plt.subplots(1, n_plots, figsize=(6 * n_plots, 5))
        
        # 1. Matrice de Confusion
        cm = confusion_matrix(y_test, y_pred)
        sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', ax=axes[0], cbar=False)
        axes[0].set_title("🔲 Matrice de Confusion")
        axes[0].set_ylabel("Classe Réelle")
        axes[0].set_xlabel("Classe Prédite")
        
        # 2. Courbe ROC
        has_proba = hasattr(best_model, "predict_proba")
        if has_proba:
            y_proba = best_model.predict_proba(X_test_prep)
            if is_binary:
                fpr, tpr, _ = roc_curve(y_test, y_proba[:, 1])
                roc_auc = auc(fpr, tpr)
                axes[1].plot(fpr, tpr, color='darkorange', lw=2, label=f'ROC Curve (AUC = {roc_auc:.3f})')
                axes[1].plot([0, 1], [0, 1], color='navy', lw=1.5, linestyle='--')
                axes[1].set_title("📈 Courbe ROC")
                axes[1].set_xlabel("Faux Positifs (FPR)")
                axes[1].set_ylabel("Vrais Positifs (TPR)")
                axes[1].legend(loc="lower right")
                
                # 3. Courbe PR
                prec, rec, _ = precision_recall_curve(y_test, y_proba[:, 1])
                pr_auc = auc(rec, prec)
                axes[2].plot(rec, prec, color='forestgreen', lw=2, label=f'PR Curve (AUC = {pr_auc:.3f})')
                axes[2].set_title("📈 Courbe Precision-Recall")
                axes[2].set_xlabel("Recall (Sensibilité)")
                axes[2].set_ylabel("Precision (Pureté)")
                axes[2].legend(loc="lower left")
            else:
                from sklearn.preprocessing import label_binarize
                y_test_bin = label_binarize(y_test, classes=classes)
                for i, cl in enumerate(classes):
                    fpr, tpr, _ = roc_curve(y_test_bin[:, i], y_proba[:, i])
                    roc_auc = auc(fpr, tpr)
                    axes[1].plot(fpr, tpr, lw=1.5, label=f'Classe {cl} (AUC = {roc_auc:.2f})')
                axes[1].plot([0, 1], [0, 1], color='navy', lw=1, linestyle='--')
                axes[1].set_title("📈 Courbe ROC (Multi-classe)")
                axes[1].set_xlabel("Faux Positifs (FPR)")
                axes[1].set_ylabel("Vrais Positifs (TPR)")
                axes[1].legend(loc="lower right")
        else:
            axes[1].text(0.5, 0.5, "predict_proba non supporté\npour ce modèle", ha="center", va="center", fontsize=12, color="gray")
            axes[1].set_title("📈 Courbe ROC non disponible")
            if is_binary:
                axes[2].text(0.5, 0.5, "predict_proba non supporté", ha="center", va="center", fontsize=12, color="gray")
                axes[2].set_title("📈 Courbe PR non disponible")
                
        plt.tight_layout()
        plt.savefig(os.path.join(OUTPUT_DIR, '04_classification_evaluation.png'), dpi=120, bbox_inches='tight')
        plt.show()
    except Exception as e_plot:
        print(f"⚠️ Erreur graphiques classification : {e_plot}")

# ── 4.2 Trajectoire : NON-SUPERVISÉ (PROFILING) ───────────────────────
elif TYPE_TACHE == "unsupervised":
    print("\n📊 Profilage des Clusters (Senior Approach)")
    df_profile = pd.DataFrame(X_test_prep, columns=[f"f_{i}" for i in range(X_test_prep.shape[1])])
    df_profile['cluster'] = y_pred
    cluster_means = df_profile.groupby('cluster').mean()
    global_means  = df_profile.drop('cluster', axis=1).mean()
    diff_rel = (cluster_means - global_means) / (global_means + 1e-6) * 100
    print("🔥 Top features par cluster (Écart à la moyenne globale) :")
    display(diff_rel.T.style.background_gradient(cmap='RdYlGn'))

# ── 4.3 Métriques Standards ──────────────────────────────────────────
if TYPE_TACHE == "classification":
    print("\n📋 Rapport de Classification :")
    print(classification_report(y_test, y_pred))
    if best_name not in results:
        results[best_name] = {}
    results[best_name]['score'] = accuracy_score(y_test, y_pred)
    results[best_name]['model'] = best_model
elif TYPE_TACHE == "regression":
    r2_val = r2_score(y_test, y_pred)
    mae_val = mean_absolute_error(y_test, y_pred)
    rmse_val = np.sqrt(mean_squared_error(y_test, y_pred))
    
    print(f"📊 R² Score : {r2_val:.4f}")
    print(f"📊 MAE      : {mae_val:.4f}")
    print(f"📊 RMSE     : {rmse_val:.4f}")
    
    if best_name not in results:
        results[best_name] = {}
    results[best_name]['score'] = r2_val
    results[best_name]['model'] = best_model
    
    # ── Analyse des Résidus ──────────────────────────────────────────
    print("\n🔬 Analyse Diagnostique des Résidus...")
    residuals = y_test - y_pred
    
    fig, ax = plt.subplots(1, 2, figsize=(14, 5))
    
    # 1. Residuals Plot (Valeurs prédites vs Résidus) - Homoscédasticité
    ax[0].scatter(y_pred, residuals, alpha=0.5, edgecolors='k', color='teal')
    ax[0].axhline(y=0, color='r', linestyle='--')
    ax[0].set_xlabel('Valeurs Prédites')
    ax[0].set_ylabel('Résidus')
    ax[0].set_title('Graphique des Résidus (Homoscédasticité)')
    ax[0].grid(True, alpha=0.3)
    
    # 2. Q-Q Plot (Normalité des résidus standardisés)
    import statsmodels.api as sm
    sm.qqplot(residuals, fit=True, line='r', ax=ax[1])
    ax[1].set_title('Q-Q Plot (Normalité)')
    ax[1].grid(True, alpha=0.3)
    
    plt.tight_layout()
    import os
    plt.savefig(os.path.join(OUTPUT_DIR, '04_regression_residuals.png'), dpi=150, bbox_inches='tight')
    plt.show()
```

### 📊 Interprétation du Graphique des Résidus
Ce graphique permet de vérifier l'hypothèse d'homoscédasticité et l'absence de modèles non linéaires résiduels.
*   **Le scénario idéal :** Les résidus doivent s'éparpiller de manière parfaitement symétrique, aléatoire et homogène autour de la ligne horizontale $e_i = 0$. Cela signifie que l'erreur de notre modèle est purement aléatoire et de variance constante.
*   **Présence d'Hétéroscédasticité :** Si la dispersion des points s'accroît à mesure que les valeurs prédites augmentent (formant un cône ou un entonnoir), l'incertitude de prédiction est plus forte pour les valeurs élevées. *Recommandation : appliquer une transformation logarithmique sur la cible ou segmenter le modèle.*
*   **Erreur Structurelle :** Une concentration de points décrivant une courbe non linéaire (ex: forme en U) signale que le modèle échoue à capturer certaines relations géométriques.

### 📈 Interprétation du Diagramme Q-Q Plot
Le graphique Quantile-Quantile (Q-Q Plot) compare les quantiles empiriques de nos résidus standardisés aux quantiles théoriques d'une loi normale standard. Il valide la pertinence de nos intervalles de confiance.
*   **Le scénario idéal :** Un alignement rectiligne parfait sur la diagonale rouge à 45 degrés témoigne d'une normalité robuste de nos résidus, ce qui valide pleinement l'utilisation des écarts-types pour mesurer la confiance des prédictions.
*   **Présence de queues épaisses ou d'asymétrie :** Tout décrochage significatif des points aux extrémités révèle une déviation par rapport à la loi normale, indiquant la présence de valeurs aberrantes non modélisées ou d'une asymétrie résiduelle persistante.

```python
# ── 4.4 Interprétabilité (XAI) ────────────────────────────────────────
import shap
print("\n🧠 Analyse SHAP (Interprétabilité Globale)")
try:
    # On utilise un échantillon pour la rapidité
    X_sample = X_test_prep[:100]  # Réduire à 100 pour être sûr de la performance
    
    # Détecter si c'est TabICL
    is_tabicl = "TabICL" in type(best_model).__name__
    
    if is_tabicl:
        from tabicl.shap import get_shap_values
        print("💡 Analyse SHAP effectuée via l'intégration native tabicl.shap.")
        shap_values = get_shap_values(best_model, X_sample)
    else:
        # Détecter si c'est un StackingClassifier/Regressor ou autre modèle complexe
        model_to_explain = best_model
        if type(best_model).__name__ in ['StackingClassifier', 'StackingRegressor']:
            # Essayer d'expliquer le meilleur estimateur de base (plus rapide et supporté par TreeExplainer)
            if hasattr(best_model, 'named_estimators_') and len(best_model.named_estimators_) > 0:
                # On cherche un modèle d'arbre dans les estimateurs nommés
                for name, est in best_model.named_estimators_.items():
                    if type(est).__name__ in ['RandomForestClassifier', 'RandomForestRegressor', 
                                              'LGBMClassifier', 'LGBMRegressor',
                                              'XGBClassifier', 'XGBRegressor',
                                              'CatBoostClassifier', 'CatBoostRegressor',
                                              'GradientBoostingClassifier', 'GradientBoostingRegressor']:
                        model_to_explain = est
                        print(f"💡 Analyse SHAP effectuée sur l'estimateur de base '{name}' du Stacking.")
                        break
        
        # Si c'est toujours le Stacking (ou si on n'a pas trouvé d'arbre), on passe la fonction de prédiction
        if model_to_explain is best_model:
            # SHAP a besoin d'un callable pour les modèles génériques
            if hasattr(best_model, "predict_proba") and TYPE_TACHE == "classification":
                explainer = shap.Explainer(best_model.predict_proba, X_train_prep[:50])
            else:
                explainer = shap.Explainer(best_model.predict, X_train_prep[:50])
        else:
            explainer = shap.Explainer(model_to_explain, X_train_prep[:50])
            
        shap_values = explainer(X_sample)
    
    plt.figure(figsize=(10, 6))
    if hasattr(shap_values, "shape") and len(shap_values.shape) == 3:
        class_idx = 1 if shap_values.shape[2] > 1 else 0
        shap.summary_plot(shap_values[:, :, class_idx], X_sample, show=False)
    else:
        shap.summary_plot(shap_values, X_sample, show=False)
        
    plt.title("🌍 Importance Globale des Variables (SHAP)")
    plt.show()
except Exception as e:
    print(f"⚠️ SHAP non disponible pour ce modèle : {e}")

# ── 4.5 Diagnostics du Data Scientist Senior (Automatisés)
print("\n" + "=" * 60)
print("🧠 DIAGNOSTICS DE ROBUSTESSE (SENIOR DATA SCIENCE AUDIT)")
print("=" * 60)
if TYPE_TACHE == "classification":
    from sklearn.metrics import classification_report
    report_dict = classification_report(y_test, y_pred, output_dict=True)
    acc = report_dict['accuracy']
    macro_f1 = report_dict['macro avg']['f1-score']
    print(f"✅ Accuracy Globale : {acc:.4f} | Macro F1 : {macro_f1:.4f}")
    
    # Vérification du déséquilibre de performance
    recalls = [report_dict[str(cls)]['recall'] for cls in np.unique(y_test) if str(cls) in report_dict]
    if recalls:
        gap = max(recalls) - min(recalls)
        print(f"👉 Gap de rappel max entre classes : {gap*100:.2f}%")
        if gap > 0.30:
            print("   🚨 ALERTE BIAIS : Déséquilibre important de performance entre les classes.")
            print("   → Recommandation : Ajuster les poids des classes ou le seuil de décision.")
        else:
            print("   ✅ Équité : La performance est équilibrée sur toutes les classes.")
            
        # Alerte classe totalement manquée
        if min(recalls) == 0.0:
            print("   🚨 ALERTE CRITIQUE : Au moins une classe a un rappel de 0.0 (complètement ignorée) !")
            
    # Vérification d'Overfitting simple
    if hasattr(best_model, "score") and 'X_train_prep' in globals():
        try:
            train_score = best_model.score(X_train_prep, y_train)
            test_score = best_model.score(X_test_prep, y_test)
            if train_score - test_score > 0.15:
                print(f"   🚨 ALERTE OVERFITTING : Train Score ({train_score:.4f}) vs Test Score ({test_score:.4f}) trop éloignés.")
                print("   → Recommandation : Augmenter la régularisation ou réduire la complexité du modèle.")
        except:
            pass

elif TYPE_TACHE == "regression":
    from scipy.stats import skew, spearmanr
    from statsmodels.stats.stattools import durbin_watson
    
    r2 = r2_score(y_test, y_pred)
    rmse = np.sqrt(mean_squared_error(y_test, y_pred))
    residuals = y_test - y_pred
    skewness_val = skew(residuals)
    dw = durbin_watson(residuals)
    
    print(f"✅ Coefficient de Détermination R² : {r2:.4f} | RMSE : {rmse:.4f}")
    print(f"✅ Erreurs - Asymétrie (Skewness) : {skewness_val:.4f} | Durbin-Watson : {dw:.2f}")
    
    # Interprétation
    if r2 < 0.4:
        print("   🚨 ALERTE PERFORMANCE : Le pouvoir prédictif R² est faible.")
    if abs(skewness_val) > 1.5:
        print("   🚨 ALERTE ASYMÉTRIE : Les erreurs ne sont pas distribuées normalement.")
        print("   → Recommandation : Envisager une transformation log ou Box-Cox de la cible.")
    if dw < 1.5 or dw > 2.5:
        print("   🚨 ALERTE AUTOCORRÉLATION : Les résidus montrent une corrélation sérielle.")
        print("   → Recommandation : Utiliser un split chronologique ou des lags temporels.")
        
    # Hétéroscédasticité
    try:
        _, p_val = spearmanr(y_pred, np.abs(residuals))
        print(f"✅ Hétéroscédasticité (p-value) : {p_val:.4f}")
        if p_val < 0.05:
            print("   🚨 ALERTE HÉTÉROSCÉDASTICITÉ : La variance des résidus n'est pas constante (effet entonnoir).")
            print("   → Recommandation : Les prédictions sur les grandes valeurs sont plus incertaines.")
    except:
        pass

print("\n✅ ÉVALUATION SENIOR TERMINÉE")
```

## Rapport Final

```python
print("\n" + "=" * 60)
print(f"📋 RAPPORT FINAL — {NOM_BASE}")
print("=" * 60)
print(f"  Tâche : {TYPE_TACHE.upper()} | Modèle : {best_name}")
print("  📁 Sorties :", OUTPUT_DIR)
print("=" * 60)
```

## Rapport d'évaluation visuelle

{EVAL_PLOT}

## 🧠 Rapport d'Interprétation Qualitatif RAG (Agent IA Senior)

{LLM_INTERPRETATION}
