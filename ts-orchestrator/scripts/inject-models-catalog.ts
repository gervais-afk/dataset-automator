import neo4j from 'neo4j-driver';
import fs from 'fs';
import path from 'path';

async function main() {
  const passwords = ['password123', 'password'];
  let driver: any;

  for (const pwd of passwords) {
    const tempDriver = neo4j.driver('bolt://127.0.0.1:7687', neo4j.auth.basic('neo4j', pwd));
    try {
      await tempDriver.verifyConnectivity();
      driver = tempDriver;
      console.log(`✅ Connecté à Neo4j (password: ${pwd})`);
      break;
    } catch {
      await tempDriver.close();
    }
  }

  if (!driver) {
    console.error('❌ Impossible de se connecter à Neo4j.');
    return;
  }

  const cypherFile = path.resolve(__dirname, '../../scripts/neo4j/enrich_models_catalog.cypher');
  const cypherText = fs.readFileSync(cypherFile, 'utf8');
  
  // Split on semicolons, keeping multi-line statements intact
  const statements = cypherText
    .split(/;\s*\n/)
    .map(s => s.trim())
    .filter(s => s.length > 0 && !s.startsWith('//'));

  const session = driver.session();
  console.log(`📦 ${statements.length} déclarations à injecter dans Neo4j...`);

  let ok = 0;
  let errors = 0;
  try {
    for (let i = 0; i < statements.length; i++) {
      const stmt = statements[i];
      if (!stmt || stmt.startsWith('//')) continue;
      try {
        await session.run(stmt);
        ok++;
        console.log(`  ✅ [${i+1}/${statements.length}] OK`);
      } catch (e: any) {
        errors++;
        console.error(`  ❌ [${i+1}] ERREUR: ${e.message?.substring(0, 100)}`);
        console.error(`     Statement: ${stmt.substring(0, 80)}...`);
      }
    }
  } finally {
    await session.close();
    await driver.close();
  }

  console.log(`\n🏁 Injection terminée: ${ok} OK, ${errors} erreurs`);
}

main();
