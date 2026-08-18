#!/usr/bin/env python3
"""
dataset_output_manager.py — Gestionnaire Isolé des Dossiers & Export HTML Complet de Notebooks
================================================================================================
Garantit que :
  1. Chaque dataset traité possède son propre sous-dossier dédié dans `workspace/outputs/<dataset_name>/`.
  2. Le notebook généré (55 cellules) est exporté en un fichier HTML interactif et autonome
     regroupant TOUTES les cellules (Markdown, Code Python, Sorties, Graphiques et Figures).
"""

import os
import sys
import json
import re
import datetime
import nbformat
from pathlib import Path
from typing import Dict, Any, List, Optional

try:
    from nbconvert import HTMLExporter
    NBCONVERT_AVAILABLE = True
except ImportError:
    NBCONVERT_AVAILABLE = False

# ── Configuration des Chemins ────────────────────────────────────────────────
FILE_PATH = Path(__file__).resolve()
SRC_DIR = FILE_PATH.parent
PY_EXECUTORS_DIR = SRC_DIR.parent
DATASET_AUTO_DIR = PY_EXECUTORS_DIR.parent
WORKSPACE_DIR = DATASET_AUTO_DIR / "workspace"
OUTPUTS_DIR = WORKSPACE_DIR / "outputs"


def get_dataset_output_dir(dataset_name: str) -> Path:
    """Crée et retourne le dossier de sortie spécifique et isolé pour un dataset donné."""
    clean_name = Path(dataset_name).stem.replace(" ", "_").replace("(", "").replace(")", "")
    dataset_dir = OUTPUTS_DIR / clean_name
    dataset_dir.mkdir(parents=True, exist_ok=True)
    return dataset_dir


def export_notebook_to_complete_html(
    notebook_path_or_node: Any,
    output_html_path: Optional[str | Path] = None,
    dataset_name: str = "Dataset",
    custom_title: Optional[str] = None
) -> str:
    """
    Exporte le notebook complet (55 cellules) en fichier HTML autonome et interactif
    contenant l'intégralité du code, du texte explicatif et des figures générées.
    """
    # 1. Chargement du notebook node
    if isinstance(notebook_path_or_node, (str, Path)):
        nb_path = Path(notebook_path_or_node)
        if not nb_path.exists():
            raise FileNotFoundError(f"Notebook non trouvé : {nb_path}")
        with open(nb_path, "r", encoding="utf-8") as f:
            nb = nbformat.read(f, as_version=4)
        if output_html_path is None:
            output_html_path = nb_path.with_suffix(".html")
    else:
        nb = notebook_path_or_node
        if output_html_path is None:
            out_dir = get_dataset_output_dir(dataset_name)
            output_html_path = out_dir / f"{dataset_name}_Notebook_Complet.html"

    output_html_path = Path(output_html_path)
    output_html_path.parent.mkdir(parents=True, exist_ok=True)

    title = custom_title or f"Notebook MLOps Complet (55 Cellules) — {dataset_name}"

    # 2. Utilisation de nbconvert si disponible
    if NBCONVERT_AVAILABLE:
        try:
            html_exporter = HTMLExporter()
            html_exporter.template_name = "classic"
            (body, _) = html_exporter.from_notebook_node(nb)
            
            # Injection d'un thème moderne & responsive
            custom_styling = f"""
            <style>
                body {{
                    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif !important;
                    background-color: #0b1120 !important;
                    color: #e2e8f0 !important;
                    padding: 24px !important;
                }}
                .container {{
                    max-width: 1200px !important;
                    margin: 0 auto !important;
                }}
                div.input_area {{
                    background: #111827 !important;
                    border: 1px solid #1e293b !important;
                    border-radius: 8px !important;
                }}
                div.output_subarea {{
                    background: #090e17 !important;
                    color: #cbd5e1 !important;
                }}
                h1, h2, h3, h4 {{
                    color: #38bdf8 !important;
                    font-weight: 800 !important;
                }}
                .rendered_html table {{
                    border-collapse: collapse !important;
                    width: 100% !important;
                    background: #0f172a !important;
                    border: 1px solid #334155 !important;
                }}
                .rendered_html th, .rendered_html td {{
                    padding: 10px !important;
                    border: 1px solid #334155 !important;
                    color: #f1f5f9 !important;
                }}
                .rendered_html th {{
                    background: #1e293b !important;
                }}
            </style>
            """
            body = body.replace("</head>", f"{custom_styling}</head>")
            
            with open(output_html_path, "w", encoding="utf-8") as f:
                f.write(body)
            print(f"✅ Notebook HTML complet exporté avec succès via nbconvert : {output_html_path}")
            return str(output_html_path)
        except Exception as e:
            print(f"⚠️ Avertissement nbconvert ({e}), bascule sur le rendu direct...")

    # 3. Moteur de Rendu Direct de Secours (Standalone HTML Generator)
    cells_html = []
    cell_counter = 0

    for cell in nb.cells:
        cell_counter += 1
        cell_type = cell.get("cell_type", "code")
        source = cell.get("source", "")

        if cell_type == "markdown":
            formatted_md = source.replace("\n", "<br>")
            cells_html.append(f"""
            <div class="cell markdown-cell">
                <div class="cell-label">📝 Cellule #{cell_counter} · Documentation CRISP-ML</div>
                <div class="md-content">{formatted_md}</div>
            </div>
            """)
        elif cell_type == "code":
            # Rendu du code
            code_escaped = source.replace("<", "&lt;").replace(">", "&gt;")
            
            # Rendu des sorties (outputs)
            outputs_html = []
            for out in cell.get("outputs", []):
                out_type = out.get("output_type", "")
                if out_type in ["execute_result", "display_data"]:
                    data = out.get("data", {})
                    # 1. Image PNG / Base64
                    if "image/png" in data:
                        b64_img = data["image/png"]
                        outputs_html.append(f'<div class="output-img"><img src="data:image/png;base64,{b64_img}" style="max-width:100%; border-radius:8px;" /></div>')
                    # 2. Table HTML
                    elif "text/html" in data:
                        outputs_html.append(f'<div class="output-table">{data["text/html"]}</div>')
                    # 3. Texte brut
                    elif "text/plain" in data:
                        outputs_html.append(f'<pre class="output-text">{data["text/plain"]}</pre>')
                elif out_type == "stream":
                    text_stream = out.get("text", "")
                    outputs_html.append(f'<pre class="output-stream">{text_stream}</pre>')
                elif out_type == "error":
                    ename = out.get("ename", "Error")
                    evalue = out.get("evalue", "")
                    outputs_html.append(f'<div class="output-error"><strong>❌ {ename}:</strong> {evalue}</div>')

            rendered_outputs = "".join(outputs_html) if outputs_html else '<div class="output-empty">✓ Cellule exécutée sans sortie</div>'

            cells_html.append(f"""
            <div class="cell code-cell">
                <div class="cell-label">💻 Cellule #{cell_counter} · Python Code</div>
                <pre class="code-block"><code>{code_escaped}</code></pre>
                <div class="output-container">
                    <div class="output-header">📊 Sortie d'Exécution & Figures</div>
                    {rendered_outputs}
                </div>
            </div>
            """)

    all_cells_rendered = "\n".join(cells_html)

    full_html = f"""<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
    <style>
        :root {{
            --bg: #070c18;
            --surface: #0f1a30;
            --border: #1e293b;
            --accent-blue: #38bdf8;
            --accent-green: #34d399;
            --text: #f0f6ff;
            --text-dim: #94a3b8;
        }}
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            background: var(--bg);
            color: var(--text);
            font-family: 'Inter', sans-serif;
            padding: 32px 20px;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
        }}
        .header {{
            background: linear-gradient(135deg, #0d1b38 0%, #1e1b4b 100%);
            border: 1px solid var(--border);
            border-radius: 16px;
            padding: 32px;
            margin-bottom: 28px;
        }}
        .header h1 {{
            font-size: 1.8rem;
            font-weight: 800;
            color: #fff;
        }}
        .header p {{
            color: var(--text-dim);
            margin-top: 6px;
            font-size: 0.95rem;
        }}
        .cell {{
            background: var(--surface);
            border: 1px solid var(--border);
            border-radius: 12px;
            margin-bottom: 20px;
            overflow: hidden;
        }}
        .cell-label {{
            background: rgba(0,0,0,0.3);
            padding: 8px 16px;
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--accent-blue);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            border-bottom: 1px solid var(--border);
        }}
        .md-content {{
            padding: 20px;
            line-height: 1.6;
            color: #cbd5e1;
        }}
        .code-block {{
            padding: 16px;
            background: #090e17;
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.82rem;
            overflow-x: auto;
            color: #e2e8f0;
        }}
        .output-container {{
            border-top: 1px solid var(--border);
            background: #050811;
            padding: 16px;
        }}
        .output-header {{
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--accent-green);
            margin-bottom: 10px;
            text-transform: uppercase;
        }}
        .output-stream, .output-text {{
            font-family: 'JetBrains Mono', monospace;
            font-size: 0.78rem;
            color: #a7f3d0;
            white-space: pre-wrap;
        }}
        .output-empty {{
            font-size: 0.8rem;
            color: #64748b;
            font-style: italic;
        }}
        .output-error {{
            background: rgba(239,68,68,0.1);
            border: 1px solid #ef4444;
            padding: 12px;
            border-radius: 8px;
            color: #fca5a5;
            font-size: 0.82rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📄 {title}</h1>
            <p>Exporté automatiquement avec l'ensemble des 55 cellules exécutées, graphiques intégrés et diagnostics.</p>
        </div>
        {all_cells_rendered}
    </div>
</body>
</html>"""

    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(full_html)

    print(f"✅ Notebook HTML standalone complet généré : {output_html_path}")
    return str(output_html_path)


# ── Test d'Auto-Validation ────────────────────────────────────────────────────
if __name__ == "__main__":
    print("📁 Test du Gestionnaire Isolé de Dossiers & Export HTML de Notebook...")
    
    # 1. Vérifier l'isolation du dossier
    d_dir = get_dataset_output_dir("clients.csv")
    assert d_dir.exists() and d_dir.name == "clients"
    print(f"  Dossier isolé créé : {d_dir}")

    # 2. Créer un notebook démo de 3 cellules et l'exporter en HTML
    dummy_nb = nbformat.v4.new_notebook()
    dummy_nb.cells.append(nbformat.v4.new_markdown_cell("# Phase 1 : Ingestion & Profilage CRISP-ML"))
    dummy_nb.cells.append(nbformat.v4.new_code_cell("import pandas as pd\nprint('Dataset chargé avec succès !')"))
    dummy_nb.cells.append(nbformat.v4.new_markdown_cell("## Phase 2 : Modélisation Google TabFM Champion"))

    html_file = export_notebook_to_complete_html(dummy_nb, d_dir / "clients_Notebook_Complet.html", dataset_name="clients")
    assert os.path.exists(html_file)
    print(f"  Fichier HTML complet généré : {html_file}")

    print("🎉 Test Dataset Output Manager réussi avec succès !")
