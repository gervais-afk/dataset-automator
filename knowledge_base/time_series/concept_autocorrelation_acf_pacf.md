---
title: Autocorrélation (ACF/PACF)
domain: time_series
type: concept
---

# Autocorrélation (ACF/PACF)

**Definition**: Les fonctions d'autocorrélation (ACF) et d'autocorrélation partielle (PACF) mesurent la corrélation d'une série temporelle avec ses propres valeurs retardées (lags).
Elles sont essentielles pour identifier le nombre de retards significatifs (Lags) à intégrer dans les modèles (ex: ordre p pour la partie AR, ordre q pour la partie MA des modèles ARIMA).

**Related Tools**: statsmodels, matplotlib

**Quand l'utiliser** :
- Pour déterminer la saisonnalité cachée (des pics réguliers sur l'ACF).
- Pour construire des "Lagged Features" optimisées sans polluer le modèle avec des retards inutiles.

**Code Snippet** :
```python
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
import matplotlib.pyplot as plt

fig, ax = plt.subplots(1, 2, figsize=(12, 4))
plot_acf(df['Target'], ax=ax[0])
plot_pacf(df['Target'], ax=ax[1])
plt.show()
```
