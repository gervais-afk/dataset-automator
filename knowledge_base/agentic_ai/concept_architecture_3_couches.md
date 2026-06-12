---
title: Architecture Agentique à 3 Couches
domain: agentic_ai
type: concept
---

# Architecture Agentique à 3 Couches

**Definition**: Modèle d'architecture d'entreprise divisant les systèmes en Couche d'Orchestration (plan de contrôle), Couche Cognitive (raisonnement) et Couche des Outils (action).

## Graph Context
- **Concept Name**: Architecture Agentique à 3 Couches
- **Category**: agentic_ai
- **Is_A**: Architecture Framework
- **Requires**: Model Context Protocol (MCP)
- **Solves**: Surcharge cognitive des agents monolithiques.

## Description détaillée
Face à la complexité des flux de travail en entreprise, un agent monolithique échoue souvent. L'architecture à 3 couches résout ce problème :
1. **La Couche d'Orchestration** : Le "plan de contrôle" (Control Plane). Elle gère l'état, le routage et s'assure que le workflow est respecté. (ex: LangGraph).
2. **La Couche Cognitive** : Le "moteur de raisonnement". C'est ici qu'interviennent les LLMs pour prendre des décisions sur la base du contexte fourni.
3. **La Couche des Outils** : Le "plan d'action" (Action Plane). C'est l'interface avec le monde réel (API, Bases de données). 

**Intégration MCP** : Le Model Context Protocol (MCP) est le standard idéal pour concevoir la Couche des Outils, permettant aux agents de se brancher sur l'infrastructure de l'entreprise de manière sécurisée.

## Liens
- Implémenté via: LangGraph, MCP
- Concepts liés: Société d'Agents

**Sources**:
- Leadership in Agentic AI - Module 2 : Architecting the Agentic Enterprise
