/**
 * replInterpreter.ts — SOVEREIGN.BI Enterprise Context & Action Layer
 *
 * Genkit tool exposing the REPL sandbox (Python Execution Engine) to AI agents.
 *
 * Allows the agent to write a complete analysis script (Pandas, Neo4j, SQL)
 * and execute it in a single call without chaining multiple sequential requests.
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

// ─── Paths ──────────────────────────────────────────────────────────────────────────────────

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

// ─── Genkit Tool Export ──────────────────────────────────────────────────────────────────────────────

export const getREPLInterpreter = (ai: any) =>
  ai.defineTool(
    {
      name: 'replInterpreter',
      description:
        "Executes a Python data analysis script in a secure REPL sandbox (Python Sandbox). " +
        "The environment already has pre-loaded objects: " +
        "- `pd` (Pandas), `np` (NumPy), `json` " +
        "- `load_csv('filename.csv')`: loads a file from the data/ folder into a DataFrame " +
        "- `query_neo4j(cypher_str)`: executes deterministic Cypher on the knowledge graph " +
        "- `query_sql(sql_str)`: executes SQL (not recommended as it is not configured by default) " +
        "Use this tool to bundle multiple complex explorations into a single script instead of chaining " +
        "multiple sequential requests.",
      inputSchema: z.object({
        script: z
          .string()
          .describe("Python source code to execute in the REPL (e.g., `df = load_csv('diabetes_data_upload.csv'); print(df.describe())`)"),
        timeoutMs: z
          .number()
          .int()
          .min(1000)
          .max(30000)
          .default(10000)
          .describe("Execution timeout in ms (default: 10000)"),
      }),
      outputSchema: z.any(),
    },
    async (input: { script: string; timeoutMs: number }): Promise<REPLResult> => {
      const startTime = Date.now();

      logger.info(`⚡ [REPLInterpreter] Launching script in REPL Sandbox...`);

      if (!fs.existsSync(REPL_SCRIPT)) {
        return {
          status: 'ERROR',
          output: '',
          error: `[REPLInterpreter] Script repl_sandbox.py introuvable : ${REPL_SCRIPT}`,
        };
      }

      // Temporary input and output files
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
            error: '[REPLInterpreter] The sandbox did not produce an output file.',
          };
        }

        const rawResult = JSON.parse(fs.readFileSync(tmpOutput, 'utf-8'));
        const executionTimeMs = Date.now() - startTime;

        logger.info(
          `      [REPLInterpreter] Execution completed in ${executionTimeMs}ms — ` +
          `status: ${rawResult.status}`,
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
        logger.error({ err }, `❌ [REPLInterpreter] Execution error: ${err.message}`);
        return {
          status: 'ERROR',
          output: '',
          error: `REPL Error: ${err.message}`,
          executionTimeMs,
        };
      } finally {
        if (fs.existsSync(tmpInput))  fs.unlinkSync(tmpInput);
        if (fs.existsSync(tmpOutput)) fs.unlinkSync(tmpOutput);
      }
    },
  );
