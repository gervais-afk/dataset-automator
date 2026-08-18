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
// Entity Resolution — resolves aliases to a stable MID
// =============================================================================

/**
 * Resolves an entity name (which may be an alias) to its stable MID in the database.
 * Searches on the primary name AND on the aliases array.
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
// ABAC — Retrieve allowed actions for a given role
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
    logger.warn(`⚠️ [ABAC] Failed to load allowed actions: ${err.message}`);
    return [];
  } finally {
    await session.close();
  }
}

// =============================================================================
// Multi-hop GraphRAG — Deterministic graph traversal (limited BFS)
// =============================================================================

/**
 * Performs a multi-hop traversal from an entity MID with ABAC filtering.
 * Returns a GraphHop path, discovered entities, and semantic triples.
 */
async function multiHopTraversal(
  driver: Driver,
  startMid: string,
  maxDepth: number,
  userRole: string,
): Promise<{ hops: GraphHop[]; entities: OntologyEntity[]; triples: SemanticTriple[] }> {
  const session = driver.session();
  try {
    // ABAC-filtered multi-hop traversal:
    // - Only entities whose `roles` contains the user's role (or `roles` is absent) are included.
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
// Genkit Tool Export
// =============================================================================

export const getGraphRAGReasoner = (ai: any) =>
  ai.defineTool(
    {
      name: 'graphRAGReasoner',
      description:
        "Performs a deterministic multi-hop traversal of the knowledge graph (GraphRAG/OAG). " +
        "Returns a structured context composed of typed entities, semantic triples, and allowed actions " +
        "based on the user's ABAC role. Use instead of classic vector RAG for complex questions " +
        "requiring multi-hop reasoning (e.g., supplier impact, data dependencies).",
      inputSchema: z.object({
        question: z
          .string()
          .describe("The business question asked by the user."),
        startEntityName: z
          .string()
          .describe(
            "Name or alias of the starting entity for graph traversal (e.g., supplier name, product name).",
          ),
        maxDepth: z
          .number()
          .int()
          .min(1)
          .max(5)
          .default(3)
          .describe(
            'Maximum multi-hop traversal depth (1–5). Default: 3.',
          ),
        userContext: z
          .object({
            userId: z.string(),
            userRole: z.string().describe(
              "User's ABAC role code (e.g., ANALYST, MANAGER, ADMIN, AI_AGENT).",
            ),
            agentId: z.string().optional(),
            sessionId: z.string(),
          })
          .describe("User context for ABAC filtering."),
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
          `🕸️  [GraphRAG] Starting multi-hop traversal from "${input.startEntityName}" ` +
          `(depth: ${input.maxDepth}, role: ${input.userContext.userRole})`,
        );

        // 1. Starting entity resolution (Entity Resolution / Alias matching)
        const startMid = await resolveEntityMid(driver, input.startEntityName);
        if (!startMid) {
          logger.warn(
            `⚠️  [GraphRAG] Entity not found: "${input.startEntityName}". ` +
            `Check the name or aliases in the graph.`,
          );
          return {
            error: `Entity "${input.startEntityName}" not found in the knowledge graph. ` +
                   `Check the entity name or its aliases.`,
          };
        }

        logger.info(`✅  [GraphRAG] Entité résolue → MID: ${startMid}`);

        // 2. Retrieve allowed ABAC actions for this role
        const allowedActions = await getAllowedActions(
          driver,
          input.userContext.userRole,
        );

        // 3. Multi-hop traversal with ABAC filtering
        const { hops, entities, triples } = await multiHopTraversal(
          driver,
          startMid,
          input.maxDepth,
          input.userContext.userRole,
        );

        const executionTimeMs = Date.now() - startTime;

        logger.info(
          `✅  [GraphRAG] Traversal complete: ${hops.length} hops, ` +
          `${entities.length} entities, ${triples.length} triples — ${executionTimeMs}ms`,
        );

        // 4. Build OAG context for the LLM
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

        // 5. Build the executed Cypher query (for traceability)
        const rawCypherQuery =
          `MATCH path = (start:Entity { mid: "${startMid}" })-[*1..${input.maxDepth}]-(neighbor:Entity) ` +
          `WHERE neighbor.roles IS NULL OR "${input.userContext.userRole}" IN neighbor.roles ` +
          `RETURN path LIMIT 50`;

        return { oagContext, rawCypherQuery };
      } catch (error: any) {
        logger.error({ error }, `❌  [GraphRAG] Traversal error: ${error.message}`);
        return { error: error.message };
      } finally {
        await driver.close();
      }
    },
  );
