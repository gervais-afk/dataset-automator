/**
 * ontologySchema.ts — SOVEREIGN.BI Enterprise Context & Action Layer
 *
 * Définit les interfaces TypeScript alignées sur l'ontologie Neo4j (Cypher Natif + n10s).
 *
 * Sections :
 *   1. NOMS   : Entités, Propriétés, Concepts, Relations
 *   2. VERBES : ActionType, Proposal, ActionLog
 *   3. ABAC   : Rôles, Politiques, UserContext
 *   4. OAG    : Format de contexte structuré pour le LLM (Ontology-Augmented Generation)
 */

// =============================================================================
// SECTION 1 : NOMS — Ontologie des Entités Métier
// =============================================================================

/** Identifiant machine stable unique (Machine ID) pour une entité métier. */
export type MachineId = string;

/** Un triplet sémantique explicite (Sujet → Prédicat → Objet). */
export interface SemanticTriple {
  subject: string;   // MID ou nom de l'entité source
  predicate: string; // Nom de la relation (ex: "FOURNIT", "REMPLACE")
  object: string;    // MID ou nom de l'entité cible
  weight?: number;   // Poids optionnel pour le scoring de traversée
}

/** Nœud d'Entité dans le graphe de connaissances (label :Entity). */
export interface OntologyEntity {
  mid: MachineId;                       // Identifiant machine unique et stable
  name: string;                          // Nom principal de l'entité
  type: string;                          // Type (ex: "Product", "Supplier", "Invoice")
  aliases?: string[];                    // Noms alternatifs pour la résolution d'entités
  properties?: Record<string, unknown>;  // Attributs métier supplémentaires
  roles?: string[];                      // Rôles ABAC autorisés à accéder à cette entité
}

/** Nœud de Concept sémantique (label :Concept, compatible RDF/SKOS). */
export interface OntologyConcept {
  uri: string;          // URI unique du concept (compatible W3C / n10s)
  prefLabel: string;    // Libellé principal (SKOS prefLabel)
  altLabels?: string[]; // Libellés alternatifs (SKOS altLabel)
  definition?: string;  // Définition du concept
  broader?: string;     // URI du concept parent (hiérarchie SKOS)
  narrower?: string[];  // URI des concepts enfants
}

/** Relation directionnelle entre deux entités dans le graphe. */
export interface OntologyRelation {
  sourceId: MachineId;
  targetId: MachineId;
  type: string;                          // Ex: "FOURNIT", "REMPLACE", "DEPOND_DE"
  properties?: Record<string, unknown>;
}

// =============================================================================
// SECTION 2 : VERBES — Ontologie des Actions, Propositions et Journal
// =============================================================================

/** Niveau de risque d'une action métier. */
export type RiskLevel = 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

/** Type d'action autorisée (nœud :ActionType dans Neo4j). */
export interface ActionType {
  code: string;           // Ex: "STOCK_REORDER"
  label: string;          // Libellé lisible
  description: string;
  riskLevel: RiskLevel;
  requiresHuman: boolean;   // Validation humaine obligatoire
  guardrailCheck: boolean;  // Exécution des garde-fous DataGuard requise
}

/** Statut d'une proposition d'action. */
export type ProposalStatus =
  | 'PENDING_GUARDRAIL'   // En attente de vérification par DataGuard
  | 'PENDING_HUMAN'       // En attente de validation humaine
  | 'APPROVED'            // Approuvée, prête pour exécution
  | 'REJECTED'            // Rejetée par garde-fou ou humain
  | 'EXECUTED'            // Exécutée avec succès dans le système cible
  | 'FAILED';             // Échec lors de l'exécution

/** Proposition d'action générée par un agent IA (nœud :Proposal dans Neo4j). */
export interface ActionProposal {
  proposalId: string;
  actionType: string;                    // Code de l'action (:ActionType.code)
  payload: Record<string, unknown>;      // Données de l'action
  context?: string;                      // Contexte textuel de la décision IA
  agentId: string;                       // Identifiant de l'agent IA à l'origine
  userRole: string;                      // Rôle ABAC de l'utilisateur déclencheur
  status: ProposalStatus;
  guardrailScore?: number;               // Score de sécurité retourné par DataGuard (0–100)
  guardrailMessage?: string;             // Message explicatif du garde-fou
  humanApprovedBy?: string;             // Identifiant de l'approbateur humain
  createdAt: string;                     // ISO 8601 timestamp de création
  updatedAt?: string;                    // ISO 8601 timestamp de dernière mise à jour
}

/** Entrée immuable du journal d'actions (nœud :ActionLog dans Neo4j). */
export interface ActionLogEntry {
  logId: string;
  proposalId: string;                    // Référence à la :Proposal d'origine
  actionType: string;
  status: 'SUCCESS' | 'FAILED' | 'BLOCKED';
  executedBy: string;                    // ID de l'agent ou de l'humain exécutant
  executedAt: string;                    // ISO 8601 timestamp d'exécution
  inputPayload: Record<string, unknown>; // Données d'entrée (immuables)
  outputSummary: string;
  errorMessage?: string;
}

// =============================================================================
// SECTION 3 : ABAC — Attribute-Based Access Control
// =============================================================================

/** Definition of an ABAC role (:Role node in Neo4j). */
export interface OntologyRole {
  code: string;
  label: string;
  allowedActions: string[]; // Codes of authorized :ActionType
}

/** User context injected into each request for ABAC filtering. */
export interface UserContext {
  userId: string;
  userRole: string;  // ABAC role code (e.g., "MANAGER")
  agentId?: string;  // If user = AI agent
  sessionId: string;
}

// =============================================================================
// SECTION 4 : OAG — Ontology-Augmented Generation Context
// Structured format provided to the LLM (replaces raw text blocks from classic RAG).
// =============================================================================

/** A "hop" in a multi-hop graph traversal. */
export interface GraphHop {
  fromEntity: string;
  relationLabel: string;
  toEntity: string;
  properties?: Record<string, unknown>;
}

/** Full OAG context provided to the LLM for a given request. */
export interface OAGContext {
  question: string;
  resolvedPath: GraphHop[];            // Deterministic path traversed in the graph
  entities: OntologyEntity[];          // Relevant entities extracted from the graph
  triples: SemanticTriple[];           // Semantic triples from the context
  userContext: UserContext;
  allowedActions: ActionType[];        // Actions this user can trigger
  metadata: {
    queryDepth: number;
    entitiesFound: number;
    executionTimeMs: number;
  };
}

/** Result returned by the GraphRAG Reasoner. */
export interface GraphRAGResult {
  oagContext: OAGContext;
  rawCypherQuery: string;                         // Executed Cypher query (traceability)
  suggestedProposal?: Partial<ActionProposal>;    // Suggested action proposal (if applicable)
}
