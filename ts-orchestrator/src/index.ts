console.log("=== SCRIPT STARTED ===");
import { genkit, z } from 'genkit';
// Import openAI plugin removed since we use a custom model
import { execSync, spawn } from 'child_process';
import { writeFileSync, unlinkSync, readdirSync, existsSync } from 'fs';
import * as path from 'path';
import axios from 'axios';
import pino from 'pino';
import * as readline from 'readline';
import { StateManager, PipelineState } from './stateManager';
import { RagRetriever } from './agents/ragRetriever';
import { KnowledgeGraphClient } from './rag/knowledge-graph-client';
import { ChartInterpreter } from './vision/chart-interpreter';
import { Guardrail } from './guardrails';
import { FirestoreService } from './firebase/firestore';
import { generateStrategyWithSelfHealing } from './agents/strategyGenerator';

// Helper pour exécuter python de manière asynchrone sans bloquer l'Event Loop
async function runPythonAsync(command: string, args: string[], cwd: string, jobId?: string): Promise<string> {
  return new Promise((resolve, reject) => {
    const pyProcess = spawn(command, args, { cwd });
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
              logger.error(`❌ Worker Python (Job ${jobId}) ne répond plus (Timeout > 60s). Arrêt forcé (SIGKILL).`);
              
              pyProcess.kill('SIGKILL');
              
              await FirestoreService.updateJobStatus(jobId, {
                status: 'failed',
                current_message: 'Erreur: Le traitement Python a planté silencieusement (OOM/Deadlock). Timeout Heartbeat atteint.'
              });
              
              if (monitorInterval) clearInterval(monitorInterval);
              reject(new Error(`Python Worker Heartbeat Timeout (>${HEARTBEAT_TIMEOUT_MS}ms). Process killed.`));
            }
          }
        } catch (e) {
          logger.warn(`Erreur lors du monitoring heartbeat: ${e}`);
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
      if (monitorInterval) clearInterval(monitorInterval);
      if (code === 0) resolve(stdoutData);
      else reject(new Error(`Exit code ${code}\nStderr: ${stderrData}\nStdout: ${stdoutData}`));
    });
  });
}

const logger = pino({
  transport: {
    target: 'pino-pretty'
  }
});

const ai = genkit({});

// Definition d'un modele custom pour LM Studio qui bypasse les bugs du plugin openai
// Cela permet d'avoir 100% de fiabilite avec Axios TOUT EN affichant les traces dans l'UI Genkit !
const localGemmaModel = ai.defineModel(
  {
    name: 'lmstudio/gemma-4-12b',
  },
  async (request) => {
    // Extraction du prompt depuis la structure Genkit
    let promptText = "";
    if (request.messages && request.messages.length > 0) {
       const content = request.messages[0].content;
       if (Array.isArray(content) && content.length > 0) {
           promptText = content[0].text || "";
       }
    }

    const response = await axios.post('http://127.0.0.1:1234/v1/chat/completions', {
      model: 'google/gemma-4-12b',
      messages: [{ role: 'user', content: promptText }],
      temperature: request.config?.temperature || 0.2
    }, {
      timeout: 0,
      headers: { 'Content-Type': 'application/json' }
    });

    return {
      message: {
        role: 'model',
        content: [{ text: response.data.choices[0].message.content }]
      }
    };
  }
);

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
    logger.info("🧠 Démarrage du Cerveau Orchestrateur");
    logger.info("============================================");

    // 1. Profiling via Python Muscles
    logger.info("\n[PHASE 1] Appel aux Muscles Python pour Profiler le CSV...");
    const csvPath = path.resolve(process.cwd(), input.csvPath);
    const safePath = csvPath.replace(/\\/g, '/');
    const nomBase = path.basename(csvPath, '.csv');
  
    let pythonOutput = '';
    try {
      pythonOutput = execSync(`uv run python -c "from src.server import profile_dataset; print(profile_dataset('${safePath}'))"`, {
        cwd: 'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
        encoding: 'utf-8'
      });
    } catch (err: any) {
      logger.error("Erreur lors de l'appel Python (Profilage)", err);
      if (err.stdout) logger.error("STDOUT: " + err.stdout.toString());
      if (err.stderr) logger.error("STDERR: " + err.stderr.toString());
      return { status: "failed", reason: "Profiling failed during Python execution." };
    }

    if (!pythonOutput || pythonOutput.trim() === '') {
      logger.error("❌ Erreur : Le profiler Python n'a renvoyé aucun résultat.");
      return { status: "failed", reason: "Python profiling output was empty." };
    }

    const profileData = JSON.parse(pythonOutput.trim());
    if (profileData.error) {
      logger.error(`❌ Échec du profilage du dataset : ${profileData.error}`);
      return { status: "failed", reason: profileData.error };
    }

    state.update({
      currentPhase: 'profiling',
      profile: profileData
    });
    logger.info(`[PHASE 1] Dataset Profilé : ${profileData.total_rows} lignes, ${profileData.total_columns} colonnes.`);

    // Auto-detection or user specification of task type and target column
    const resolvedTarget = input.target || profileData.suggested_target || "";
    const resolvedTaskType = input.taskType || profileData.suggested_task_type || "regression";
    logger.info(`🎯 Target résolue : ${resolvedTarget || "Aucune (Clustering)"} | Tâche résolue : ${resolvedTaskType}`);

    // 🔥 INITIALISATION FIREBASE JOB
    const jobId = await FirestoreService.createJob(nomBase);
    logger.info(`🔗 Tracking UI démarré avec le Job ID: ${jobId}`);

    // 1.5 Adversarial Validation
    logger.info("\n[PHASE 1.5] Validation Adversariale (Détection de Drift Temporel)...");
    let adversarialContext = "";
    try {
      const advOutput = await runPythonAsync(
        'uv',
        ['run', 'python', '-c', `from src.server import run_adversarial_validation; print(run_adversarial_validation('${safePath}', '${resolvedTarget}', '${resolvedTaskType}', '${jobId}'))`],
        'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
        jobId
      );
      const advResult = JSON.parse(advOutput.trim());
      if (advResult.drift_detected) {
        logger.warn(`⚠️ Drift temporel détecté ! (AUC: ${advResult.auc.toFixed(2)})`);
        adversarialContext = `⚠️ ALERTE ADVERSARIAL VALIDATION : Un data drift a été détecté (AUC de l'Adversarial Validator: ${advResult.auc.toFixed(2)}). Les features suivantes sont les plus suspectes d'avoir changé dans le temps : ${JSON.stringify(advResult.suspicious_features)}. Recommandation : ${advResult.recommendation}`;
      } else {
        logger.info("✅ Aucun drift temporel détecté par l'Adversarial Validator.");
      }
    } catch (e: any) {
       logger.warn(`⚠️ Erreur de l'Adversarial Validator (Ignorée) : ${e.message}`);
    }

    // 2. Strategizing (True Graph RAG Retrieval via Neo4j)
    logger.info("\n[PHASE 2] Le Stratège interroge la Base de Connaissances Neo4j (Graph RAG)...");
    
    const ragClient = new KnowledgeGraphClient();
    const knowledge = await ragClient.queryForStrategy('Data cleaning', profileData);
    await ragClient.close();
    
    logger.info("📚 Connaissances récupérées par l'agent (Neo4j) :");
    logger.info(`Concepts: ${knowledge.relevantConcepts.length}, Règles: ${knowledge.decisionRules.length}, Procédures: ${knowledge.procedures.length}`);

    // L'agent définit sa stratégie basée sur ces connaissances via LM Studio
    logger.info("🤖 Génération de la stratégie finale via LM Studio (Gemma 4 12B)...");
    
    // Contexte complet à passer à l'agent
    const context = `
Voici le profil du dataset :
${JSON.stringify(state.get().profile, null, 2)}

${adversarialContext}

📚 RELEVANT KNOWLEDGE (From Knowledge Graph):
${knowledge.relevantConcepts.map(c => `- **${c.name}** (${c.category}): ${c.definition}`).join('\n')}

🎯 DECISION RULES (Apply these expert heuristics):
${knowledge.decisionRules.map(d => `
**${d.question}**
${d.branches.map((b, i) => `  ${i + 1}. IF ${b.condition}\n     THEN ${b.action}\n     (Confidence: ${(b.confidence * 100).toFixed(0)}%)`).join('\n')}`).join('\n')}

📋 PROCEDURES AVAILABLE:
${knowledge.procedures.map(p => `- ${p.title}`).join('\n')}

Tu dois concevoir une stratégie de nettoyage pour la tâche suivante : **${resolvedTaskType.toUpperCase()}** avec la colonne cible (target) : **${resolvedTarget || "Aucune (Clustering)"}**.
`;

    // Appel à la boucle de Self-Healing
    const { strategy, source } = await generateStrategyWithSelfHealing(
      ai,
      localGemmaModel,
      context,
      resolvedTarget,
      resolvedTaskType,
      jobId,
      3 // max retries
    );

    logger.info(`Réponse de LM Studio validée ! Source de la stratégie : ${source}`);
    
    // On notifie Firestore que l'on passe à l'étape suivante
    await FirestoreService.updateJobStatus(jobId, { 
      status: 'cleaning',
      current_message: 'Stratégie générée, en attente de validation humaine ou exécution'
    });

    state.update({
      currentPhase: 'strategizing',
      strategy: strategy
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
      
      // Fonction utilitaire pour prompt asynchrone
      const askQuestion = (query: string): Promise<string> => {
          const rl = readline.createInterface({
              input: process.stdin,
              output: process.stdout,
          });
          return new Promise(resolve => rl.question(query, ans => {
              rl.close();
              resolve(ans);
          }));
      };

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
      const strategyStr = JSON.stringify(strategy);
      const tempSchemaPath = "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors/temp_schema.json";
      writeFileSync(tempSchemaPath, strategyStr, 'utf-8');
      
      await FirestoreService.updateJobStatus(jobId, { status: 'cleaning', progress_percent: 10, current_message: 'Nettoyage des données en cours...' });

      const pyOutput = await runPythonAsync(
        'uv', 
        ['run', 'python', '-c', `from src.server import apply_cleaning_strategy; import json; schema=open('temp_schema.json', encoding='utf-8').read(); print(apply_cleaning_strategy('${csvPath.replace(/\\/g, '/')}', schema, '${jobId}'))`],
        'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
        jobId
      );
      
      // Parse the FastMCP tool return object
      mcpReturn = JSON.parse(pyOutput.trim());
      if (mcpReturn.error) {
        logger.error(`❌ Échec du nettoyage des données : ${mcpReturn.error}`);
        return { status: "failed", reason: mcpReturn.error };
      }
      logger.info("Résultat du nettoyage :");
      console.log(mcpReturn);
    } catch (err: any) {
      logger.error("Erreur d'exécution Python (Nettoyage)", err);
      if (err.stdout) logger.error("STDOUT: " + err.stdout.toString());
      if (err.stderr) logger.error("STDERR: " + err.stderr.toString());
      return { status: "failed", reason: "Data cleaning failed during Python execution." };
    }
    
    // 3.5 Evaluating the strategy by running a quick model
    logger.info("\n[PHASE 3.5] Évaluation du modèle (Génération des métriques Structurées JSON et Artifacts PNG)...");
    
    await FirestoreService.updateJobStatus(jobId, { status: 'evaluating', progress_percent: 30, current_message: 'Calcul des métriques (Silhouette, F1-Score)...' });

    let evalReturn;
    try {
      const cleanedCsvPath = mcpReturn.cleanedDataPath
        ? path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", mcpReturn.cleanedDataPath)
        : "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/data_processed/cleaned.csv";
        
      const target = resolvedTarget;
      const taskType = resolvedTaskType;
      
      const evalOutput = await runPythonAsync(
        'uv',
        ['run', 'python', '-c', `from src.server import evaluate_model; import json; print(json.dumps(evaluate_model('${cleanedCsvPath.replace(/\\/g, '/')}', '${target}', '${taskType}', '${jobId}')))`],
        'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
        jobId
      );
      
      evalReturn = JSON.parse(evalOutput.trim());
      if (evalReturn.error) {
        logger.error(`❌ Échec de l'évaluation : ${evalReturn.error}`);
        return { status: "failed", reason: evalReturn.error };
      }
      logger.info("Résultat de l'Évaluation :");
      console.log(evalReturn);
    } catch (err: any) {
      logger.error("Erreur d'exécution Python (Évaluation)", err);
      if (err.stdout) logger.error("STDOUT: " + err.stdout.toString());
      if (err.stderr) logger.error("STDERR: " + err.stderr.toString());
      return { status: "failed", reason: "Model evaluation failed during Python execution." };
    }
    
    // 4. Validating (Guardrails)
    logger.info("\n[PHASE 4] Validation des métriques par le Guardrail Strict...");
    
    const finalEvaluation = evalReturn.evaluation;
    const isValid = Guardrail.validateEvaluation(finalEvaluation);
    
    if (isValid) {
      logger.info("✅ Guardrail Mathématique validé !");
      
      // 4.5 Double Guardrail Visuel
      const artifacts = finalEvaluation?.artifacts;
      if (artifacts && (artifacts.confusion_matrix_path || artifacts.residuals_path)) {
        logger.info("\n[PHASE 4.5] Double Guardrail Visuel (Analyse par l'Oeil de l'IA)...");
        let visionResult = null;
        
        // On prend le premier graphique disponible (soit classification, soit régression)
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
          if (visionResult.additionalIssues && visionResult.additionalIssues.length > 0) {
            logger.error(`❌ Rejet du Pipeline par la Vision. Problèmes détectés : ${visionResult.additionalIssues.join(', ')}`);
            logger.error(`Feedback à renvoyer au LLM : "L'inspection visuelle révèle des erreurs fatales non vues par les métriques."`);
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

        const explOutput = await runPythonAsync(
          'uv',
          ['run', 'python', '-c', `from src.server import run_explainability_audit; print(run_explainability_audit('${cleanedCsvPath}', '${resolvedTarget}', '${resolvedTaskType}', '${jobId}'))`],
          'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
          jobId
        );
        const explResult = JSON.parse(explOutput.trim());
        if (explResult.status === 'completed') {
           logger.info(`✅ Audit d'Explicabilité terminé. Risk Score: ${explResult.risk_score}/10`);
           if (explResult.risk_score > 5) {
               logger.warn(`⚠️ AVERTISSEMENT EXPLICABILITÉ : ${explResult.recommendations.join(' ')}`);
           }
        }
      } catch (e: any) {
         logger.warn(`⚠️ Erreur de l'Explainability Auditor (Ignorée) : ${e.message}`);
      }

      // 5. Notebook Generation (Full MLOps)
      logger.info("\n[PHASE 6] Génération du Notebook Full MLOps (CRISP-ML(Q))...");
      
      await FirestoreService.updateJobStatus(jobId, { status: 'generating_notebook', progress_percent: 80, current_message: 'Assemblage des blocs Markdown et du code Python dans le Notebook...' });

      try {
        const cleanedCsvPath = mcpReturn.cleanedDataPath
          ? path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", mcpReturn.cleanedDataPath).replace(/\\/g, '/')
          : `C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/${nomBase}/cleaned.csv`;

        const nbPath = `C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/${nomBase}/${nomBase}_Analyse_Full_MLOps.ipynb`.replace(/\\/g, '/');
        
        const strategyStr = JSON.stringify(strategy);
        const tempSchemaPath = "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors/temp_schema.json";
        writeFileSync(tempSchemaPath, strategyStr, 'utf-8');

        const nbOutput = await runPythonAsync(
          'uv',
          ['run', 'python', '-c', `from src.server import generate_notebook; import json; schema=open('temp_schema.json', encoding='utf-8').read(); print(generate_notebook('${cleanedCsvPath}', schema, '${nbPath}'))`],
          'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
          jobId
        );
        
        // Nettoyage du fichier temporaire
        unlinkSync("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors/temp_schema.json");
        
        const nbResult = JSON.parse(nbOutput.trim());
        if (nbResult.status === "success") {
          logger.info(`✅ Notebook généré avec succès à l'emplacement : ${nbResult.notebookPath}`);
        } else {
          logger.error(`❌ Échec de la génération du Notebook : ${nbResult.error}`);
        }
      } catch (err: any) {
        logger.error("Erreur Python (Génération Notebook)", err);
        if (err.stdout) logger.error("STDOUT: " + err.stdout.toString());
        if (err.stderr) logger.error("STDERR: " + err.stderr.toString());
      }
      
      logger.info("✅ Pipeline terminé avec succès.");
    } else {
      logger.error("❌ " + Guardrail.getErrorReport());
      logger.info("🔄 Auto-Tuning en cours avec Optuna...");
      
      try {
        const cleanedCsvPath = mcpReturn.cleanedDataPath
          ? path.resolve("C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors", mcpReturn.cleanedDataPath)
          : "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/data_processed/cleaned.csv";

        const target = resolvedTarget;
        const taskType = resolvedTaskType;
        
        const optunaOutput = await runPythonAsync(
          'uv',
          ['run', 'python', '-c', `from src.server import auto_tune_model; print(auto_tune_model('${cleanedCsvPath.replace(/\\/g, '/')}', '${target}', '${taskType}', '${jobId}'))`],
          'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
          jobId
        );
        
        const optunaResult = JSON.parse(optunaOutput.trim());
        if (optunaResult.error) {
          logger.error(`❌ Échec de l'Auto-Tuning : ${optunaResult.error}`);
          return { status: "failed", reason: optunaResult.error };
        }

        if (optunaResult.status === 'success') {
          logger.info(`✅ Auto-Tuning réussi ! Nouveau score : ${optunaResult.optimized_score}`);
          logger.info(`Meilleurs paramètres : ${JSON.stringify(optunaResult.best_params)}`);
          
          // 5.5 Explainability Audit
          logger.info("\n[PHASE 5.5] Audit d'Explicabilité (SHAP)...");
          try {
            const explOutput = await runPythonAsync(
              'uv',
              ['run', 'python', '-c', `from src.server import run_explainability_audit; print(run_explainability_audit('${cleanedCsvPath.replace(/\\/g, '/')}', '${resolvedTarget}', '${resolvedTaskType}', '${jobId}'))`],
              'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
              jobId
            );
            const explResult = JSON.parse(explOutput.trim());
            if (explResult.status === 'completed') {
               logger.info(`✅ Audit d'Explicabilité terminé après Auto-Tuning. Risk Score: ${explResult.risk_score}/10`);
               if (explResult.risk_score > 5) {
                   logger.warn(`⚠️ AVERTISSEMENT EXPLICABILITÉ : ${explResult.recommendations.join(' ')}`);
               }
            }
          } catch (e: any) {
             logger.warn(`⚠️ Erreur de l'Explainability Auditor (Ignorée) : ${e.message}`);
          }

          logger.info("\n[PHASE 6] Génération du Notebook Full MLOps (Avec paramètres optimisés)...");
          const nbPath = `C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/workspace/outputs/${nomBase}/${nomBase}_Analyse_Full_MLOps.ipynb`.replace(/\\/g, '/');
          
          const optimizedStrategy = { ...strategy, best_params: optunaResult.best_params };
          const strategyStr = JSON.stringify(optimizedStrategy);
          const tempSchemaPath = "C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors/temp_schema.json";
          writeFileSync(tempSchemaPath, strategyStr, 'utf-8');
          
          const nbOutput = await runPythonAsync(
            'uv',
            ['run', 'python', '-c', `from src.server import generate_notebook; import json; schema=open('temp_schema.json', encoding='utf-8').read(); print(generate_notebook('${cleanedCsvPath}', schema, '${nbPath}'))`],
            'C:/Users/HP/cam_data_sov_solutions newversion/dataset_automator/py-executors',
            jobId
          );
          
          unlinkSync(tempSchemaPath);
          
          const nbResult = JSON.parse(nbOutput.trim());
          if (nbResult.status === "success") {
            logger.info(`✅ Notebook généré avec succès après Optuna à l'emplacement : ${nbResult.notebookPath}`);
          } else {
            logger.error(`❌ Échec de la génération du Notebook (Optuna) : ${nbResult.error}`);
          }
        } else {
          logger.error(`❌ Échec de l'Auto-Tuning Optuna : ${optunaResult.error}`);
        }
      } catch (err: any) {
        logger.error("Erreur Python (Auto-Tuning) : " + (err.message || err));
        if (err.stdout) logger.error("STDOUT: " + err.stdout.toString());
        if (err.stderr) logger.error("STDERR: " + err.stderr.toString());
      }
    }
    
    logger.info("============================================");
    return { status: "success", strategy };
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
      if (arg === '--target' && i + 1 < process.argv.length) {
        target = process.argv[++i];
      } else if (arg === '--task' && i + 1 < process.argv.length) {
        taskType = process.argv[++i];
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
            inputCsv = path.join(dataDir, files[choice - 1]);
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
  } catch (error) {
    console.error("Pipeline failed:", error);
  }
}

main().catch(console.error);
