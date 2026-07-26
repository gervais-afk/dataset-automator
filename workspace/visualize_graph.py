#!/usr/bin/env python3
"""
visualize_graph.py — SOVEREIGN.BI Neo4j Interactive Graph Visualizer

Génère une visualisation HTML interactive du Knowledge Graph Neo4j.
Exporte un fichier `knowledge_graph_view.html` navigable en 2D/3D avec vis.js.
"""

import os
import json
from neo4j import GraphDatabase

NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://127.0.0.1:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password123")

COLOR_MAP = {
    "Domain": "#4CAF50",
    "InterpretationRule": "#FF9800",
    "PerformanceThreshold": "#F44336",
    "FairnessThreshold": "#E91E63",
    "BusinessCost": "#9C27B0",
    "Concept": "#2196F3",
    "SemanticConcept": "#03A9F4",
    "Model": "#00BCD4",
    "Tool": "#673AB7",
    "Remedy": "#FF5722",
    "DecisionTree": "#795548",
    "Alert": "#D32F2F"
}

def export_graph_to_html(output_html_path: str = "knowledge_graph_view.html", limit: int = 150):
    driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    nodes = []
    edges = []
    node_ids = set()

    with driver.session() as session:
        # Récupérer les nœuds et relations principaux
        query = f"""
        MATCH (n)-[r]->(m)
        RETURN labels(n) as n_lbl, n.name as n_name, id(n) as n_id,
               type(r) as r_type,
               labels(m) as m_lbl, m.name as m_name, id(m) as m_id
        LIMIT {limit}
        """
        result = session.run(query)
        for rec in result:
            n_id = str(rec["n_id"])
            m_id = str(rec["m_id"])

            n_lbl = rec["n_lbl"][0] if rec["n_lbl"] else "Entity"
            m_lbl = rec["m_lbl"][0] if rec["m_lbl"] else "Entity"

            n_name = rec["n_name"] or f"{n_lbl}_{n_id}"
            m_name = rec["m_name"] or f"{m_lbl}_{m_id}"

            if n_id not in node_ids:
                nodes.append({
                    "id": n_id,
                    "label": str(n_name),
                    "group": n_lbl,
                    "color": COLOR_MAP.get(n_lbl, "#9E9E9E"),
                    "title": f"<b>{n_lbl}</b><br>{n_name}"
                })
                node_ids.add(n_id)

            if m_id not in node_ids:
                nodes.append({
                    "id": m_id,
                    "label": str(m_name),
                    "group": m_lbl,
                    "color": COLOR_MAP.get(m_lbl, "#9E9E9E"),
                    "title": f"<b>{m_lbl}</b><br>{m_name}"
                })
                node_ids.add(m_id)

            edges.append({
                "from": n_id,
                "to": m_id,
                "label": rec["r_type"],
                "arrows": "to"
            })

    driver.close()

    # Template HTML vis.js
    html_content = f"""<!DOCTYPE html>
<html>
<head>
  <meta charset="utf-8">
  <title>DATASET AUTOMATOR — Visualiseur de Graphe Neo4j</title>
  <script type="text/javascript" src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"></script>
  <style>
    body {{ font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; padding: 0; background: #0f172a; color: #e2e8f0; }}
    header {{ background: #1e293b; padding: 15px 20px; display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #334155; }}
    h1 {{ margin: 0; font-size: 1.2rem; color: #38bdf8; }}
    #mynetwork {{ width: 100vw; height: calc(100vh - 60px); background: #0f172a; }}
    .stats {{ font-size: 0.9rem; color: #94a3b8; }}
  </style>
</head>
<body>
  <header>
    <h1>🕸️ DATASET AUTOMATOR Knowledge Graph Explorer</h1>
    <div class="stats">Nœuds : <b>{len(nodes)}</b> | Relations : <b>{len(edges)}</b></div>
  </header>
  <div id="mynetwork"></div>

  <script type="text/javascript">
    const nodes = new vis.DataSet({json.dumps(nodes, ensure_ascii=False)});
    const edges = new vis.DataSet({json.dumps(edges, ensure_ascii=False)});

    const container = document.getElementById('mynetwork');
    const data = {{ nodes: nodes, edges: edges }};
    const options = {{
      nodes: {{
        shape: 'dot',
        size: 18,
        font: {{ size: 13, color: '#f8fafc' }},
        borderWidth: 2
      }},
      edges: {{
        font: {{ size: 10, align: 'middle', color: '#64748b' }},
        color: {{ color: '#475569', highlight: '#38bdf8' }},
        smooth: {{ type: 'continuous' }}
      }},
      physics: {{
        barnesHut: {{ gravitationalConstant: -3000, centralGravity: 0.3, springLength: 95 }},
        stabilization: {{ iterations: 150 }}
      }}
    }};
    const network = new vis.Network(container, data, options);
  </script>
</body>
</html>
"""

    os.makedirs(os.path.dirname(output_html_path) if os.path.dirname(output_html_path) else ".", exist_ok=True)
    with open(output_html_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"✅ Graphe Neo4j exporté avec succès dans : {output_html_path}")
    return output_html_path

if __name__ == "__main__":
    export_graph_to_html("dataset_automator/workspace/knowledge_graph_view.html")
