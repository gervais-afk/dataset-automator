# 📝 Étape 3 — Traitement du Langage Naturel (Classification de Texte)

Objectif : Prétraiter des textes bruts (nettoyage de caractères, ponctuation), extraire des caractéristiques numériques (TF-IDF) et entraîner un classifieur de sentiments ou de catégories.

```python
import pandas as pd
import numpy as np
import os
import re
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')

print("=" * 60)
print("📝 TRAITEMENT DU LANGAGE NATUREL (NLP)")
print("=" * 60)

# Détection des colonnes de texte et de classe
text_col = 'texte'
target_col = globals().get('TARGET_COL') or 'label'

if text_col not in df.columns:
    # On prend la première colonne textuelle longue
    text_cols = [c for c in df.columns if df[c].dtype == object]
    text_col = text_cols[0] if text_cols else df.columns[0]

if target_col not in df.columns:
    target_col = [c for c in df.columns if any(k in c.lower() for k in ['label', 'target', 'sentiment', 'class'])][0]

print(f"📊 Variables utilisées : Texte = '{text_col}' | Cible = '{target_col}'")

# ── 1. Nettoyage de Texte Simple (Preprocessing) ──────────────────────
def clean_text(text):
    text = str(text).lower()
    text = re.sub(r'[^\w\s]', ' ', text) # Supprimer la ponctuation
    text = re.sub(r'\s+', ' ', text).strip() # Supprimer les espaces multiples
    return text

print("\n⏳ Nettoyage des textes...")
df_nlp = df.dropna(subset=[text_col, target_col]).copy()
df_nlp['cleaned_text'] = df_nlp[text_col].apply(clean_text)

# Split Train/Test
X_tr, X_te, y_tr, y_te = train_test_split(df_nlp['cleaned_text'], df_nlp[target_col], test_size=0.2, random_state=42)

# ── 2. Vectorisation TF-IDF ───────────────────────────────────────────
print("⏳ Vectorisation numérique (TF-IDF)...")
vectorizer = TfidfVectorizer(max_features=2000, stop_words='english')
X_train_vec = vectorizer.fit_transform(X_tr)
X_test_vec = vectorizer.transform(X_te)

print(f"   - Taille du vocabulaire extrait : {len(vectorizer.vocabulary_)}")

# ── 3. Modélisation (Classification Logistique) ───────────────────────
print("⏳ Entraînement du classifieur (Régression Logistique)...")
clf = LogisticRegression(max_iter=1000, random_state=42)
clf.fit(X_train_vec, y_tr)

# Prédictions
y_pred = clf.predict(X_test_vec)

# ── 4. Évaluation ─────────────────────────────────────────────────────
print("\n📋 Rapport de Classification :")
print(classification_report(y_te, y_pred))

# Enregistrement pour l'orchestrateur
best_name = "TF-IDF Logistic Regression"
best_model = clf
results = {best_name: {"score": float(np.mean(y_te == y_pred)), "model": clf}}
y_test = y_te
X_test_prep = X_test_vec
```

### Visualisation : Top Mots Discriminants

```python
# Analyse des coefficients pour comprendre les décisions (si binaire)
classes = clf.classes_
if len(classes) == 2:
    coefficients = clf.coef_[0]
    feature_names = np.array(vectorizer.get_feature_names_out())
    
    # Récupérer les 10 mots les plus influents pour chaque classe
    top_indices = np.argsort(coefficients)
    top_neg = top_indices[:10]
    top_pos = top_indices[-10:]
    
    impact_df = pd.DataFrame({
        'Mot': np.concatenate([feature_names[top_neg], feature_names[top_pos]]),
        'Coefficient': np.concatenate([coefficients[top_neg], coefficients[top_pos]]),
        'Classe': [classes[0]]*10 + [classes[1]]*10
    })
    
    plt.figure(figsize=(10, 6))
    sns.barplot(data=impact_df, x='Coefficient', y='Mot', hue='Classe', dodge=False, palette='coolwarm')
    plt.title("Importance locale des termes (Top 10 par classe)")
    plt.savefig(os.path.join(OUTPUT_DIR, '03_nlp_feature_importance.png'), dpi=150)
    plt.show()
else:
    # Matrice de confusion pour le multi-classe
    cm = confusion_matrix(y_te, y_pred)
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt='d', cmap='Blues', xticklabels=classes, yticklabels=classes)
    plt.ylabel('Réel')
    plt.xlabel('Prédit')
    plt.title('Matrice de Confusion (Classification de Textes)')
    plt.savefig(os.path.join(OUTPUT_DIR, '03_nlp_confusion_matrix.png'), dpi=150)
    plt.show()
```
