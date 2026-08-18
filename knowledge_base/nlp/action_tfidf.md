---
type: action
title: Traitement de Texte (TF-IDF)
domain: nlp
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# TF-IDF (Term Frequency-Inverse Document Frequency)

**Definition**: Technique permettant de transformer du texte brut en caractéristiques numériques exploitables par un modèle de Machine Learning. Elle valorise les mots fréquents dans un document précis, mais pénalise les mots trop fréquents dans l'ensemble du corpus (ex: "le", "de").

**Related Tools**: scikit-learn

**Quand l'utiliser** :
- Le dataset contient une colonne contenant du texte brut long (commentaires, descriptions, tweets).
- Le profil montre une colonne `object` ou `string` avec une très haute cardinalité et une longueur moyenne élevée.

**Code Snippet** :
```python
from sklearn.feature_extraction.text import TfidfVectorizer

# Initialisation en retirant les mots vides de sens (stop_words)
# On limite à 100 features pour ne pas faire exploser la mémoire du modèle ML
tfidf = TfidfVectorizer(max_features=100, stop_words='english')

# Transformation du texte en matrice numérique dense
text_matrix = tfidf.fit_transform(df['colonne_texte'].fillna('')).toarray()
df_text = pd.DataFrame(text_matrix, columns=tfidf.get_feature_names_out())

# On joint ces nouvelles colonnes numériques au dataset principal
df = pd.concat([df.drop(columns=['colonne_texte']), df_text], axis=1)
```
