---
type: decision_tree
title: mlops-kubernetes
domain: mlops
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Decision: Quand faut-il utiliser Kubernetes pour le déploiement ML ?

**Root Consideration**: Volume de trafic et nombre de modèles en production

**Branches**:
- IF Beginning, proof of concept, low traffic THEN Utiliser une simple VM avec Docker + FastAPI et MLflow local
- IF 5+ models in production / need auto-scaling / advanced strategies (A/B testing, Canary) THEN Utiliser Kubernetes (avec KServe ou Seldon Core)
