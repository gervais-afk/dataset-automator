import * as fs from 'fs';
import * as path from 'path';
import pino from 'pino';

const logger = pino({ transport: { target: 'pino-pretty' } });

export class RagRetriever {
  static loadKnowledgeBase(domain: string): string {
    const domainDir = path.join(__dirname, '..', '..', '..', 'knowledge_base', domain);
    
    if (!fs.existsSync(domainDir)) {
      logger.warn(`[RAG WARN] Aucun dossier de connaissances trouvé pour le domaine : ${domain}`);
      return '';
    }

    try {
      const files = fs.readdirSync(domainDir).filter(f => f.endsWith('.md'));
      let combinedKnowledge = `=== KNOWLEDGE BASE: ${domain.toUpperCase()} ===\n`;
      
      for (const file of files) {
        const filePath = path.join(domainDir, file);
        const content = fs.readFileSync(filePath, 'utf-8');
        combinedKnowledge += `\n--- Document: ${file} ---\n${content}\n`;
      }
      
      logger.info(`[RAG INFO] ${files.length} documents chargés pour le domaine ${domain}`);
      return combinedKnowledge;
    } catch (error) {
      logger.error({ err: error }, `[RAG ERROR] Erreur lors de la lecture du domaine ${domain}`);
      return '';
    }
  }
}
