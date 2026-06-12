---
title: Transform Data with dbt
domain: data_engineering
type: procedure
---

# Procedure: Transform Data with dbt

**Objective**: 

## Steps
### Step 1: Définir les transformations SQL modulaires
```python
SELECT customer_id, SUM(amount) 
FROM {{ ref('stg_transactions') }} 
GROUP BY 1
```
**Tools**: N/A

**Validation/Pitfalls**: 
