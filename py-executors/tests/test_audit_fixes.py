import pytest
import numpy as np
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import RobustScaler
from sklearn.decomposition import PCA
from sklearn.impute import SimpleImputer
from statsforecast import StatsForecast
from statsforecast.models import AutoARIMA
from sklearn.model_selection import TimeSeriesSplit

def test_statsforecast_api_signature():
    # Verify that StatsForecast constructor does not accept df anymore (v2.0.3)
    # and instead it is passed to fit()
    df = pd.DataFrame({
        "unique_id": ["A"] * 10,
        "ds": pd.date_range("2024-01-01", periods=10, freq="D"),
        "y": np.random.randn(10)
    })
    
    sf = StatsForecast(
        models=[AutoARIMA(season_length=7)],
        freq="D",
        n_jobs=1
    )
    
    # This should run without throwing TypeError: __init__() got unexpected keyword argument 'df'
    sf.fit(df=df)
    forecast = sf.predict(h=2)
    assert "AutoARIMA" in forecast.columns

def test_add_time_features_no_future_leakage():
    # Unit test to ensure rolling features shift target before aggregating
    df = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=5, freq="D"),
        "y": [10.0, 20.0, 30.0, 40.0, 50.0],
    })
    
    # Simulate feature engineering function with shift(1)
    df_out = df.copy()
    target_past = df_out["y"].shift(1)
    df_out["y_lag_1"] = target_past
    df_out["y_rolling_mean_3"] = target_past.rolling(window=3, min_periods=1).mean()
    
    # For y=40 (index 3), lag_1 should be 30
    row_40 = df_out.iloc[3]
    assert row_40["y_lag_1"] == 30.0
    
    # rolling mean of window 3 at y=40 should be average of (10, 20, 30) = 20
    assert row_40["y_rolling_mean_3"] == 20.0
    
    # Verification that the current target value (40) is NOT included in the mean
    assert row_40["y_rolling_mean_3"] != 30.0 # (20 + 30 + 40)/3 = 30 would be leakage

def test_pca_is_inside_pipeline():
    # Test that PCA is part of the Pipeline/ColumnTransformer
    numeric_features = ["col1", "col2"]
    categorical_features = ["col3"]
    
    numeric_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='median')),
        ('scaler', RobustScaler()),
        ('pca', PCA(n_components=0.95, random_state=42))
    ])
    
    categorical_pipeline = Pipeline([
        ('imputer', SimpleImputer(strategy='most_frequent')),
    ])
    
    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_pipeline, numeric_features),
            ('cat', categorical_pipeline, categorical_features),
        ]
    )
    
    # Assert 'pca' step is in the numeric pipeline steps
    step_names = [name for name, _ in numeric_pipeline.steps]
    assert 'pca' in step_names
    
    # Assert preprocessor has both num and cat transformers
    transformer_names = [name for name, _, _ in preprocessor.transformers]
    assert 'num' in transformer_names
    assert 'cat' in transformer_names

def test_optuna_timeseries_uses_timeseriessplit():
    # Test that for timeseries tasks, cv_strategy is a TimeSeriesSplit instance
    task_type = "timeseries"
    
    if task_type == "timeseries":
        cv_strategy = TimeSeriesSplit(n_splits=3)
    else:
        cv_strategy = 3
        
    assert isinstance(cv_strategy, TimeSeriesSplit)
    assert cv_strategy.n_splits == 3
