import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import pino from 'pino';

const logger = pino({ transport: { target: 'pino-pretty' } });

export class GraphRetriever {
  /**
   * Étape 1 : Appel léger à LM Studio pour extraire les concepts clés du profil
   */
  static async extractConcepts(profile: any): Promise<string[]> {
    logger.info("\n[Graph RAG] Extraction des concepts clés via LM Studio...");
    
    // Simplifier le profil pour ne pas exploser le contexte dès l'étape 1
    const minimalProfile = {
      total_rows: profile.total_rows,
      total_columns: profile.total_columns,
      features: profile.features.map((f: any) => ({
        name: f.name,
        type: f.type,
        missing_percentage: f.missing_percentage,
        skewness: f.skewness
      }))
    };

    const prompt = `
Tu es l'Agent Stratège Data Science.
Analyse ce profil de dataset JSON et donne-moi une liste de 2 ou 3 mots-clés représentant des concepts métier à explorer dans notre base de connaissances (ex: Stationnarité, Lagged Features, Valeurs Aberrantes, K-Means, etc.).
Ne donne aucune autre explication. Renvoie UNIQUEMENT un tableau JSON de chaînes de caractères.
Profil du dataset :
${JSON.stringify(minimalProfile)}

Exemple attendu : ["stationnarité", "log_transform"]
`;

    try {
      const response = await axios.post('http://127.0.0.1:1234/v1/chat/completions', {
        model: 'google/gemma-4-12b',
        messages: [{ role: 'user', content: prompt }],
        temperature: 0.1
      });

      const responseText = response.data.choices[0].message.content;
      
      // Essayer de parser proprement le JSON retourné
      const match = responseText.match(/\[(.*?)\]/s);
      if (match) {
        const concepts = JSON.parse(`[${match[1]}]`);
        logger.info(`[Graph RAG] Concepts extraits : ${concepts.join(', ')}`);
        return concepts;
      }
      return [];
    } catch (err) {
      logger.error("[Graph RAG ERROR] Impossible d'extraire les concepts via LLM.");
      return [];
    }
  }

  /**
   * Étape 2 : Récupérer UNIQUEMENT les fiches markdown pertinentes
   */
  static retrieveRelevantKnowledge(domain: string, concepts: string[]): string {
    const domainDir = path.join(__dirname, '..', '..', '..', 'knowledge_base', domain);
    
    if (!fs.existsSync(domainDir)) {
      logger.warn(`[Graph RAG WARN] Aucun dossier de connaissances trouvé pour le domaine : ${domain}`);
      return '';
    }

    try {
      const files = fs.readdirSync(domainDir).filter(f => f.endsWith('.md'));
      let combinedKnowledge = `=== TARGETED KNOWLEDGE BASE: ${domain.toUpperCase()} ===\n`;
      let loadedCount = 0;
      
      for (const file of files) {
        const filePath = path.join(domainDir, file);
        const content = fs.readFileSync(filePath, 'utf-8');
        
        // Recherche des mots-clés dans la fiche (Frontmatter YAML ou corps du texte)
        const contentLower = content.toLowerCase();
        // Fallback: si aucun concept n'est renvoyé, on ne charge rien (ou on charge un fallback générique)
        // Pour éviter l'explosion de contexte, on est très restrictif
        const matches = concepts.some(concept => contentLower.includes(concept.toLowerCase().trim()));
        
        if (matches) {
          combinedKnowledge += `\n--- Document: ${file} ---\n${content}\n`;
          loadedCount++;
        }
      }
      
      // Fallback si 0 match : on renvoie juste les concepts pour guider un peu
      if (loadedCount === 0) {
        logger.info(`[Graph RAG INFO] 0 document parfaitement matché. Envoi des concepts nus.`);
        return `Concepts identifiés (aucune fiche détaillée trouvée) : ${concepts.join(', ')}`;
      }
      
      logger.info(`[Graph RAG INFO] ${loadedCount}/${files.length} documents pertinents ciblés pour le domaine ${domain}`);
      
      // Troncation ultime de sécurité si le texte combiné est encore trop long (ex: > 4000 caractères)
      if (combinedKnowledge.length > 4000) {
        logger.warn("[Graph RAG WARN] Les fiches combinées dépassent 4000 caractères. Troncation de sécurité activée.");
        return combinedKnowledge.substring(0, 4000) + "\n...[TRONQUÉ]";
      }
      
      return combinedKnowledge;
    } catch (error) {
      logger.error({ err: error }, `[Graph RAG ERROR] Erreur lors de la lecture du domaine ${domain}`);
      return '';
    }
  }
}
