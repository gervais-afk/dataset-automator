# 🤖 Dataset Automator — Universal MLOps, Multi-Modal Data Engineering & Agentic RAG Pipeline

[![Firebase Genkit](https://img.shields.io/badge/Firebase_Genkit-Agentic_Framework-FFCA28?style=for-the-badge&logo=firebase)](https://firebase.google.com/docs/genkit)
[![Neo4j](https://img.shields.io/badge/Neo4j-5.20_GraphRAG-008CC1?style=for-the-badge&logo=neo4j)](https://neo4j.com/)
[![MLflow](https://img.shields.io/badge/MLOps-MLflow_Tracking-0194E2?style=for-the-badge&logo=mlflow)](https://mlflow.org/)
[![Google AI](https://img.shields.io/badge/Google_AI-Gemma_&_Gemini-4285F4?style=for-the-badge&logo=google)](https://ai.google.dev/gemma)
[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?style=for-the-badge&logo=python)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-green?style=for-the-badge)](#license)

> **Dataset Automator** is an end-to-end, multi-modal MLOps platform engineered for automated dataset preprocessing, knowledge graph semantic indexing, experiment tracking, and agentic decision intelligence. Created & maintained by **KOA MARIE GERVAIS NELLY** (`@gervais-afk`).

---

## 🌟 Comprehensive Platform Architecture & Data Flow

```mermaid
graph TD
    subgraph Ingestion ["Multi-Modal Data Ingestion Layer"]
        Tabular["Tabular / CSV / Excel"]
        TimeSeries["Time-Series Datasets"]
        SQLData["Relational Databases PostgreSQL / SQL"]
        TextDocs["Unstructured Text and PDF Documents"]
    end

    subgraph Processing ["Automated Processing Engine"]
        Cleaner["Data Cleaning and Normalization"]
        FeatureEng["Automated Feature Engineering"]
        QualityAudit["Data Drift and Quality Auditor"]
    end

    subgraph Intelligence ["Knowledge Graph and MLOps Layer"]
        Neo4jGraph["Neo4j 5.20 Knowledge Graph Indexer"]
        MLflowTrack["MLflow Metric Tracking and Lineage"]
        GenkitAgent["Firebase Genkit Agentic Reasoning"]
    end

    subgraph Outputs ["Automated Outputs and Insights"]
        CleanData["Cleaned and Enriched Datasets"]
        GraphInsights["GraphRAG Semantic Search"]
        AIReports["Executive Markdown Insights"]
    end

    Ingestion --> Processing
    Processing --> Intelligence
    Intelligence --> Outputs
```

---

## 🚀 Key Capabilities & Modules

1. **📥 Universal Multi-Modal Ingestion**: Handles tabular data, time-series, relational SQL schemas, unstructured text documents, and domain-specific BTP datasets seamlessly.
2. **🧹 Automated Data Hygiene & Quality Audit**: Automatically identifies missing values, out-of-range anomalies, structural inconsistencies, and data drift.
3. **🕸️ Neo4j 5.20 Knowledge Graph Indexer**: Constructs semantic relationships between entities, attributes, and data dependencies for high-precision GraphRAG.
4. **📊 MLflow Tracking & Lineage**: Full reproducibility tracking for dataset versions, model metrics, parameter tuning, and execution graphs.
5. **🤖 Agentic Insight Generation (Genkit + Gemma/Gemini)**: Multi-agent execution traces delivering natural language data summaries, SQL generation, and automated report synthesis.

---

## 💻 Tech Stack & Repository Structure

- **`ts-orchestrator/`**: TypeScript multi-agent orchestrator powered by **Firebase Genkit**.
- **`py-executors/`**: Python 3.11 data engineering pipelines, feature engineering, and cleaning algorithms.
- **`mcp-neo4j-server/`**: Neo4j 5.20 Cypher query engine and GraphRAG knowledge graph generator.
- **`scripts/`**: Automated seeding and cost enrichment scripts.

---

## 👨‍💻 Author & Intellectual Property

* **Author & Lead Engineer**: **KOA MARIE GERVAIS NELLY** ([@gervais-afk](https://github.com/gervais-afk))
* **Education**: MSc. in Artificial Intelligence & Data Science (University of Ngaoundéré) & B.Sc. in Civil Engineering (ISTDI / IUC Douala).
* **Flagship Project**: Founder of **[Archi Cam AI](https://github.com/gervais-afk/archi-cam-ai)**.

---

## 📄 License

Proprietary License — All Rights Reserved.  
Copyright (c) 2026 **KOA MARIE GERVAIS NELLY (@gervais-afk)**. All rights reserved.
