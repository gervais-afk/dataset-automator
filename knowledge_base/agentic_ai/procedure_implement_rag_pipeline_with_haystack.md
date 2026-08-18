---
type: procedure
title: Implement RAG Pipeline with Haystack
domain: agentic_ai
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Procedure: Implement RAG Pipeline with Haystack

**Objective**: 

## Steps
### Step 1: Créer un pipeline modulaire
```python
from haystack import Pipeline
from haystack.components.retrievers.in_memory import InMemoryBM25Retriever
from haystack.components.generators import OpenAIGenerator
pipeline = Pipeline()
pipeline.add_component('retriever', InMemoryBM25Retriever(document_store=document_store))
pipeline.add_component('generator', OpenAIGenerator())
```
**Tools**: N/A

**Validation/Pitfalls**: 
