import { OKFReader } from '../src/rag/okfReader';
import * as path from 'path';

function test() {
  const filePath = path.resolve(__dirname, '../../knowledge_base/medical/medical_context.okf.md');
  console.log(`Parsing OKF file at: ${filePath}`);
  try {
    const context = OKFReader.parse(filePath);
    console.log("✅ Parsing successful!");
    console.log(JSON.stringify(context, null, 2));
  } catch (error) {
    console.error("❌ Parsing failed:", error);
  }
}

test();
