/**
 * entityReconciler.ts — SOVEREIGN.BI Enterprise Context & Action Layer
 *
 * Outil Genkit exposant la réconciliation d'entités (Entity Resolution) via
 * le script Python entity_resolver.py.
 *
 * Permet à l'agent IA de :
 *  1. Soumettre une liste d'entités brutes (noms, types, sources) à réconcilier
 *  2. Obtenir les MIDs stables résolus + le rapport de déduplication
 *  3. Les nouvelles entités sont automatiquement insérées dans Neo4j
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

// ─── Export de l'outil Genkit ─────────────────────────────────────────────────

export const getEntityReconciler = (ai: any) =>
  ai.defineTool(
    {
      name: 'entityReconciler',
      description:
        "Réconcilie des entités brutes provenant de sources hétérogènes (ERP, CRM, Excel, PDF) " +
        "avec les entités canoniques du graphe de connaissances Neo4j. " +
        "Utilise un algorithme de matching fuzzy (rapidfuzz) pour identifier les doublons, " +
        "attribue un Machine ID (MID) stable à chaque entité, et enrichit les aliases sans écraser " +
        "les données existantes. " +
        "Retourne le statut de résolution (MATCHED/NEW/AMBIGUOUS) et le MID pour chaque entité soumise. " +
        "À utiliser lorsqu'on reçoit des données d'une nouvelle source et qu'on doit les intégrer " +
        "dans l'ontologie sans créer de doublons.",
      inputSchema: z.object({
        entities: z
          .array(
            z.object({
              name:       z.string().describe("Nom de l'entité brute"),
              type:       z.string().describe("Type de l'entité (ex: 'Supplier', 'GIC', 'Product')"),
              source:     z.string().describe("Source des données (ex: 'ERP_SAP', 'CRM_Salesforce')"),
              aliases:    z.array(z.string()).optional().describe("Noms alternatifs connus"),
              properties: z.record(z.unknown()).optional().describe("Attributs métier additionnels"),
            }),
          )
          .min(1)
          .max(100)
          .describe("Liste des entités brutes à réconcilier (max 100 par appel)"),
        similarityThreshold: z
          .number()
          .int()
          .min(50)
          .max(100)
          .default(85)
          .describe("Seuil de similarité fuzzy pour considérer deux entités comme identiques (50–100, défaut: 85)"),
        dryRun: z
          .boolean()
          .default(false)
          .describe("Si true, simule la résolution sans écrire dans Neo4j"),
      }),
      outputSchema: z.any(),
    },
    async (input: {
      entities: RawEntityInput[];
      similarityThreshold: number;
      dryRun: boolean;
    }): Promise<{ results: ResolutionResultOutput[]; summary: object } | { error: string }> => {

      logger.info(
        `🔗 [EntityReconciler] Début réconciliation — ${input.entities.length} entités, ` +
        `seuil: ${input.similarityThreshold}%, dry-run: ${input.dryRun}`,
      );

      // ── Vérification du script Python ──────────────────────────────────────
      if (!fs.existsSync(RESOLVER_SCRIPT)) {
        return { error: `[EntityReconciler] Script entity_resolver.py introuvable : ${RESOLVER_SCRIPT}` };
      }

      // Créer des fichiers temporaires pour l'échange de données
      const tmpInput  = path.join(os.tmpdir(), `entity_input_${Date.now()}.json`);
      const tmpOutput = path.join(os.tmpdir(), `entity_output_${Date.now()}.json`);

      // Convertir les entités en format compatible avec entity_resolver.py
      const entitiesForPython = input.entities.map(e => ({
        name:       e.name,
        type:       e.type,
        source:     e.source,
        aliases:    e.aliases || [],
        properties: e.properties || {},
      }));

      fs.writeFileSync(tmpInput, JSON.stringify(entitiesForPython, null, 2), 'utf-8');

      try {
        // Logique de configuration de l'URI Neo4j pour l'exécution subprocess
        const neo4jUri = process.env.NEO4J_URI || 'bolt://127.0.0.1:7687';
        const neo4jUser = process.env.NEO4J_USER || 'neo4j';
        const neo4jPassword = process.env.NEO4J_PASSWORD || 'password123';

        // Appel via subprocess Python (même pattern que guardrailAuditor.ts)
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

        // Lire les résultats
        if (!fs.existsSync(tmpOutput)) {
          logger.warn('[EntityReconciler] Pas de fichier de sortie — résultats non disponibles');
          return {
            results: [],
            summary: {
              total:   input.entities.length,
              matched: 0,
              new:     0,
              message: 'Réconciliation effectuée (résultats non exportés — vérifiez --output)',
            },
          };
        }

        const rawResults: ResolutionResultOutput[] = JSON.parse(
          fs.readFileSync(tmpOutput, 'utf-8'),
        );

        // Calculer le résumé
        const matched   = rawResults.filter(r => r.status === 'MATCHED').length;
        const newCount  = rawResults.filter(r => r.status === 'NEW').length;
        const ambiguous = rawResults.filter(r => r.status === 'AMBIGUOUS').length;

        logger.info(
          `✅  [EntityReconciler] Terminé — ` +
          `${matched} matchés, ${newCount} nouveaux, ${ambiguous} ambigus`,
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
          `⚠️  [EntityReconciler] Subprocess Python échoué : ${err.message}. ` +
          `Retour d'un résultat vide.`,
        );
        return {
          error: `Subprocess entity_resolver.py échoué : ${err.message}. ` +
                 `Assurez-vous que l'environnement virtuel Python est opérationnel.`
        };
      } finally {
        if (fs.existsSync(tmpInput))  fs.unlinkSync(tmpInput);
        if (fs.existsSync(tmpOutput)) fs.unlinkSync(tmpOutput);
      }
    },
  );
