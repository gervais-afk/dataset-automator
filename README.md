# 🤖 Dataset Automator — Universal Multi-Modal MLOps, Multi-Domain Data Engineering & Agentic RAG Platform

[![Firebase Genkit](https://img.shields.io/badge/Firebase_Genkit-Agentic_Framework-FFCA28?style=for-the-badge&logo=firebase)](https://firebase.google.com/docs/genkit)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.20_GraphRAG-008CC1?style=for-the-badge&logo=neo4j)](https://neo4j.com/)
[![MLflow](https://img.shields.io/badge/MLOps-MLflow_Tracking-0194E2?style=for-the-badge&logo=mlflow)](https://mlflow.org/)
[![Google AI](https://img.shields.io/badge/Google_AI-Gemma_&_Gemini-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev/gemma)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-green?style=for-the-badge)](#license)

> **Dataset Automator** is an end-to-end, **Universal Multi-Modal & Multi-Domain MLOps Platform** engineered for automated data engineering, 33-domain MLOps knowledge indexing, experiment tracking, adversarial drift detection, and agentic decision intelligence. Created & maintained by **KOA MARIE GERVAIS NELLY** (`@gervais-afk`).

---

## 🌟 Universal Multi-Modal Platform Architecture & Data Flow

```mermaid
graph TD
    classDef inputStyle fill:#141f38,stroke:#63b3ed,stroke-width:2px,color:#ffffff,rx:10px,ry:10px;
    classDef coreStyle fill:#1a1538,stroke:#b794f4,stroke-width:2px,color:#ffffff,rx:10px,ry:10px;
    classDef auditStyle fill:#132626,stroke:#4fd1c5,stroke-width:2px,color:#ffffff,rx:10px,ry:10px;
    classDef outStyle fill:#2b1828,stroke:#f6ad55,stroke-width:2px,color:#ffffff,rx:10px,ry:10px;

    subgraph Ingestion ["📥 1. Multi-Modal Data Ingestion Layer"]
        Tabular["📊 Tabular Data<br/><i>(CSV, Excel, Parquet)</i>"]:::inputStyle
        NLPText["📝 Text & NLP Docs<br/><i>(PDF, TXT, Unstructured)</i>"]:::inputStyle
        VisionImg["🖼️ Vision & VLM Charts<br/><i>(Diagrams, Images)</i>"]:::inputStyle
        SQLRel["🗄️ Relational SQL<br/><i>(PostgreSQL, MySQL)</i>"]:::inputStyle
        GraphEnt["🕸️ Knowledge Entities<br/><i>(Ontology Nodes, Cypher)</i>"]:::inputStyle
        TimeSer["📈 Temporal Sequences<br/><i>(Time-Series Data)</i>"]:::inputStyle
    end

    subgraph Intelligence ["🧠 2. Dual-Engine Intelligence & GraphRAG Layer"]
        TSOrchestrator["⚡ TS Orchestrator Gateway<br/><i>(Node.js + Firebase Genkit)</i>"]:::coreStyle
        Neo4jRAG["🕸️ Neo4j 5.20 GraphRAG<br/><i>(33 Domain Knowledge Bases)</i>"]:::coreStyle
        LocalLLM["🤖 Local Gemma 4 12B QAT<br/><i>(Sovereign Edge VLM/LLM)</i>"]:::coreStyle
        PyExecutors["🐍 FastMCP Python Executors<br/><i>(Scikit-Learn, CatBoost, Optuna)</i>"]:::coreStyle
    end

    subgraph Governance ["🛡️ 3. Audit, Quality & Safety Governance Engine"]
        DriftAuditor["🕵️‍♂️ Adversarial Drift Auditor<br/><i>(RandomForest Data Leakage)</i>"]:::auditStyle
        SHAPEngine["⚖️ SHAP Game Theory Engine<br/><i>(Feature Importance & Risk)</i>"]:::auditStyle
        ZodGuard["🛡️ Zod Guardrails Loop<br/><i>(Self-Healing Schema Validator)</i>"]:::auditStyle
        MLflowLineage["📉 MLflow Lineage & Registry<br/><i>(SQLite Experiment Tracking)</i>"]:::auditStyle
    end

    subgraph ControlCenter ["🎛️ 4. Control Center & Automated Deliverables"]
        StreamlitUI["🎛️ Streamlit Dashboard<br/><i>(app_dashboard.py UI)</i>"]:::outStyle
        NotebookFactory["📄 CRISP-ML(Q) Factory<br/><i>(Executable .ipynb Notebooks)</i>"]:::outStyle
        ModelCards["📋 Automated Model Cards<br/><i>(Governance & Data Contracts)</i>"]:::outStyle
    end

    Ingestion -->|1. Multi-Modal Stream| TSOrchestrator
    TSOrchestrator -->|2. Cypher Queries| Neo4jRAG
    Neo4jRAG -->|3. Domain Rules & Concepts| TSOrchestrator
    TSOrchestrator -->|4. Local RAG Prompts| LocalLLM
    TSOrchestrator -->|5. FastMCP JSON-RPC| PyExecutors

    PyExecutors -->|6. Data Profiling| DriftAuditor
    PyExecutors -->|7. Explainability Score| SHAPEngine
    PyExecutors -->|8. Schema Validation| ZodGuard
    PyExecutors -->|9. Metric Logging| MLflowLineage

    ZodGuard -->|10. Self-Healing Loop| TSOrchestrator
    Governance -->|11. Real-Time Telemetry| StreamlitUI
    Governance -->|12. Notebook Generation| NotebookFactory
    NotebookFactory -->|13. Governance Export| ModelCards
```

---

## 🚀 33 Integrated Knowledge & MLOps Domains

Dataset Automator embeds a comprehensive knowledge ontology across **33 specialized data science & industry domains**:

| Category | Supported Domains & Capabilities |
| :--- | :--- |
| **Supervised ML** | Classification, Regression, XGBoost, CatBoost, LightGBM, Random Forest, Feature Engineering |
| **Unsupervised ML** | Clustering (K-Means, DBSCAN, Hierarchical), Dimensionality Reduction (PCA, UMAP, t-SNE), Association Rules |
| **Advanced Analytics** | Anomaly & Outlier Detection, Survival Analysis, Causal Inference, A/B Testing, Optimization |
| **Multi-Modal AI** | Natural Language Processing (NLP), Computer Vision & VLM Chart Interpretation, Time-Series Forecasting |
| **Advanced Paradigms** | Graph Analysis & Network Science, Reinforcement Learning, Semi-Supervised Learning, Recommendation Engines |
| **Vertical Industry Knowledge** | Finance & Credit Scoring, Healthcare & Medical, BTP / Civil Engineering, E-Commerce, HR Analytics, Meteorology |
| **MLOps & Governance** | Data Cleaning, Data Validation, Data Engineering, Orchestration, Modeling, Development Tools, Validation |

---

## ⚙️ Key Core Modules

1. **🧠 Dual-Engine Decoupled Architecture**: High-level reasoning powered by **TypeScript + Firebase Genkit**, paired with deterministic high-performance computing powered by **Python 3.11 FastMCP Workers**.
2. **🕸️ Neo4j 5.20 GraphRAG Engine**: Semantic knowledge graph linking concepts, business cost rules, data quality metrics, and model choice heuristics.
3. **🕵️‍♂️ Adversarial Quality & SHAP Risk Engine**: Automatic detection of data leakage, target drift, distribution shifts, and feature importance explainability via SHAP.
4. **🛡️ Zod Guardrails & Self-Healing**: Automated feedback loops for prompt self-healing and output schema validation.
5. **🎛️ Interactive Streamlit Control Center**: Real-time pipeline execution, dataset inspection, metric visualization, and interactive GraphRAG search in `app_dashboard.py`.
6. **📄 Automated CRISP-ML(Q) Notebook Factory**: Produces complete, execution-ready Jupyter notebooks (`.ipynb`), data contracts, and standardized model cards.

---

## 💻 Tech Stack & Repository Structure

- **`ts-orchestrator/`**: TypeScript multi-agent orchestrator built on **Firebase Genkit**.
- **`py-executors/`**: Python 3.11 FastMCP workers, ML pipeline algorithms, notebook factory, and Streamlit UI.
- **`mcp-neo4j-server/`**: Neo4j 5.20 Cypher query engine and GraphRAG knowledge indexer.
- **`knowledge_base/`**: 33 domain specification markdowns, heuristics, and concept definitions.
- **`workspace/`**: MLflow SQLite registry (`mlflow.db`), artifacts, outputs, and generated notebooks.

---

## ⚡ Quickstart & Ports Overview

```bash
# 1-Click System Launcher (Launches all background services)
.\launch_all.bat
```

| Service | Port | Description |
| :--- | :--- | :--- |
| **Streamlit Control Center** | `8501` | Interactive Dashboard UI (`app_dashboard.py`) |
| **Neo4j Graph Database** | `7687` | Cypher Bolt Endpoint & GraphRAG Browser (`7474`) |
| **FastMCP Python Executors** | `8000` | FastMCP Tool Server for ML execution |
| **TS Orchestrator Gateway** | `3001` | Node.js / Genkit Agentic Router |
| **MLflow Experiment Server** | `5000` | MLflow Tracking UI & Lineage |

---

## 👨‍💻 Author & Intellectual Property

* **Author & Lead Engineer**: **KOA MARIE GERVAIS NELLY** ([@gervais-afk](https://github.com/gervais-afk))
* **Education**: MSc. in Artificial Intelligence & Data Science (University of Ngaoundéré) & B.Sc. in Civil Engineering (ISTDI / IUC Douala).
* **Flagship Platform**: Creator of **Dataset Automator** and **[Archi Cam AI](https://github.com/gervais-afk/archi-cam-ai)**.

---

## 📄 License

Proprietary License — All Rights Reserved.  
Copyright (c) 2026 **KOA MARIE GERVAIS NELLY (@gervais-afk)**. All rights reserved.
