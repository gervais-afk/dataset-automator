---
type: procedure
title: Setup Data Validation with Pandera Schemas
domain: data_engineering
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
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
