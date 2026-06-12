---
title: agentic-framework-selection
domain: agentic_ai
type: decision_tree
---

# Decision: Quel framework d'agents IA open source choisir ?

**Root Consideration**: Exigences du projet et infrastructure existante

**Branches**:
- IF Processing large document collections (internal knowledge bases, legal search, financial reports) THEN Utiliser Haystack (orienté pipeline et RAG-natif)
- IF Need human-in-the-loop approval steps or long-running stateful workflows THEN Utiliser LangGraph
- IF .NET teams with existing enterprise infrastructure / Azure THEN Utiliser Semantic Kernel
- IF Fastest path from zero to a working agent loop (single-agent automation scripts) THEN Utiliser Smolagents
- IF Team includes non-engineers who need a visual, low-code interface THEN Utiliser Dify
