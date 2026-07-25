import { z } from 'genkit';
import neo4j, { Driver } from 'neo4j-driver';
import pino from 'pino';
import {
  OAGContext,
  GraphRAGResult,
  GraphHop,
  OntologyEntity,
  SemanticTriple,
  UserContext,
  ActionType,
} from '../contexts/ontologySchema';

const logger = pino({ transport: { target: 'pino-pretty' } });

// =============================================================================
// Helpers Neo4j
// =============================================================================

function createDriver(): Driver {
  const uri      = process.env.NEO4J_URI      || 'bolt://127.0.0.1:7687';
  const user     = process.env.NEO4J_USER     || 'neo4j';
  const password = process.env.NEO4J_PASSWORD || 'password123';
  return neo4j.driver(uri, neo4j.auth.basic(user, password), {
    encrypted: 'ENCRYPTION_OFF',
  });
}

// =============================================================================
// Entity Resolution — résolution des alias vers un MID stable
// =============================================================================

/**
 * Résout un nom d'entité (qui peut être un alias) vers son MID stable en base.
 * Effectue une recherche sur le nom principal ET sur le tableau d'aliases.
 */
async function resolveEntityMid(
  driver: Driver,
  name: string,
): Promise<string | null> {
  const session = driver.session();
  try {
    const result = await session.run(
      `MATCH (e:Entity)
       WHERE e.name = $name OR $name IN e.aliases
       RETURN e.mid AS mid LIMIT 1`,
      { name },
    );
    const firstRecord = result.records[0];
    return firstRecord ? firstRecord.get('mid') : null;
  } finally {
    await session.close();
  }
}

// =============================================================================
// ABAC — Récupération des actions autorisées pour un rôle donné
// =============================================================================

async function getAllowedActions(
  driver: Driver,
  userRole: string,
): Promise<ActionType[]> {
  const session = driver.session();
  try {
    const result = await session.run(
      `MATCH (r:Role { code: $userRole })
       UNWIND r.allowedActions AS actionCode
       MATCH (at:ActionType { code: actionCode })
       RETURN at`,
      { userRole },
    );
    return result.records.map((rec) => {
      const props = rec.get('at').properties;
      return {
        code: props.code,
        label: props.label,
        description: props.description,
        riskLevel: props.riskLevel,
        requiresHuman: props.requiresHuman,
        guardrailCheck: props.guardrailCheck,
      } as ActionType;
    });
  } catch (err: any) {
    logger.warn(`⚠️ [ABAC] Impossible de charger les actions autorisées : ${err.message}`);
    return [];
  } finally {
    await session.close();
  }
}

// =============================================================================
// Multi-hop GraphRAG — Traversée déterministe du graphe (BFS limité)
// =============================================================================

/**
 * Effectue une traversée multi-sauts depuis un MID d'entité avec filtrage ABAC.
 * Retourne un chemin de GraphHop, les entités trouvées et les triplets sémantiques.
 */
async function multiHopTraversal(
  driver: Driver,
  startMid: string,
  maxDepth: number,
  userRole: string,
): Promise<{ hops: GraphHop[]; entities: OntologyEntity[]; triples: SemanticTriple[] }> {
  const session = driver.session();
  try {
    // Traversée multi-sauts ABAC-filtrée :
    // - Seules les entités dont `roles` contient le rôle de l'utilisateur (ou `roles` est absent) sont incluses.
    const result = await session.run(
      `MATCH path = (start:Entity { mid: $startMid })-[*1..${maxDepth}]-(neighbor:Entity)
       WHERE neighbor.roles IS NULL OR $userRole IN neighbor.roles
       WITH path, nodes(path) AS pathNodes, relationships(path) AS pathRels
       LIMIT 50
       RETURN pathNodes, pathRels`,
      { startMid, userRole },
    );

    const hops: GraphHop[] = [];
    const entityMap = new Map<string, OntologyEntity>();
    const triples: SemanticTriple[] = [];

    for (const record of result.records) {
      const pathNodes = record.get('pathNodes');
      const pathRels  = record.get('pathRels');

      pathNodes.forEach((node: any) => {
        const p = node.properties;
        if (!entityMap.has(p.mid)) {
          entityMap.set(p.mid, {
            mid: p.mid,
            name: p.name,
            type: node.labels[0] || 'Entity',
            aliases: p.aliases || [],
            properties: p,
            roles: p.roles || [],
          });
        }
      });

      pathRels.forEach((rel: any, idx: number) => {
        const fromNode = pathNodes[idx]?.properties;
        const toNode   = pathNodes[idx + 1]?.properties;
        if (!fromNode || !toNode) return;

        hops.push({
          fromEntity: fromNode.name || fromNode.mid,
          relationLabel: rel.type,
          toEntity: toNode.name || toNode.mid,
          properties: rel.properties,
        });

        triples.push({
          subject: fromNode.name || fromNode.mid,
          predicate: rel.type,
          object: toNode.name || toNode.mid,
        });
      });
    }

    return { hops, entities: Array.from(entityMap.values()), triples };
  } finally {
    await session.close();
  }
}

// =============================================================================
// Export de l'outil Genkit
// =============================================================================

export const getGraphRAGReasoner = (ai: any) =>
  ai.defineTool(
    {
      name: 'graphRAGReasoner',
      description:
        "Effectue une traversée déterministe multi-sauts du graphe de connaissances (GraphRAG/OAG). " +
        "Retourne un contexte structuré composé d'entités typées, de triplets sémantiques et d'actions autorisées " +
        "selon le rôle ABAC de l'utilisateur. À utiliser à la place du RAG vectoriel classique pour les questions " +
        "complexes nécessitant un raisonnement multi-sauts (ex: impact fournisseur, dépendances de données).",
      inputSchema: z.object({
        question: z
          .string()
          .describe("La question métier posée par l'utilisateur."),
        startEntityName: z
          .string()
          .describe(
            "Nom ou alias de l'entité de départ pour la traversée du graphe (ex: nom d'un fournisseur, d'un produit).",
          ),
        maxDepth: z
          .number()
          .int()
          .min(1)
          .max(5)
          .default(3)
          .describe(
            'Profondeur maximale de la traversée multi-sauts (1–5). Par défaut : 3.',
          ),
        userContext: z
          .object({
            userId: z.string(),
            userRole: z.string().describe(
              "Code du rôle ABAC de l'utilisateur (ex: ANALYST, MANAGER, ADMIN, AI_AGENT).",
            ),
            agentId: z.string().optional(),
            sessionId: z.string(),
          })
          .describe("Contexte utilisateur pour le filtrage ABAC."),
      }),
      outputSchema: z.any(),
    },
    async (input: {
      question: string;
      startEntityName: string;
      maxDepth: number;
      userContext: { userId: string; userRole: string; agentId?: string; sessionId: string };
    }): Promise<GraphRAGResult | { error: string }> => {
      const startTime = Date.now();
      const driver = createDriver();

      try {
        logger.info(
          `🕸️  [GraphRAG] Démarrage traversée multi-sauts depuis "${input.startEntityName}" ` +
          `(profondeur: ${input.maxDepth}, rôle: ${input.userContext.userRole})`,
        );

        // 1. Résolution de l'entité de départ (Entity Resolution / Alias matching)
        const startMid = await resolveEntityMid(driver, input.startEntityName);
        if (!startMid) {
          logger.warn(
            `⚠️  [GraphRAG] Entité introuvable : "${input.startEntityName}". ` +
            `Vérifiez le nom ou les aliases dans le graphe.`,
          );
          return {
            error: `Entité "${input.startEntityName}" introuvable dans le graphe de connaissances. ` +
                   `Vérifiez le nom ou les aliases de l'entité.`,
          };
        }

        logger.info(`✅  [GraphRAG] Entité résolue → MID: ${startMid}`);

        // 2. Récupération des actions ABAC autorisées pour ce rôle
        const allowedActions = await getAllowedActions(
          driver,
          input.userContext.userRole,
        );

        // 3. Traversée multi-sauts avec filtrage ABAC
        const { hops, entities, triples } = await multiHopTraversal(
          driver,
          startMid,
          input.maxDepth,
          input.userContext.userRole,
        );

        const executionTimeMs = Date.now() - startTime;

        logger.info(
          `✅  [GraphRAG] Traversée terminée : ${hops.length} sauts, ` +
          `${entities.length} entités, ${triples.length} triplets — ${executionTimeMs}ms`,
        );

        // 4. Construction du contexte OAG pour le LLM
        const oagContext: OAGContext = {
          question: input.question,
          resolvedPath: hops,
          entities,
          triples,
          userContext: input.userContext as UserContext,
          allowedActions,
          metadata: {
            queryDepth: input.maxDepth,
            entitiesFound: entities.length,
            executionTimeMs,
          },
        };

        // 5. Construction de la requête Cypher exécutée (pour traçabilité)
        const rawCypherQuery =
          `MATCH path = (start:Entity { mid: "${startMid}" })-[*1..${input.maxDepth}]-(neighbor:Entity) ` +
          `WHERE neighbor.roles IS NULL OR "${input.userContext.userRole}" IN neighbor.roles ` +
          `RETURN path LIMIT 50`;

        return { oagContext, rawCypherQuery };
      } catch (error: any) {
        logger.error({ error }, `❌  [GraphRAG] Erreur lors de la traversée : ${error.message}`);
        return { error: error.message };
      } finally {
        await driver.close();
      }
    },
  );
