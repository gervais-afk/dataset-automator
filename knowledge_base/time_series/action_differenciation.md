---
type: action
title: Différenciation (Stationnarisation)
domain: time_series
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Différenciation (Stationnarisation)

**Definition**: Technique mathématique visant à rendre une série temporelle stationnaire en calculant la différence entre des observations consécutives. 

**Related Tools**: pandas, numpy

**Quand l'utiliser** :
- **Absolument obligatoire** si le Test ADF (Augmented Dickey-Fuller) donne une p-value > 0.05.
- La différenciation de 1er ordre (`d=1`) supprime une tendance linéaire.
- La différenciation de 2ème ordre (`d=2`) supprime une tendance quadratique (accélération).
- La différenciation saisonnière (ex: `d=12`) supprime une saisonnalité forte.

**Code Snippet** :
```python
# Différenciation de 1er ordre
df['target_diff'] = df['Target'].diff().dropna()

# Différenciation saisonnière (ex: mensuelle)
df['target_diff_season'] = df['Target'].diff(12).dropna()
```
