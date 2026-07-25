import neo4j from 'neo4j-driver';

async function main() {
  const driver = neo4j.driver('bolt://127.0.0.1:7687', neo4j.auth.basic('neo4j', 'password123'));
  try { await driver.verifyConnectivity(); } catch {
    console.error('❌ Neo4j non joignable'); return;
  }

  const session = driver.session();
  const fixes = [
    // Migrer les nœuds génériques ambigus vers les nœuds typés
    // XGBoost générique → pointer vers XGBoost Classifier
    `MATCH (m:Model {name: 'XGBoost'}) WHERE m.task_type IS NULL
     SET m.task_type = 'classification', m.python_class = 'XGBClassifier',
         m.library = 'xgboost', m.registered = true,
         m.alias_for = 'XGBoost Classifier'`,

    // XGBoost Regressor legacy → enrichir
    `MATCH (m:Model {name: 'XGBoost Regressor'}) WHERE m.task_type IS NULL
     SET m.task_type = 'regression', m.python_class = 'XGBRegressor',
         m.library = 'xgboost', m.registered = true`,

    // LightGBM générique → classification
    `MATCH (m:Model {name: 'LightGBM'}) WHERE m.task_type IS NULL
     SET m.task_type = 'classification', m.python_class = 'LGBMClassifier',
         m.library = 'lightgbm', m.registered = true,
         m.alias_for = 'LightGBM Classifier'`,

    // RandomForest générique → classification
    `MATCH (m:Model {name: 'RandomForest'}) WHERE m.task_type IS NULL
     SET m.task_type = 'classification', m.python_class = 'RandomForestClassifier',
         m.library = 'sklearn', m.registered = true,
         m.alias_for = 'RandomForest Classifier'`,

    // KMeans générique → clustering
    `MATCH (m:Model {name: 'KMeans'}) WHERE m.task_type IS NULL
     SET m.task_type = 'clustering', m.python_class = 'KMeans',
         m.library = 'sklearn', m.registered = true`,

    // TabICL générique → classification (usage principal)
    `MATCH (m:Model {name: 'TabICL'}) WHERE m.task_type IS NULL
     SET m.task_type = 'classification', m.python_class = 'TabICLClassifier',
         m.library = 'tabicl', m.registered = true,
         m.alias_for = 'TabICL Classifier'`,

    // Ajouter Prophet manquant
    `MERGE (m:Model {name: 'Prophet'})
     SET m.task_type = 'timeseries', m.python_class = 'Prophet',
         m.library = 'prophet', m.registered = true`,
  ];

  let ok = 0;
  for (const [i, stmt] of fixes.entries()) {
    try {
      await session.run(stmt);
      const name = stmt.match(/'([^']+)'/)?.[1] || `stmt ${i+1}`;
      console.log(`  ✅ [${i+1}/${fixes.length}] ${name}`);
      ok++;
    } catch (e: any) {
      console.error(`  ❌ [${i+1}] ${e.message?.substring(0, 100)}`);
    }
  }

  await session.close();
  await driver.close();
  console.log(`\n🏁 Migration terminée: ${ok}/${fixes.length} OK`);
}

main();
