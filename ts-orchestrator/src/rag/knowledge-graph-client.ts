import neo4j, { Driver, Session } from 'neo4j-driver';

export interface RAGContext {
  relevantConcepts: Array<{
    name: string;
    definition: string;
    category: string;
  }>;
  decisionRules: Array<{
    question: string;
    branches: Array<{
      condition: string;
      action: string;
      confidence: number;
    }>;
  }>;
  procedures: Array<{
    title: string;
    steps: string[];
  }>;
}

export class KnowledgeGraphClient {
  private driver: Driver;

  constructor() {
    this.driver = neo4j.driver(
      'bolt://localhost:7687',
      neo4j.auth.basic('neo4j', 'password123') // Updated to match docker run command
    );
  }

  async queryForStrategy(
    userIntent: string,
    datasetProfile: any
  ): Promise<RAGContext> {
    const session = this.driver.session();

    try {
      // 1. Détecter les domaines pertinents
      const domains = this.inferDomains(datasetProfile);

      // 2. Récupérer les concepts (limité par token budget)
      const conceptsResult = await session.run(`
        MATCH (c:Concept)-[:BELONGS_TO]->(d:Domain)
        WHERE d.name IN $domains
        RETURN c.name AS name, 
               c.definition AS definition,
               c.category AS category,
               c.token_estimate AS tokens
        ORDER BY c.token_estimate ASC
        LIMIT 10
      `, { domains });

      const concepts = conceptsResult.records.map(r => ({
        name: r.get('name'),
        definition: r.get('definition'),
        category: r.get('category')
      }));

      // 3. Récupérer les règles de décision
      const decisionsResult = await session.run(`
        MATCH (dt:DecisionTree)-[:HAS_BRANCH]->(b:DecisionBranch)
        WHERE dt.context IN $domains
        RETURN dt.question AS question,
               collect({
                 condition: b.condition,
                 action: b.action,
                 confidence: b.confidence
               }) AS branches
      `, { domains });

      const decisionRules = decisionsResult.records.map(r => ({
        question: r.get('question'),
        branches: r.get('branches')
      }));

      // 4. Récupérer les procédures (optionnel, si besoin)
      const proceduresResult = await session.run(`
        MATCH (p:Procedure)-[:HAS_STEP]->(s:Step)
        WHERE p.domain IN $domains
        WITH p, s ORDER BY s.order
        RETURN p.title AS title,
               collect(s.action) AS steps
        LIMIT 3
      `, { domains });

      const procedures = proceduresResult.records.map(r => ({
        title: r.get('title'),
        steps: r.get('steps')
      }));

      return { relevantConcepts: concepts, decisionRules, procedures };

    } finally {
      await session.close();
    }
  }

  async queryForGovernanceRules(): Promise<any> {
    const session = this.driver.session();
    try {
      const result = await session.run(`
        MATCH (dt:DecisionTree {id: 'agentic-human-supervision'})-[:HAS_BRANCH]->(b:DecisionBranch)
        RETURN dt.question AS question,
               collect({
                 condition: b.condition,
                 action: b.action,
                 order: b.order
               }) AS rules
      `);
      
      if (result.records.length === 0) return null;
      
      const record = result.records[0];
      return {
        question: record.get('question'),
        rules: record.get('rules')
      };
    } finally {
      await session.close();
    }
  }

  private inferDomains(profile: any): string[] {
    const domains = ['data_engineering']; // Toujours pertinent

    // Détection automatique
    if (profile.features?.some((f: any) => f.type === 'datetime')) {
      domains.push('time_series');
    }

    if (profile.total_rows > 50000) {
      domains.push('supervised_learning');
    }

    // Ajouter MLOps si en production
    if (process.env.MLOPS_ENABLED === 'true') {
      domains.push('mlops');
    }

    return domains;
  }

  async close() {
    await this.driver.close();
  }
}
