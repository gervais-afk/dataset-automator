---
type: procedure
title: Build Code-Generating Agent with Smolagents
domain: agentic_ai
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
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
