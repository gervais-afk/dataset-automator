import { z, ZodError } from 'zod';
import pino from 'pino';
import { FirestoreService } from '../firebase/firestore';

const logger = pino({ transport: { target: 'pino-pretty' } });

// ======================
// SCHEMA ZOD EXACT
// ======================
export const CleaningStrategySchema = z.object({
  target: z.string().nullable().describe("La colonne cible de la tâche ou 'None' si clustering"),
  task_type: z.enum([
    "regression", "classification", "clustering", "timeseries",
    "anomaly_detection", "survival_analysis", "recommender_system",
    "causal_inference", "association_rules", "ab_testing",
    "semi_supervised", "optimization", "graph_analysis",
    "reinforcement_learning", "nlp", "computer_vision"
  ]).describe("Le type de tâche ML"),
  steps: z.array(z.object({
    column: z.string().describe("Le nom exact de la colonne (ou 'all')"),
    action: z.enum(["drop", "impute_mean", "impute_median", "scale", "winsorize", "k_means", "encode", "sanitize_phone", "normalize_cam_geo", "clean_fcfa", "parse_momo", "pca", "add_time_features", "formula"]).describe("L'action technique stricte à appliquer"),
    formula: z.string().optional().describe("Expression mathématique à évaluer, ex: 'Weight / (Height ** 2)'"),
    reasoning: z.string().optional().describe("La justification métier tirée du graphe Neo4j")
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
    },
    {
      "column": "IMC",
      "action": "formula",
      "formula": "Weight / (Height ** 2)",
      "reasoning": "Calcul de l'Indice de Masse Corporelle"
    }
  ]
}`;

function buildSystemPrompt(target: string): string {
  return `Tu es l'Agent Stratège Data Science.
Analyse le profil du dataset et génère une stratégie de nettoyage.

Tu DOIS répondre EXCLUSIVEMENT avec un JSON valide respectant STRICTEMENT ce schéma d'exemple :

${STRATEGY_TEMPLATE}

RÈGLES STRICTES :
- Ne rajoute aucune clé supplémentaire (pas de "cleaning_strategy", "feature_engineering", etc.)
- Ne mets aucun texte avant ou après le JSON.
- Utilise uniquement les "action" autorisées dans l'enum (drop, impute_mean, impute_median, scale, winsorize, k_means, encode, sanitize_phone, normalize_cam_geo, clean_fcfa, parse_momo, pca, add_time_features, formula).
- Si tu utilises l'action "formula", tu DOIS obligatoirement fournir le champ "formula" contenant la formule arithmétique correspondante issue de la base de connaissances (ex: "Weight / (Height ** 2)").
- FILTRAGE DES ÉTAPES (CRITIQUE) :
  * Décrivez uniquement les colonnes qui requièrent RÉELLEMENT une action (valeurs manquantes > 0%, catégorielles à encoder, ou asymétrie extrême > 1.5 à mettre à l'échelle, ou formules du domaine à évaluer).
  * Si une colonne numérique est déjà complète (0% missing) et équilibrée, ne l'incluez PAS dans la liste des étapes. Moins il y a d'étapes inutiles, plus le JSON est généré rapidement et sans erreur.
- ATTENTION AUX COMPATIBILITÉS DE TYPES ET PROTECTION DES FEATURES :
  * Ne supprimez PAS (action 'drop') de colonnes prédictives clés (comme le Poids 'Weight', la Taille 'Height', 'Age') sous prétexte de drift. Supprimez un identifiant unique ou une colonne vide (> 50% NaNs), mais conservez les variables métier clés.
  * Ne mets JAMAIS 'scale', 'winsorize', 'impute_mean' ou 'impute_median' sur des colonnes de texte ou de date.
  * Ne mets JAMAIS d'étape de nettoyage ou de suppression sur la colonne cible (target) (ici '${target}'). Ne lui associez JAMAIS l'action 'drop' ni aucune autre action. Elle doit obligatoirement être conservée intacte pour l'entraînement.
- GESTION DES VALEURS MANQUANTES (NaNs) et CATÉGORIELLES :
  * Si une colonne numérique a des NaNs (> 0%), appliquez obligatoirement 'impute_median' ou 'impute_mean' (ou 'drop').
  * Si une colonne catégorielle a des NaNs, appliquez 'encode' ou 'drop'.
- ANALYSE SANS HALLUCINATION :
  * Utilisez uniquement les pourcentages réels de valeurs manquantes et d'asymétrie décrits dans le profil du dataset de ce run. Ne recopiez JAMAIS les pourcentages d'exemples comme '5.14%' ou '8.85%' du template ou d'anciens runs.
- Sois précis et déterministe.
- EXTRÊMEMENT IMPORTANT : Rends le champ "reasoning" de chaque étape extrêmement court (maximum 4 mots).
- IMPORTANT : Réponds DIRECTEMENT avec le JSON valide. Ne fais PAS de chaîne de pensée (chain of thought). Ton format de sortie doit être uniquement le JSON.`;
}

function buildUserPrompt(context: string, lastError: string, missingColumns: string[]): string {
  // Tronquer le contexte pour éviter les prompts de + de 1500 tokens
  // Le contexte Neo4j peut être très volumineux (concepts + règles + procédures)
  // Fix: réduit à 1800 chars (~450 tokens) pour laisser ~2000 tokens au modèle pour générer
  const MAX_CONTEXT_CHARS = 1800; // ~450 tokens
  const trimmedContext = context.length > MAX_CONTEXT_CHARS
    ? context.substring(0, MAX_CONTEXT_CHARS) + '\n... [Contexte tronqué pour rester dans les limites du modèle]'
    : context;

  let prompt = `Voici le profil du dataset et les connaissances disponibles :
${trimmedContext}

⚠️ RÈGLE CRITIQUE DE VALIDATION :
Les colonnes suivantes contiennent des valeurs manquantes et doivent OBLIGATOIREMENT être imputées ('impute_mean', 'impute_median', 'encode') ou supprimées ('drop') dans la liste "steps" :
${missingColumns.length > 0 ? missingColumns.map(c => `- ${c}`).join('\n') : "(aucune colonne avec valeurs manquantes)"}

Génère la stratégie de nettoyage pour ce jeu de données en respectant le schéma JSON.`;

  if (lastError) {
    prompt += `\n\nATTENTION - Ta précédente réponse a été rejetée par le validateur avec l'erreur suivante :
[${lastError}]

Corrige IMPÉRATIVEMENT ton JSON pour qu'il respecte exactement le schéma attendu. Ne renvoie QUE le JSON valide.`;
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
  const normalizedTask = (taskType || '').toLowerCase();
  
  if (normalizedTask === 'classification' || normalizedTask === 'regression') {
    return {
      target: target || "class",
      task_type: (normalizedTask as any),
      steps: [
        { column: 'all', action: 'impute_median', reasoning: 'Fallback: Imputation par médiane pour les valeurs manquantes' },
        { column: 'all', action: 'encode', reasoning: 'Fallback: Encodage de toutes les variables catégorielles pour la modélisation' }
      ]
    };
  }
  
  if (normalizedTask === 'timeseries' || normalizedTask === 'time_series') {
    return {
      target: target || "Close",
      task_type: "timeseries",
      steps: [
        { column: 'all', action: 'impute_median', reasoning: 'Fallback: Imputation par médiane pour les séries temporelles' },
        { column: 'all', action: 'scale', reasoning: 'Fallback: Mise à l\'échelle pour stabiliser la variance' }
      ]
    };
  }
  
  // Default fallback for clustering or other tasks
  return {
    target: target || "unsupervised_segments",
    task_type: (normalizedTask as any) || "clustering",
    steps: [
      { column: 'all', action: 'impute_median', reasoning: 'Fallback: Imputation par médiane' },
      { column: 'all', action: 'scale', reasoning: 'Fallback: Standardisation requise pour la cohérence des échelles' }
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
  maxRetries: number = 3,
  tools?: any[]
): Promise<{ strategy: CleaningStrategy; source: string }> {
  
  let lastError = '';

  // Extraction préalable des colonnes contenant des valeurs manquantes à partir du contexte
  const missingColumns: string[] = [];
  const lines = context.split('\n');
  for (const line of lines) {
    const match = line.match(/^\s*-\s+([a-zA-Z0-9_\-]+)\s+\([^)]+\):\s+([0-9.]+)\s*%\s+missing/);
    if (match) {
      const colName = match[1];
      const missingPctStr = match[2];
      if (colName && missingPctStr) {
        const missingPct = parseFloat(missingPctStr);
        if (missingPct > 0) {
          missingColumns.push(colName);
        }
      }
    }
  }

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

      const systemPrompt = buildSystemPrompt(target);
      const userPrompt = buildUserPrompt(context, lastError, missingColumns);

      const response = await ai.generate({
        model: model,
        system: systemPrompt,
        prompt: userPrompt,
        ...(tools && tools.length > 0 ? { tools } : {}),
        config: {
          temperature: attempt === 1 ? 0.4 : 0.3,
          maxOutputTokens: 1000  // Fix: la stratégie JSON est petite, mais 600 peut tronquer sur de grands datasets
        }
      });

      const rawText = response.text;

      // ─── DEGENERATION DETECTOR (strategyGenerator) ───────────────────────
      // Si le modèle génère des séquences répétitives (??????, ssql???..., 
      // ou du texte répété > 30 fois de suite), c'est une dégenérescence LLM.
      // On passe DIRECTEMENT au fallback sans perdre du temps à retenter.
      const degenerationPattern = /(\?{10,}|(.{3,})\2{15,})/s;
      const sqlJunkPattern = /^[a-z]{0,10}\?{5,}/i; // ex: "ssql?????..."
      if (degenerationPattern.test(rawText) || sqlJunkPattern.test(rawText.trim())) {
        logger.warn(`🧨 [DEGENERATION DÉTECTÉE dans strategyGenerator] Réponse corrompue (longueur: ${rawText.length}). Passage direct au fallback sans retry.`);
        const fallback = getFallbackStrategy(target, taskType);
        return { strategy: fallback, source: 'fallback_degeneration' };
      }
      // ─────────────────────────────────────────────────────────────────────

      const jsonString = extractJsonFromText(rawText);
      const parsed = JSON.parse(jsonString);
      const strategy = CleaningStrategySchema.parse(parsed);

      // Validation métier & ML additionnelle pour le Self-Healing
      if (strategy.steps && strategy.target) {
        for (const step of strategy.steps) {
          if (step.column === strategy.target) {
            if (['scale', 'winsorize', 'impute_mean', 'impute_median'].includes(step.action)) {
              const validationErr = new Error(`Validation Error : La colonne cible '${strategy.target}' ne doit JAMAIS subir l'action de nettoyage '${step.action}' car cela corrompt sa distribution pour la modélisation.`);
              validationErr.name = 'ValidationError';
              throw validationErr;
            }
            if (step.action === 'drop') {
              const validationErr = new Error(`Validation Error : La colonne cible '${strategy.target}' ne doit JAMAIS être supprimée (action 'drop'). Le modèle a besoin de cette colonne pour s'entraîner.`);
              validationErr.name = 'ValidationError';
              throw validationErr;
            }
          }
        }
      }

      // Validation de la gestion obligatoire des valeurs manquantes (NaNs)
      if (strategy.steps) {
        const missingColumns: string[] = [];
        const lines = context.split('\n');
        for (const line of lines) {
          const match = line.match(/^\s*-\s+([a-zA-Z0-9_\-]+)\s+\([^)]+\):\s+([0-9.]+)\s*%\s+missing/);
          if (match) {
            const colName = match[1];
            const missingPctStr = match[2];
            if (colName && missingPctStr) {
              const missingPct = parseFloat(missingPctStr);
              if (missingPct > 0) {
                missingColumns.push(colName);
              }
            }
          }
        }

        const hasAllImpute = strategy.steps.some(s => s.column === 'all' && ['impute_mean', 'impute_median', 'encode'].includes(s.action));
        if (!hasAllImpute) {
          for (const col of missingColumns) {
            if (col === strategy.target) continue;
            const handled = strategy.steps.some(s => 
              s.column === col && ['impute_mean', 'impute_median', 'drop', 'encode'].includes(s.action)
            );
            if (!handled) {
              const validationErr = new Error(`Validation Error : La colonne '${col}' contient des valeurs manquantes mais n'est pas imputée ('impute_mean', 'impute_median', 'encode') ou supprimée ('drop') dans la stratégie de nettoyage.`);
              validationErr.name = 'ValidationError';
              throw validationErr;
            }
          }
        }
      }

      if (attempt > 1) {
        logger.info(`✅ Stratégie corrigée avec succès par Gemma au retry ${attempt} !`);
      }
      
      return { strategy, source: attempt === 1 ? 'human_validated' : 'self_healing' };

    } catch (error: any) {
      logger.error(error, `❌ Erreur attrapée à la tentative ${attempt}`);
      
      const isValidationError = error instanceof ZodError || 
                                error.name === 'ZodError' || 
                                error.name === 'ValidationError' ||
                                error instanceof SyntaxError ||
                                error.name === 'SyntaxError' ||
                                (error.message && (
                                  error.message.toLowerCase().includes('json') ||
                                  error.message.toLowerCase().includes('schema validation failed') ||
                                  error.message.toLowerCase().includes('validation') ||
                                  error.message.toLowerCase().includes('parse')
                                ));

      if (isValidationError) {
        lastError = error.message;
        logger.warn(`❌ Tentative ${attempt}/${maxRetries} - Erreur de validation ou syntaxe: ${lastError}`);
        
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
      } else {
        // Erreurs critiques (timeout, réseau, etc.) : Fallback immédiat
        logger.error(`❌ Erreur de communication ou timeout avec le LLM : ${error.message || error}`);
        logger.warn("Activation immédiate de la stratégie de secours (Fallback) pour éviter de bloquer le pipeline.");
        await FirestoreService.updateJobStatus(jobId, { 
          current_message: "Échec de connexion/timeout LLM. Stratégie de secours activée.",
          strategy_source: 'fallback'
        });
        return { strategy: getFallbackStrategy(target, taskType), source: 'fallback' };
      }
    }
  }

  return { strategy: getFallbackStrategy(target, taskType), source: 'fallback' };
}
