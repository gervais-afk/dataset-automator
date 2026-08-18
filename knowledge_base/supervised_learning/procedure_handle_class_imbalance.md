---
type: procedure
title: Handle Class Imbalance
domain: supervised_learning
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Procedure: Handle Class Imbalance

**Objective**: 

## Steps
### Step 1: Appliquer des poids compensatoires
```python
from sklearn.ensemble import RandomForestClassifier
rf = RandomForestClassifier(class_weight='balanced')
```
**Tools**: N/A

### Step 2: Traiter les valeurs extrêmes
```python
from scipy.stats.mstats import winsorize
X_train['feature'] = winsorize(X_train['feature'], limits=[0.01, 0.01])
```
**Tools**: N/A

**Validation/Pitfalls**: 
