import neo4j from 'neo4j-driver';
import fs from 'fs';
import path from 'path';

async function main() {
  const passwords = ['password123', 'password'];
  let driver;
  let activePassword = '';

  for (const pwd of passwords) {
    console.log(`Testing connection with password: ${pwd}`);
    const tempDriver = neo4j.driver(
      'bolt://127.0.0.1:7687',
      neo4j.auth.basic('neo4j', pwd)
    );
    try {
      await tempDriver.verifyConnectivity();
      driver = tempDriver;
      activePassword = pwd;
      console.log(`✅ Connected successfully with password: ${pwd}`);
      break;
    } catch (e: any) {
      console.log(`❌ Failed with password ${pwd}: ${e.message}`);
      await tempDriver.close();
    }
  }

  if (!driver) {
    console.error("❌ Could not connect to Neo4j with any known password. Is the container fully started?");
    return;
  }
  
  const cypherFile = path.resolve(__dirname, '../../scripts/neo4j/import-knowledge-graph.cypher');
  const cypherText = fs.readFileSync(cypherFile, 'utf8');
  const statements = cypherText.split(/;\s*$/m).filter(s => s.trim().length > 0);
  
  const session = driver.session();
  console.log(`Injecting ${statements.length} statements into Neo4j...`);
  
  try {
    for (let i = 0; i < statements.length; i++) {
      const stmt = statements[i]?.trim();
      if (!stmt) continue;
      if (stmt.startsWith('//') && !stmt.includes('\n')) continue; 
      
      console.log(`Executing statement ${i + 1}/${statements.length}...`);
      await session.run(stmt);
    }
    console.log("✅ Injection complete!");
  } catch (error) {
    console.error("❌ Error during injection:", error);
  } finally {
    await session.close();
    await driver.close();
  }
}

main();
