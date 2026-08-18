---
type: procedure
title: Handle Outliers with Winsorization
domain: data_engineering
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
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
