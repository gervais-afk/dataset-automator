---
title: mlops-infrastructure
domain: mlops
type: decision_tree
---

# Decision: Faut-il choisir des services Cloud Managés ou de l'Open-Source hébergé ?

**Root Consideration**: Ressources et maturité de l'organisation

**Branches**:
- IF Starting out / limited DevOps resources / need fast time to value THEN Utiliser Managed cloud services (AWS SageMaker, Azure ML, Vertex AI)
- IF Mature organization / strong platform team / need full control / avoid vendor lock-in THEN Utiliser Self-hosted open-source (Kubeflow, MLflow sur clusters custom)
