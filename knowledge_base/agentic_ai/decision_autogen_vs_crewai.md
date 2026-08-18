---
type: decision_tree
title: autogen-vs-crewai
domain: agentic_ai
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Decision: Faut-il utiliser AutoGen, CrewAI ou Microsoft Agent Framework ?

**Root Consideration**: Type de workflow et écosystème

**Branches**:
- IF Building structured, deterministic business workflows ou besoin d'efficacité de tokens THEN Utiliser CrewAI
- IF Deploying on Azure / Microsoft 365 ecosystem ou intégration Copilot THEN Utiliser Microsoft Agent Framework
- IF Starting a new project that would have used AutoGen THEN Utiliser Microsoft Agent Framework (AutoGen Legacy est en mode maintenance depuis fév. 2026)
