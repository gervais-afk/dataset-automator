# 🏆 Benchmarking Senior & Trajectoires Itératives

Conformément aux standards Senior : **Baseline (Simplicité) ➔ Avancé (Performance) ➔ SOTA (Optimisation).**

```python
import time
import numpy as np
import pandas as pd
from sklearn.model_selection import (RepeatedStratifiedKFold, RepeatedKFold, cross_val_score)

print(f"🏆 TRAJECTOIRE DE BENCHMARK — Mode: {TYPE_TACHE.upper()}")
print("-" * 60)

results = {}

# ── TRAJECTOIRE 1 : CLASSIFICATION ────────────────────────────────────
if TYPE_TACHE == "classification":
    from sklearn.linear_model import LogisticRegression
    from sklearn.ensemble import RandomForestClassifier
    from xgboost import XGBClassifier
    from lightgbm import LGBMClassifier
    from sklearn.dummy import DummyClassifier

    MODELES = {
        "Baseline (LogReg)": LogisticRegression(max_iter=1000),
        "RandomForest"      : RandomForestClassifier(n_estimators=100, max_depth=10, random_state=42),
        "XGBoost"           : XGBClassifier(n_estimators=100, learning_rate=0.1, random_state=42),
        "LightGBM"          : LGBMClassifier(n_estimators=100, verbose=-1, random_state=42),
    }
    try:
        from catboost import CatBoostClassifier
        MODELES["CatBoost"] = CatBoostClassifier(iterations=100, verbose=0, random_state=42)
    except ImportError:
        pass
    try:
        from tabfm import TabFMClassifier
        MODELES["TabFM (Google Foundation)"] = TabFMClassifier()
    except Exception:
        try:
            from tabicl import TabICLClassifier
            MODELES["TabICL (SOTA)"] = TabICLClassifier()
        except Exception:
            pass
    cv = RepeatedStratifiedKFold(n_splits=5, n_repeats=2, random_state=42)
    metric = "accuracy"

# ── TRAJECTOIRE 2 : RÉGRESSION ───────────────────────────────────────
elif TYPE_TACHE == "regression":
    from sklearn.linear_model import Ridge, Lasso
    from sklearn.ensemble import RandomForestRegressor
    from xgboost import XGBRegressor
    from lightgbm import LGBMRegressor

    MODELES = {
        "Baseline (Ridge)": Ridge(),
        "Lasso (FeatureSel)": Lasso(alpha=0.1),
        "RandomForest"      : RandomForestRegressor(n_estimators=100, max_depth=10, random_state=42),
        "XGBoost"           : XGBRegressor(n_estimators=100, learning_rate=0.1, random_state=42),
        "LightGBM"          : LGBMRegressor(n_estimators=100, verbose=-1, random_state=42),
    }
    try:
        from catboost import CatBoostRegressor
        MODELES["CatBoost"] = CatBoostRegressor(iterations=100, verbose=0, random_state=42)
    except ImportError:
        pass
    try:
        from tabfm import TabFMRegressor
        MODELES["TabFM (Google Foundation)"] = TabFMRegressor()
    except Exception:
        try:
            from tabicl import TabICLRegressor
            MODELES["TabICL (SOTA)"] = TabICLRegressor()
        except Exception:
            pass
    cv = RepeatedKFold(n_splits=5, n_repeats=2, random_state=42)
    metric = "r2"

# ── TRAJECTOIRE 3 : NON-SUPERVISÉ (CLUSTERING) ────────────────────────
elif TYPE_TACHE == "unsupervised":
    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.mixture import GaussianMixture
    try:
        from hdbscan import HDBSCAN
        HAS_HDBSCAN = True
    except ImportError:
        HAS_HDBSCAN = False

    MODELES = {
        "Baseline (K-Means)": KMeans(n_clusters=3, n_init=10, random_state=42),
        "Hiérarchique"      : AgglomerativeClustering(n_clusters=3),
        "GMM (Probabiliste)": GaussianMixture(n_components=3, random_state=42),
    }
    if HAS_HDBSCAN:
        MODELES["HDBSCAN (Density)"] = HDBSCAN(min_cluster_size=5)
    
    cv = None # Pas de CV simple en non-supervisé
    metric = "silhouette"

# ── TRAJECTOIRE 4 : TIME SERIES ──────────────────────────────────────
elif TYPE_TACHE == "timeseries":
    # Note : Le Senior compare ARIMA vs ML avec Lag Features
    from statsmodels.tsa.statespace.sarimax import SARIMAX
    from xgboost import XGBRegressor
    print("📈 Trajectoire TS : ARIMA (Stat) vs XGBoost (ML + Lags)")
    # (Logic de benchmark spécifique TS à implémenter selon le split temporel)
    MODELES = {"XGBoost_TS": XGBRegressor()}
    cv = None
    metric = "mae"

# ── EXÉCUTION DU BANC D'ESSAI ────────────────────────────────────────
for name, model in MODELES.items():
    t0 = time.time()
    try:
        if cv:
            n_jobs = 1 if "TabICL" in name else -1
            scores = cross_val_score(model, X_train_prep, y_train, cv=cv, scoring=metric, n_jobs=n_jobs)
            m_score = scores.mean()
            m_std = scores.std()
        else:
            # Cas non-supervisé / spécifique
            if TYPE_TACHE in ["timeseries", "regression", "classification"]:
                model.fit(X_train_prep, y_train)
            else:
                # Éviter le crash/lenteur extrême de la classification hiérarchique sur les grands datasets
                if name == "Hiérarchique" and X_train_prep.shape[0] > 10000:
                    print(f"      ⚠️ Taille importante ({X_train_prep.shape[0]} lignes). Échantillonnage à 10 000 pour l'algorithme Hiérarchique.")
                    indices = np.random.RandomState(42).choice(X_train_prep.shape[0], 10000, replace=False)
                    model.fit(X_train_prep[indices])
                else:
                    model.fit(X_train_prep)
            m_score = 0 # Calculé plus tard dans evaluation
            m_std = 0
        
        dt = (time.time() - t0) * 1000 # ms
        results[name] = {"score": m_score, "time_ms": dt, "model": model}
        print(f"✅ {name:<20} | {metric.upper()}: {m_score:.4f} | Latence: {dt:.1f}ms")
    except Exception as e:
        print(f"❌ {name:<20} | Erreur: {str(e)[:50]}")

best_name = max(results, key=lambda k: results[k]["score"]) if cv else list(MODELES.keys())[0]
print(f"\n🥇 Modèle retenu pour itération : {best_name}")
```

## Comparatif Multi-dimensionnel

| Dimension | Baseline | Avancé (Champion) | SOTA (Optuna) |
| :--- | :--- | :--- | :--- |
| **Interprétabilité** | Haute (White Box) | Moyenne (Black Box) | Faible (Complex) |
| **Latence Inférence** | < 1ms | ~10-50ms | ~50-100ms |
| **Risque Overfit** | Faible | Modéré | Élevé (nécessite CV) |

```python
# ── Optimisation Finale (si gain > 5%) ───────────────────────────────
import optuna
# ... (Logique Optuna déjà présente dans le template précédent)
```
