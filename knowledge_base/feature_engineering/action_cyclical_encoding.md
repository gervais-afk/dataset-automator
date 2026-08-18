---
type: action
title: Cyclical Feature Encoding (Encodage Cyclique)
domain: feature_engineering
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Cyclical Feature Encoding

## 1. Graph Context (Metadonnées pour Agents)
- **Concept Name**: Cyclical Feature Encoding
- **Category**: feature_engineering
- **Is_A**: Technique de transformation
- **Requires**: [Pandas, Scikit-learn, Numpy]
- **Solves**: [Discontinuité temporelle, Perte de l'aspect circulaire du temps]
- **Related_Concepts**: [SplineTransformer, Time Series, Features Temporelles]

## 2. Definition
Méthode transformant des caractéristiques temporelles périodiques (heure du jour, jour de la semaine, mois de l'année) en coordonnées mathématiques circulaires via des fonctions sinus et cosinus. Cela permet au modèle de comprendre que 23h59 et 00h01 sont très proches, contrairement à un encodage ordinal pur (23 vs 0).

## 3. Propriétés
- Maintient la distance réelle entre les extrêmes cycliques.
- Alternative plus simple au `SplineTransformer`.

## 4. Procédure & Code Snippet
Pour un attribut "heure" (0-23) :
```python
import numpy as np
import pandas as pd

# Supposons df['hour'] avec max = 24
df['hour_sin'] = np.sin(2 * np.pi * df['hour'] / 24.0)
df['hour_cos'] = np.cos(2 * np.pi * df['hour'] / 24.0)
```
