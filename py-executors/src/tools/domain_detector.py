"""
Détecte automatiquement le domaine métier et le type de données
pour router vers le bon pipeline de notebooks.
"""

import re
import json
import numpy  as np
import pandas as pd
from dataclasses import dataclass
from typing      import Optional


@dataclass
class DataProfile:
    """
    Profil complet d'un dataset.
    Détermine le pipeline optimal à générer.
    """
    # ── Type de tâche ─────────────────────────────────────────────
    task_type      : str   = "regression"
    # classification | regression | clustering |
    # timeseries | multilabel | anomaly_detection

    # ── Domaine métier ────────────────────────────────────────────
    domain         : str   = "general"
    # medical | finance | ecommerce | hr | environment | general

    # ── Caractéristiques dataset ──────────────────────────────────
    has_datetime   : bool  = False
    has_text       : bool  = False
    has_geo        : bool  = False
    is_imbalanced  : bool  = False
    has_missing    : bool  = False
    n_classes      : int   = 0
    is_multilabel  : bool  = False
    is_timeseries  : bool  = False

    # ── Cible ─────────────────────────────────────────────────────
    target_col     : str   = ""
    target_type    : str   = ""   # binary | multiclass | continuous
    date_col       : str   = ""   # Pour les séries temporelles

    # ── Recommandations ───────────────────────────────────────────
    recommended_models   : list = None
    recommended_metrics  : list = None
    preprocessing_flags  : list = None

    def __post_init__(self):
        if self.recommended_models  is None: self.recommended_models  = []
        if self.recommended_metrics is None: self.recommended_metrics = []
        if self.preprocessing_flags is None: self.preprocessing_flags = []


# ── Signatures de domaine ─────────────────────────────────────────

_DOMAIN_SIGNATURES = {
    "medical": {
        "columns" : [
            "diagnosis", "disease", "patient", "age", "bmi",
            "glucose", "insulin", "blood", "pressure", "cancer",
            "tumor", "malignant", "benign", "obesity", "diabetes",
            "cholesterol", "hemoglobin", "weight", "height",
        ],
        "filename": ["wdbc", "diabetes", "cancer", "medical",
                     "obesity", "heart", "breast"],
    },
    "finance": {
        "columns" : [
            "price", "open", "close", "high", "low", "volume",
            "return", "yield", "revenue", "profit", "loss",
            "btc", "stock", "crypto", "asset", "portfolio",
        ],
        "filename": ["btc", "stock", "finance", "crypto",
                     "asset", "trading", "forex"],
    },
    "ecommerce": {
        "columns" : [
            "sales", "revenue", "order", "customer", "product",
            "category", "quantity", "discount", "shipping",
            "rating", "review", "cart", "transaction",
        ],
        "filename": ["ecommerce", "sales", "shop", "retail",
                     "commerce", "amazon"],
    },
    "hr": {
        "columns" : [
            "employee", "salary", "department", "position",
            "attrition", "performance", "hire", "tenure",
            "gender", "education", "satisfaction",
        ],
        "filename": ["hr", "employee", "attrition", "workforce",
                     "human_resources"],
    },
    "environment": {
        "columns" : [
            "temperature", "humidity", "pollution", "co2",
            "rainfall", "wind", "pressure", "emission",
            "energy", "solar", "consumption",
        ],
        "filename": ["weather", "climate", "environment",
                     "energy", "pollution"],
    },
}


def detect_domain(
    df      : pd.DataFrame,
    filename: str = "",
) -> str:
    """
    Détecte le domaine métier depuis les noms de colonnes et le nom de fichier.
    """
    scores      = {domain: 0 for domain in _DOMAIN_SIGNATURES}
    cols_lower  = [c.lower() for c in df.columns]
    file_lower  = filename.lower()

    for domain, sigs in _DOMAIN_SIGNATURES.items():
        # Score colonnes
        for col in cols_lower:
            if any(sig in col for sig in sigs["columns"]):
                scores[domain] += 2

        # Score nom de fichier (plus fiable)
        if any(sig in file_lower for sig in sigs["filename"]):
            scores[domain] += 3

    best_domain = max(scores, key=scores.get)
    best_score  = scores[best_domain]

    return best_domain if best_score >= 2 else "general"


def detect_timeseries(df: pd.DataFrame) -> tuple[bool, Optional[str]]:
    """Détecte si le dataset est une série temporelle."""
    # ── Test par mots-clés de colonnes (Forcé) ──────────────────
    for col in df.columns:
        col_lower = col.lower()
        if any(kw in col_lower for kw in ["date", "time", "timestamp", "datetime", "year", "month"]):
            return True, col

    # ── Test par contenu de fichier (Forcé) ──────────────────────
    if any(kw in str(df.columns).lower() for kw in ["btc", "crypto", "price", "volume"]):
        # On cherche la première colonne qui ressemble à une date ou l'index
        return True, df.columns[0]

    return False, None


def detect_imbalance(
    y         : pd.Series,
    threshold : float = 0.15,
) -> bool:
    """
    Détecte un déséquilibre de classes (classification).
    """
    if y.dtype == object or y.nunique() <= 20:
        counts = y.value_counts(normalize=True)
        return float(counts.min()) < threshold
    return False


def build_data_profile(
    df      : pd.DataFrame,
    filename: str = "",
) -> DataProfile:
    """
    Construit le profil complet du dataset.
    """
    profile = DataProfile()

    # ── Domaine ───────────────────────────────────────────────────
    profile.domain = detect_domain(df, filename)

    # ── Série temporelle ──────────────────────────────────────────
    profile.is_timeseries, ts_col = detect_timeseries(df)
    profile.has_datetime          = profile.is_timeseries
    profile.date_col              = ts_col if ts_col else ""

    # ── Colonnes texte ────────────────────────────────────────────
    text_cols = [
        c for c in df.columns
        if df[c].dtype == object
        and df[c].apply(lambda x: len(str(x))).mean() > 50   # Texte long → probable NLP
    ]
    profile.has_text = len(text_cols) > 0

    # ── Valeurs manquantes ────────────────────────────────────────
    profile.has_missing = bool(df.isna().any().any())

    # ── Détection cible et tâche ──────────────────────────────────
    profile = _detect_task(df, profile)

    # ── Modèles et métriques recommandés ─────────────────────────
    profile = _recommend_pipeline(profile)

    return profile


def _detect_task(df: pd.DataFrame, profile: DataProfile) -> DataProfile:
    """Détecte la tâche ML et la cible optimale avec heuristiques avancées."""

    col_cat = df.select_dtypes(exclude=np.number).columns.tolist()
    col_num = df.select_dtypes(include=np.number).columns.tolist()
    all_cols = [c.lower() for c in df.columns]

    # ── Heuristique CLUSTERING (Priorité Haute pour Segmentation) ──
    # Si Ecommerce + colonnes d'ID + pas de cible évidente -> Clustering
    segmentation_kws = ["customer", "client", "user", "visitor", "id", "segment"]
    has_seg_signal = any(any(kw in c for kw in segmentation_kws) for c in all_cols)
    
    if profile.domain in ["ecommerce", "hr"] and has_seg_signal:
        # Si on n'a pas de cible catégorielle claire (ex: Churn), le clustering est plus probable
        has_clear_target = any(kw in c for c in all_cols for kw in ["target", "label", "class", "churn"])
        if not has_clear_target:
            profile.task_type = "clustering"
            profile.target_col = "" # Pas de cible en non-supervisé
            return profile

    # ── Priorité 1 : Série temporelle ────────────────────────────
    if profile.is_timeseries:
        profile.task_type  = "timeseries"
        # On prend la dernière colonne numérique comme cible par défaut pour les TS
        profile.target_col = col_num[-1] if col_num else ""
        return profile

    # ── Priorité 2 : Cible catégorielle ──────────────────────────
    # On cherche souvent la dernière colonne pour la cible
    for col in reversed(col_cat):
        n_unique = df[col].nunique()
        # Une cible ne doit pas être un ID (trop de valeurs uniques)
        if 2 <= n_unique <= 20 and (n_unique / len(df) < 0.5):
            profile.task_type   = "classification"
            profile.target_col  = col
            profile.target_type = "binary" if n_unique == 2 else "multiclass"
            profile.n_classes   = n_unique
            if n_unique == 2:
                profile.is_imbalanced = detect_imbalance(df[col])
            return profile

    # ── Priorité 3 : Numérique à faible cardinalité ───────────────
    for col in reversed(col_num):
        n_unique = df[col].nunique()
        if 2 <= n_unique <= 10 and (n_unique / len(df) < 0.05):
            profile.task_type   = "classification"
            profile.target_col  = col
            profile.target_type = "binary" if n_unique == 2 else "multiclass"
            profile.n_classes   = n_unique
            return profile

    # ── Priorité 4 : Régression ───────────────────────────────────
    if col_num:
        # On prend la dernière colonne numérique comme cible par défaut
        profile.task_type   = "regression"
        profile.target_col  = col_num[-1]
        profile.target_type = "continuous"
        return profile

    # ── Fallback : Clustering ─────────────────────────────────────
    profile.task_type = "clustering"
    return profile


def _recommend_pipeline(profile: DataProfile) -> DataProfile:
    """
    Recommande modèles, métriques et flags preprocessing
    """
    _MODELS = {
        "classification": [
            "LogisticRegression", "RandomForestClassifier",
            "GradientBoostingClassifier", "SVC",
        ],
        "regression": [
            "Ridge", "Lasso",
            "RandomForestRegressor", "GradientBoostingRegressor",
        ],
        "clustering": [
            "KMeans", "DBSCAN", "AgglomerativeClustering",
        ],
        "timeseries": [
            "ARIMA", "ExponentialSmoothing", "LinearRegression(trend)",
        ],
    }

    _METRICS = {
        "binary"      : ["accuracy", "f1", "roc_auc", "precision", "recall"],
        "multiclass"  : ["accuracy", "f1_weighted", "cohen_kappa"],
        "continuous"  : ["r2", "rmse", "mae"],
        "clustering"  : ["silhouette", "davies_bouldin", "calinski_harabasz"],
        "timeseries"  : ["mae", "mape", "rmse"],
    }

    profile.recommended_models  = _MODELS.get(profile.task_type, [])
    profile.recommended_metrics = _METRICS.get(
        profile.target_type or profile.task_type, []
    )

    flags = []
    if profile.has_missing   : flags.append("imputation")
    if profile.is_imbalanced : flags.append("smote_or_weights")
    if profile.has_text      : flags.append("tfidf_or_embed")
    if profile.has_datetime  : flags.append("time_features")
    if profile.domain == "medical": flags.append("feature_importance_shap")

    profile.preprocessing_flags = flags
    return profile
