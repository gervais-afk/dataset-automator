import os
import json
import subprocess
import numpy as np
import matplotlib.pyplot as plt

def run_test():
    scratch_dir = os.path.dirname(os.path.abspath(__file__))
    validator_path = os.path.join(scratch_dir, "..", "py-executors", "src", "tools", "chart_validator.py")
    python_exe = os.path.join(scratch_dir, "..", "py-executors", ".venv", "Scripts", "python.exe")
    
    print("=== STARTING CHART VALIDATOR TESTS ===")
    
    # 1. Créer une image valide (avec du bruit/tracé)
    valid_img_path = os.path.join(scratch_dir, "test_valid.png")
    plt.figure(figsize=(2, 2))
    plt.plot([0, 1], [0, 1])
    plt.savefig(valid_img_path)
    plt.close()
    
    # 2. Créer une image monochrome/vide (écart-type proche de 0)
    blank_img_path = os.path.join(scratch_dir, "test_blank.png")
    # Créer un tableau blanc de 100x100 pixels et le sauvegarder
    blank_data = np.ones((100, 100, 3))
    plt.imsave(blank_img_path, blank_data)
    
    # 3. Chemin pour une image inexistante/corrompue
    missing_img_path = os.path.join(scratch_dir, "test_missing.png")
    if os.path.exists(missing_img_path):
        os.remove(missing_img_path)
        
    def execute_validator(image_path, chart_type, metrics):
        cmd = [
            python_exe,
            validator_path,
            "--image_path", image_path,
            "--chart_type", chart_type,
            "--metrics", json.dumps(metrics)
        ]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            print(f"Error executing validator: {res.stderr}")
            return None
        return json.loads(res.stdout.strip())

    # --- TEST 1 : Classification Confusion Matrix (Valide) ---
    print("\n--- Test 1: Confusion Matrix (Valide) ---")
    metrics_class_ok = {
        "accuracy": 0.85,
        "macro_f1": 0.82,
        "per_class_recall": {"0": 0.80, "1": 0.90}
    }
    res = execute_validator(valid_img_path, "confusion_matrix", metrics_class_ok)
    print(json.dumps(res, indent=2))
    assert res["confirmsMetrics"] == True
    
    # --- TEST 2 : Classification avec Classe Ignorée ---
    print("\n--- Test 2: Confusion Matrix (Classe ignorée) ---")
    metrics_class_bad = {
        "accuracy": 0.50,
        "macro_f1": 0.40,
        "per_class_recall": {"0": 0.00, "1": 0.98}
    }
    res = execute_validator(valid_img_path, "confusion_matrix", metrics_class_bad)
    print(json.dumps(res, indent=2))
    assert res["confirmsMetrics"] == False
    assert any("ignoree" in issue for issue in res["additionalIssues"])
    
    # --- TEST 3 : Classification avec Écart Extrême de Rappel ---
    print("\n--- Test 3: Confusion Matrix (Gap extrême de rappel) ---")
    metrics_class_gap = {
        "accuracy": 0.60,
        "macro_f1": 0.55,
        "per_class_recall": {"0": 0.08, "1": 0.92}
    }
    res = execute_validator(valid_img_path, "confusion_matrix", metrics_class_gap)
    print(json.dumps(res, indent=2))
    assert res["confirmsMetrics"] == False
    assert any("Desequilibre" in issue or "rappel critique" in issue for issue in res["additionalIssues"])
    
    # --- TEST 4 : Résidus Régression (Valide) ---
    print("\n--- Test 4: Residuals (Valide) ---")
    metrics_reg_ok = {
        "r2": 0.75,
        "rmse": 1.2,
        "residuals_skewness": 0.1,
        "heteroscedasticity_p_value": 0.25,
        "residuals_durbin_watson": 1.95
    }
    res = execute_validator(valid_img_path, "residuals", metrics_reg_ok)
    print(json.dumps(res, indent=2))
    assert res["confirmsMetrics"] == True
    
    # --- TEST 5 : Résidus avec Hétéroscédasticité et Autocorrélation ---
    print("\n--- Test 5: Residuals (Anomalies critiques) ---")
    metrics_reg_bad = {
        "r2": 0.05,
        "rmse": 10.5,
        "residuals_skewness": 2.5,
        "heteroscedasticity_p_value": 0.0001,
        "residuals_durbin_watson": 0.5
    }
    res = execute_validator(valid_img_path, "residuals", metrics_reg_bad)
    print(json.dumps(res, indent=2))
    assert res["confirmsMetrics"] == False
    assert len(res["additionalIssues"]) >= 4

    # --- TEST 6 : Image Vide / Monochrome ---
    print("\n--- Test 6: Image Vide/Monochrome ---")
    res = execute_validator(blank_img_path, "confusion_matrix", metrics_class_ok)
    print(json.dumps(res, indent=2))
    assert res["confirmsMetrics"] == False
    assert any("vide ou entierement monochrome" in issue for issue in res["additionalIssues"])
    
    # --- TEST 7 : Image Introuvable ---
    print("\n--- Test 7: Image Introuvable ---")
    res = execute_validator(missing_img_path, "confusion_matrix", metrics_class_ok)
    print(json.dumps(res, indent=2))
    assert res["confirmsMetrics"] == False
    assert any("Image introuvable" in issue for issue in res["additionalIssues"])

    # Nettoyage
    for path_to_del in [valid_img_path, blank_img_path]:
        if os.path.exists(path_to_del):
            os.remove(path_to_del)
            
    print("\n✅ TOUS LES TESTS SONT PASSÉS AVEC SUCCÈS !")

if __name__ == "__main__":
    run_test()
