---
title: Société d'Agents
domain: agentic_ai
type: concept
---

# Société d'Agents

**Definition**: Paradigme où des flux de travail complexes sont gérés par un réseau d'agents hautement spécialisés coordonnés par un orchestrateur, évitant la surcharge de contexte des agents généralistes.

## Graph Context
- **Concept Name**: Société d'Agents
- **Category**: agentic_ai
- **Is_A**: Multi-Agent Pattern
- **Implemented_By**: CrewAI, LangGraph
- **Solves**: Surcharge de contexte (Context Window bloat), Manque de spécialisation.

## Description détaillée
Le paradigme de "Société d'Agents" (Society of Agents) s'oppose au concept du "God Agent" (Agent Omniscient). 

Au lieu de fournir un prompt massif de 10 000 tokens à un seul agent pour lui demander d'être à la fois Ingénieur DevOps, Développeur Front-end et Architecte BDD, le travail est divisé.

### Avantages clés :
1. **Focus Sémantique** : Chaque agent reçoit uniquement les instructions (Skills) et les outils nécessaires à son rôle.
2. **Asynchronisme** : Les agents peuvent travailler en parallèle sur des sous-tâches.
3. **Gouvernance** : Il est plus facile d'auditer les erreurs d'un agent spécifique (ex: l'agent QA) que de déboguer le raisonnement d'un agent monolithique.

**Outils d'implémentation** :
- **CrewAI** excelle pour définir statiquement ces rôles et leurs processus.
- **LangGraph** excelle pour définir dynamiquement la manière dont cette société communique et s'échange l'état du système.

**Sources**:
- Leadership in Agentic AI - Module 2 : Architecting the Agentic Enterprise
