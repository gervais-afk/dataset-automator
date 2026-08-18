---
type: action
title: Pandera Data Validation
domain: data_validation
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Pandera Data Validation

## 1. Graph Context (Metadonnées pour Agents)
- **Concept Name**: Pandera Data Validation
- **Category**: data_validation
- **Is_A**: Processus de test de qualité de données
- **Requires**: [Pandas, Polars, Pandera]
- **Solves**: [Bugs silencieux de données manquantes, Changement de type inattendu, Erreurs de distribution]
- **Related_Concepts**: [Great Expectations, Data Engineering]

## 2. Definition
Méthodologie consistant à définir des schémas stricts (typage, valeurs nulles autorisées, plages de valeurs) pour les DataFrames. Si les données ingérées ne respectent pas le schéma, une erreur explicite est levée avant l'entraînement du modèle.

## 3. Propriétés
- Supporte Pandas, Polars et PySpark.
- Intégration facile avec `pytest` et `Hypothesis` pour la génération de fausses données (property-based testing).

## 4. Procédure & Code Snippet
```python
import pandera as pa
from pandera.typing import Series, DataFrame

# Définition du schéma typé
class ClientSchema(pa.SchemaModel):
    age: Series[int] = pa.Field(ge=18, le=120)
    salary: Series[float] = pa.Field(nullable=True)
    role: Series[str] = pa.Field(isin=["Admin", "User"])

# Validation à la volée via décorateur
@pa.check_types
def process_data(df: DataFrame[ClientSchema]) -> DataFrame[ClientSchema]:
    return df
```
