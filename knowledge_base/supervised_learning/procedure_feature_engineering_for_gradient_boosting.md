---
title: Feature Engineering for Gradient Boosting
domain: supervised_learning
type: procedure
---

# Procedure: Feature Engineering for Gradient Boosting

**Objective**: 

## Steps
### Step 1: Combiner des colonnes catégorielles
```python
for i, c1 in enumerate(CATS[:-1]):
    for j, c2 in enumerate(CATS[i+1:]):
        n = f'{c1}_{c2}'
        train[n] = train[c1].astype('str') + '_' + train[c2].astype('str')
```
**Tools**: N/A

**Validation/Pitfalls**: 
