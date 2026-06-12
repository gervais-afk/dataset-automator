---
title: Process Large DataFrames with Polars
domain: data_engineering
type: procedure
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
