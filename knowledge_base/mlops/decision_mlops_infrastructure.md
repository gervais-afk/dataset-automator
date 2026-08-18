---
type: decision_tree
title: mlops-infrastructure
domain: mlops
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Decision: Faut-il choisir des services Cloud Managés ou de l'Open-Source hébergé ?

**Root Consideration**: Ressources et maturité de l'organisation

**Branches**:
- IF Starting out / limited DevOps resources / need fast time to value THEN Utiliser Managed cloud services (AWS SageMaker, Azure ML, Vertex AI)
- IF Mature organization / strong platform team / need full control / avoid vendor lock-in THEN Utiliser Self-hosted open-source (Kubeflow, MLflow sur clusters custom)
