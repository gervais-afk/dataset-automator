// === ENRICHISSEMENT DES RÈGLES D'INTERPRÉTATION MÉTIER (RAG) ===

// 1. Récupération des Domaines existants ou création
MERGE (d_val:Domain {name: 'validation'})
MERGE (d_sl:Domain {name: 'supervised_learning'})
MERGE (d_cl:Domain {name: 'clustering'})
MERGE (d_ts:Domain {name: 'time_series'});

// 2. Règle : Paradoxe de l'Accuracy et du Rappel (Effondrement de classe)
MATCH (d_val:Domain {name: 'validation'})
MATCH (d_sl:Domain {name: 'supervised_learning'})
MERGE (r1:InterpretationRule {name: 'AccuracyRecallParadox'})
SET r1 += {
  description: "L'accuracy globale est élevée mais le rappel sur une classe minoritaire est très faible ou nul (effondrement de classe).",
  guideline: "Indiquez que l'accuracy globale est trompeuse car le modèle sur-privilégie la classe majoritaire. Recommandez de recalibrer les poids des classes (class_weight='balanced') ou d'ajuster le seuil de décision pour optimiser le rappel.",
  business_impact: "Faux négatifs critiques non détectés (fraudes ou maladies manquées), entraînant des pertes directes ou des risques opérationnels majeurs."
}
MERGE (r1)-[:BELONGS_TO]->(d_val)
MERGE (r1)-[:BELONGS_TO]->(d_sl);

// 3. Règle : Hétéroscédasticité des résidus
MATCH (d_val:Domain {name: 'validation'})
MATCH (d_sl:Domain {name: 'supervised_learning'})
MERGE (r2:InterpretationRule {name: 'HeteroscedasticityWarning'})
SET r2 += {
  description: "La variance des résidus n'est pas constante (effet entonnoir dans le graphique des résidus).",
  guideline: "Signalez que la fiabilité des prédictions est instable et varie selon l'échelle. Les prédictions sur de grandes valeurs/montants sont beaucoup plus incertaines. Recommandez d'ajouter une marge de sécurité (buffer) aux décisions financières majeures.",
  business_impact: "Risque de sur-évaluation ou sous-évaluation importante sur les dossiers à forte valeur financière."
}
MERGE (r2)-[:BELONGS_TO]->(d_val)
MERGE (r2)-[:BELONGS_TO]->(d_sl);

// 4. Règle : Autocorrélation des résidus (Durbin-Watson)
MATCH (d_val:Domain {name: 'validation'})
MATCH (d_ts:Domain {name: 'time_series'})
MERGE (r3:InterpretationRule {name: 'AutocorrelationErrors'})
SET r3 += {
  description: "Les erreurs sont corrélées sériellement dans le temps (Durbin-Watson en dehors de [1.5, 2.5]).",
  guideline: "Les erreurs de prédiction ne sont pas indépendantes. Les intervalles de confiance standards sont sous-estimés (le modèle est trop confiant). Recommandez d'ajouter des variables auto-régressives (lags) ou d'utiliser un split chronologique strict.",
  business_impact: "Biais temporel systématique menant à des prévisions de tendances faussées sur le long terme."
}
MERGE (r3)-[:BELONGS_TO]->(d_val)
MERGE (r3)-[:BELONGS_TO]->(d_ts);

// 5. Règle : Fuite de données / Concentration SHAP
MATCH (d_val:Domain {name: 'validation'})
MATCH (d_sl:Domain {name: 'supervised_learning'})
MERGE (r4:InterpretationRule {name: 'ShapLeakage'})
SET r4 += {
  description: "Une seule variable représente plus de 80% de l'importance globale SHAP.",
  guideline: "Alerte de concentration extrême. Il y a un fort risque de Data Leakage (variable du futur ou contenant indirectement la cible) ou de dépendance excessive à une seule caractéristique. Recommandez d'auditer et d'exclure temporairement cette variable pour tester la robustesse.",
  business_impact: "Le modèle semblera parfait en test (overfitting ou fuite) mais s'effondrera complètement lors de son déploiement réel."
}
MERGE (r4)-[:BELONGS_TO]->(d_val)
MERGE (r4)-[:BELONGS_TO]->(d_sl);

// 6. Règle : Faible silhouette en clustering
MATCH (d_val:Domain {name: 'validation'})
MATCH (d_cl:Domain {name: 'clustering'})
MERGE (r5:InterpretationRule {name: 'LowSilhouette'})
SET r5 += {
  description: "Le score de silhouette de la segmentation est inférieur à 0.25.",
  guideline: "Les clusters se chevauchent fortement et ne sont pas bien séparés. La segmentation client n'est pas fiable. Recommandez de réduire les dimensions (PCA/UMAP) avant de faire le K-Means ou de revoir la sélection de caractéristiques.",
  business_impact: "Campagnes marketing inefficaces ou ciblages erronés car les segments de clientèle ne sont pas distincts."
}
MERGE (r5)-[:BELONGS_TO]->(d_val)
MERGE (r5)-[:BELONGS_TO]->(d_cl);
