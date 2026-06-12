---
title: Implement RAG Pipeline with Haystack
domain: agentic_ai
type: procedure
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
