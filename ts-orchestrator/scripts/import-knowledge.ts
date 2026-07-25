import { KnowledgeGraphClient } from '../src/rag/knowledge-graph-client';
import * as path from 'path';
import * as fs from 'fs';

async function main() {
  console.log("⚡ Starting Knowledge Import...");
  const client = new KnowledgeGraphClient();
  const inputPath = path.resolve(__dirname, '../knowledge-share.json');
  
  if (!fs.existsSync(inputPath)) {
    console.error(`❌ Error: Shared knowledge file not found at ${inputPath}. Please run export first!`);
    await client.close();
    process.exit(1);
  }

  try {
    const count = await client.importSharedKnowledge(inputPath);
    console.log(`\n✅ SUCCESS! Imported ${count} anonymized runs into the local Neo4j database.`);
  } catch (error) {
    console.error("❌ Error during import:", error);
  } finally {
    await client.close();
  }
}

main();
