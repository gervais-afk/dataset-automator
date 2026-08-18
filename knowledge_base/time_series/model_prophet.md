---
type: model
title: Prophet (Modèles Additifs)
domain: time_series
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Prophet (Modèles Additifs)

**Definition**: Modèle prédictif robuste développé par Meta, basé sur une décomposition additive. Il modélise les tendances non linéaires avec des saisonnalités (quotidienne, hebdomadaire, annuelle) et des effets de jours fériés.

**Related Tools**: prophet

**Quand l'utiliser** :
- Données historiques avec plusieurs saisons (ex: impact des week-ends + impact annuel).
- Données avec des jours fériés ou des événements spéciaux très marquants (ex: Black Friday).
- Séries temporelles présentant des données manquantes ou des valeurs aberrantes (Prophet y est extrêmement robuste).

**Code Snippet** :
```python
from prophet import Prophet

# Prophet exige les colonnes 'ds' (dates) et 'y' (valeurs)
df_p = df.reset_index().rename(columns={'Date': 'ds', 'Target': 'y'})

m = Prophet()
m.fit(df_p)

future = m.make_future_dataframe(periods=30)
forecast = m.predict(future)
m.plot(forecast)
```
