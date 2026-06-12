---
title: mlops-kubernetes
domain: mlops
type: decision_tree
---

# Decision: Quand faut-il utiliser Kubernetes pour le déploiement ML ?

**Root Consideration**: Volume de trafic et nombre de modèles en production

**Branches**:
- IF Beginning, proof of concept, low traffic THEN Utiliser une simple VM avec Docker + FastAPI et MLflow local
- IF 5+ models in production / need auto-scaling / advanced strategies (A/B testing, Canary) THEN Utiliser Kubernetes (avec KServe ou Seldon Core)
