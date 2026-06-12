---
title: Build Code-Generating Agent with Smolagents
domain: agentic_ai
type: procedure
---

# Procedure: Build Code-Generating Agent with Smolagents

**Objective**: 

## Steps
### Step 1: Initialiser le CodeAgent avec un LLM
```python
from smolagents import CodeAgent, HfApiModel
model = HfApiModel()
agent = CodeAgent(tools=[], model=model)
```
**Tools**: N/A

**Validation/Pitfalls**: 
