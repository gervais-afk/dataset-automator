---
title: Handle Class Imbalance
domain: supervised_learning
type: procedure
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
