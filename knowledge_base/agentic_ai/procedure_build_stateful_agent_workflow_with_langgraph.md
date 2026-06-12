---
title: Build Stateful Agent Workflow with LangGraph
domain: agentic_ai
type: procedure
---

# Procedure: Build Stateful Agent Workflow with LangGraph

**Objective**: 

## Steps
### Step 1: Définir le graphe d'états (DAG) et les nœuds
```python
from langgraph.graph import StateGraph
workflow = StateGraph(AgentState)
workflow.add_node('researcher', research_agent)
workflow.add_node('writer', writer_agent)
```
**Tools**: N/A

### Step 2: Configurer le routage
```python
workflow.add_edge('researcher', 'writer')
workflow.add_conditional_edges('writer', check_quality, {'approve': 'human_review', 'reject': 'researcher'})
```
**Tools**: N/A

**Validation/Pitfalls**: 
