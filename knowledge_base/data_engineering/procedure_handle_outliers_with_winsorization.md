---
title: Handle Outliers with Winsorization
domain: data_engineering
type: procedure
---

# Procedure: Handle Outliers with Winsorization

**Objective**: 

## Steps
### Step 1: Appliquer la winsorisation
```python
from scipy.stats.mstats import winsorize
df['age_winsorized'] = winsorize(df['age'], limits=[0.01, 0.01])
```
**Tools**: N/A

**Validation/Pitfalls**: 
