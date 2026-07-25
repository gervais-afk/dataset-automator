import os
import pytest
import pandas as pd
import numpy as np
from tools.data_contract import DataContract
from tools.mlops_utils import generate_model_card, generate_run_manifest, run_deployment_quality_gate

def test_data_contract_validation():
    # 1. Contrat valide
    df_valid = pd.DataFrame({
        "Date": pd.date_range("2024-01-01", periods=10, freq="D"),
        "Open": np.random.randn(10),
        "Close": np.random.randn(10),
        "Volume": [100.0] * 10
    })
    
    contract = DataContract(
        target_col="Volume",
        task_type="timeseries",
        date_col="Date",
        expected_columns=["Open", "Close", "Volume"]
    )
    
    res = contract.validate(df_valid)
    assert res["status"] == "PASSED"
    assert len(res["anomalies"]) == 0
    
    # 2. Contrat invalide (colonne attendue manquante)
    df_invalid = df_valid.drop(columns=["Close"])
    res_inv = contract.validate(df_invalid)
    assert res_inv["status"] == "FAILED"
    assert any(a["type"] == "missing_columns" for a in res_inv["anomalies"])

def test_mlops_utils_generation(tmp_path):
    output_dir = str(tmp_path)
    metrics = {"accuracy": 0.88, "shap_surrogate_fidelity": 0.94}
    
    # Test Quality Gate
    gate = run_deployment_quality_gate(metrics, "RandomForest", "classification")
    assert gate["status"] == "APPROVED"
    assert gate["checks"]["accuracy_above_threshold"] is True
    
    # Test Model Card
    generate_model_card(output_dir, "test_dataset", "classification", "class", metrics, "RandomForest", gate["status"])
    assert os.path.exists(os.path.join(output_dir, "MODEL_CARD.md"))
    
    # Test Run Manifest
    # Create a dummy CSV file to get hash
    dummy_csv = os.path.join(output_dir, "dummy.csv")
    with open(dummy_csv, "w") as f:
        f.write("col1,col2\n1,2")
        
    generate_run_manifest(output_dir, dummy_csv, "class", "classification", metrics, "RandomForest")
    assert os.path.exists(os.path.join(output_dir, "run_manifest.json"))
