import neo4j from 'neo4j-driver';
import fs from 'fs';
import path from 'path';

async function main() {
  const passwords = ['password123', 'password'];
  let driver;

  for (const pwd of passwords) {
    console.log(`Testing connection with password: ${pwd}`);
    const tempDriver = neo4j.driver(
      'bolt://127.0.0.1:7687',
      neo4j.auth.basic('neo4j', pwd)
    );
    try {
      await tempDriver.verifyConnectivity();
      driver = tempDriver;
      console.log(`✅ Connected successfully with password: ${pwd}`);
      break;
    } catch (e: any) {
      console.log(`❌ Failed with password ${pwd}: ${e.message}`);
      await tempDriver.close();
    }
  }

  if (!driver) {
    console.error("❌ Could not connect to Neo4j with any known password.");
    return;
  }
  
  const filesToInject = [
    path.resolve(__dirname, '../../scripts/neo4j/enrich_interpretation_rules.cypher'),
    path.resolve(__dirname, '../../scripts/neo4j/enrich_business_costs.cypher'),
    path.resolve(__dirname, '../../scripts/neo4j/enrich_mlops_advanced.cypher')
  ];
  
  const session = driver.session();
  console.log("Cleaning up any existing empty nodes without labels...");
  try {
    await session.run("MATCH (n) WHERE labels(n) = [] DETACH DELETE n");
    console.log("✅ Cleanup complete.");
  } catch (err: any) {
    console.warn(`⚠️ Warning during cleanup: ${err.message}`);
  }

  for (const cypherFile of filesToInject) {
    if (!fs.existsSync(cypherFile)) {
      console.warn(`⚠️ File not found: ${cypherFile}`);
      continue;
    }
    console.log(`\nReading and injecting file: ${path.basename(cypherFile)}...`);
    const cypherText = fs.readFileSync(cypherFile, 'utf8');
    const statements = cypherText.split(/;\s*$/m).filter(s => s.trim().length > 0);
    
    console.log(`Injecting ${statements.length} statements into Neo4j...`);
    try {
      for (let i = 0; i < statements.length; i++) {
        const stmt = statements[i]?.trim();
        if (!stmt) continue;
        if (stmt.startsWith('//') && !stmt.includes('\n')) continue; 
        
        console.log(`Executing statement ${i + 1}/${statements.length}...`);
        await session.run(stmt);
      }
      console.log(`✅ File ${path.basename(cypherFile)} injection complete!`);
    } catch (error) {
      console.error(`❌ Error during injection of ${path.basename(cypherFile)}:`, error);
    }
  }

  await session.close();
  await driver.close();
}

main();
