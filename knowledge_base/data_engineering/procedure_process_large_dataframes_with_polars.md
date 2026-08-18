---
type: procedure
title: Process Large DataFrames with Polars
domain: data_engineering
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Procedure: Process Large DataFrames with Polars

**Objective**: 

## Steps
### Step 1: Charger les données
```python
import polars as pl
df = pl.read_parquet('data.parquet')
```
**Tools**: N/A

### Step 2: Appliquer des transformations
```python
df = df.with_columns([pl.col('count').shift(1).alias('lag_1')])
```
**Tools**: N/A

**Validation/Pitfalls**: 
