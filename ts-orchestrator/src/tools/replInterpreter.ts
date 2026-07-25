/**
 * replInterpreter.ts — SOVEREIGN.BI Enterprise Context & Action Layer
 *
 * Outil Genkit exposant le bac à sable REPL (Python Execution Engine) aux agents IA.
 *
 * Permet à l'agent d'écrire un script d'analyse complet (Pandas, Neo4j, SQL)
 * et de l'exécuter en 1 seul appel sans multiplier les requêtes séquentielles.
 */

import { z } from 'genkit';
import * as path from 'path';
import * as fs from 'fs';
import * as os from 'os';
import { execFile } from 'child_process';
import { promisify } from 'util';
import pino from 'pino';

const execFileAsync = promisify(execFile);
const logger = pino({ transport: { target: 'pino-pretty' } });

// ─── Chemins ──────────────────────────────────────────────────────────────────

const PYTHON_EXE = path.resolve(
  __dirname, '..', '..', '..', 'py-executors', '.venv', 'Scripts', 'python.exe',
);

const REPL_SCRIPT = path.resolve(
  __dirname, '..', '..', '..', 'py-executors', 'src', 'tools', 'repl_sandbox.py',
);

// ─── Interfaces ───────────────────────────────────────────────────────────────

export interface REPLResult {
  status: 'SUCCESS' | 'ERROR' | 'BLOCKED';
  output: string;
  stderr?: string;
  result?: unknown;
  error?: string | null;
  executionTimeMs?: number;
}

// ─── Export Outil Genkit ──────────────────────────────────────────────────────

export const getREPLInterpreter = (ai: any) =>
  ai.defineTool(
    {
      name: 'replInterpreter',
      description:
        "Exécute un script Python d'analyse de données dans un bac à sable REPL sécurisé (Python Sandbox). " +
        "L'environnement dispose déjà des objets pré-chargés : " +
        "- `pd` (Pandas), `np` (NumPy), `json` " +
        "- `load_csv('filename.csv')` : charge un fichier du dossier data/ dans un DataFrame " +
        "- `query_neo4j(cypher_str)` : exécute du Cypher déterministe sur le graphe de connaissances " +
        "- `query_sql(sql_str)` : exécute du SQL (non recommandé car non configuré par défaut) " +
        "Utiliser cet outil pour regrouper plusieurs explorations complexes en un seul script au lieu d'enchaîner " +
        "de multiples requêtes séquentielles.",
      inputSchema: z.object({
        script: z
          .string()
          .describe("Code source Python à exécuter dans le REPL (ex: `df = load_csv('diabetes_data_upload.csv'); print(df.describe())`)"),
        timeoutMs: z
          .number()
          .int()
          .min(1000)
          .max(30000)
          .default(10000)
          .describe("Temps limite d'exécution en ms (défaut: 10000)"),
      }),
      outputSchema: z.any(),
    },
    async (input: { script: string; timeoutMs: number }): Promise<REPLResult> => {
      const startTime = Date.now();

      logger.info(`⚡ [REPLInterpreter] Lancement du script dans le REPL Sandbox...`);

      if (!fs.existsSync(REPL_SCRIPT)) {
        return {
          status: 'ERROR',
          output: '',
          error: `[REPLInterpreter] Script repl_sandbox.py introuvable : ${REPL_SCRIPT}`,
        };
      }

      // Fichiers temporaires d'entrée et de sortie
      const tmpInput  = path.join(os.tmpdir(), `repl_input_${Date.now()}.json`);
      const tmpOutput = path.join(os.tmpdir(), `repl_output_${Date.now()}.json`);

      fs.writeFileSync(tmpInput, JSON.stringify({ script: input.script }, null, 2), 'utf-8');

      try {
        const neo4jUri = process.env.NEO4J_URI || 'bolt://127.0.0.1:7687';
        const neo4jUser = process.env.NEO4J_USER || 'neo4j';
        const neo4jPassword = process.env.NEO4J_PASSWORD || 'password123';

        await execFileAsync(
          PYTHON_EXE,
          [REPL_SCRIPT, '--input', tmpInput, '--output', tmpOutput],
          {
            timeout: input.timeoutMs,
            maxBuffer: 1024 * 1024 * 5,
            env: {
              ...process.env,
              NEO4J_URI: neo4jUri,
              NEO4J_USER: neo4jUser,
              NEO4J_PASSWORD: neo4jPassword
            }
          },
        );

        if (!fs.existsSync(tmpOutput)) {
          return {
            status: 'ERROR',
            output: '',
            error: '[REPLInterpreter] Le bac à sable n\'a pas produit de fichier de sortie.',
          };
        }

        const rawResult = JSON.parse(fs.readFileSync(tmpOutput, 'utf-8'));
        const executionTimeMs = Date.now() - startTime;

        logger.info(
          `      [REPLInterpreter] Exécution terminée en ${executionTimeMs}ms — ` +
          `statut: ${rawResult.status}`,
        );

        return {
          status: rawResult.status || 'SUCCESS',
          output: rawResult.output || '',
          stderr: rawResult.stderr || '',
          result: rawResult.result ?? null,
          error: rawResult.error || null,
          executionTimeMs,
        };

      } catch (err: any) {
        const executionTimeMs = Date.now() - startTime;
        logger.error({ err }, `❌ [REPLInterpreter] Erreur d'exécution : ${err.message}`);
        return {
          status: 'ERROR',
          output: '',
          error: `Erreur REPL : ${err.message}`,
          executionTimeMs,
        };
      } finally {
        if (fs.existsSync(tmpInput))  fs.unlinkSync(tmpInput);
        if (fs.existsSync(tmpOutput)) fs.unlinkSync(tmpOutput);
      }
    },
  );
