/**
 * entityReconciler.ts — SOVEREIGN.BI Enterprise Context & Action Layer
 *
 * Genkit tool exposing Entity Resolution via the Python entity_resolver.py script.
 *
 * Allows the AI agent to:
 *  1. Submit a list of raw entities (names, types, sources) for reconciliation
 *  2. Obtain resolved stable MIDs + the deduplication report
 *  3. New entities are automatically inserted into Neo4j
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

const RESOLVER_SCRIPT = path.resolve(
  __dirname, '..', '..', '..', 'py-executors', 'src', 'tools', 'entity_resolver.py',
);

// ─── Types ────────────────────────────────────────────────────────────────────

export interface RawEntityInput {
  name: string;
  type: string;
  source: string;
  aliases?: string[];
  properties?: Record<string, unknown>;
}

export interface ResolutionResultOutput {
  raw_name: string;
  status: 'MATCHED' | 'NEW' | 'AMBIGUOUS';
  resolved_mid: string | null;
  resolved_name: string | null;
  similarity_score: number;
  matched_alias: string | null;
  is_new: boolean;
  aliases_added: string[];
}

// ─── Genkit Tool Export ─────────────────────────────────────────────────────────────────────

export const getEntityReconciler = (ai: any) =>
  ai.defineTool(
    {
      name: 'entityReconciler',
      description:
        "Reconciles raw entities from heterogeneous sources (ERP, CRM, Excel, PDF) " +
        "with canonical entities in the Neo4j knowledge graph. " +
        "Uses a fuzzy matching algorithm (rapidfuzz) to identify duplicates, " +
        "assigns a stable Machine ID (MID) to each entity, and enriches aliases without overwriting " +
        "existing data. " +
        "Returns the resolution status (MATCHED/NEW/AMBIGUOUS) and the MID for each submitted entity. " +
        "Use when receiving data from a new source and needing to integrate it " +
        "into the ontology without creating duplicates.",
      inputSchema: z.object({
        entities: z
          .array(
            z.object({
              name:       z.string().describe("Raw entity name"),
              type:       z.string().describe("Entity type (e.g., 'Supplier', 'GIC', 'Product')"),
              source:     z.string().describe("Data source (e.g., 'ERP_SAP', 'CRM_Salesforce')"),
              aliases:    z.array(z.string()).optional().describe("Known alternative names"),
              properties: z.record(z.unknown()).optional().describe("Additional business attributes"),
            }),
          )
          .min(1)
          .max(100)
          .describe("List of raw entities to reconcile (max 100 per call)"),
        similarityThreshold: z
          .number()
          .int()
          .min(50)
          .max(100)
          .default(85)
          .describe("Fuzzy similarity threshold to consider two entities identical (50–100, default: 85)"),
        dryRun: z
          .boolean()
          .default(false)
          .describe("If true, simulates resolution without writing to Neo4j"),
      }),
      outputSchema: z.any(),
    },
    async (input: {
      entities: RawEntityInput[];
      similarityThreshold: number;
      dryRun: boolean;
    }): Promise<{ results: ResolutionResultOutput[]; summary: object } | { error: string }> => {

      logger.info(
        `🔗 [EntityReconciler] Starting reconciliation — ${input.entities.length} entities, ` +
        `threshold: ${input.similarityThreshold}%, dry-run: ${input.dryRun}`,
      );

      // ── Verify Python script exists ──────────────────────────────────────────────
      if (!fs.existsSync(RESOLVER_SCRIPT)) {
        return { error: `[EntityReconciler] Script entity_resolver.py not found: ${RESOLVER_SCRIPT}` };
      }

      // Create temporary files for data exchange
      const tmpInput  = path.join(os.tmpdir(), `entity_input_${Date.now()}.json`);
      const tmpOutput = path.join(os.tmpdir(), `entity_output_${Date.now()}.json`);

      // Convert entities to format compatible with entity_resolver.py
      const entitiesForPython = input.entities.map(e => ({
        name:       e.name,
        type:       e.type,
        source:     e.source,
        aliases:    e.aliases || [],
        properties: e.properties || {},
      }));

      fs.writeFileSync(tmpInput, JSON.stringify(entitiesForPython, null, 2), 'utf-8');

      try {
        // Neo4j URI configuration logic for subprocess execution
        const neo4jUri = process.env.NEO4J_URI || 'bolt://127.0.0.1:7687';
        const neo4jUser = process.env.NEO4J_USER || 'neo4j';
        const neo4jPassword = process.env.NEO4J_PASSWORD || 'password123';

        // Subprocess Python call (same pattern as guardrailAuditor.ts)
        const args = [
          RESOLVER_SCRIPT,
          '--input',     tmpInput,
          '--threshold', String(input.similarityThreshold),
          '--output',    tmpOutput,
          '--verbose',
        ];

        if (input.dryRun) args.push('--dry-run');

        await execFileAsync(PYTHON_EXE, args, {
          maxBuffer: 1024 * 1024 * 10,
          env: {
            ...process.env,
            NEO4J_URI: neo4jUri,
            NEO4J_USER: neo4jUser,
            NEO4J_PASSWORD: neo4jPassword
          }
        });

        // Read results
        if (!fs.existsSync(tmpOutput)) {
          logger.warn('[EntityReconciler] No output file found — results unavailable');
          return {
            results: [],
            summary: {
              total:   input.entities.length,
              matched: 0,
              new:     0,
              message: 'Reconciliation completed (results not exported — check --output)',
            },
          };
        }

        const rawResults: ResolutionResultOutput[] = JSON.parse(
          fs.readFileSync(tmpOutput, 'utf-8'),
        );

        // Calculate summary
        const matched   = rawResults.filter(r => r.status === 'MATCHED').length;
        const newCount  = rawResults.filter(r => r.status === 'NEW').length;
        const ambiguous = rawResults.filter(r => r.status === 'AMBIGUOUS').length;

        logger.info(
          `✅  [EntityReconciler] Completed — ` +
          `${matched} matched, ${newCount} new, ${ambiguous} ambiguous`,
        );

        return {
          results: rawResults,
          summary: {
            total:     rawResults.length,
            matched,
            new:       newCount,
            ambiguous,
            dryRun:    input.dryRun,
            threshold: input.similarityThreshold,
          },
        };

      } catch (err: any) {
        logger.warn(
          `⚠️  [EntityReconciler] Python subprocess failed: ${err.message}. ` +
          `Returning empty result.`,
        );
        return {
          error: `Subprocess entity_resolver.py failed: ${err.message}. ` +
                 `Make sure the Python virtual environment is operational.`
        };
      } finally {
        if (fs.existsSync(tmpInput))  fs.unlinkSync(tmpInput);
        if (fs.existsSync(tmpOutput)) fs.unlinkSync(tmpOutput);
      }
    },
  );
