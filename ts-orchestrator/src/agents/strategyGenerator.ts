import { z, ZodError } from 'zod';
import pino from 'pino';
import { FirestoreService } from '../firebase/firestore';

const logger = pino({ transport: { target: 'pino-pretty' } });

// ======================
// SCHEMA ZOD EXACT
// ======================
export const CleaningStrategySchema = z.object({
  target: z.string().describe("La colonne cible de la tâche ou 'None' si clustering"),
  task_type: z.enum(["regression", "classification", "clustering", "timeseries"]).describe("Le type de tâche ML"),
  steps: z.array(z.object({
    column: z.string().describe("Le nom exact de la colonne (ou 'all')"),
    action: z.enum(["drop", "impute_mean", "impute_median", "scale", "winsorize", "k_means", "encode"]).describe("L'action technique stricte à appliquer"),
    reasoning: z.string().describe("La justification métier tirée du graphe Neo4j")
  })).describe("La séquence ordonnée des étapes de nettoyage")
});

export type CleaningStrategy = z.infer<typeof CleaningStrategySchema>;

// ======================
// PROMPT TEMPLATE
// ======================
const STRATEGY_TEMPLATE = `{
  "target": "nom_de_la_colonne_cible",
  "task_type": "timeseries",
  "steps": [
    {
      "column": "nom_colonne",
      "action": "winsorize",
      "reasoning": "Justification de l'action selon les connaissances Neo4j"
    }
  ]
}`;

function buildPrompt(context: string, lastError: string, attempt: number): string {
  let prompt = `Tu es l'Agent Stratège Data Science.
Analyse le profil du dataset et génère une stratégie de nettoyage.

Contexte du dataset et Connaissances :
${context}

Tu DOIS répondre EXCLUSIVEMENT avec un JSON valide respectant STRICTEMENT ce schéma d'exemple :

${STRATEGY_TEMPLATE}

RÈGLES STRICTES :
- Ne rajoute aucune clé supplémentaire (pas de "cleaning_strategy", "feature_engineering", etc.)
- Ne mets aucun texte avant ou après le JSON.
- Utilise uniquement les "action" autorisées dans l'enum (drop, impute_mean, impute_median, scale, winsorize, k_means, encode).
- Sois précis et déterministe.`;

  if (lastError) {
    prompt += `\n\nATTENTION - Ta précédente réponse a été rejetée par le validateur strict Zod avec l'erreur suivante :
[${lastError}]

Corrige IMPÉRATIVEMENT ton JSON pour qu'il respecte exactement le schéma attendu. Ne renvoie QUE le JSON valide cette fois. Ne rajoute pas de texte markdown autour.`;
  }

  return prompt;
}

function extractJsonFromText(text: string): string {
  // Extrait le contenu entre les premières accolades {} ou [] même avec du markdown
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (jsonMatch) return jsonMatch[0];
  return text;
}

function getFallbackStrategy(target: string, taskType: string): CleaningStrategy {
  return {
    target: target || "unsupervised_segments",
    task_type: (taskType as any) || "clustering",
    steps: [
      { column: 'income, spending_score', action: 'scale', reasoning: 'Fallback: Standardisation requise' },
      { column: 'all', action: 'k_means', reasoning: 'Fallback: Recherche de clusters' }
    ]
  };
}

// ======================
// MAIN FUNCTION AVEC SELF-HEALING
// ======================
export async function generateStrategyWithSelfHealing(
  ai: any,
  model: any,
  context: string,
  target: string,
  taskType: string,
  jobId: string,
  maxRetries: number = 3
): Promise<{ strategy: CleaningStrategy; source: string }> {
  
  let lastError = '';

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      if (attempt > 1) {
        logger.warn(`🔄 Tentative d'auto-correction (Retry ${attempt}/${maxRetries}) en cours...`);
        await FirestoreService.updateJobStatus(jobId, { 
            current_message: `Erreur LLM détectée. Tentative d'auto-correction Zod (${attempt}/${maxRetries})...`,
            retries_count: attempt - 1,
            last_zod_error: lastError
        });
        
        // Backoff exponentiel (1s, 2s, 4s...)
        const backoffMs = Math.pow(2, attempt - 1) * 1000;
        await new Promise(r => setTimeout(r, backoffMs));
      }

      const promptText = buildPrompt(context, lastError, attempt);

      const response = await ai.generate({
        model: model,
        prompt: promptText,
        output: {
          format: "json",
          schema: CleaningStrategySchema
        },
        config: {
          temperature: attempt === 1 ? 0.2 : 0.1
        }
      });

      // Si Genkit (via Zod interne) réussit à parser :
      let strategy = response.output;
      
      if (!strategy) {
         // Fallback manuel si l'output n'a pas été parsé par Genkit
         const rawText = response.text();
         const jsonString = extractJsonFromText(rawText);
         const parsed = JSON.parse(jsonString);
         strategy = CleaningStrategySchema.parse(parsed);
      }

      if (attempt > 1) {
        logger.info(`✅ Stratégie corrigée avec succès par Gemma au retry ${attempt} !`);
      }
      
      return { strategy, source: attempt === 1 ? 'human_validated' : 'self_healing' };

    } catch (error: any) {
      // Genkit jette souvent des ZodError enveloppées ou directement des ZodError
      if (error.name === 'ZodError' || error.message.includes('Schema validation failed')) {
        lastError = error.message;
        
        logger.warn(`❌ Tentative ${attempt}/${maxRetries} - Erreur de validation de schéma: ${lastError}`);
        
        if (attempt === maxRetries) {
          logger.error("Échec du Self-Healing après le maximum de retries. Activation du Fallback.");
          await FirestoreService.updateJobStatus(jobId, { 
            current_message: "Échec du Self-Healing. Stratégie de secours activée.",
            strategy_source: 'fallback'
          });
          return { strategy: getFallbackStrategy(target, taskType), source: 'fallback' };
        }
        
        // On continue sur le retry suivant
        continue;
      }
      
      // Autres erreurs (réseau, timeout, etc.)
      logger.error(`Erreur inattendue à la tentative ${attempt}`, error);
      if (attempt === maxRetries) {
          return { strategy: getFallbackStrategy(target, taskType), source: 'fallback' };
      }
    }
  }

  return { strategy: getFallbackStrategy(target, taskType), source: 'fallback' };
}
