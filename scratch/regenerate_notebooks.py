import os
import re
import sys
import glob
from pathlib import Path
import nbformat
import pandas as pd
import numpy as np
from nbconvert.preprocessors import ExecutePreprocessor

# Ensure py-executors/src is in python path
sys.path.append(str(Path(__file__).parent.parent / "py-executors" / "src"))
from notebook_factory import assemble_notebook_from_steps
from tools.domain_detector import detect_domain

def extract_variables_from_setup(setup_code):
    vars = {}
    for var_name in ["FILE_PATH", "TARGET_COL", "OUTPUT_DIR", "RAW_DIR", "PROCESSED_DIR", "INTERIM_DIR", "MODELS_DIR", "NB_DIR", "DATASET_NAME", "TYPE_TACHE", "DATE_COL", "NOM_BASE"]:
        # Match both single and double quotes, and handle raw strings r"..."
        match = re.search(fr'{var_name}\s*=\s*(?:r?"|r?\')(.*?)(?:"|\')', setup_code)
        if match:
            vars[var_name] = match.group(1)
        else:
            vars[var_name] = ""
    return vars

def regenerate_notebook(nb_path):
    print(f"\n--- Regenerating: {nb_path} ---")
    old_nb = nbformat.read(nb_path, as_version=4)
    
    # 1. Find the setup cell and dynamic cleaning cell in the old notebook
    setup_code = None
    dynamic_clean_cell = None
    
    for cell in old_nb.cells:
        if cell.cell_type == "code":
            if "FILE_PATH" in cell.source and "mlflow.set_tracking_uri" in cell.source:
                setup_code = cell.source
            if "df_clean = df.copy()" in cell.source:
                dynamic_clean_cell = cell
                
    if not setup_code:
        print("   ❌ Setup cell not found in old notebook!")
        return False
        
    vars = extract_variables_from_setup(setup_code)
    file_path = vars["FILE_PATH"]
    target_col = vars["TARGET_COL"]
    nom_base = vars["NOM_BASE"] or Path(nb_path).stem.replace("_Analyse_Full_MLOps", "")
    type_tache = vars["TYPE_TACHE"] or "classification"
    date_col = vars["DATE_COL"]
    
    print(f"   Variables: Nom={nom_base}, Task={type_tache}, Target={target_col}, File={file_path}")
    
    # 2. Build the summary object for the factory
    try:
        df = pd.read_csv(file_path)
        num_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        cat_cols = df.select_dtypes(exclude=[np.number]).columns.tolist()
        nrows = len(df)
        ncols = len(df.columns)
        domain = detect_domain(df, os.path.basename(file_path))
    except Exception as e:
        print(f"   ⚠️ Could not read CSV: {e}. Using fallbacks.")
        num_cols, cat_cols, nrows, ncols = [], [], 0, 0
        domain = "general"
        
    summary = {
        "fichier": file_path,
        "tache_ml": type_tache.upper(),
        "is_timeseries": type_tache.lower() == "timeseries" or type_tache.lower() == "time_series" or bool(date_col),
        "date_col": date_col,
        "domaine": domain,
        "colonnes_numeriques": num_cols,
        "colonnes_categorielles": cat_cols,
        "dimensions": {"lignes": nrows, "colonnes": ncols},
        "cible_suggeree": {"cible": target_col}
    }
    
    # 3. Call the factory to assemble a new notebook from templates
    is_clustering = (type_tache.lower() == "clustering" or type_tache.lower() == "unsupervised" or not bool(target_col))
    
    new_nb, n_cells = assemble_notebook_from_steps(
        file_path=file_path,
        target_col=target_col,
        summary=summary,
        nom_base=nom_base,
        is_clustering=is_clustering,
        algo_clustering="benchmark"
    )
    
    # 4. Inject the dynamic cleaning cell
    if dynamic_clean_cell:
        print("   -> Injecting Dynamic Cleaning Strategy Cell")
        insert_idx = len(new_nb.cells)
        for i, cell in enumerate(new_nb.cells):
            if cell.cell_type == "code" and "df_raw.copy()" in cell.source:
                insert_idx = i + 1
                break
        
        # Insert markdown header + code cell
        clean_md_cell = nbformat.v4.new_markdown_cell("## 🤖 Stratégie de Nettoyage Dynamique (Agent IA)\n\nL'agent a défini et exécuté la stratégie suivante basée sur la connaissance (Graph RAG) :")
        new_nb.cells = new_nb.cells[:insert_idx] + [clean_md_cell, dynamic_clean_cell] + new_nb.cells[insert_idx:]
        
    # Save the clean regenerated notebook
    nbformat.write(new_nb, nb_path)
    print("   ✅ Notebook successfully regenerated and saved.")
    
    # 5. Execute the notebook
    print("   ⏳ Running execution...")
    try:
        ep = ExecutePreprocessor(timeout=600, kernel_name='python3')
        ep.preprocess(new_nb, {'metadata': {'path': str(Path(nb_path).parent)}})
        # Save executed notebook
        nbformat.write(new_nb, nb_path)
        print("   ✅ Notebook executed successfully with zero errors!")
        return True
    except Exception as e:
        print(f"   ❌ Execution failed: {e}")
        # Save partially executed notebook with errors to help debug
        nbformat.write(new_nb, nb_path)
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
        # Re-initialize git checkout for this file first to clear any corrupted replace attempts
        try:
            os.system(f'git checkout "{nb_path}"')
        except:
            pass
            
        success = regenerate_notebook(nb_path)
        if success:
            success_count += 1
        else:
            failed_count += 1
            
    print("\n==========================================")
    print(f"Regeneration completed. Success: {success_count}, Failed: {failed_count}")
    print("==========================================")
    
    if failed_count > 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
