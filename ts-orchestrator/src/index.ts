console.log("=== SCRIPT STARTED ===");
import './pre-start';
import { genkit, z } from 'genkit';
// Import openAI plugin removed since we use a custom model
import { execSync, spawn } from 'child_process';
import { writeFileSync, unlinkSync, readdirSync, existsSync } from 'fs';
import * as path from 'path';
import axios from 'axios';
import pino from 'pino';
import * as readline from 'readline';
const { Client: MCPClient } = require('@modelcontextprotocol/sdk/client/index.js');
const { StdioClientTransport: MCPTransport } = require('@modelcontextprotocol/sdk/client/stdio.js');
import { StateManager, PipelineState } from './stateManager';
import { RagRetriever } from './agents/ragRetriever';
import { KnowledgeGraphClient } from './rag/knowledge-graph-client';
import { ChartInterpreter } from './vision/chart-interpreter';
import { Guardrail } from './guardrails';
import { FirestoreService } from './firebase/firestore';
import { generateStrategyWithSelfHealing } from './agents/strategyGenerator';
import { getActiveModelName } from './llm-utils';
import { getGraphRAGReasoner } from './tools/graphRAGReasoner';
import { getEntityReconciler } from './tools/entityReconciler';
import { getREPLInterpreter } from './tools/replInterpreter';
import { PiiSanitizer } from './utils/piiSanitizer';

function buildInterpretationPrompt(
  domain: string,
  taskType: string,
  metrics: any,
  visionResult: any,
  interpretationRules: any[],
  businessCosts: any = null
): string {
  let rulesText = "";
  if (interpretationRules && interpretationRules.length > 0) {
    rulesText = interpretationRules.map(r => 
      `- Rule [${r.name}]: ${r.description}\n  * Guidelines: ${r.guideline}\n  * Business Impact: ${r.business_impact}`
    ).join("\n");
  } else {
    rulesText = "No specific Neo4j interpretation rules available. Use state-of-the-art standards.";
  }

  let visionText = "No visual anomaly detected.";
  if (visionResult) {
    const issues = visionResult.additionalIssues || [];
    const patterns = visionResult.visualPatterns || [];
    visionText = `Rendered chart status: ${visionResult.confirmsMetrics ? 'Consistent with metrics' : 'Anomalies detected'}\n` +
                 `Detected patterns: ${patterns.join(', ')}\n` +
                 `Raised alerts: ${issues.join(', ')}`;
  }

  let businessCostsText = "No reference business financial costs provided.";
  if (businessCosts) {
    businessCostsText = `Business financial costs calculated for this project:
    - False Positive (FP) / False alarm: - ${businessCosts.cost_FP} ${businessCosts.currency}
    - False Negative (FN) / Missed default or anomaly: - ${businessCosts.cost_FN} ${businessCosts.currency}
    - True Positive (TP) / Correct decision: + ${businessCosts.gain_TP} ${businessCosts.currency}
    
    ROI Rule: Calculate and explicitly comment on the estimated financial impact by applying these costs to actual model errors (e.g., FP and FN from confusion matrix if available, or test set error rate). Translate technical metrics into net financial gains or avoided losses.`;
  }
  let fairnessText = "";
  if (metrics && metrics.fairness) {
    const f = metrics.fairness;
    fairnessText = `\n--- FAIRNESS EVALUATION (FAIRNESS GUARDRAIL) ---
    Identified sensitive attribute: "${f.sensitive_attribute}"
    Calculated Disparate Impact Ratio: ${f.disparate_impact_ratio.toFixed(3)}
    Selection rates by group: ${JSON.stringify(f.selection_rates)}
    
    Fairness Guideline: You must comment on this disparate impact ratio in your report in a dedicated ethics & fairness paragraph. A value outside [0.8, 1.25] indicates potential model bias.`;
  }

  return `You are a Senior Data Scientist specializing in AI model auditing.
Analyze the model evaluation results to write the explainability and final interpretation report for the project.

--- CONTEXT ---
Business Domain: ${domain}
Task Type: ${taskType}

--- FINANCIAL IMPACT AND BUSINESS COSTS ---
${businessCostsText}
${fairnessText}

--- BUSINESS INTERPRETATION GUIDELINES (Extracted from Neo4j) ---
${rulesText}

--- EVALUATION RESULTS ---
Real Metrics: ${JSON.stringify(metrics, null, 0)}
Evaluation Chart Analysis:
${visionText}

--- REPORTING INSTRUCTIONS ---
1. Write a qualitative interpretation report formatted in Markdown in English (approx. 2-3 paragraphs).
2. Do not comment on technical code. Explain what these numbers and charts mean concretely for the business, decision-making, and net financial impact.
3. Be direct, factual, and rigorous. Strictly apply Neo4j guidelines if metrics cross critical thresholds (such as recall imbalance or overfitting).
4. Remain professional. Do not add conversational introductions or conclusions, start directly with the report content.
`;
}

// Helper pour récupérer la saisie console de l'utilisateur
function askQuestion(query: string): Promise<string> {
  const rl = readline.createInterface({
    input: process.stdin,
    output: process.stdout,
  });
  return new Promise(resolve => rl.question(query, ans => {
    rl.close();
    resolve(ans);
  }));
}

// Registres globaux pour suivre et nettoyer les processus enfants / transports MCP
const spawnedProcesses: any[] = [];
const activeTransports: any[] = [];

function cleanupActiveProcesses() {
  console.log("\n🧹 [Cleanup] Clean shutdown of all Python processes and MCP connections...");
  
  for (const proc of spawnedProcesses) {
    try {
      proc.kill('SIGKILL');
    } catch (e) {}
  }
  
  for (const transport of activeTransports) {
    try {
      transport.close();
    } catch (e) {}
  }
}

// Enregistrement des hooks de fermeture de Node.js
process.on('exit', cleanupActiveProcesses);
process.on('SIGINT', () => {
  cleanupActiveProcesses();
  process.exit(0);
});
process.on('SIGTERM', () => {
  cleanupActiveProcesses();
  process.exit(0);
});

// Helper to execute Python asynchronously without blocking the Event Loop
async function runPythonAsync(command: string, args: string[], cwd: string, jobId?: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const pyProcess = spawn(command, args, { cwd });
    spawnedProcesses.push(pyProcess);
    let stdoutData = '';
    let stderrData = '';

    let monitorInterval: NodeJS.Timeout | null = null;
    const HEARTBEAT_TIMEOUT_MS = 60 * 1000; // 60 seconds

    if (jobId) {
      monitorInterval = setInterval(async () => {
        try {
          const job = await FirestoreService.getJob(jobId);
          if (job && job.last_heartbeat) {
            const lastHbTime = new Date(job.last_heartbeat).getTime();
            const now = Date.now();
            if (now - lastHbTime > HEARTBEAT_TIMEOUT_MS) {
              logger.error(`❌ Worker Python (Job ${jobId}) is no longer responding (Timeout > 60s). Forcing shutdown (SIGKILL).`);
              
              pyProcess.kill('SIGKILL');
              
              await FirestoreService.updateJobStatus(jobId, {
                status: 'failed',
                current_message: 'Error: Python execution crashed silently (OOM/Deadlock). Heartbeat timeout reached.'
              });
              
              if (monitorInterval) clearInterval(monitorInterval);
              reject(new Error(`Python Worker Heartbeat Timeout (>${HEARTBEAT_TIMEOUT_MS}ms). Process killed.`));
            }
          }
        } catch (e) {
          logger.warn(`Error during heartbeat monitoring: ${e}`);
        }
      }, 15000); // Check every 15s
    }

    pyProcess.stdout.on('data', (data) => {
      stdoutData += data.toString();
    });

    pyProcess.stderr.on('data', (data) => {
      stderrData += data.toString();
    });

    pyProcess.on('close', (code) => {
      const idx = spawnedProcesses.indexOf(pyProcess);
      if (idx !== -1) spawnedProcesses.splice(idx, 1);
      if (monitorInterval) clearInterval(monitorInterval);
      if (code === 0) resolve(stdoutData);
      else reject(new Error(`Exit code ${code}\nStderr: ${stderrData}\nStdout: ${stdoutData}`));
    });
  });
}

const logger = pino({
  level: 'debug',
  transport: {
    target: 'pino-pretty'
  }
});

const ai = genkit({});

// Instanciation des outils SOVEREIGN.BI Agentic
export const graphRAGReasoner = getGraphRAGReasoner(ai);
export const entityReconciler = getEntityReconciler(ai);
export const replInterpreter = getREPLInterpreter(ai);

// Definition d'un modele custom pour LM Studio qui bypasse les bugs du plugin openai
// Cela permet d'avoir 100% de fiabilite avec Axios TOUT EN affichant les traces dans l'UI Genkit !
const localGemmaModel = ai.defineModel(
  {
    name: 'lmstudio/gemma-4-12b',
  },
  async (request) => {
    logger.info("🤖 AI Model invoked by Genkit");
    
    // Convert all Genkit messages into standard chat completion messages
    const chatMessages = (request.messages || []).map(msg => {
      let text = "";
      if (Array.isArray(msg.content) && msg.content.length > 0) {
        text = msg.content[0]?.text || "";
      }
      // Unicode normalization to strip out all accents (avoids Windows UTF-8 double encoding/corruption)
      const cleanText = text.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      return {
        role: msg.role === 'model' ? 'assistant' : msg.role,
        content: cleanText
      };
    });

    const provider = process.env.LLM_PROVIDER || 'local';
    const apiKey = process.env.OPENROUTER_API_KEY || '';
    const primaryModel = process.env.PRIMARY_MODEL || 'google/gemini-3.5-flash';
    const fallbackModel = process.env.FALLBACK_MODEL || 'google/gemma-4-26b-a4b-it';

    if (provider === 'openrouter') {
      logger.info(`📡 [OpenRouter] Sending request to OpenRouter... Messages count: ${chatMessages.length}.`);
      let modelToUse = primaryModel;
      let attempt = 1;
      let response;
      
      try {
        logger.info(`📡 [OpenRouter] Attempt 1: calling Gemini 3.5 Flash (${primaryModel})...`);
        response = await axios.post('https://openrouter.ai/api/v1/chat/completions', {
          model: primaryModel,
          messages: chatMessages,
          temperature: request.config?.temperature || 0.2,
          max_tokens: request.config?.maxOutputTokens || 1024,
        }, {
          timeout: 180000, // 3 minutes timeout for OpenRouter
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
            'HTTP-Referer': 'http://localhost:3000',
            'X-Title': 'Dataset Automator'
          }
        });
      } catch (err: any) {
        const errMsg = err.response ? `HTTP ${err.response.status} - ${JSON.stringify(err.response.data)}` : (err.message || err);
        logger.warn(`⚠️ [OpenRouter] Primary model Gemini failed: ${errMsg}`);
        logger.warn(`🔄 [OpenRouter] Attempt 2: falling back to Gemma 4 (${fallbackModel})...`);
        
        try {
          response = await axios.post('https://openrouter.ai/api/v1/chat/completions', {
            model: fallbackModel,
            messages: chatMessages,
            temperature: request.config?.temperature || 0.2,
            max_tokens: request.config?.maxOutputTokens || 1024,
          }, {
            timeout: 180000,
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${apiKey}`,
              'HTTP-Referer': 'http://localhost:3000',
              'X-Title': 'Dataset Automator'
            }
          });
          modelToUse = fallbackModel;
        } catch (fallbackErr: any) {
          const fallbackErrMsg = fallbackErr.response ? `HTTP ${fallbackErr.response.status} - ${JSON.stringify(fallbackErr.response.data)}` : (fallbackErr.message || fallbackErr);
          logger.error(`❌ [OpenRouter] Fallback model Gemma 4 also failed: ${fallbackErrMsg}`);
          throw fallbackErr;
        }
      }

      logger.info(`✅ [OpenRouter] Response received using model: ${modelToUse}`);
      const replyContent = response.data.choices[0].message.content || "";
      return {
        message: {
          role: 'model',
          content: [{ text: replyContent }]
        }
      };
    } else {
      const activeModel = await getActiveModelName();
      logger.info(`📡 Sending request to LM Studio (modèle: ${activeModel})... Nombre de messages : ${chatMessages.length}.`);
      if (chatMessages.length > 0) {
        const lastMsg = chatMessages[chatMessages.length - 1];
        if (lastMsg && lastMsg.content) {
          logger.debug({ lastMessageContent: lastMsg.content.substring(0, 500) + "..." }, "Last message sent");
        }
      }

      try {
        const response = await axios.post('http://127.0.0.1:1234/v1/chat/completions', {
          model: activeModel,
          messages: chatMessages,
          temperature: request.config?.temperature || 0.2,
          max_tokens: request.config?.maxOutputTokens || 1024,
          repetition_penalty: 1.1
        }, {
          timeout: 2700000,
          headers: { 'Content-Type': 'application/json' }
        });

        logger.info("✅ Response received from LM Studio!");
        const replyContent = response.data.choices[0].message.content || "";
        return {
          message: {
            role: 'model',
            content: [{ text: replyContent }]
          }
        };
      } catch (err: any) {
        const errMsg = err.response ? `HTTP ${err.response.status} - ${JSON.stringify(err.response.data)}` : (err.message || err);
        logger.error(`❌ Error during LM Studio call: ${errMsg}`);
        throw err;
      }
    }
  }
);

function formatCompactProfile(profile: any): string {
  if (!profile) return "No profile available.";
  let result = `Dataset Summary:
- Total Rows: ${profile.total_rows}
- Total Columns: ${profile.total_columns}
- Suggested Target: ${profile.suggested_target || "None (Clustering)"}
- Suggested Task: ${profile.suggested_task_type || "clustering"}
- Domain: ${profile.domaine || "general"}

Features Profile:\n`;

  if (profile.features && Array.isArray(profile.features)) {
    for (const feat of profile.features) {
      const missingStr = feat.missing_percentage > 0 ? `${feat.missing_percentage.toFixed(2)}% missing` : "0% missing";
      if (feat.type === 'categorical') {
        result += `- ${feat.name} (categorical): ${missingStr}, cardinality: ${feat.cardinality || 0}\n`;
      } else {
        const skewStr = feat.skewness !== undefined && feat.skewness !== null ? `, skew: ${feat.skewness.toFixed(2)}` : "";
        result += `- ${feat.name} (numeric): ${missingStr}${skewStr}\n`;
      }
    }
  }
  return result;
}

// Initial State
const state = new StateManager<PipelineState>({
  currentPhase: 'profiling'
});

// Define the main orchestrator flow to track everything in Genkit Developer UI
// Define the main orchestrator flow to track everything in Genkit Developer UI
const orchestratorFlow = ai.defineFlow(
  {
    name: 'dataOrchestratorFlow',
    inputSchema: z.object({
      csvPath: z.string(),
      target: z.string().optional(),
      taskType: z.string().optional()
    }),
  },
  async (input) => {
    console.log("=== ORCHESTRATOR FLOW CALLED ===");
    logger.info("============================================");
    logger.info("🧠 Starting Orchestrator Brain");
    logger.info("============================================");

    // 1. Démarrer et connecter le client MCP Python
    logger.info("🔌 Connecting to Python MCP Server (Workers)...");
    const pyTransport = new MCPTransport({
      command: '.venv/Scripts/python.exe',
      args: ['-u', 'src/server.py'],
      cwd: 'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
      env: { PYTHONIOENCODING: 'utf-8' },
      stderr: 'inherit'
    });
    activeTransports.push(pyTransport);

    const pyClient = new MCPClient({
      name: 'ts-orchestrator-python-client',
      version: '1.0.0'
    }, {
      capabilities: {},
      connectionTimeout: 300000
    });

    try {
      await pyClient.connect(pyTransport);
      logger.info("✅ Successfully connected to Python MCP server!");
      logger.info("📈 MLflow tracking available at: http://127.0.0.1:5000");

      // 1. Profiling via Python Muscles
      logger.info("\n[PHASE 1] Calling Python Workers to Profile CSV...");
      const csvPath = path.resolve(process.cwd(), input.csvPath);
      const safePath = csvPath.replace(/\\/g, '/');
      const nomBase = path.basename(csvPath, '.csv');
      let finalNbPath: string | null = null;
      let pythonOutput = '';
      try {
        const response = await pyClient.callTool({
          name: 'profile_dataset',
          arguments: { file_path: safePath }
        }, undefined, { timeout: 600000 });
        pythonOutput = (response.content[0] as { type: 'text'; text: string }).text;
      } catch (err: any) {
        logger.error("Error during Python call (Profiling)", err);
        return { status: "failed", reason: "Profiling failed during Python execution." };
      }

      if (!pythonOutput || pythonOutput.trim() === '') {
        logger.error("❌ Error: Python profiler returned no result.");
        return { status: "failed", reason: "Python profiling output was empty." };
      }

      const profileData = JSON.parse(pythonOutput.trim());
      if (profileData.error) {
        logger.error(`❌ Dataset profiling failed: ${profileData.error}`);
        return { status: "failed", reason: profileData.error };
      }

      state.update({
        currentPhase: 'profiling',
        profile: profileData
      });
      logger.info(`[PHASE 1] Dataset Profiled: ${profileData.total_rows} rows, ${profileData.total_columns} columns.`);

      // Auto-detection or user specification of task type and target column
      let resolvedTarget = input.target || profileData.suggested_target || "";
      let resolvedTaskType = input.taskType || profileData.suggested_task_type || "regression";
      const inferredDomain = profileData.domaine || "general";

      logger.info(`\n🔍 [AUTO-DETECTION] Detected business domain: "${inferredDomain}"`);
      logger.info(`🔍 [AUTO-DETECTION] Suggested task type: "${resolvedTaskType}"`);
      logger.info(`🔍 [AUTO-DETECTION] Suggested target column: "${resolvedTarget || "None (Clustering)"}"\n`);

      const confirmSelection = await askQuestion("⚠️ Confirm domain detection and task type? [Y/N] (Y by default): ");
      if (confirmSelection.trim().toUpperCase() === 'N') {
        logger.info("\n🛠️ Mode manuel activé. Veuillez spécifier les paramètres :");
        const customTaskType = await askQuestion("👉 Enter desired task type (e.g. classification, regression, timeseries, anomaly_detection, survival_analysis, recommender_system, causal_inference, association_rules, ab_testing, semi_supervised, optimization, graph_analysis, reinforcement_learning, nlp, computer_vision): ");
        if (customTaskType.trim()) {
          resolvedTaskType = customTaskType.trim().toLowerCase();
        }
        const customTarget = await askQuestion("👉 Enter target column name (leave empty for clustering): ");
        resolvedTarget = customTarget.trim();
        logger.info(`🎯 Paramètres mis à jour par l'utilisateur -> Target : "${resolvedTarget || "Aucune"}" | Tâche : "${resolvedTaskType}"`);
      } else {
        logger.info("✅ Automatic detection confirmed.");
      }

      // 2.5 Calculer ou charger les coûts métiers
      let businessCosts: any = null;
      let costSource = "aucune";
      
      // Recherche d'une colonne monétaire numérique dans le profil
      if (profileData.features && Array.isArray(profileData.features)) {
        const monetaryKeywords = ["montant", "fcfa", "amount", "prix", "price", "salary"];
        const monetaryFeat = profileData.features.find((f: any) => 
          f.type === 'numeric' && 
          monetaryKeywords.some(keyword => f.name.toLowerCase().includes(keyword)) &&
          typeof f.mean === 'number' && f.mean > 0
        );
        
        if (monetaryFeat) {
          const meanVal = monetaryFeat.mean;
          businessCosts = {
            cost_FP: Math.round(0.1 * meanVal),
            cost_FN: Math.round(1.0 * meanVal),
            gain_TP: Math.round(0.2 * meanVal),
            currency: "FCFA",
            detected_column: monetaryFeat.name
          };
          costSource = `dataset statistics (detected monetary column: "${monetaryFeat.name}" with mean ${meanVal.toFixed(0)} FCFA)`;
        }
      }
      
      // Fallback sur Neo4j
      if (!businessCosts) {
        try {
          const costClient = new KnowledgeGraphClient();
          const dbCosts = await costClient.queryBusinessCosts(inferredDomain);
          await costClient.close();
          if (dbCosts) {
            businessCosts = dbCosts;
            costSource = `Neo4j reference rules (domain: "${inferredDomain}")`;
          }
        } catch (e: any) {
          logger.warn(`⚠️ Unable to load business costs from Neo4j: ${e.message}`);
        }
      }
      
      if (businessCosts) {
        logger.info(`💰 [BUSINESS COSTS] Business costs initialized via ${costSource} :`);
        logger.info(`   - Faux Positif (FP) : ${businessCosts.cost_FP} ${businessCosts.currency}`);
        logger.info(`   - Faux Négatif (FN) : ${businessCosts.cost_FN} ${businessCosts.currency}`);
        logger.info(`   - Vrai Positif (TP) : ${businessCosts.gain_TP} ${businessCosts.currency}`);
      } else {
        logger.warn(`⚠️ [BUSINESS COSTS] No business cost defined.`);
      }

      let failedRunId: string | null = null;

      // 2.6 Interrogation RAG pour les Échecs passés (Self-Healing) et Contrats de Données
      let failuresPromptText = "";
      let dataContractAssertionsCode = "";
      let fairnessThresholdText = "";
      let fairnessThresholds: any = null;

      try {
        const ragClientEx = new KnowledgeGraphClient();
        
        // 2.6.1 Récupérer les échecs résolus
        const pastFailures = await ragClientEx.queryPastRunFailures(inferredDomain, resolvedTaskType);
        if (pastFailures && pastFailures.length > 0) {
          failuresPromptText = "\n⚠️ RECALL OF PREVIOUS FAILURES AND RESOLUTIONS IN THIS DOMAIN:\n" +
            pastFailures.map(f => 
              `- A previous execution on dataset "${f.dataset}" failed with alert: "${f.errorType}" (détail: "${f.errorDetail}").\n` +
              `  * This error was successfully RESOLVED by applying the following strategy:\n` +
              `    ${f.resolvedStrategy}\n` +
              `    Associated Champion Model: ${f.resolvedModel}`
            ).join("\n") +
            "\n👉 Guideline: Avoid repeating the same errors. Adjust your cleaning strategy/hyperparameters to directly apply the resolution documented above.";
          logger.info(`💡 [SELF-HEALING RAG] ${pastFailures.length} échec(s) résolu(s) trouvé(s) et injecté(s) dans le contexte.`);
        }

        // 2.6.2 Récupérer les Data Contracts pour chaque colonne et construire le schéma Pandera
        let hasContracts = false;
        let contractColumnsCode = "";
        if (profileData.features && Array.isArray(profileData.features)) {
          for (const feat of profileData.features) {
            const constraints = await ragClientEx.queryConstraintsForColumn(feat.name);
            if (constraints && constraints.length > 0) {
              hasContracts = true;
              for (const c of constraints) {
                if (c.type === 'regex') {
                  contractColumnsCode += `        "${feat.name}": Column(str, checks=Check.str_matches(r"${c.value}"), nullable=True),\n`;
                } else if (c.type === 'min_value') {
                  contractColumnsCode += `        "${feat.name}": Column(float, checks=Check.greater_than_or_equal_to(${c.value}), nullable=True),\n`;
                }
              }
            }
          }
        }

        if (hasContracts) {
          dataContractAssertionsCode = `
# ── Data Contract Validation with Pandera (Lazy Evaluation)
import pandera as pa
from pandera.pandas import DataFrameSchema, Column, Check

schema = DataFrameSchema(
    columns={
${contractColumnsCode}    }
)

try:
    schema.validate(df, lazy=True)
    print("✅ Pandera validation successful: Data schema strictly respected.")
except pa.errors.SchemaErrors as err:
    print("❌ Pandera data contract validation failed.")
    # Affichage des failure_cases
    import traceback
    display(err.failure_cases)
    # Saving non-compliant rows to Quarantine
    quarantine_path = INTERIM_DIR / "quarantine_errors.csv"
    err.failure_cases.to_csv(quarantine_path, index=False)
    print(f"⚠️ Error quarantine file generated at: {quarantine_path}")
`;
        }

        // 2.6.3 Récupérer les seuils d'équité
        fairnessThresholds = await ragClientEx.queryFairnessThreshold(inferredDomain);
        if (fairnessThresholds) {
          fairnessThresholdText = `Seuils d'équité de référence (Neo4j) :
      - Impact Disparate attendu : entre ${fairnessThresholds.min_disparate_impact} et ${fairnessThresholds.max_disparate_impact} (sur l'attribut sensible).`;
        }

        await ragClientEx.close();
      } catch (e: any) {
        logger.warn(`⚠️ Impossible d'initialiser les connaissances avancées (Neo4j): ${e.message}`);
      }

      if (!dataContractAssertionsCode) {
        dataContractAssertionsCode = "# No semantic data contract specified for this dataset.";
      }

      // 🔥 INITIALISATION FIREBASE JOB
      const jobId = await FirestoreService.createJob(nomBase);
      logger.info(`🔗 Tracking UI démarré avec le Job ID: ${jobId}`);

      // 1.5 Adversarial Validation
      logger.info("\n[PHASE 1.5] Adversarial Validation (Temporal Drift Detection)...");
      let adversarialContext = "";
      try {
        const advOutput = await pyClient.callTool({
          name: 'run_adversarial_validation',
          arguments: {
            file_path: safePath,
            target: resolvedTarget,
            task: resolvedTaskType,
            job_id: jobId
          }
        }, undefined, { timeout: 600000 });
        const advResult = JSON.parse((advOutput.content[0] as { type: 'text'; text: string }).text.trim());
        if (advResult.drift_detected) {
          logger.warn(`⚠️ Temporal drift detected! (AUC: ${advResult.auc.toFixed(2)})`);
          adversarialContext = `⚠️ ADVERSARIAL VALIDATION ALERT: Data drift detected (Adversarial Validator AUC: ${advResult.auc.toFixed(2)}). The following features are most suspected of shifting over time: ${JSON.stringify(advResult.suspicious_features)}. Recommendation: ${advResult.recommendation}`;
        } else {
          logger.info("✅ No temporal drift detected by Adversarial Validator.");
        }
      } catch (e: any) {
         logger.warn(`⚠️ Adversarial Validator error (Ignored): ${e.message}`);
      }

      // 2. Strategizing (True Graph RAG Retrieval via Neo4j)
      logger.info("\n[PHASE 2] Le Stratège interroge la Base de Connaissances Neo4j (Graph RAG)...");
      
      const ragClient = new KnowledgeGraphClient();
      let knowledge = { relevantConcepts: [] as any[], decisionRules: [] as any[], procedures: [] as any[] };
      try {
        knowledge = await ragClient.queryForStrategy('Data cleaning', profileData);
      } catch (e: any) {
        logger.warn(`⚠️ Neo4j inaccessible, utilisation de connaissances vides : ${e.message}`);
      }
      
      // Récupérer les mappings de colonnes sémantiques (Feature Store)
      const columnMappings: any[] = [];
      if (profileData.features && Array.isArray(profileData.features)) {
        for (const feat of profileData.features) {
          try {
            const mapping = await ragClient.queryColumnMappings(feat.name);
            if (mapping) {
              columnMappings.push({ column: feat.name, ...mapping });
            }
          } catch (e) {
            // Ignorer silencieusement si la table n'est pas connectée
          }
        }
      }

      // Récupérer les runs similaires (mémoire épisodique) — format compact
      let pastRunsContext = "";
      try {
        const topRunsSummary = await ragClient.getTopSimilarRuns(inferredDomain, resolvedTaskType);
        if (topRunsSummary) {
          // Pas de question à l'utilisateur : toujours injecté, mais compact (~150 tokens max)
          pastRunsContext = topRunsSummary;
          logger.info(`📜 Mémoire épisodique compact injectée (${topRunsSummary.length} chars).`);
        }
      } catch (e) {
        // Ignorer si Neo4j non disponible
      }

      let columnMappingsContext = "";
      if (columnMappings.length > 0) {
        columnMappingsContext = `\n🏷️ SEMANTIC COLUMN MAPPINGS (Feature Store):
Some columns already have recommended concepts and actions in the graph:
${columnMappings.slice(0, 3).map(cm => `- Column "${cm.column}" -> Concept "${cm.concept}" (${cm.definition}). Recommended action: "${cm.action}"`).join('\n')}\n`;
      }

      // L'agent définit sa stratégie basée sur ces connaissances via LM Studio
      const activeModelName = await getActiveModelName();
      logger.info(`🤖 Génération de la stratégie finale via LM Studio (${activeModelName})...`);
      
      // Contexte complet à passer à l'agent
      const context = `
Voici le profil du dataset :
${formatCompactProfile(state.get().profile)}

${adversarialContext}
${pastRunsContext}
${columnMappingsContext}
${failuresPromptText}

📚 RELEVANT KNOWLEDGE (From Knowledge Graph):
${knowledge.relevantConcepts.slice(0, 5).map(c => `- **${c.name}** (${c.category}): ${c.definition}${c.formula ? ` [FORMULE OKF DISPONIBLE : "${c.formula}" -> colonne cible : "${c.target_column}"]` : ''}`).join('\n')}

🎯 DECISION RULES (Apply these expert heuristics):
${knowledge.decisionRules.slice(0, 2).map((d: any) => `
**${d.question}**
${d.branches.slice(0, 2).map((b: any, i: number) => `  ${i + 1}. IF ${b.condition}\n     THEN ${b.action}\n     (Confidence: ${(b.confidence * 100).toFixed(0)}%)`).join('\n')}`).join('\n')}

📋 PROCEDURES AVAILABLE:
${knowledge.procedures.slice(0, 1).map(p => `- ${p.title}`).join('\n')}

Tu dois concevoir une stratégie de nettoyage pour la tâche suivante : **${resolvedTaskType.toUpperCase()}** avec la colonne cible (target) : **${resolvedTarget || "None (Clustering)"}**.
`;

      // Appel à la boucle de Self-Healing
      const { strategy, source } = await generateStrategyWithSelfHealing(
        ai,
        localGemmaModel,
        context,
        resolvedTarget,
        resolvedTaskType,
        jobId,
        3, // max retries
        [graphRAGReasoner, replInterpreter] // outils SOVEREIGN.BI disponibles pour l'agent
      );

      logger.info(`Réponse de LM Studio validée ! Source de la stratégie : ${source}`);
      
      // On notifie Firestore que l'on passe à l'étape suivante
      await FirestoreService.updateJobStatus(jobId, { 
        status: 'cleaning',
        current_message: 'Stratégie générée, en attente de validation humaine ou exécution'
      });

      state.update({
        currentPhase: 'strategizing',
        strategy: {
          ...strategy,
          target: strategy.target || ""
        }
      });

      logger.info("✅ Stratégie définie par l'Agent avec RAG.");
      console.dir(strategy, { depth: null, colors: true });

      // =========================================================================
      // GOUVERNANCE HUMAN-IN-THE-LOOP (Niveau 2 : Supervision)
      // =========================================================================
      logger.info("\n[GOUVERNANCE] Lecture des règles d'Architecture Agentique (Neo4j)...");
      const ragClientForGov = new KnowledgeGraphClient();
      const govRules = await ragClientForGov.queryForGovernanceRules();
      await ragClientForGov.close();
      
      if (govRules) {
        logger.info(`Question: ${govRules.question}`);
        logger.info(`Règle détectée : L'exécution physique (Phase 3) modifie le système.`);
        logger.info(`-> Application de la Règle issue du Graphe : "Niveau 2 : Supervision avec fenêtre de révision humaine (validation avant de lancer un pipeline)".\n`);
        
        const answer = await askQuestion("⚠️ Action requise : Acceptez-vous cette stratégie de nettoyage ? [O/N] : ");
        if (answer.trim().toUpperCase() !== 'O') {
            logger.error("❌ Action rejetée par l'humain. Le pipeline est interrompu par la gouvernance.");
            return { status: "rejected", reason: "Human loop denied execution." };
        }
        logger.info("✅ Stratégie validée par l'humain. Levée de la pause, poursuite du pipeline.");
      } else {
        logger.warn("⚠️ Arbre de gouvernance non trouvé dans Neo4j. Contournement (fallback).");
      }

      // 3. Executing Strategy physically
      logger.info("\n[PHASE 3] Exécution de la stratégie via les Muscles Python...");
      logger.info("Application de la stratégie de nettoyage sur le fichier CSV...");
      
      await FirestoreService.updateJobStatus(jobId, { 
        current_message: 'Exécution physique (Python) de la stratégie de nettoyage'
      });
      
      let mcpReturn;
      try {
        await FirestoreService.updateJobStatus(jobId, { status: 'cleaning', progress_percent: 10, current_message: 'Nettoyage des données en cours...' });

        const pyOutput = await pyClient.callTool({
          name: 'apply_cleaning_strategy',
          arguments: {
            file_path: csvPath.replace(/\\/g, '/'),
            cleaning_schema: JSON.stringify(strategy),
            job_id: jobId
          }
        }, undefined, { timeout: 600000 });
        
        mcpReturn = JSON.parse((pyOutput.content[0] as { type: 'text'; text: string }).text.trim());
        if (mcpReturn.error) {
          logger.error(`❌ Échec du nettoyage des données : ${mcpReturn.error}`);
          return { status: "failed", reason: mcpReturn.error };
        }
        logger.info("Résultat du nettoyage :");
        console.log(mcpReturn);
      } catch (err: any) {
        logger.error("Erreur d'exécution Python (Nettoyage)", err);
        return { status: "failed", reason: "Data cleaning failed during Python execution." };
      }
      
      // 3.5 Evaluating the strategy by running a quick model
      logger.info("\n[PHASE 3.5] Évaluation du modèle (Génération des métriques Structurées JSON et Artifacts PNG)...");
      
      await FirestoreService.updateJobStatus(jobId, { status: 'evaluating', progress_percent: 30, current_message: 'Calcul des métriques (Silhouette, F1-Score)...' });

      let evalReturn;
      let evaluatedModelName = "RandomForest";
      let isValid = false;
      
      // Récupérer les seuils de performance depuis Neo4j
      let perfThresholds: any = null;
      try {
        const ragClientEx = new KnowledgeGraphClient();
        perfThresholds = await ragClientEx.queryPerformanceThreshold(inferredDomain);
        await ragClientEx.close();
        if (perfThresholds) {
          logger.info(`🎯 Seuils de performance chargés depuis Neo4j (${inferredDomain}) : min_f1=${perfThresholds.min_f1}, min_r2=${perfThresholds.min_r2}, max_overfitting_gap=${perfThresholds.max_overfitting_gap}`);
        }
      } catch (e: any) {
        logger.warn(`⚠️ Impossible de charger les seuils de performance de Neo4j: ${e.message}`);
      }

      try {
        const cleanedCsvPath = mcpReturn.cleanedDataPath
          ? path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", mcpReturn.cleanedDataPath)
          : "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/data_processed/cleaned.csv";
          
        const target = resolvedTarget;
        const taskType = resolvedTaskType;
        
        // 1. Évaluation initiale avec RandomForest
        const evalOutput = await pyClient.callTool({
          name: 'evaluate_model',
          arguments: {
            file_path: cleanedCsvPath.replace(/\\/g, '/'),
            target: target,
            task: taskType,
            model_name: 'RandomForest',
            job_id: jobId
          }
        }, undefined, { timeout: 1200000 });
        
        evalReturn = JSON.parse((evalOutput.content[0] as { type: 'text'; text: string }).text.trim());
        if (evalReturn.error) {
          logger.error(`❌ Échec de l'évaluation RandomForest : ${evalReturn.error}`);
          return { status: "failed", reason: evalReturn.error };
        }
        logger.info("Résultat de l'Évaluation (RandomForest) :");
        console.log(evalReturn);
        
        // 2. Vérification des Guardrails pour RandomForest
        let finalEvaluation = evalReturn.evaluation;
        isValid = Guardrail.validateEvaluation(finalEvaluation, perfThresholds || undefined, fairnessThresholds || undefined);
        
        // 3. Alternative de remédiation TabFM si RandomForest échoue (hors clustering)
        if (!isValid && taskType !== "clustering") {
          logger.warn("⚠️ Guardrail Mathématique échoué pour RandomForest. Évaluation de l'alternative de remédiation TabFM...");
          await FirestoreService.updateJobStatus(jobId, { 
            status: 'evaluating', 
            current_message: 'Modèle classique non valide. Évaluation de TabFM...' 
          });
          
          try {
            const tabfmOutput = await pyClient.callTool({
              name: 'evaluate_model',
              arguments: {
                file_path: cleanedCsvPath.replace(/\\/g, '/'),
                target: target,
                task: taskType,
                model_name: 'TabFM',
                job_id: jobId
              }
            }, undefined, { timeout: 1200000 }); // 20 minutes timeout pour CPU
            
            const tabfmReturn = JSON.parse((tabfmOutput.content[0] as { type: 'text'; text: string }).text.trim());
            if (!tabfmReturn.error) {
              const tabfmEval = tabfmReturn.evaluation;
              const isTabfmValid = Guardrail.validateEvaluation(tabfmEval, perfThresholds || undefined, fairnessThresholds || undefined);
              if (isTabfmValid) {
                logger.info("✅ TabFM a validé le Guardrail Mathématique ! Élection de TabFM comme modèle Champion.");
                evalReturn = tabfmReturn;
                evaluatedModelName = "TabFM";
                isValid = true;
              } else {
                logger.warn("❌ TabFM a également échoué aux Guardrails.");
              }
            } else {
              logger.warn(`⚠️ Erreur d'évaluation TabFM : ${tabfmReturn.error}`);
            }
          } catch (tabfmErr: any) {
            logger.warn(`⚠️ Échec de l'exécution de TabFM : ${tabfmErr.message}`);
          }
        }
      } catch (err: any) {
        logger.error("Erreur d'exécution Python (Évaluation) détaillée :", err);
        if (err.stack) {
          logger.error(err.stack);
        }
        return { status: "failed", reason: `Model evaluation failed: ${err.message || err}` };
      }
      
      // 4. Validating (Guardrails)
      logger.info("\n[PHASE 4] Validation des métriques par le Guardrail Strict...");
      
      const finalEvaluation = evalReturn.evaluation;
      let optunaResult: any = undefined;
      
      if (isValid) {
        logger.info(`✅ Guardrail Mathématique validé avec le modèle ${evaluatedModelName} !`);
        
        let visionResult: any = null;

        // 4.5 Double Guardrail Visuel
        const artifacts = finalEvaluation?.artifacts;
        if (artifacts && (artifacts.confusion_matrix_path || artifacts.residuals_path)) {
          logger.info("\n[PHASE 4.5] Double Guardrail Visuel (Analyse par l'Oeil de l'IA)...");
          
          if (artifacts.confusion_matrix_path) {
            const confusionMatrixPathAbs = path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", artifacts.confusion_matrix_path);
            visionResult = await ChartInterpreter.analyzeConfusionMatrix(confusionMatrixPathAbs, finalEvaluation.metrics);
          } else if (artifacts.residuals_path) {
            const residualsPathAbs = path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", artifacts.residuals_path);
            visionResult = await ChartInterpreter.analyzeResiduals(residualsPathAbs, finalEvaluation.metrics);
          }
          
          if (visionResult) {
            if (!visionResult.confirmsMetrics) {
              logger.error(`❌ Conflit détecté entre la Vision et les Maths !`);
            }
            const actualIssues = (visionResult.additionalIssues || []).filter((issue: string) => {
              const clean = issue.trim().toLowerCase();
              return clean !== 'none' && clean !== 'n/a' && !clean.startsWith('none') && !clean.startsWith('no issues') && !clean.startsWith('no critical issues');
            });
            if (actualIssues.length > 0) {
              logger.error(`❌ Rejet du Pipeline par la Vision. Problèmes détectés : ${actualIssues.join(', ')}`);
              return { status: "failed", reason: "Visual verification failed." };
            }
            logger.info("✅ Validation Visuelle confirmée ! L'image est saine.");
          }
        }
        
        // 5.5 Explainability Audit
        logger.info("\n[PHASE 5.5] Audit d'Explicabilité (SHAP)...");
        try {
          const cleanedCsvPath = mcpReturn.cleanedDataPath
            ? path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", mcpReturn.cleanedDataPath).replace(/\\/g, '/')
            : `C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/${nomBase}/cleaned.csv`;

          const explOutput = await pyClient.callTool({
            name: 'run_explainability_audit',
            arguments: {
              file_path: cleanedCsvPath,
              target: resolvedTarget,
              task: resolvedTaskType,
              model_name: evaluatedModelName,
              job_id: jobId
            }
          }, undefined, { timeout: 600000 });
          const explResult = JSON.parse((explOutput.content[0] as { type: 'text'; text: string }).text.trim());
          if (explResult.status === 'completed') {
             logger.info(`✅ Audit d'Explicabilité terminé. Risk Score: ${explResult.risk_score}/10`);
             if (explResult.risk_score > 5) {
                 logger.warn(`⚠️ AVERTISSEMENT EXPLICABILITÉ : ${explResult.recommendations.join(' ')}`);
             }
          }
        } catch (e: any) {
           logger.warn(`⚠️ Erreur de l'Explainability Auditor (Ignorée) : ${e.message}`);
        }

        // 4.6 RAG & LLM Qualitative Interpretation
        let interpretationRules: any[] = [];
        try {
          const ruleClient = new KnowledgeGraphClient();
          const domainsToQuery = ['validation'];
          if (resolvedTaskType === 'clustering' || resolvedTaskType === 'unsupervised') {
            domainsToQuery.push('clustering');
          } else if (resolvedTaskType === 'timeseries' || resolvedTaskType === 'time_series') {
            domainsToQuery.push('time_series');
          } else {
            domainsToQuery.push('supervised_learning');
          }
          if (inferredDomain && inferredDomain !== 'general') {
            domainsToQuery.push(inferredDomain);
          }
          
          for (const d of domainsToQuery) {
            const rules = await ruleClient.queryInterpretationRules(d);
            if (rules && rules.length > 0) {
              interpretationRules.push(...rules);
            }
          }
          await ruleClient.close();
          logger.info(`✅ ${interpretationRules.length} règles d'interprétation chargées depuis Neo4j.`);
        } catch (e: any) {
          logger.warn(`⚠️ Impossible de récupérer les règles d'interprétation Neo4j: ${e.message}`);
        }

        let qualitativeInterpretation = "";
        try {
          logger.info("\n[LLM] Génération du Rapport d'Interprétation Qualitatif RAG (Llama)...");
          const interpretationPrompt = buildInterpretationPrompt(
            inferredDomain,
            resolvedTaskType,
            finalEvaluation.metrics,
            visionResult,
            interpretationRules,
            businessCosts
          );
          
          // Masquage DLP : sanitise le prompt avant envoi au LLM (protège les PII éventuelles dans le profil)
          const { sanitizedText: safePrompt, maskedCount } = PiiSanitizer.sanitize(interpretationPrompt);
          if (maskedCount > 0) logger.warn(`🔒 [PiiSanitizer] ${maskedCount} données sensibles masquées dans le prompt d'interprétation.`);
          const response = await ai.generate({
            model: localGemmaModel,
            prompt: safePrompt,
            tools: [graphRAGReasoner, replInterpreter],
            config: { temperature: 0.2, maxOutputTokens: 2048 }  // 2048 pour laisser de la place à la réponse (contexte LLaMA 8B = 4096)
          });
          qualitativeInterpretation = response.text || "";
          // Détection de sortie dégénérée (boucles ???... ou répétitions) - guard anti-hallucination
          const degenerationPattern = /(\?{10,}|!{10,}|\.{10,}|oppers|\s{50,})/;
          if (!qualitativeInterpretation || degenerationPattern.test(qualitativeInterpretation)) {
            logger.warn("⚠️ Sortie LLM dégénérée détectée (boucle de répétition). Utilisation du rapport de secours.");
            const m = finalEvaluation.metrics;
            qualitativeInterpretation = `## Rapport d'évaluation automatique\n\n**Domaine :** ${inferredDomain} | **Tâche :** ${resolvedTaskType}\n\n**Métriques principales :** F1 = ${(m.macro_f1 || m.cv_mean_f1 || 0).toFixed(3)}, Accuracy = ${(m.accuracy || 0).toFixed(3)}, Overfitting Gap = ${(m.overfitting_gap || 0).toFixed(3)}\n\n*Note : Le rapport qualitatif LLM n'a pas pu être généré (contexte trop chargé). Les métriques brutes sont disponibles dans MLflow.*`;
          }
          logger.info("✅ Rapport d'Interprétation qualitatif généré avec succès.");
        } catch (e: any) {
          logger.warn(`⚠️ Échec de la génération du rapport d'interprétation qualitatif : ${e.message}`);
          qualitativeInterpretation = "*Erreur de génération du rapport qualitatif par le LLM.*";
        }

        // 5. Notebook Generation (Full MLOps)
        logger.info("\n[PHASE 6] Génération du Notebook Full MLOps (CRISP-ML(Q))...");
        
        await FirestoreService.updateJobStatus(jobId, { status: 'generating_notebook', progress_percent: 80, current_message: 'Assemblage des blocs Markdown et du code Python dans le Notebook...' });

        try {
          const cleanedCsvPath = mcpReturn.cleanedDataPath
            ? path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", mcpReturn.cleanedDataPath).replace(/\\/g, '/')
            : `C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/${nomBase}/cleaned.csv`;

          const nbPath = `C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/${nomBase}/${nomBase}_Analyse_Full_MLOps.ipynb`.replace(/\\/g, '/');
          
          const nbOutput = await pyClient.callTool({
            name: 'generate_notebook',
            arguments: {
              file_path: cleanedCsvPath,
              cleaning_schema: JSON.stringify(strategy),
              output_nb_path: nbPath,
              llm_interpretation: qualitativeInterpretation,
              business_costs: businessCosts ? JSON.stringify(businessCosts) : "",
              data_contract_assertions: dataContractAssertionsCode
            }
          }, undefined, { timeout: 180000 });
          
          const nbResult = JSON.parse((nbOutput.content[0] as { type: 'text'; text: string }).text.trim());
          if (nbResult.status === "success") {
            logger.info(`✅ Notebook généré avec succès à l'emplacement : ${nbResult.notebookPath}`);
            finalNbPath = nbPath;
          } else {
            logger.error(`❌ Échec de la génération du Notebook : ${nbResult.error}`);
          }
        } catch (err: any) {
          logger.error("Erreur Python (Génération Notebook)", err);
        }
        
        logger.info("✅ Pipeline terminé avec succès.");
      } else {
        logger.error("❌ " + Guardrail.getErrorReport());
        
        failedRunId = jobId + "-failed";
        try {
          const failClient = new KnowledgeGraphClient();
          const alertType = finalEvaluation?.issues[0]?.type || "guardrail_failure";
          const detail = finalEvaluation?.issues[0]?.message || Guardrail.getErrorReport() || "Les métriques n'ont pas franchi le Guardrail mathématique.";
          await failClient.saveFailedRun(failedRunId, nomBase, inferredDomain, resolvedTaskType, alertType, detail);
          await failClient.close();
          logger.info(`📝 Échec du run enregistré dans Neo4j (ID: ${failedRunId})`);
        } catch (e: any) {
          logger.warn(`⚠️ Impossible d'enregistrer l'échec du run: ${e.message}`);
        }
        
        // Interroger Neo4j pour obtenir des conseils de remédiation
        const issues = finalEvaluation?.issues || [];
        let remedyAdvice = "";
        try {
          const remedyClient = new KnowledgeGraphClient();
          for (const issue of issues) {
            const remedy = await remedyClient.queryRemediationRules(issue.type);
            if (remedy) {
              logger.info(`💡 [NEO4J REMÈDE] Solution trouvée pour "${issue.type}" : ${remedy.action}`);
              remedyAdvice += `\n- Pour "${issue.type}" : ${remedy.action}. Snippet suggéré : ${remedy.code_snippet}`;
            }
          }
          await remedyClient.close();
        } catch (e: any) {
          logger.warn(`⚠️ Impossible de récupérer les remèdes Neo4j: ${e.message}`);
        }

        logger.info("🔄 Auto-Tuning en cours avec Optuna...");
        await FirestoreService.updateJobStatus(jobId, {
          status: 'evaluating',
          current_message: `Guardrails échoués. Remède Neo4j détecté : ${remedyAdvice || "Auto-Tuning Optuna"}`
        });
        
        try {
          const cleanedCsvPath = mcpReturn.cleanedDataPath
            ? path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", mcpReturn.cleanedDataPath)
            : "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/data_processed/cleaned.csv";

          const target = resolvedTarget;
          const taskType = resolvedTaskType;
          
          const optunaOutput = await pyClient.callTool({
            name: 'auto_tune_model',
            arguments: {
              file_path: cleanedCsvPath.replace(/\\/g, '/'),
              target: target,
              task: taskType,
              job_id: jobId
            }
          }, undefined, { timeout: 1200000 });
          
          optunaResult = JSON.parse((optunaOutput.content[0] as { type: 'text'; text: string }).text.trim());
          if (optunaResult.error) {
            logger.error(`❌ Échec de l'Auto-Tuning : ${optunaResult.error}`);
            return { status: "failed", reason: optunaResult.error };
          }

          if (optunaResult.status === 'success') {
            logger.info(`✅ Auto-Tuning réussi ! Nouveau score : ${optunaResult.optimized_score}`);
            logger.info(`Meilleurs paramètres : ${JSON.stringify(optunaResult.best_params)}`);
            
            // 4.5-bis : Guardrail Visuel sur le chemin Optuna (miroir du chemin valide)
            let visionResultOptuna: any = null;
            const optunaArtifacts = optunaResult.artifacts;
            if (optunaArtifacts && (optunaArtifacts.confusion_matrix_path || optunaArtifacts.residuals_path || optunaArtifacts.pca_path)) {
              logger.info("\n[PHASE 4.5-bis] Double Guardrail Visuel sur le modèle Optuna...");
              if (optunaArtifacts.confusion_matrix_path) {
                const cmPath = path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", optunaArtifacts.confusion_matrix_path);
                visionResultOptuna = await ChartInterpreter.analyzeConfusionMatrix(cmPath, { score: optunaResult.optimized_score });
              } else if (optunaArtifacts.residuals_path) {
                const resPath = path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", optunaArtifacts.residuals_path);
                visionResultOptuna = await ChartInterpreter.analyzeResiduals(resPath, { score: optunaResult.optimized_score });
              }
              if (visionResultOptuna) {
                const optunaIssues = (visionResultOptuna.additionalIssues || []).filter((issue: string) => {
                  const clean = issue.trim().toLowerCase();
                  return clean !== 'none' && clean !== 'n/a' && !clean.startsWith('none') && !clean.startsWith('no issues') && !clean.startsWith('no critical issues');
                });
                if (optunaIssues.length > 0) {
                  logger.error(`❌ Rejet du Pipeline Optuna par la Vision. Problèmes : ${optunaIssues.join(', ')}`);
                  return { status: "failed", reason: "Visual verification failed after Optuna tuning." };
                }
                logger.info("✅ Validation Visuelle du modèle Optuna confirmée !");
              }
            }

            // 5.5 Explainability Audit
            logger.info("\n[PHASE 5.5] Audit d'Explicabilité (SHAP)...");
            try {
              const explOutput = await pyClient.callTool({
                name: 'run_explainability_audit',
                arguments: {
                  file_path: cleanedCsvPath.replace(/\\/g, '/'),
                  target: resolvedTarget,
                  task: resolvedTaskType,
                  job_id: jobId
                }
              }, undefined, { timeout: 600000 });
              const explResult = JSON.parse((explOutput.content[0] as { type: 'text'; text: string }).text.trim());
              if (explResult.status === 'completed') {
                 logger.info(`✅ Audit d'Explicabilité terminé après Auto-Tuning. Risk Score: ${explResult.risk_score}/10`);
                 if (explResult.risk_score > 5) {
                     logger.warn(`⚠️ AVERTISSEMENT EXPLICABILITÉ : ${explResult.recommendations.join(' ')}`);
                 }
              }
            } catch (e: any) {
               logger.warn(`⚠️ Erreur de l'Explainability Auditor (Ignorée) : ${e.message}`);
            }

            // 4.6 RAG & LLM Qualitative Interpretation (Optuna path)
            let interpretationRules: any[] = [];
            try {
              const ruleClient = new KnowledgeGraphClient();
              const domainsToQuery = ['validation'];
              if (resolvedTaskType === 'clustering' || resolvedTaskType === 'unsupervised') {
                domainsToQuery.push('clustering');
              } else if (resolvedTaskType === 'timeseries' || resolvedTaskType === 'time_series') {
                domainsToQuery.push('time_series');
              } else {
                domainsToQuery.push('supervised_learning');
              }
              if (inferredDomain && inferredDomain !== 'general') {
                domainsToQuery.push(inferredDomain);
              }
              
              for (const d of domainsToQuery) {
                const rules = await ruleClient.queryInterpretationRules(d);
                if (rules && rules.length > 0) {
                  interpretationRules.push(...rules);
                }
              }
              await ruleClient.close();
            } catch (e: any) {
              logger.warn(`⚠️ Impossible de récupérer les règles d'interprétation Neo4j: ${e.message}`);
            }

            let qualitativeInterpretation = "";
            try {
              logger.info("\n[LLM] Génération du Rapport d'Interprétation Qualitatif RAG après Auto-Tuning (Llama)...");
              const interpretationPrompt = buildInterpretationPrompt(
                inferredDomain,
                resolvedTaskType,
                { score: optunaResult.optimized_score, best_params: optunaResult.best_params },
                visionResultOptuna, // pas de null, on passe le résultat du guardrail visuel
                interpretationRules,
                businessCosts
              );
              
              const response = await ai.generate({
                model: localGemmaModel,
                prompt: interpretationPrompt,
                tools: [graphRAGReasoner, replInterpreter],
                config: { temperature: 0.2, maxOutputTokens: 2048 }  // 2048 pour laisser de la place à la réponse (contexte LLaMA 8B = 4096)
              });
              qualitativeInterpretation = response.text || "";
              // Détection de sortie dégénérée (boucles ???... ou répétitions) - guard anti-hallucination
              const degenerationPattern = /(\?{10,}|!{10,}|\.{10,}|oppers|\s{50,})/;
              if (!qualitativeInterpretation || degenerationPattern.test(qualitativeInterpretation)) {
                logger.warn("⚠️ Sortie LLM dégénérée détectée (boucle de répétition) après Optuna. Utilisation du rapport de secours.");
                const bestScore = optunaResult?.optimized_score || 0;
                const bestParams = JSON.stringify(optunaResult?.best_params || {}, null, 0);
                qualitativeInterpretation = `## Rapport post-optimisation automatique\n\n**Domaine :** ${inferredDomain} | **Tâche :** ${resolvedTaskType}\n\n**Score Optuna :** ${bestScore.toFixed(3)} | **Meilleurs paramètres :** ${bestParams}\n\n*Note : Le rapport qualitatif LLM n'a pas pu être généré (contexte saturé). Les métriques et paramètres optimaux sont disponibles dans MLflow.*`;
              }
              logger.info("✅ Rapport d'Interprétation qualitatif généré avec succès après Optuna.");
            } catch (e: any) {
              logger.warn(`⚠️ Échec de la génération du rapport d'interprétation qualitatif (Optuna) : ${e.message}`);
              qualitativeInterpretation = "*Erreur de génération du rapport qualitatif par le LLM.*";
            }

            logger.info("\n[PHASE 6] Génération du Notebook Full MLOps (Avec paramètres optimisés)...");
            const nbPath = `C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/${nomBase}/${nomBase}_Analyse_Full_MLOps.ipynb`.replace(/\\/g, '/');
            
            const optimizedStrategy = { ...strategy, best_params: optunaResult.best_params };
            
            const nbOutput = await pyClient.callTool({
              name: 'generate_notebook',
              arguments: {
                file_path: cleanedCsvPath,
                cleaning_schema: JSON.stringify(optimizedStrategy),
                output_nb_path: nbPath,
                llm_interpretation: qualitativeInterpretation,
                business_costs: businessCosts ? JSON.stringify(businessCosts) : "",
                data_contract_assertions: dataContractAssertionsCode
              }
            }, undefined, { timeout: 180000 });
            
            const nbResult = JSON.parse((nbOutput.content[0] as { type: 'text'; text: string }).text.trim());
            if (nbResult.status === "success") {
              logger.info(`✅ Notebook généré avec succès après Optuna à l'emplacement : ${nbResult.notebookPath}`);
              finalNbPath = nbPath;
            } else {
              logger.error(`❌ Échec de la génération du Notebook (Optuna) : ${nbResult.error}`);
            }
          } else {
            logger.error(`❌ Échec de l'Auto-Tuning Optuna : ${optunaResult.error}`);
          }
        } catch (err: any) {
          logger.error("Erreur Python (Auto-Tuning) : " + (err.message || err));
        }
      }
      
      // Sauvegarder les métriques du run dans Neo4j (Mémoire Épisodique)
      try {
        const saveMemory = await askQuestion("\n⚠️ Voulez-vous enregistrer cette session de run (stratégie et métriques d'évaluation) dans la mémoire épisodique de Neo4j ? [O/N] (O par défaut) : ");
        if (saveMemory.trim().toUpperCase() !== 'N') {
          logger.info("\n[NEO4J] Enregistrement de l'exécution dans le Graphe de Connaissances...");
          const writeRagClient = new KnowledgeGraphClient();
          let championModel = "RandomForest";
          let finalMetrics = {};
          
          if (isValid) {
            championModel = evaluatedModelName;
            finalMetrics = finalEvaluation?.metrics || {};
          } else if (typeof optunaResult !== 'undefined' && optunaResult.status === 'success') {
            championModel = optunaResult.best_params?.model_name || "RandomForest";
            finalMetrics = { score: optunaResult.optimized_score };
          }
          
          await writeRagClient.saveRunMetadata(
            jobId,
            nomBase,
            inferredDomain,
            resolvedTaskType,
            championModel,
            finalMetrics,
            strategy,
            {
              status: isValid ? 'SUCCESS' : 'PARTIAL',
              alerts: (finalEvaluation?.issues || []) as Array<{type: string; severity: string}>,
              nRows: profileData?.total_rows || 0,
              nCols: profileData?.total_columns || 0
            }
          );
          if (failedRunId) {
            await writeRagClient.saveResolutionRelation(failedRunId, jobId);
            logger.info(`🔗 Relation de résolution enregistrée dans Neo4j : ${failedRunId} -> RESOLVED_BY -> ${jobId}`);
          }
          await writeRagClient.close();
          logger.info("✅ Enregistrement Neo4j terminé.");
        } else {
          logger.info("⏭️ Enregistrement en mémoire épisodique sauté à la demande de l'utilisateur (phase de rodage).");
        }
      } catch (e: any) {
        logger.warn(`⚠️ Impossible d'enregistrer le run dans Neo4j: ${e.message}`);
      }

      // Proposer l'exécution automatique et/ou l'ouverture du notebook
      if (finalNbPath && existsSync(finalNbPath)) {
        const executeNb = await askQuestion("\n⚡ Voulez-vous exécuter automatiquement le notebook en arrière-plan ? [O/N] (N par défaut) : ");
        if (executeNb.trim().toUpperCase() === 'O') {
          logger.info("⏳ Exécution automatique du notebook (nbconvert --execute)... Cela peut prendre quelques minutes.");
          try {
            await runPythonAsync(
              '.venv/Scripts/python.exe',
              ['-m', 'jupyter', 'nbconvert', '--to', 'notebook', '--execute', '--inplace', '--ExecutePreprocessor.timeout=3600', finalNbPath],
              'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors'
            );
            logger.info("✅ Notebook exécuté et mis à jour avec succès !");
          } catch (nbErr: any) {
            logger.error(`❌ Échec de l'exécution automatique du notebook : ${nbErr.message}`);
          }
        }
        
        const openNb = await askQuestion("\n📂 Voulez-vous ouvrir le dossier contenant le notebook dans l'explorateur Windows ? [O/N] (O par défaut) : ");
        if (openNb.trim().toUpperCase() !== 'N') {
          try {
            const folderPath = path.dirname(finalNbPath).replace(/\//g, '\\');
            execSync(`explorer.exe "${folderPath}"`);
            logger.info("✅ Explorateur de fichiers Windows ouvert.");
          } catch (openErr: any) {
            logger.warn(`⚠️ Impossible d'ouvrir l'explorateur : ${openErr.message}`);
          }
        }
      }

      logger.info("============================================");
      return { status: "success", strategy };
    } finally {
      logger.info("🔌 Fermeture des connexions MCP...");
      const idx = activeTransports.indexOf(pyTransport);
      if (idx !== -1) activeTransports.splice(idx, 1);
      await pyTransport.close();
    }
  }
);

async function main() {
  console.log("=== MAIN FUNCTION STARTED ===");
  try {
    let inputCsv = "";
    let target = "";
    let taskType = "";

    // Parse options from command line:
    // e.g. npm run dev -- "../../data/diabetes_data_upload.csv" --target "class" --task "classification"
    for (let i = 2; i < process.argv.length; i++) {
      const arg = process.argv[i];
      if (!arg) continue;
      if (arg === '--target' && i + 1 < process.argv.length) {
        target = process.argv[++i] || "";
      } else if (arg === '--task' && i + 1 < process.argv.length) {
        taskType = process.argv[++i] || "";
      } else if (!arg.startsWith('--')) {
        inputCsv = arg;
      }
    }
    
    const askQuestionLocal = (query: string): Promise<string> => {
      const rl = readline.createInterface({
        input: process.stdin,
        output: process.stdout,
      });
      return new Promise(resolve => rl.question(query, ans => {
        rl.close();
        resolve(ans);
      }));
    };

    if (!inputCsv) {
      const dataDir = path.resolve(__dirname, '../../../data');
      if (existsSync(dataDir)) {
        const files = readdirSync(dataDir).filter(f => f.endsWith('.csv'));
        if (files.length > 0) {
          console.log("\n📊 Aucun dataset spécifié. Veuillez choisir parmi les datasets disponibles :");
          files.forEach((file, index) => {
            console.log(`  ${index + 1}. ${file}`);
          });
          console.log(`  ${files.length + 1}. Spécifier un autre chemin`);
          
          let choice = -1;
          while (choice < 1 || choice > files.length + 1) {
            const answer = await askQuestionLocal(`Veuillez entrer votre choix (1-${files.length + 1}) : `);
            choice = parseInt(answer.trim(), 10);
            if (isNaN(choice)) {
              choice = -1;
            }
          }
          
          if (choice === files.length + 1) {
            const customPath = await askQuestionLocal("Entrez le chemin absolu ou relatif du fichier CSV : ");
            inputCsv = customPath.trim();
          } else {
            const selectedFile = files[choice - 1];
            inputCsv = path.join(dataDir, selectedFile || "");
          }
        }
      }
    }

    if (!inputCsv) {
      inputCsv = "C:/Users/HP/cam_data_sov_solutions newversion/data/diabetes_data_upload.csv";
      logger.info(`[DATA] Fallback sur le dataset par défaut : ${inputCsv}`);
    }
    
    await orchestratorFlow({
      csvPath: inputCsv,
      target: target || undefined,
      taskType: taskType || undefined
    });
    process.exit(0);
  } catch (error) {
    console.error("Pipeline failed:", error);
    process.exit(1);
  }
}

main().catch((err) => {
  console.error(err);
  process.exit(1);
});
