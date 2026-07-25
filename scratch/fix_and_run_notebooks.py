import os
import re
import sys
import glob
from pathlib import Path
import nbformat
from nbconvert.preprocessors import ExecutePreprocessor

# Ensure py-executors/src is in python path
sys.path.append(str(Path(__file__).parent.parent / "py-executors" / "src"))
from notebook_factory import _get_base64_eval_plot

def fix_notebook_cells(nb_path):
    print(f"\n--- Processing: {nb_path} ---")
    nb = nbformat.read(nb_path, as_version=4)
    
    file_path_val = None
    nom_base_val = Path(nb_path).stem.replace("_Analyse_Full_MLOps", "")
    
    # 1. First pass to find variables (like FILE_PATH)
    for cell in nb.cells:
        if cell.cell_type == "code":
            # Extract FILE_PATH
            match = re.search(r'FILE_PATH\s*=\s*r?"([^"]+)"', cell.source)
            if match:
                file_path_val = match.group(1)
            else:
                match = re.search(r"FILE_PATH\s*=\s*r?'([^']+)'", cell.source)
                if match:
                    file_path_val = match.group(1)

    print(f"Detected Nom Base: {nom_base_val}")
    print(f"Detected File Path: {file_path_val}")

    # 2. Modify cells
    modified = False
    for cell in nb.cells:
        # A. Setup cell: Inject MLflow Allow File Store
        if cell.cell_type == "code" and "mlflow.set_tracking_uri" in cell.source:
            if "MLFLOW_ALLOW_FILE_STORE" not in cell.source:
                print("   -> Injecting MLFLOW_ALLOW_FILE_STORE in Setup")
                cell.source = cell.source.replace(
                    "mlflow_dir = Path(OUTPUT_DIR) / 'mlruns'",
                    "import os\nos.environ[\"MLFLOW_ALLOW_FILE_STORE\"] = \"true\"\nmlflow_dir = Path(OUTPUT_DIR) / 'mlruns'"
                )
                cell.source = cell.source.replace(
                    "mlflow_dir = Path(OUTPUT_DIR) / 'mlruns'",
                    "import os\nos.environ[\"MLFLOW_ALLOW_FILE_STORE\"] = \"true\"\nmlflow_dir = Path(OUTPUT_DIR) / 'mlruns'"
                )
                modified = True

        # B. Benchmarking cell: Fix fit with y_train if supervised
        if cell.cell_type == "code" and "cross_val_score" in cell.source and "model.fit(X_train_prep)" in cell.source:
            print("   -> Fixing fit call in Benchmarking")
            cell.source = cell.source.replace(
                "model.fit(X_train_prep)",
                'if TYPE_TACHE in ["timeseries", "regression", "classification"]:\n                model.fit(X_train_prep, y_train)\n            else:\n                model.fit(X_train_prep)'
            )
            modified = True

        # C. Evaluation cell: Fix NotFittedError and support advanced models
        if cell.cell_type == "code" and "results[best_name][\"model\"]" in cell.source and "best_model = results" in cell.source:
            if "check_is_fitted" not in cell.source:
                print("   -> Fixing model fit validation in Evaluation")
                target_content = 'best_model = results[best_name]["model"]\n# Gestion hybride predict / fit_predict'
                replacement_content = """# Sélection du modèle à évaluer : final_model si entraîné, sinon stacking_model s'il est là, sinon best_model
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

# Gestion hybride predict / fit_predict"""
                cell.source = cell.source.replace(target_content, replacement_content)
                modified = True

        # D. Timeseries Evaluation cell: Fix retrieval & fitting
        if cell.cell_type == "code" and "best_result = results[best_name]" in cell.source and "model_type = best_result" in cell.source:
            if "check_is_fitted" not in cell.source:
                print("   -> Fixing timeseries model fit validation in Evaluation")
                target_content = """# ── Récupération du meilleur modèle ──────────────────────────────────
best_result = results[best_name]
model_type = best_result.get('type', 'ML')"""
                replacement_content = """# ── Récupération du meilleur modèle ──────────────────────────────────
if 'final_model' in globals():
    best_model = final_model
    best_name = "Final Model (Pseudo-Labeling)"
    model_type = "ML"
    print("Using final_model (Pseudo-Labeling) for evaluation")
elif 'stacking_model' in globals():
    best_model = stacking_model
    best_name = "Stacking Model"
    model_type = "ML"
    print("Using stacking_model for evaluation")
else:
    best_result = results[best_name]
    model_type = best_result.get('type', 'ML')
    best_model = best_result['model']

# Check if model is fitted, if not, fit it
if model_type == "ML" and TYPE_TACHE == "timeseries":
    from sklearn.utils.validation import check_is_fitted
    from sklearn.exceptions import NotFittedError
    try:
        check_is_fitted(best_model)
    except NotFittedError:
        print(f"⏳ Fitting {best_name} on X_train_prep...")
        best_model.fit(X_train_prep, y_train)"""
                cell.source = cell.source.replace(target_content, replacement_content)
                modified = True

        # E. Update Visual Evaluation Plot
        if cell.cell_type == "markdown" and ("![Rapport Visuel]" in cell.source or "{EVAL_PLOT}" in cell.source or "Aucun graphique d'évaluation visuelle disponible" in cell.source):
            print("   -> Updating Visual Evaluation Plot Image")
            new_img_md = _get_base64_eval_plot(nom_base_val, file_path_val)
            cell.source = f"## Rapport d'évaluation visuelle\n\n{new_img_md}"
            modified = True

    if modified:
        nbformat.write(nb, nb_path)
        print("   ✅ Notebook successfully fixed on disk.")
    else:
        print("   ℹ️ No modifications required.")
    
    # 3. Execute notebook
    print("   ⏳ Running execution...")
    try:
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        ep.preprocess(nb, {'metadata': {'path': str(Path(nb_path).parent)}})
        # Save executed notebook
        nbformat.write(nb, nb_path)
        print("   ✅ Notebook executed successfully with zero errors!")
        return True
    except Exception as e:
        print(f"   ❌ Execution failed: {e}")
        # Save partially executed notebook with errors to help debug
        nbformat.write(nb, nb_path)
        return False

def main():
    outputs_dir = Path(__file__).parent.parent / "workspace" / "outputs"
    print(f"Scanning notebooks in {outputs_dir}...")
    notebooks = glob.glob(str(outputs_dir / "**" / "*.ipynb"), recursive=True)
    
    # Filter out checkpoint files
    notebooks = [n for n in notebooks if ".ipynb_checkpoints" not in n]
    
    success_count = 0
    failed_count = 0
    
    for nb_path in notebooks:
        success = fix_notebook_cells(nb_path)
        if success:
            success_count += 1
        else:
            failed_count += 1
            
    print("\n==========================================")
    print(f"Verification completed. Success: {success_count}, Failed: {failed_count}")
    print("==========================================")
    
    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
