import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import pino from 'pino';
import { getActiveModelName } from '../llm-utils';

const logger = pino({ transport: { target: 'pino-pretty' } });

export class GraphRetriever {
  /**
   * Step 1: Lightweight LM Studio call to extract key concepts from the profile
   */
  static async extractConcepts(profile: any): Promise<string[]> {
    logger.info("\n[Graph RAG] Extracting key concepts via LM Studio...");
    
    // Simplify the profile to avoid exploding context at step 1
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
You are the Data Science Strategist Agent.
Analyze this JSON dataset profile and give me a list of 2 or 3 keywords representing business concepts to explore in our knowledge base (e.g., Stationarity, Lagged Features, Outliers, K-Means, etc.).
Do not give any other explanation. Return ONLY a JSON array of strings.
Dataset profile:
${JSON.stringify(minimalProfile)}

Expected example: ["stationarity", "log_transform"]
`;

    try {
      const provider = process.env.LLM_PROVIDER || 'local';
      const apiKey = process.env.OPENROUTER_API_KEY || '';
      const primaryModel = process.env.PRIMARY_MODEL || 'google/gemini-3.5-flash';
      const fallbackModel = process.env.FALLBACK_MODEL || 'google/gemma-4-26b-a4b-it';
      
      let response;
      if (provider === 'openrouter') {
        logger.info(`📡 [Graph RAG] Extracting concepts via OpenRouter...`);
        try {
          response = await axios.post('https://openrouter.ai/api/v1/chat/completions', {
            model: primaryModel,
            messages: [{ role: 'user', content: prompt }],
            temperature: 0.1
          }, {
            timeout: 180000,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${apiKey}`,
              'HTTP-Referer': 'http://localhost:3000',
              'X-Title': 'Dataset Automator'
            }
          });
        } catch (err: any) {
          logger.warn(`⚠️ [Graph RAG] Primary model Gemini failed for concepts extraction. Trying fallback Gemma 4...`);
          response = await axios.post('https://openrouter.ai/api/v1/chat/completions', {
            model: fallbackModel,
            messages: [{ role: 'user', content: prompt }],
            temperature: 0.1
          }, {
            timeout: 180000,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${apiKey}`,
              'HTTP-Referer': 'http://localhost:3000',
              'X-Title': 'Dataset Automator'
            }
          });
        }
      } else {
        const activeModel = await getActiveModelName();
        response = await axios.post('http://127.0.0.1:1234/v1/chat/completions', {
          model: activeModel,
          messages: [{ role: 'user', content: prompt }],
          temperature: 0.1
        }, {
          timeout: 300000
        });
      }

      const responseText = response.data.choices[0].message.content;
      
      // Try to cleanly parse the returned JSON
      const match = responseText.match(/\[(.*?)\]/s);
      if (match) {
        const concepts = JSON.parse(`[${match[1]}]`);
        logger.info(`[Graph RAG] Concepts extracted: ${concepts.join(', ')}`);
        return concepts;
      }
      return [];
    } catch (err) {
      logger.error("[Graph RAG ERROR] Unable to extract concepts via LLM.");
      return [];
    }
  }

  static parseFrontmatter(content: string): { meta: Record<string, any>; body: string } {
    const match = content.match(/^---\r?\n([\s\S]+?)\r?\n---/);
    if (!match || !match[1]) return { meta: {}, body: content };
    const meta: Record<string, any> = {};
    const lines = match[1].split(/\r?\n/);
    for (const line of lines) {
      if (line.includes(':')) {
        const parts = line.split(':');
        const key = parts[0]?.trim();
        const val = parts.slice(1).join(':').trim();
        if (key) {
          meta[key] = val;
        }
      }
    }
    return { meta, body: content.substring(match[0].length).trim() };
  }

  static calculateTrustTier(meta: Record<string, any>): { tier: 'TIER_1' | 'TIER_2' | 'EXCLUDE'; reason?: string } {
    if (meta.status && meta.status.toLowerCase() === 'deprecated') {
      return { tier: 'EXCLUDE', reason: 'Concept is marked as deprecated' };
    }
    if (meta.stale_after) {
      const staleDate = new Date(meta.stale_after);
      if (!isNaN(staleDate.getTime()) && staleDate < new Date()) {
        return { tier: 'EXCLUDE', reason: 'Concept has expired stale_after freshness date' };
      }
    }
    if (meta.verified && (meta.verified.includes('human:') || meta.verified.includes('@'))) {
      return { tier: 'TIER_1' };
    }
    return { tier: 'TIER_2' };
  }

  /**
   * Étape 2 : Récupérer UNIQUEMENT les fiches markdown pertinentes et certifiées OKF v0.2
   */
  static retrieveRelevantKnowledge(domain: string, concepts: string[]): string {
    const domainDir = path.join(__dirname, '..', '..', '..', 'knowledge_base', domain);
    
    if (!fs.existsSync(domainDir)) {
      logger.warn(`[Graph RAG WARN] Aucun dossier de connaissances trouvé pour le domaine : ${domain}`);
      return '';
    }

    try {
      const files = fs.readdirSync(domainDir).filter(f => f.endsWith('.md'));
      let combinedKnowledge = `=== TARGETED KNOWLEDGE BASE (OKF v0.2 TRUST-TIERED): ${domain.toUpperCase()} ===\n`;
      let loadedCount = 0;
      
      for (const file of files) {
        const filePath = path.join(domainDir, file);
        const content = fs.readFileSync(filePath, 'utf-8');
        const { meta, body } = this.parseFrontmatter(content);
        
        // Trust Tier computation according to OKF v0.2 standard
        const trust = this.calculateTrustTier(meta);
        if (trust.tier === 'EXCLUDE') {
          logger.warn(`[Graph RAG OKF] Excluding record ${file}: ${trust.reason}`);
          continue;
        }

        const contentLower = content.toLowerCase();
        const matches = concepts.some(concept => contentLower.includes(concept.toLowerCase().trim()));
        
        if (matches) {
          const badge = trust.tier === 'TIER_1' ? '🛡️ [OKF TIER 1 - HUMAN REVIEWED]' : '🤖 [OKF TIER 2 - MACHINE CONFIRMED]';
          combinedKnowledge += `\n--- Document: ${file} ${badge} ---\n`;
          combinedKnowledge += `Title: ${meta.title || file}\n`;
          if (meta.sources) combinedKnowledge += `Sources: ${meta.sources}\n`;
          combinedKnowledge += `${body}\n`;
          loadedCount++;
        }
      }
      
      if (loadedCount === 0) {
        logger.info(`[Graph RAG INFO] 0 documents perfectly matched. Sending raw concepts.`);
        return `Identified concepts (no detailed records found): ${concepts.join(', ')}`;
      }
      
      logger.info(`[Graph RAG INFO] ${loadedCount}/${files.length} OKF v0.2 certified documents targeted for domain ${domain}`);
      
      if (combinedKnowledge.length > 5000) {
        logger.warn("[Graph RAG WARN] Combined records exceed 5000 characters. Safety truncation activated.");
        return combinedKnowledge.substring(0, 5000) + "\n...[TRUNCATED]";
      }
      
      return combinedKnowledge;
    } catch (error) {
      logger.error({ err: error }, `[Graph RAG ERROR] Error reading domain ${domain}`);
      return '';
    }
  }
}
