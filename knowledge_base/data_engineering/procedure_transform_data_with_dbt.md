---
type: procedure
title: Transform Data with dbt
domain: data_engineering
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
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
