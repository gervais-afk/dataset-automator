import { z, ZodError } from 'zod';
import pino from 'pino';
import { FirestoreService } from '../firebase/firestore';

const logger = pino({ transport: { target: 'pino-pretty' } });

// ======================
// EXACT ZOD SCHEMA
// ======================
export const CleaningStrategySchema = z.object({
  target: z.string().nullable().describe("Target column for the task or 'None' if clustering"),
  task_type: z.enum([
    "regression", "classification", "clustering", "timeseries",
    "anomaly_detection", "survival_analysis", "recommender_system",
    "causal_inference", "association_rules", "ab_testing",
    "semi_supervised", "optimization", "graph_analysis",
    "reinforcement_learning", "nlp", "computer_vision"
  ]).describe("ML task type"),
  steps: z.array(z.object({
    column: z.string().describe("Exact column name (or 'all')"),
    action: z.enum(["drop", "impute_mean", "impute_median", "scale", "winsorize", "k_means", "encode", "sanitize_phone", "normalize_cam_geo", "clean_fcfa", "parse_momo", "pca", "add_time_features", "formula"]).describe("Strict technical action to apply"),
    formula: z.string().optional().describe("Mathematical expression to evaluate, e.g. 'Weight / (Height ** 2)'"),
    reasoning: z.string().optional().describe("Business justification from Neo4j graph")
  })).describe("Ordered sequence of cleaning steps")
});

export type CleaningStrategy = z.infer<typeof CleaningStrategySchema>;

// ======================
// PROMPT TEMPLATE
// ======================
const STRATEGY_TEMPLATE = `{
  "target": "target_column_name",
  "task_type": "timeseries",
  "steps": [
    {
      "column": "column_name",
      "action": "winsorize",
      "reasoning": "Outliers handling"
    },
    {
      "column": "BMI",
      "action": "formula",
      "formula": "Weight / (Height ** 2)",
      "reasoning": "Body Mass Index calculation"
    }
  ]
}`;

function buildSystemPrompt(target: string): string {
  return `You are the Data Science Strategist Agent.
Analyze the dataset profile and generate a cleaning strategy.

You MUST reply EXCLUSIVELY with valid JSON STRICTLY conforming to this example schema:

${STRATEGY_TEMPLATE}

STRICT RULES:
- Do not add any extra keys (no "cleaning_strategy", "feature_engineering", etc.)
- Do not add any text before or after the JSON.
- Use only the allowed actions in the enum (drop, impute_mean, impute_median, scale, winsorize, k_means, encode, sanitize_phone, normalize_cam_geo, clean_fcfa, parse_momo, pca, add_time_features, formula).
- If you use the "formula" action, you MUST provide the "formula" field with the corresponding arithmetic formula from the knowledge base (e.g., "Weight / (Height ** 2)").
- STEP FILTERING (CRITICAL):
  * Only describe columns that ACTUALLY require an action (missing values > 0%, categorical to encode, extreme skewness > 1.5 to scale, or domain formulas to evaluate).
  * If a numeric column is already complete (0% missing) and balanced, do NOT include it in the steps list.
- TYPE COMPATIBILITY & FEATURE PROTECTION:
  * Do NOT drop key predictive columns (like 'Weight', 'Height', 'Age') due to drift. Drop unique IDs or mostly empty columns (> 50% NaNs), but preserve key domain variables.
  * NEVER apply 'scale', 'winsorize', 'impute_mean' or 'impute_median' on text or date columns.
  * NEVER apply a cleaning or drop step on the target column ('${target}'). It must be preserved intact for training.
- MISSING VALUES & CATEGORICALS:
  * If a numeric column has NaNs (> 0%), you must apply 'impute_median' or 'impute_mean' (or 'drop').
  * If a categorical column has NaNs, apply 'encode' or 'drop'.
- HALLUCINATION-FREE ANALYSIS:
  * Only use the real percentages of missing values and skewness described in the current run's dataset profile.
- Be precise and deterministic.
- EXTREMELY IMPORTANT: Keep the "reasoning" field for each step very short (maximum 4 words).
- IMPORTANT: Reply DIRECTLY with the valid JSON. Do NOT output a chain of thought.`;
}

function buildUserPrompt(context: string, lastError: string, missingColumns: string[]): string {
  // Truncate context to avoid prompts exceeding token budget
  const MAX_CONTEXT_CHARS = 1800; // ~450 tokens
  const trimmedContext = context.length > MAX_CONTEXT_CHARS
    ? context.substring(0, MAX_CONTEXT_CHARS) + '\n... [Context truncated to stay within model limits]'
    : context;

  let prompt = `Here is the dataset profile and available knowledge:
${trimmedContext}

⚠️ CRITICAL VALIDATION RULE:
The following columns contain missing values and MUST be imputed ('impute_mean', 'impute_median', 'encode') or dropped ('drop') in the "steps" list:
${missingColumns.length > 0 ? missingColumns.map(c => `- ${c}`).join('\n') : "(no columns with missing values)"}

Generate the cleaning strategy for this dataset complying with the JSON schema.`;

  if (lastError) {
    prompt += `\n\nWARNING - Your previous response was rejected by the validator with the following error:
[${lastError}]

IMPERATIVELY fix your JSON so it strictly matches the expected schema. Return ONLY valid JSON.`;
  }
  return prompt;
}

function extractJsonFromText(text: string): string {
  // Extracts content between first braces {} even with markdown formatting
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
        { column: 'all', action: 'impute_median', reasoning: 'Fallback: Median imputation for missing values' },
        { column: 'all', action: 'encode', reasoning: 'Fallback: Encode categorical variables' }
      ]
    };
  }
  
  if (normalizedTask === 'timeseries' || normalizedTask === 'time_series') {
    return {
      target: target || "Close",
      task_type: "timeseries",
      steps: [
        { column: 'all', action: 'impute_median', reasoning: 'Fallback: Median imputation for time series' },
        { column: 'all', action: 'scale', reasoning: 'Fallback: Scaling for variance stabilization' }
      ]
    };
  }
  
  // Default fallback for clustering or other tasks
  return {
    target: target || "unsupervised_segments",
    task_type: (normalizedTask as any) || "clustering",
    steps: [
      { column: 'all', action: 'impute_median', reasoning: 'Fallback: Median imputation' },
      { column: 'all', action: 'scale', reasoning: 'Fallback: Standard scaling for cluster distance' }
    ]
  };
}

// ======================
// MAIN FUNCTION WITH SELF-HEALING
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

  // Extract columns containing missing values from context
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
        logger.warn(`🔄 Self-healing attempt (Retry ${attempt}/${maxRetries}) in progress...`);
        await FirestoreService.updateJobStatus(jobId, { 
            current_message: `LLM error detected. Zod self-healing attempt (${attempt}/${maxRetries})...`,
            retries_count: attempt - 1,
            last_zod_error: lastError
        });
        
        // Exponential backoff (1s, 2s, 4s...)
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
          maxOutputTokens: 1000
        }
      });

      const rawText = response.text;

      // ─── DEGENERATION DETECTOR (strategyGenerator) ───────────────────────
      const degenerationPattern = /(\?{10,}|(.{3,})\2{15,})/s;
      const sqlJunkPattern = /^[a-z]{0,10}\?{5,}/i;
      if (degenerationPattern.test(rawText) || sqlJunkPattern.test(rawText.trim())) {
        logger.warn(`🧨 [DEGENERATION DETECTED in strategyGenerator] Corrupted response (length: ${rawText.length}). Switching directly to fallback.`);
        const fallback = getFallbackStrategy(target, taskType);
        return { strategy: fallback, source: 'fallback_degeneration' };
      }
      // ─────────────────────────────────────────────────────────────────────

      const jsonString = extractJsonFromText(rawText);
      const parsed = JSON.parse(jsonString);
      const strategy = CleaningStrategySchema.parse(parsed);

      // Business & ML validation for Self-Healing
      if (strategy.steps && strategy.target) {
        for (const step of strategy.steps) {
          if (step.column === strategy.target) {
            if (['scale', 'winsorize', 'impute_mean', 'impute_median'].includes(step.action)) {
              const validationErr = new Error(`Validation Error: Target column '${strategy.target}' must NEVER undergo cleaning action '${step.action}' as this alters its distribution.`);
              validationErr.name = 'ValidationError';
              throw validationErr;
            }
            if (step.action === 'drop') {
              const validationErr = new Error(`Validation Error: Target column '${strategy.target}' must NEVER be dropped. The model needs this column for training.`);
              validationErr.name = 'ValidationError';
              throw validationErr;
            }
          }
        }
      }

      // Mandatory missing values validation
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
              const validationErr = new Error(`Validation Error: Column '${col}' contains missing values but is not imputed or dropped in the cleaning strategy.`);
              validationErr.name = 'ValidationError';
              throw validationErr;
            }
          }
        }
      }

      if (attempt > 1) {
        logger.info(`✅ Strategy successfully self-healed by model on retry ${attempt}!`);
      }
      
      return { strategy, source: attempt === 1 ? 'human_validated' : 'self_healing' };

    } catch (error: any) {
      logger.error(error, `❌ Error caught on attempt ${attempt}`);
      
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
        logger.warn(`❌ Attempt ${attempt}/${maxRetries} - Validation or syntax error: ${lastError}`);
        
        if (attempt === maxRetries) {
          logger.error("Self-Healing failed after max retries. Activating Fallback.");
          await FirestoreService.updateJobStatus(jobId, { 
            current_message: "Self-Healing failed. Fallback strategy activated.",
            strategy_source: 'fallback'
          });
          return { strategy: getFallbackStrategy(target, taskType), source: 'fallback' };
        }
        
        continue;
      } else {
        // Critical errors: immediate fallback
        logger.error(`❌ Communication error or timeout with LLM: ${error.message || error}`);
        logger.warn("Immediate fallback activation to prevent pipeline blocking.");
        await FirestoreService.updateJobStatus(jobId, { 
          current_message: "LLM connection failure/timeout. Fallback strategy activated.",
          strategy_source: 'fallback'
        });
        return { strategy: getFallbackStrategy(target, taskType), source: 'fallback' };
      }
    }
  }

  return { strategy: getFallbackStrategy(target, taskType), source: 'fallback' };
}
