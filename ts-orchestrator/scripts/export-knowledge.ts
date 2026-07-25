import { KnowledgeGraphClient } from '../src/rag/knowledge-graph-client';
import * as path from 'path';

async function main() {
  console.log("⚡ Starting Anonymized Knowledge Export...");
  const client = new KnowledgeGraphClient();
  const outputPath = path.resolve(__dirname, '../knowledge-share.json');
  
  try {
    await client.exportAnonymizedKnowledge(outputPath);
    console.log(`\n✅ SUCCESS! Anonymized runs exported successfully to: ${outputPath}`);
  } catch (error) {
    console.error("❌ Error during export:", error);
  } finally {
    await client.close();
  }
}

main();
