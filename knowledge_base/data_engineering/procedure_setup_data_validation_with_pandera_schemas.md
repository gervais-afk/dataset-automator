---
title: Setup Data Validation with Pandera Schemas
domain: data_engineering
type: procedure
---

# Procedure: Setup Data Validation with Pandera Schemas

**Objective**: 

## Steps
### Step 1: Définir un schéma basé sur les classes
```python
import pandera as pa
from pandera.typing import Series

class TransactionSchema(pa.DataFrameModel):
    amount: Series[float] = pa.Field(gt=0, le=50000)
    merchant_category: Series[str] = pa.Field(isin=['retail', 'food'])
```
**Tools**: N/A

### Step 2: Valider paresseusement en production
```python
try:
    validated_df = TransactionSchema.validate(df, lazy=True)
except pa.errors.SchemaErrors as err:
    print(err.failure_cases)
```
**Tools**: N/A

**Validation/Pitfalls**: 
