#!/usr/bin/env python3
"""
repl_sandbox.py — SOVEREIGN.BI Enterprise Context & Action Layer

Moteur d'exécution REPL sécurisé (Python Sandbox).

Permet à l'agent IA d'exécuter des scripts Python d'analyse de données (Pandas,
NumPy, Neo4j, PostgreSQL) en une seule étape d'exploration.

Environnement pré-chargé :
  - pd (Pandas), np (NumPy), json, os, sys, re, math
  - get_neo4j_driver() : Connexion Bolt à Neo4j
  - get_postgres_conn() : Connexion psycopg2 à PostgreSQL (si installé)
  - load_csv(filename) : Helper pour lire rapidement un CSV du dossier data/

Usage CLI :
  python repl_sandbox.py --script "import pandas as pd; df = load_csv('TB_CLIENT.csv'); print(f'Total clients: {len(df)}')"
  python repl_sandbox.py --input script_tmp.py --output output_tmp.json
"""

import os
import sys
import json
import argparse
import io
import contextlib
import traceback
from pathlib import Path

# Résolution des répertoires pour l'espace de travail Dataset Automator
# Fichier actuel : dataset_automator/py-executors/src/tools/repl_sandbox.py
BASE_DIR = Path(__file__).resolve().parents[4]  # c:\Users\HP\cam_data_sov_solutions newversion
sys.path.insert(0, str(BASE_DIR))

# Imports optionnels sécurisés
try:
    import pandas as pd
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False

try:
    from neo4j import GraphDatabase
    NEO4J_AVAILABLE = True
except ImportError:
    NEO4J_AVAILABLE = False

try:
    import psycopg2
    POSTGRES_AVAILABLE = True
except ImportError:
    POSTGRES_AVAILABLE = False

# ─── Config & Helpers pre-chargés dans la Sandbox ─────────────────────────────

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://127.0.0.1:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

PG_HOST     = os.getenv("DB_HOST",     "127.0.0.1")
PG_PORT     = os.getenv("DB_PORT",     "5432")
PG_NAME     = os.getenv("DB_NAME",     "postgres")
PG_USER     = os.getenv("DB_USER",     "postgres")
PG_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DATA_DIR = BASE_DIR / "data"

def get_neo4j_driver():
    """Retourne un driver Neo4j connecté."""
    if not NEO4J_AVAILABLE:
        raise RuntimeError("Driver neo4j non disponible (pip install neo4j)")
    return GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_postgres_conn():
    """Retourne une connexion PostgreSQL."""
    if not POSTGRES_AVAILABLE:
        raise RuntimeError("Driver psycopg2 non disponible sur ce système (non requis pour Dataset Automator).")
    conn_str = f"host={PG_HOST} port={PG_PORT} dbname={PG_NAME} user={PG_USER} password={PG_PASSWORD}"
    return psycopg2.connect(conn_str)

def load_csv(filename: str, sep: str = ",", encoding: str = "utf-8"):
    """Helper pour charger un fichier CSV du dossier data/ dans un DataFrame Pandas."""
    if not PANDAS_AVAILABLE:
        raise RuntimeError("Pandas non disponible")
    
    filepath = DATA_DIR / filename
    if not filepath.exists():
        # Fallback si le nom ne contient pas .csv
        if not filename.endswith(".csv"):
            filepath = DATA_DIR / f"{filename}.csv"
    
    if not filepath.exists():
        raise FileNotFoundError(f"Fichier introuvable dans data/ : {filename} (recherché dans {DATA_DIR})")
    
    # Essayer le séparateur spécifié, fallback sur auto-détection
    try:
        df = pd.read_csv(filepath, sep=sep, encoding=encoding, low_memory=False)
    except Exception:
        try:
            df = pd.read_csv(filepath, sep=";", encoding=encoding, low_memory=False)
        except Exception:
            df = pd.read_csv(filepath, sep=None, engine="python", encoding=encoding)
            
    # Red-Teaming Parade: Forcer la limite d'affichage pour éviter le goulot IPC (stdio) et le Context Overflow
    pd.options.display.max_rows = 20
    pd.options.display.max_columns = 10
    pd.options.display.max_colwidth = 50
    return df

def query_neo4j(cypher: str, params: dict = None):
    """Helper rapide pour exécuter une requête Cypher et retourner des dicts."""
    driver = get_neo4j_driver()
    with driver.session() as session:
        result = session.run(cypher, params or {})
        records = [dict(record) for record in result]
    driver.close()
    return records

def query_sql(sql: str, params: tuple = None):
    """Helper rapide pour exécuter du SQL sur PostgreSQL."""
    if not POSTGRES_AVAILABLE:
        raise RuntimeError("PostgreSQL non configuré/disponible sur ce projet (non requis pour Dataset Automator).")
    if PANDAS_AVAILABLE:
        conn = get_postgres_conn()
        df = pd.read_sql_query(sql, conn, params=params)
        conn.close()
        return df
    else:
        conn = get_postgres_conn()
        with conn.cursor() as cur:
            cur.execute(sql, params)
            cols = [desc[0] for desc in cur.description] if cur.description else []
            rows = cur.fetchall()
        conn.close()
        return [dict(zip(cols, row)) for row in rows]

# ─── Helpers Data Science & Inspection REPL (Jake VanderPlas Handbook) ──────

def detect_outliers(df: pd.DataFrame, col: str, method: str = "iqr") -> dict:
    """Détecte les outliers d'une colonne selon IQR ou Z-score."""
    if col not in df.columns:
        return {"error": f"Colonne '{col}' inexistante."}
    series = df[col].dropna()
    if method == "zscore":
        mean, std = series.mean(), series.std()
        if std == 0: return {"outliers_count": 0, "pct": 0.0}
        z_scores = (series - mean) / std
        outliers = series[abs(z_scores) > 3]
    else:
        q1, q3 = series.quantile(0.25), series.quantile(0.75)
        iqr = q3 - q1
        outliers = series[(series < q1 - 1.5 * iqr) | (series > q3 + 1.5 * iqr)]
    return {
        "column": col,
        "method": method,
        "outliers_count": len(outliers),
        "pct": round(len(outliers) / len(df) * 100, 2),
        "min_outlier": float(outliers.min()) if not outliers.empty else None,
        "max_outlier": float(outliers.max()) if not outliers.empty else None
    }

def calculate_vif(df: pd.DataFrame) -> list:
    """Calcule le VIF (Variance Inflation Factor) des variables numériques."""
    num_df = df.select_dtypes(include=[np.number]).dropna()
    if num_df.shape[1] <= 1:
        return []
    try:
        from statsmodels.stats.outliers_influence import variance_inflation_factor
        from statsmodels.tools.tools import add_constant
        X = add_constant(num_df)
        vif_data = []
        for i in range(1, X.shape[1]):
            vif_val = variance_inflation_factor(X.values, i)
            vif_data.append({"feature": X.columns[i], "vif": round(vif_val, 2)})
        return sorted(vif_data, key=lambda x: x["vif"], reverse=True)
    except Exception as e:
        return [{"error": str(e)}]

def apply_pca(df: pd.DataFrame, n_components: int = 2) -> pd.DataFrame:
    """Applique une PCA sur les variables numériques du DataFrame."""
    num_df = df.select_dtypes(include=[np.number]).dropna()
    if num_df.empty:
        return df
    try:
        from sklearn.decomposition import PCA
        from sklearn.preprocessing import StandardScaler
        X_scaled = StandardScaler().fit_transform(num_df)
        pca = PCA(n_components=n_components)
        components = pca.fit_transform(X_scaled)
        pca_cols = [f"pca_{i+1}" for i in range(n_components)]
        pca_df = pd.DataFrame(components, columns=pca_cols, index=num_df.index)
        res = df.copy()
        for col in pca_cols:
            res[col] = pca_df[col]
        return res
    except Exception as e:
        print(f"⚠️ Erreur PCA: {e}")
        return df

# ─── Bac à Sable d'Exécution (Sandbox) ───────────────────────────────────────

# Blocs de sécurité : modules restreints
FORBIDDEN_KEYWORDS = [
    "import subprocess", "import shutil", "os.system", "os.popen",
    "os.remove", "os.rmdir", "shutil.rmtree", "__import__('os').system",
    "eval(", "exec("
]

def check_script_safety(script_code: str) -> tuple[bool, str]:
    """Vérifie que le script ne contient pas de commandes système destructrices."""
    for kw in FORBIDDEN_KEYWORDS:
        if kw in script_code:
            return False, f"Instruction interdite détectée par la Sandbox REPL : '{kw}'"
    return True, ""

def execute_in_sandbox(script_code: str) -> dict:
    """
    Exécute le script Python dans l'environnement REPL sécurisé avec capture stdout/stderr.
    """
    is_safe, error_msg = check_script_safety(script_code)
    if not is_safe:
        return {
            "status": "BLOCKED",
            "output": "",
            "error": error_msg,
            "result": None,
        }

    # Red-Teaming Parade: Sécurisation stricte des builtins
    safe_builtins = __builtins__.copy() if isinstance(__builtins__, dict) else __builtins__.__dict__.copy()
    for dangerous_func in ['eval', 'exec', 'open', '__import__', 'globals', 'locals', 'compile']:
        safe_builtins.pop(dangerous_func, None)

    # Préparer le dictionnaire des globales réutilisables dans la sandbox
    sandbox_globals = {
        "__builtins__": safe_builtins,
        "json": json,
        "BASE_DIR": BASE_DIR,
        "DATA_DIR": DATA_DIR,
        "get_neo4j_driver": get_neo4j_driver,
        "get_postgres_conn": get_postgres_conn,
        "load_csv": load_csv,
        "query_neo4j": query_neo4j,
        "query_sql": query_sql,
        "detect_outliers": detect_outliers,
        "calculate_vif": calculate_vif,
        "apply_pca": apply_pca,
    }

    if PANDAS_AVAILABLE:
        sandbox_globals["pd"] = pd
    if NUMPY_AVAILABLE:
        sandbox_globals["np"] = np

    # Capture de la sortie standard stdout et stderr
    stdout_capture = io.StringIO()
    stderr_capture = io.StringIO()

    result_var = None

    try:
        with contextlib.redirect_stdout(stdout_capture), contextlib.redirect_stderr(stderr_capture):
            exec(script_code, sandbox_globals)

            # Si le script a défini une variable `result` ou `output`, la récupérer
            if "result" in sandbox_globals:
                result_var = sandbox_globals["result"]
            elif "output" in sandbox_globals:
                result_var = sandbox_globals["output"]

        output_text = stdout_capture.getvalue()
        stderr_text = stderr_capture.getvalue()

        # Rendre le résultat sérialisable en JSON
        serializable_result = None
        if result_var is not None:
            if PANDAS_AVAILABLE and isinstance(result_var, pd.DataFrame):
                serializable_result = result_var.head(50).to_dict(orient="records")
            else:
                try:
                    json.dumps(result_var)
                    serializable_result = result_var
                except TypeError:
                    serializable_result = str(result_var)
        # Red-Teaming Parade: Troncature obligatoire pour éviter le Context Overflow
        MAX_OUTPUT_LENGTH = 3000
        
        final_stdout = stdout_capture.getvalue()
        final_stderr = stderr_capture.getvalue()
        
        if len(final_stdout) > MAX_OUTPUT_LENGTH:
            final_stdout = final_stdout[:MAX_OUTPUT_LENGTH] + f"\n... [TRONQUÉ: Sortie trop longue (>{MAX_OUTPUT_LENGTH} chars)]"
            
        if len(final_stderr) > MAX_OUTPUT_LENGTH:
            final_stderr = final_stderr[:MAX_OUTPUT_LENGTH] + f"\n... [TRONQUÉ: Erreurs trop longues (>{MAX_OUTPUT_LENGTH} chars)]"

        return {
            "status": "SUCCESS",
            "output": final_stdout,
            "error": final_stderr,
            "result": result_var,
        }

    except Exception as e:
        final_stdout = stdout_capture.getvalue()
        error_trace = traceback.format_exc()
        MAX_OUTPUT_LENGTH = 3000
        
        if len(final_stdout) > MAX_OUTPUT_LENGTH:
            final_stdout = final_stdout[:MAX_OUTPUT_LENGTH] + "\n... [TRONQUÉ]"
        if len(error_trace) > MAX_OUTPUT_LENGTH:
            error_trace = error_trace[:MAX_OUTPUT_LENGTH] + "\n... [TRONQUÉ]"

        return {
            "status": "ERROR",
            "output": final_stdout,
            "error": error_trace,
            "result": None,
        }

# ─── Main CLI ─────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="SOVEREIGN.BI REPL Sandbox (Python Execution Engine)")
    parser.add_argument("--script", help="Script Python à exécuter en ligne de commande")
    parser.add_argument("--input",  help="Fichier JSON/Python contenant le script")
    parser.add_argument("--output", help="Fichier JSON de sortie")
    args = parser.parse_args()

    script_code = ""

    if args.script:
        script_code = args.script
    elif args.input:
        input_path = Path(args.input)
        if input_path.suffix == ".json":
            with open(input_path, encoding="utf-8") as f:
                data = json.load(f)
                script_code = data.get("script", "")
        else:
            with open(input_path, encoding="utf-8") as f:
                script_code = f.read()

    if not script_code.strip():
        print(json.dumps({"status": "ERROR", "error": "Aucun script fourni à la Sandbox REPL"}))
        sys.exit(1)

    result = execute_in_sandbox(script_code)

    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(result, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
