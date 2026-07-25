import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListToolsRequestSchema,
} from "@modelcontextprotocol/sdk/types.js";
import neo4j from "neo4j-driver";
import * as dotenv from "dotenv";

dotenv.config();

// Initialisation du driver Neo4j
const driver = neo4j.driver(
  process.env.NEO4J_URI || "bolt://127.0.0.1:7687",
  neo4j.auth.basic(
    process.env.NEO4J_USER || "neo4j",
    process.env.NEO4J_PASSWORD || "password123"
  )
);

// Initialisation du serveur MCP
const server = new Server(
  {
    name: "neo4j-graph-rag-server",
    version: "1.0.0",
  },
  {
    capabilities: {
      tools: {},
    },
  }
);

// Définition des outils (Tools) exposés
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "execute_cypher_query",
        description: "Exécute une requête Cypher en lecture seule sur la base de données Neo4j du Graph RAG. Utile pour les recherches complexes.",
        inputSchema: {
          type: "object",
          properties: {
            query: {
              type: "string",
              description: "La requête Cypher à exécuter (ex: MATCH (n) RETURN n LIMIT 5)",
            },
          },
          required: ["query"],
        },
      },
      {
        name: "get_concept_details",
        description: "Recherche un concept spécifique par son nom et renvoie sa définition, catégorie et relations. Parfait pour le RAG sémantique.",
        inputSchema: {
          type: "object",
          properties: {
            conceptName: {
              type: "string",
              description: "Le nom exact ou partiel du concept (ex: 'Architecture Agentique à 3 Couches')",
            },
          },
          required: ["conceptName"],
        },
      },
      {
        name: "find_related_tools",
        description: "Trouve les outils (Tools) liés à un concept ou un domaine spécifique dans le graphe.",
        inputSchema: {
          type: "object",
          properties: {
            conceptName: {
              type: "string",
              description: "Le nom du concept pour lequel chercher les outils d'implémentation associés.",
            },
          },
          required: ["conceptName"],
        },
      },
      {
        name: "evaluate_decision_tree",
        description: "Récupère un arbre de décision complet (avec toutes ses conditions et actions) pour permettre à l'agent IA de prendre une décision autonome selon un contexte (ex: 'time_series', 'agentic_ai', 'machine_learning').",
        inputSchema: {
          type: "object",
          properties: {
            context: {
              type: "string",
              description: "Le contexte ou le domaine de la décision (ex: 'machine_learning', 'agentic_ai').",
            },
          },
          required: ["context"],
        },
      }
    ],
  };
});

// Implémentation de la logique des outils
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const session = driver.session();
  try {
    switch (request.params.name) {
      
      case "execute_cypher_query": {
        const query = String(request.params.arguments?.query);
        // Protection basique : forcer la lecture
        if (query.toUpperCase().includes("DELETE") || query.toUpperCase().includes("SET ") || query.toUpperCase().includes("REMOVE") || query.toUpperCase().includes("CREATE") || query.toUpperCase().includes("MERGE")) {
             return {
                 content: [{ type: "text", text: "Erreur de sécurité : Seules les requêtes MATCH/RETURN (lecture seule) sont autorisées via MCP." }],
                 isError: true,
             }
        }
        const result = await session.run(query);
        const records = result.records.map(record => {
            const obj: any = {};
            record.keys.forEach(key => obj[key] = record.get(key));
            return obj;
        });
        return {
          content: [{ type: "text", text: JSON.stringify(records, null, 2) }],
        };
      }

      case "get_concept_details": {
        const conceptName = String(request.params.arguments?.conceptName);
        const query = `
          MATCH (c:Concept)
          WHERE c.name CONTAINS $conceptName OR toLower(c.name) CONTAINS toLower($conceptName)
          OPTIONAL MATCH (c)-[r]->(target)
          RETURN c.name as Concept, c.definition as Definition, c.category as Category, type(r) as Relationship, target.name as Target
        `;
        const result = await session.run(query, { conceptName });
        const records = result.records.map(record => ({
            Concept: record.get("Concept"),
            Definition: record.get("Definition"),
            Category: record.get("Category"),
            Relationship: record.get("Relationship"),
            Target: record.get("Target")
        }));
        return {
          content: [{ type: "text", text: JSON.stringify(records, null, 2) }],
        };
      }

      case "find_related_tools": {
        const conceptName = String(request.params.arguments?.conceptName);
        const query = `
          MATCH (c:Concept)-[r:IMPLEMENTED_BY|REQUIRES|USES|EVALUATES]->(t:Tool)
          WHERE c.name CONTAINS $conceptName OR toLower(c.name) CONTAINS toLower($conceptName)
          RETURN c.name as Concept, type(r) as Relationship, t.name as Tool, r.evidence as Evidence
        `;
        const result = await session.run(query, { conceptName });
        const records = result.records.map(record => ({
            Concept: record.get("Concept"),
            Relationship: record.get("Relationship"),
            Tool: record.get("Tool"),
            Evidence: record.get("Evidence")
        }));
        return {
          content: [{ type: "text", text: JSON.stringify(records, null, 2) }],
        };
      }

      case "evaluate_decision_tree": {
        const contextArg = String(request.params.arguments?.context);
        const query = `
          MATCH (dt:DecisionTree)-[:HAS_BRANCH]->(b:DecisionBranch)
          WHERE dt.context = $contextArg OR toLower(dt.context) = toLower($contextArg)
          RETURN dt.question as Question, dt.context as Context, b.order as Order, b.condition as Condition, b.action as Action
          ORDER BY dt.id, b.order
        `;
        const result = await session.run(query, { contextArg });
        const records = result.records.map(record => ({
            Question: record.get("Question"),
            Context: record.get("Context"),
            Order: record.get("Order").toNumber ? record.get("Order").toNumber() : record.get("Order"),
            Condition: record.get("Condition"),
            Action: record.get("Action")
        }));
        return {
          content: [{ type: "text", text: JSON.stringify(records, null, 2) }],
        };
      }

      default:
        throw new Error("Outil inconnu");
    }
  } catch (error: any) {
    return {
      content: [{ type: "text", text: `Erreur Neo4j: ${error.message}` }],
      isError: true,
    };
  } finally {
    await session.close();
  }
});

// Lancement du transport
async function run() {
  // Test de connexion rapide au démarrage (non bloquant pour stdio)
  try {
      await driver.verifyConnectivity();
      // On ne log pas dans stdout car ça casse le protocole MCP Stdio
      console.error("[MCP Neo4j] Connecté à la base de données Neo4j locale avec succès !");
  } catch (err: any) {
      console.error("[MCP Neo4j] Attention: Échec de connexion à Neo4j. Vérifiez vos identifiants ou le statut de la base. Erreur:", err.message);
  }

  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error("[MCP Neo4j] Serveur MCP démarré sur l'entrée/sortie standard (stdio).");
}

run().catch((error) => {
  console.error("Erreur fatale:", error);
  process.exit(1);
});
