#!/usr/bin/env python3
"""
notebook_validator.py — Agent de Validation du Notebook MLOps Généré
=====================================================================
Vérifie que le notebook généré est :
  1. Syntaxiquement valide (JSON + nbformat)
  2. Structurellement complet (toutes les sections attendues)
  3. Exécutable sans erreur (via nbconvert --execute, optionnel)
  4. Conforme OKF v0.2 (Cellule 0 avec Business Header + Synthèse Stratégique)

Usage :
    python notebook_validator.py [chemin_vers_notebook.ipynb] [--execute]
"""

import sys
import json
import re
import argparse
from pathlib import Path
from datetime import datetime

EXPECTED_MIN_CELLS   = 40
EXPECTED_IDEAL_CELLS = 55
TIMEOUT_PER_CELL_S   = 120

REQUIRED_SECTIONS = [
    ("Business Header (Cellule 0)",      r"(##\s*0\.|0️⃣|COMPRÉHENSION MÉTIER|Business Understanding|CRISP-ML)"),
    ("Analyse Exploratoire (EDA)",       r"#\s*(1|EDA|Analyse|Exploratoire)"),
    ("Traitement des Données",           r"#\s*(2|Nettoyage|Traitement|Cleaning)"),
    ("Benchmarking des Modèles",         r"#\s*(3|Bench|Modèles|Tournament)"),
    ("Évaluation Finale",                r"#\s*(4|Évaluation|Evaluation|Final)"),
    ("Explicabilité (SHAP/LIME)",        r"#\s*(5|SHAP|Explicab|LIME|Explainab)"),
    ("OKF v0.2 Citation",                r"(OKF|okf|GraphRAG|Neo4j|TIER)"),
    ("Raisonnement Agent",               r"(Synthèse|Raisonnement|Stratég|Agent IA)"),
    ("Guardrails Mathématiques",         r"(Durbin|VIF|Overfitting|guardrail|Garde)"),
    ("Import des Librairies",            r"(import pandas|import numpy|import sklearn)"),
    ("Chargement du Dataset",            r"(pd\.read_csv|read_csv|load_data)"),
    ("Entraînement du Modèle",           r"(\.fit\(|champion|TabFM|RandomForest)"),
    ("Métriques de Performance",         r"(accuracy_score|f1_score|classification_report|r2_score)"),
    ("Sauvegarde du Modèle",            r"(skops|joblib|pickle|save_model|model_card)"),
]

def c(text, code): return f"\033[{code}m{text}\033[0m"
def ok(m):   print(c(f"  OK  {m}", "32"))
def warn(m): print(c(f"  WRN {m}", "33"))
def err(m):  print(c(f"  ERR {m}", "31"))
def info(m): print(c(f"  INF {m}", "36"))

def find_latest_notebook(outputs_dir):
    nbs = [n for n in outputs_dir.glob("**/*.ipynb") if ".ipynb_checkpoints" not in str(n)]
    return sorted(nbs, key=lambda p: p.stat().st_mtime, reverse=True)[0] if nbs else None

def load_notebook(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)

def get_all_source(nb):
    parts = []
    for cell in nb.get("cells", []):
        src = cell.get("source", [])
        parts.append("".join(src) if isinstance(src, list) else str(src))
    return "\n".join(parts)

def check_json_format(path):
    try:
        import nbformat
        nb = nbformat.read(str(path), as_version=4)
        nbformat.validate(nb)
        ok(f"Format nbformat v{nb.nbformat}.{nb.nbformat_minor} valide")
        return True
    except Exception as e:
        err(f"Format nbformat invalide : {e}")
        return False

def check_cell_count(nb):
    cells = nb.get("cells", [])
    total = len(cells)
    code  = sum(1 for c in cells if c.get("cell_type") == "code")
    md    = sum(1 for c in cells if c.get("cell_type") == "markdown")
    if total >= EXPECTED_IDEAL_CELLS:
        ok(f"Cellules : {total} >= {EXPECTED_IDEAL_CELLS} ideal | Code:{code} Markdown:{md}")
    elif total >= EXPECTED_MIN_CELLS:
        warn(f"Cellules : {total} (entre {EXPECTED_MIN_CELLS} et {EXPECTED_IDEAL_CELLS}) | Code:{code} Markdown:{md}")
    else:
        err(f"Cellules : {total} < {EXPECTED_MIN_CELLS} minimum | Code:{code} Markdown:{md}")
    return {"total": total, "code": code, "markdown": md, "passed": total >= EXPECTED_MIN_CELLS}

def check_sections(nb):
    src = get_all_source(nb)
    results = []
    for label, pattern in REQUIRED_SECTIONS:
        found = bool(re.search(pattern, src, re.IGNORECASE | re.MULTILINE))
        results.append({"section": label, "found": found})
        if found: ok(f"Section : {label}")
        else:     err(f"ABSENTE : {label}  [pattern={pattern}]")
    return results

def check_cell0(nb):
    """Check first 8 cells for Business Header markers — matches real generated notebook format."""
    cells = nb.get("cells", [])
    # Concat source of first 8 cells (business header may span several markdown cells)
    src = "\n".join(
        "".join(cell.get("source", []))
        for cell in cells[:8]
    )
    checks = [
        # Cell 0 uses emoji + CRISP-ML format: '# ── 0️⃣ COMPRÉHENSION MÉTIER'
        ("Business Header (##0. ou 0️⃣)",   r"(##\s*0\.|0\ufe0f\u20e3|COMPRÉHENSION MÉTIER|Business Understanding|CRISP-ML)"),
        ("OKF v0.2 ou graphe Neo4j",        r"(OKF|okf|graphe de connaissances|Graph RAG|Neo4j|GraphRAG|graph_rag)"),
        ("Synthèse / Stratégie Agent",      r"(Synth[èe]se|Strat[ée]g|strat[ée]gie|nettoyage)"),
        ("Raisonnement Agent IA",           r"(Agent IA|Raisonnement|llm_interpretation|agent a d[ée]fini)"),
        ("Matrice Coûts ou KPIs",           r"(TP|FP|FN|TN|co[ûu]t|b[ée]n[ée]f|KPI|objectif m[ée]tier)"),
        ("Citation Source GraphRAG",        r"(Neo4j|GraphRAG|graph_rag|graph de connaissances|Graph RAG)"),
    ]
    details = []
    for label, pat in checks:
        found = bool(re.search(pat, src, re.IGNORECASE))
        details.append({"check": label, "found": found})
        if found: ok(f"Cellule 0 — {label}")
        else:     warn(f"Cellule 0 — Absent : {label}")
    passed = sum(1 for d in details if d["found"]) >= 4  # at least 4/6 = good
    return {"passed": passed, "details": details}

def check_empty_cells(nb):
    empties = []
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "code":
            src = "".join(cell.get("source", [])).strip()
            if len(src) < 5:
                empties.append(i)
                warn(f"Cellule code vide à l'index {i}")
    if not empties: ok("Aucune cellule code vide")
    return empties

def check_outputs(nb):
    code_cells = [c for c in nb.get("cells", []) if c.get("cell_type") == "code"]
    with_out = sum(1 for c in code_cells if c.get("outputs"))
    
    # Inspection minutieuse des erreurs d'exécution
    errors_found = []
    for idx, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "code":
            for out in cell.get("outputs", []):
                if out.get("output_type") == "error":
                    ename = out.get("ename", "UnknownError")
                    evalue = out.get("evalue", "")
                    errors_found.append({
                        "cell_index": idx,
                        "ename": ename,
                        "evalue": evalue,
                        "snippet": "".join(cell.get("source", []))[:120]
                    })
                    err(f"Cellule {idx} en erreur : {ename} — {evalue[:80]}")

    if errors_found:
        err(f"{len(errors_found)} cellule(s) contiennent des erreurs d'exécution !")
    elif with_out > 0:
        ok(f"Outputs existants : {with_out}/{len(code_cells)} cellules (0 erreur d'exécution détectée ✅)")
    else:
        info(f"Aucun output — notebook fraîchement généré (prêt à l'exécution)")

    return {
        "code_total": len(code_cells),
        "with_outputs": with_out,
        "errors_count": len(errors_found),
        "errors": errors_found,
        "has_runtime_errors": len(errors_found) > 0
    }

def execute_notebook(path):
    print(c("\n  Execution du notebook...", "36"))
    try:
        import nbformat
        from nbconvert.preprocessors import ExecutePreprocessor, CellExecutionError
        nb = nbformat.read(str(path), as_version=4)
        ep = ExecutePreprocessor(timeout=TIMEOUT_PER_CELL_S, kernel_name="python3")
        errors = []
        try:
            ep.preprocess(nb, {"metadata": {"path": str(path.parent)}})
            ok("Notebook execute sans erreur")
            out_path = path.parent / (path.stem + "_executed.ipynb")
            with open(out_path, "w", encoding="utf-8") as f:
                nbformat.write(nb, f)
            info(f"Notebook execute sauvegarde : {out_path}")
        except CellExecutionError as e:
            err(f"Erreur dans une cellule : {e.ename} — {e.evalue}")
            errors.append({"ename": e.ename, "evalue": str(e.evalue)})
        return {"executed": True, "errors": errors}
    except ImportError:
        warn("nbconvert non disponible (pip install nbconvert)")
        return {"executed": False, "reason": "nbconvert not installed"}
    except Exception as e:
        err(f"Erreur execution : {e}")
        return {"executed": False, "errors": [str(e)]}

def run_validation(notebook_path, execute=False):
    print(c(f"\n{'='*65}", "34"))
    print(c(f"  AGENT DE VALIDATION NOTEBOOK MLOPS — Dataset Automator", "1;34"))
    print(c(f"  Fichier : {notebook_path.name}", "34"))
    print(c(f"  Date    : {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", "34"))
    print(c(f"{'='*65}\n", "34"))

    report = {"notebook": str(notebook_path), "timestamp": datetime.now().isoformat(), "checks": {}}

    try:
        nb = load_notebook(notebook_path)
        ok(f"Notebook charge : {notebook_path}")
    except Exception as e:
        err(f"Impossible de charger le notebook : {e}")
        return report

    print(c("\n[1] Format nbformat", "1;36"))
    report["checks"]["format"] = check_json_format(notebook_path)

    print(c("\n[2] Comptage des Cellules", "1;36"))
    report["checks"]["cell_count"] = check_cell_count(nb)

    print(c("\n[3] Sections Obligatoires", "1;36"))
    report["checks"]["sections"] = check_sections(nb)
    found = sum(1 for s in report["checks"]["sections"] if s["found"])
    total = len(REQUIRED_SECTIONS)
    print(c(f"\n  => {found}/{total} sections presentes", "32" if found == total else "33"))

    print(c("\n[4] Cellule 0 — Business Header OKF v0.2", "1;36"))
    report["checks"]["cell0"] = check_cell0(nb)

    print(c("\n[5] Cellules Vides", "1;36"))
    report["checks"]["empty_cells"] = check_empty_cells(nb)

    print(c("\n[6] Outputs d'Execution", "1;36"))
    report["checks"]["outputs"] = check_outputs(nb)

    if execute:
        print(c("\n[7] Execution Complete", "1;36"))
        report["checks"]["execution"] = execute_notebook(notebook_path)

    # Score calculation
    cc    = report["checks"].get("cell_count", {})
    outs  = report["checks"].get("outputs", {})
    score = 0
    if report["checks"].get("format"):                           score += 20
    if cc.get("total", 0) >= EXPECTED_MIN_CELLS:                 score += 20
    if cc.get("total", 0) >= EXPECTED_IDEAL_CELLS:               score += 10
    score += int((found / max(total, 1)) * 40)
    if report["checks"].get("cell0", {}).get("passed"):          score += 10

    # Pénalité si erreurs d'exécution détectées dans les outputs
    if outs.get("has_runtime_errors"):
        err_penalty = min(outs.get("errors_count", 1) * 15, 40)
        score = max(0, score - err_penalty)
        warn(f"Pénalité d'exécution appliquée : -{err_penalty} pts ({outs.get('errors_count')} cellule(s) en erreur)")

    grade = "EXCELLENT" if score >= 90 else "BON" if score >= 70 else "MOYEN" if score >= 50 else "INSUFFISANT"
    gc = "32" if score >= 70 else "33" if score >= 50 else "31"

    print(c(f"\n{'='*65}", "34"))
    print(c(f"  SCORE : {score}/100  —  {grade}", f"1;{gc}"))
    print(c(f"  Cellules:{cc.get('total',0)}  Sections:{found}/{total}  Format:{'OK' if report['checks'].get('format') else 'KO'}  Erreurs:{outs.get('errors_count', 0)}", gc))
    print(c(f"{'='*65}\n", "34"))

    report["score"] = score
    report["grade"] = grade

    report_path = notebook_path.parent / (notebook_path.stem + "_validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    info(f"Rapport JSON : {report_path}")
    return report

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Agent Validateur Notebook MLOps")
    parser.add_argument("notebook", nargs="?", help="Chemin .ipynb (auto-detect si absent)")
    parser.add_argument("--execute", action="store_true", help="Executer le notebook via nbconvert")
    args = parser.parse_args()

    if args.notebook:
        nb_path = Path(args.notebook)
    else:
        base = Path(__file__).resolve().parent.parent
        nb_path = find_latest_notebook(base / "workspace" / "outputs")
        if not nb_path:
            print(c("Aucun notebook dans workspace/outputs/", "31"))
            sys.exit(1)
        print(c(f"Auto-detection : {nb_path}", "33"))

    if not nb_path.exists():
        print(c(f"Fichier introuvable : {nb_path}", "31"))
        sys.exit(1)

    report = run_validation(nb_path, execute=args.execute)
    sys.exit(0 if report.get("score", 0) >= 50 else 1)
