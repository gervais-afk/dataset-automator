"""
Assemblage de notebooks Jupyter depuis des templates Markdown.
Gère la substitution des variables et la construction des cellules.
"""

import re
import json
import nbformat
import sys
import os
from pathlib import Path
from typing  import Optional, Tuple
import pandas as pd
import numpy as np

# Import local pour le routing intelligent
try:
    from tools.domain_detector import DataProfile, build_data_profile
except ImportError:
    # Fallback si non trouvé
    class DataProfile: pass
    def build_data_profile(df, filename): return DataProfile()

_STEPS_DIR = Path("templates/notebook_steps")


# ══════════════════════════════════════════════════════════════════
# SUBSTITUTION DES VARIABLES
# ══════════════════════════════════════════════════════════════════

def _substitute_vars(content: str, variables: dict) -> str:
    """Substitue TOUS les placeholders {VAR} dans un template Markdown."""
    result = content
    for key, value in variables.items():
        placeholder = "{" + key + "}"
        result      = result.replace(placeholder, str(value))

    # ✅ CORRECTION : Variables dynamiques à exclure de la validation (définies à l'exécution)
    DYNAMIC_VARS = {'NEEDS_DIFF', 'adf_result', 'p_value', 'TARGET_COL', 'DATE_COL', 'EVAL_PLOT'}
    
    # Signalement des oublis (Variables en MAJUSCULES uniquement)
    remaining = re.findall(r'\{([A-Z][A-Z0-9_]{2,})\}', result)
    remaining = set(remaining) - DYNAMIC_VARS
    
    if remaining:
        print(f"   ⚠️  Placeholders non substitués : {remaining}", file=sys.stderr)
    return result


def _get_base64_eval_plot(nom_base: str) -> str:
    """Recherche le dernier graphique généré dans les dossiers d'artifacts et le retourne encodé en Base64."""
    import base64
    import glob
    import os
    from pathlib import Path
    
    paths = [
        Path("outputs") / nom_base / "*.png",
        Path("outputs") / nom_base / "models" / "*.png",
        Path("workspace/models_artifacts/*.png"),
        Path("dataset_automator/workspace/models_artifacts/*.png"),
        Path("../workspace/models_artifacts/*.png"),
        Path("../../dataset_automator/workspace/models_artifacts/*.png"),
    ]
    
    all_files = []
    for pattern in paths:
        matches = glob.glob(str(pattern))
        for m in matches:
            filename = Path(m).name.lower()
            if any(k in filename for k in ["cm_", "residuals_", "evaluation", "plot", "confusion"]):
                all_files.append(m)
                
    if not all_files:
        return "*Aucun graphique d'évaluation visuelle disponible pour cette session.*"
        
    latest_file = max(all_files, key=os.path.getmtime)
    try:
        with open(latest_file, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"![Rapport Visuel](data:image/png;base64,{encoded})"
    except Exception as e:
        return f"*Erreur lors de l'intégration de l'image d'évaluation : {e}*"


def _build_variables(
    file_path      : str,
    target_col     : str,
    summary        : dict,
    nom_base       : str,
    type_tache     : str,
    algo_clustering: str,
    date_col       : str = "",
) -> dict:
    """
    Construit la table de substitution complète.
    Règle critique : FILE_PATH toujours en chemin ABSOLU
    pour que le notebook fonctionne quel que soit le CWD.
    """
    
    # ✅ VALIDATION CRITIQUE
    if not target_col or target_col == "":
        print("   ⚠️ ALERTE : Variable cible non définie dans les paramètres.", file=sys.stderr)
        print("   → Le notebook tentera une auto-détection dans le Setup.", file=sys.stderr)
        
    file_path_abs = Path(file_path).resolve().as_posix()
    out_dir_abs   = (Path("outputs") / nom_base).resolve().as_posix()
    raw_dir_abs   = (Path("outputs") / nom_base / "data" / "raw").resolve().as_posix()
    proc_dir_abs  = (Path("outputs") / nom_base / "data" / "processed").resolve().as_posix()
    interim_dir_abs = (Path("outputs") / nom_base / "data" / "interim").resolve().as_posix()
    models_dir_abs = (Path("outputs") / nom_base / "models").resolve().as_posix()
    src_dir_abs   = (Path("outputs") / nom_base / "src").resolve().as_posix()
    nb_dir_abs    = (Path("outputs") / nom_base / "notebooks").resolve().as_posix()
    
    dims     = summary.get("dimensions", {})

    # ── Normalisation TYPE_TACHE ──────────────────────────────────
    _TACHE_MAP = {
        "clustering"    : "unsupervised",
        "unsupervised"  : "unsupervised",
        "classification": "classification",
        "regression"    : "regression",
        "timeseries"    : "timeseries",
    }
    type_tache_norm = _TACHE_MAP.get(type_tache.lower(), type_tache)

    return {
        "FILE_PATH"      : file_path_abs,
        "OUTPUT_DIR"     : out_dir_abs,
        "RAW_DIR"        : raw_dir_abs,
        "PROCESSED_DIR"  : proc_dir_abs,
        "INTERIM_DIR"    : interim_dir_abs,
        "MODELS_DIR"     : models_dir_abs,
        "SRC_DIR"        : src_dir_abs,
        "NB_DIR"         : nb_dir_abs,
        "NOM_BASE"       : nom_base,
        "DATASET_NAME"   : nom_base,
        "TARGET_COL"     : target_col,
        "TYPE_TACHE"     : type_tache_norm,
        "TACHE_ML"       : type_tache_norm,
        "CLUSTERING_ALGO": algo_clustering,
        "DATE_COL"       : date_col,
        "DOMAIN"         : summary.get("domaine", "general"),
        "N_ROWS"         : str(dims.get("lignes",   "?")),
        "N_COLS"         : str(dims.get("colonnes", "?")),
        "NUM_COLS_LIST"  : str(summary.get("colonnes_numeriques",    [])),
        "CAT_COLS_LIST"  : str(summary.get("colonnes_categorielles", [])),
        "NEEDS_DIFF"     : "{NEEDS_DIFF}",
        "EVAL_PLOT"      : _get_base64_eval_plot(nom_base),
    }


# ══════════════════════════════════════════════════════════════════
# SÉLECTION DES STEPS (ROUTING UNIVERSEL)
# ══════════════════════════════════════════════════════════════════

def _pick_step(preferred: str, fallback: str) -> Optional[str]:
    """Retourne preferred si existant, sinon fallback."""
    if (_STEPS_DIR / preferred).exists():
        return preferred
    if (_STEPS_DIR / fallback).exists():
        return fallback
    return None


def _get_steps_universal(
    profile        : DataProfile,
    steps_filter   : Optional[list] = None,
) -> list[str]:
    """
    Sélectionne les steps selon le profil complet du dataset (Phase 2).
    """
    # ── Routing par type de tâche ─────────────────────────────────
    if getattr(profile, "is_timeseries", False):
        slots = [
            ("00_setup_timeseries.md",         "00_setup_et_split.md"),
            ("01_analyse_exploratoire_eda.md",  "01_analyse_exploratoire_eda.md"),
            ("02_feature_engineering.md",       "02_preprocessing_pipelines.md"),
            ("03_timeseries_models.md",         "03_benchmarking_modeles.md"),
            ("03b_advanced_training.md",        "03_benchmarking_modeles.md"),
            ("04_evaluation_timeseries.md",     "04_evaluation_finale.md"),
            ("05_mlops_monitoring.md",          "05_mlops_monitoring.md"),
            ("06_rapport_narratif.md",          "06_rapport_narratif.md"),
        ]

    elif getattr(profile, "task_type", "") == "clustering":
        slots = [
            ("00_setup_et_split.md",              "00_setup_et_split.md"),
            ("01_analyse_exploratoire_eda.md",    "01_analyse_exploratoire_eda.md"),
            ("02_preprocessing_clustering.md",    "02_preprocessing_pipelines.md"),
            ("03_clustering_benchmark.md",        "03_benchmarking_modeles.md"),
            ("03b_advanced_training.md",          "03_benchmarking_modeles.md"),
            ("04_evaluation_clustering.md",       "04_evaluation_finale.md"),
            ("05_mlops_monitoring.md",            "05_mlops_monitoring.md"),
            ("06_rapport_narratif.md",            "06_rapport_narratif.md"),
        ]

    elif getattr(profile, "is_imbalanced", False):
        slots = [
            ("00_setup_et_split.md",              "00_setup_et_split.md"),
            ("01_analyse_exploratoire_eda.md",    "01_analyse_exploratoire_eda.md"),
            ("02_preprocessing_pipelines.md",     "02_preprocessing_pipelines.md"),
            ("02_imbalanced_handling.md",         "02_preprocessing_pipelines.md"),
            ("03_benchmarking_modeles.md",        "03_benchmarking_modeles.md"),
            ("03b_advanced_training.md",          "03_benchmarking_modeles.md"),
            ("04_evaluation_finale.md",           "04_evaluation_finale.md"),
            ("05_mlops_monitoring.md",            "05_mlops_monitoring.md"),
            ("06_rapport_narratif.md",            "06_rapport_narratif.md"),
        ]

    else:   # regression + classification équilibrée
        slots = [
            ("00_setup_et_split.md",              "00_setup_et_split.md"),
            ("01_analyse_exploratoire_eda.md",    "01_analyse_exploratoire_eda.md"),
            ("02_preprocessing_pipelines.md",     "02_preprocessing_pipelines.md"),
            ("03_benchmarking_modeles.md",        "03_benchmarking_modeles.md"),
            ("03b_advanced_training.md",          "03_benchmarking_modeles.md"),
            ("04_evaluation_finale.md",           "04_evaluation_finale.md"),
            ("05_mlops_monitoring.md",            "05_mlops_monitoring.md"),
            ("06_rapport_narratif.md",            "06_rapport_narratif.md"),
        ]

    # ── Résolution ────────────────────────────────────────────────
    steps = []
    seen  = set()
    for preferred, fallback in slots:
        chosen = _pick_step(preferred, fallback)
        if chosen and chosen not in seen:
            steps.append(chosen)
            seen.add(chosen)

    if steps_filter:
        steps = [s for s in steps if any(s.startswith(f) for f in steps_filter)]

    return steps


# ══════════════════════════════════════════════════════════════════
# ASSEMBLAGE PRINCIPAL
# ══════════════════════════════════════════════════════════════════

def assemble_notebook_from_steps(
    file_path      : str,
    target_col     : str,
    summary        : dict,
    nom_base       : str,
    is_clustering  : bool = False,
    algo_clustering: str  = "benchmark",
    steps_filter   : Optional[list] = None,
) -> tuple:
    """Assemble un notebook avec routing intelligent (Phase 2)."""
    
    tache_ml = summary.get("tache_ml", "REGRESSION")
    date_col = summary.get("date_col", "")

    # ── PRIORITÉ DES TÂCHES ───────────────────────────────────────
    # On respecte le choix explicite de l'utilisateur (is_clustering) 
    # même si des dates sont présentes.
    
    is_ts_detected = (
        summary.get("is_timeseries", False)
        or tache_ml.upper() == "TIMESERIES"
        or bool(date_col)
    )

    # Le clustering est effectif si demandé, SAUF si c'est explicitement une TS pure (BTC etc.)
    # sans signal de segmentation.
    is_clustering_effective = is_clustering
    is_ts = is_ts_detected and not is_clustering_effective

    # type_tache pour l'affichage et les templates
    if is_ts:
        type_tache = "timeseries"
    elif is_clustering_effective:
        type_tache = "unsupervised"
    else:
        type_tache = tache_ml.lower()

    # ── Table de substitution ─────────────────────────────────────
    variables = _build_variables(
        file_path       = file_path,
        target_col      = target_col,
        summary         = summary,
        nom_base        = nom_base,
        type_tache      = type_tache,
        algo_clustering = algo_clustering,
        date_col        = date_col,
    )
    # ── Sélection steps : TOUJOURS les templates riches ────────────
    # Les IDs PageIndex de l'agent (1.0, 2.0, etc.) pointent vers
    # des snippets JSON de ~100 chars. Les templates .md font ~5 KB chacun.
    # → On utilise TOUJOURS les templates, quelle que soit l'entrée de l'agent.
    
    from types import SimpleNamespace
    profile = SimpleNamespace(
        is_timeseries=is_ts,
        task_type="clustering" if is_clustering_effective else tache_ml.lower(),
        is_imbalanced=summary.get("is_imbalanced", False)
    )
    steps = _get_steps_universal(profile, None)

    # Si les templates sont vides (dossier manquant), fallback sur les IDs PageIndex
    if not steps and steps_filter:
        print("   ⚠️ Aucun template trouvé, fallback sur IDs PageIndex")
        steps = steps_filter

    # ── Notebook ──────────────────────────────────────────────────
    nb = nbformat.v4.new_notebook()
    nb.metadata.update({
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python", "version": "3.10"},
    })

    print(f"\n   📚 {len(steps)} step(s) à assembler :", file=sys.stderr)
    print(f"   🔧 TYPE_TACHE={type_tache} | DATE_COL={date_col or 'Aucune'}", file=sys.stderr)
    
    total_cells = 0
    for step_item in steps:
        step_name = ""
        raw_content = ""
        description = ""
        node_id = None

        # Cas 1 : Template fichier (cas principal et prioritaire)
        if isinstance(step_item, str) and not re.match(r'^\d+\.\d+$', step_item):
            filename = str(step_item)
            filepath = _STEPS_DIR / filename
            if filepath.exists():
                raw_content = filepath.read_text(encoding='utf-8')
                step_name = filename
            else:
                step_name = filename
                
        # Cas 2 : Dictionnaire avec ID (envoyé par l'agent)
        elif isinstance(step_item, dict):
            node_id = step_item.get("id")
            step_name = step_item.get("title") or f"Phase {node_id}"
            raw_content = step_item.get("code") or step_item.get("content") or ""
        
        # Cas 3 : ID numérique seul (ex: "1.0")
        elif isinstance(step_item, str) and re.match(r'^\d+\.\d+$', step_item):
            node_id = step_item
            step_name = f"Phase {node_id}"
            raw_content = ""

        # Fallback PageIndex si contenu vide ET ID disponible
        if not raw_content and node_id:
            tree_name = "expertise_timeseries" if is_ts else ("expertise_clustering" if is_clustering_effective else "expertise_supervised")
            raw_content = _load_code_from_expertise(node_id, tree_name)

        if not raw_content:
            raw_content = f"### {step_name}\n\n# {description}"

        # Découpage du contenu en cellules (Markdown + Code)
        step_cells = _parse_md_to_cells(raw_content)
        
        # Application de la substitution sur CHAQUE cellule
        for cell in step_cells:
            if cell.cell_type in ["code", "markdown"]:
                cell.source = _substitute_vars(cell.source, variables)
            nb.cells.append(cell)
            total_cells += 1

    return nb, total_cells


def _load_code_from_expertise(node_id: str, tree_name: str) -> Optional[str]:
    """Charge le code d'un nœud d'expertise (ou agrège ses enfants si parent)."""
    try:
        file_path = Path("knowledge") / f"{tree_name}.json"
        if not file_path.exists(): return None
        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        
        def find_recursively(nodes, target_id):
            for node in nodes:
                if node.get("id") == target_id: return node
                if "children" in node:
                    found = find_recursively(node["children"], target_id)
                    if found: return found
            return None

        target_node = find_recursively(data.get("hierarchy", []), node_id)
        if not target_node: return None

        # --- Fonction d'agrégation ---
        def aggregate_node(node):
            title   = node.get("title", "")
            content = node.get("content", "")
            code    = node.get("code_snippet", "")
            
            # Bloc Markdown
            md = f"### {title}\n\n{content}" if content else f"## {title}"
            
            # Bloc Code (si présent)
            if code:
                md += f"\n\n```python\n{code}\n```"
            
            # Si le nœud a des enfants, on les ajoute récursivement
            if "children" in node:
                for child in node["children"]:
                    md += "\n\n" + aggregate_node(child)
            
            return md

        return aggregate_node(target_node)

    except Exception as e:
        print(f"      ⚠️ Erreur expertise ({node_id}) : {e}", file=sys.stderr)
    return None

def _get_timeseries_steps(steps_filter: Optional[list]) -> list[str]:
    slots = [
        ("00_setup_timeseries.md",         "00_setup_et_split.md"),
        ("01_analyse_exploratoire_eda.md",  "01_analyse_exploratoire_eda.md"),
        ("02_feature_engineering.md",       "02_preprocessing_pipelines.md"),
        ("03_timeseries_models.md",         "03_benchmarking_modeles.md"),
        ("03b_advanced_training.md",        "03_benchmarking_modeles.md"),
        ("04_evaluation_timeseries.md",     "04_evaluation_finale.md"),
        ("05_mlops_monitoring.md",          "05_mlops_monitoring.md"),
        ("06_rapport_narratif.md",          "06_rapport_narratif.md"),
    ]
    return _resolve_slots(slots, steps_filter)

def _get_clustering_steps(steps_filter: Optional[list]) -> list[str]:
    slots = [
        ("00_setup_et_split.md",              "00_setup_et_split.md"),
        ("01_analyse_exploratoire_eda.md",    "01_analyse_exploratoire_eda.md"),
        ("02_preprocessing_clustering.md",    "02_preprocessing_pipelines.md"),
        ("03_clustering_benchmark.md",        "03_benchmarking_modeles.md"),
        ("03b_advanced_training.md",          "03_benchmarking_modeles.md"),
        ("04_evaluation_clustering.md",       "04_evaluation_finale.md"),
        ("05_mlops_monitoring.md",            "05_mlops_monitoring.md"),
        ("06_rapport_narratif.md",            "06_rapport_narratif.md"),
    ]
    return _resolve_slots(slots, steps_filter)

def _get_supervised_steps(steps_filter: Optional[list]) -> list[str]:
    slots = [
        ("00_setup_et_split.md",              "00_setup_et_split.md"),
        ("01_analyse_exploratoire_eda.md",    "01_analyse_exploratoire_eda.md"),
        ("02_preprocessing_pipelines.md",     "02_preprocessing_pipelines.md"),
        ("03_benchmarking_modeles.md",        "03_benchmarking_modeles.md"),
        ("03b_advanced_training.md",          "03_benchmarking_modeles.md"),
        ("04_evaluation_finale.md",           "04_evaluation_finale.md"),
        ("05_mlops_monitoring.md",            "05_mlops_monitoring.md"),
        ("06_rapport_narratif.md",            "06_rapport_narratif.md"),
    ]
    return _resolve_slots(slots, steps_filter)

def _resolve_slots(slots, steps_filter) -> list[str]:
    """
    Résolution intelligente des slots avec mapping des IDs (Phase 2).
    """
    # 1. Nettoyage du filtre (TS.1.0 -> 1.0)
    clean_filter = []
    if steps_filter:
        for f in steps_filter:
            if isinstance(f, str):
                # On garde le chiffre après le premier point ou le premier chiffre significatif
                match = re.search(r'(\d+\.\d+)', f)
                if match: clean_filter.append(match.group(1))
                else: clean_filter.append(f)
            else: clean_filter.append(f)

    steps = []
    seen = set()
    
    # 2. Inclusion forcée du Setup (Index 0) si on génère un notebook complet
    if not clean_filter or any(f.startswith('0') or f.startswith('1') for f in clean_filter):
        pref, fall = slots[0]
        chosen = _pick_step(pref, fall)
        if chosen:
            steps.append(chosen)
            seen.add(chosen)

    # 3. Résolution des autres slots
    for i, (pref, fall) in enumerate(slots):
        if i == 0: continue # Déjà géré
        
        # On inclut si : pas de filtre OU l'ID correspond à l'index (i) ou au nom
        include = not clean_filter
        if clean_filter:
            # Match par index (ex: '1.0' match slot index 1)
            if any(f.startswith(str(i)) for f in clean_filter):
                include = True
            # Match par nom de fichier
            elif any(pref.startswith(f) or fall.startswith(f) for f in clean_filter):
                include = True

        if include:
            chosen = _pick_step(pref, fall)
            if chosen and chosen not in seen:
                steps.append(chosen)
                seen.add(chosen)

    # 4. Toujours inclure le rapport final (Dernier slot) si ce n'est pas un test unitaire
    if len(steps) > 2:
        pref, fall = slots[-1]
        chosen = _pick_step(pref, fall)
        if chosen and chosen not in seen:
            steps.append(chosen)
            seen.add(chosen)

    return steps

def _parse_md_to_cells(content: str) -> list:
    """Convertit Markdown en cellules."""
    cells = []
    pattern = re.compile(r'```python\n(.*?)```', re.DOTALL)
    pos = 0
    for match in pattern.finditer(content):
        md_text = content[pos:match.start()].strip()
        if md_text: cells.append(nbformat.v4.new_markdown_cell(md_text))
        code = match.group(1).rstrip()
        if code: cells.append(nbformat.v4.new_code_cell(code))
        pos = match.end()
    trailing = content[pos:].strip()
    if trailing: cells.append(nbformat.v4.new_markdown_cell(trailing))
    return cells
