---
type: procedure
title: Convert Notebooks to Scripts with Jupytext
domain: data_engineering
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Procedure: Convert Notebooks to Scripts with Jupytext

**Objective**: 

## Steps
### Step 1: Configurer la synchronisation Jupytext
```python
jupytext --set-formats ipynb,py:percent notebook.ipynb
```
**Tools**: N/A

**Validation/Pitfalls**: 
