import neo4j, { Driver } from 'neo4j-driver';

export interface RAGContext {
  relevantConcepts: Array<{
    name: string;
    definition: string;
    category: string;
    formula?: string;
    target_column?: string;
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

function convertNeo4jTypes(obj: any): any {
  if (obj === null || obj === undefined) return obj;
  if (typeof obj === 'object') {
    if ('toNumber' in obj && typeof obj.toNumber === 'function') {
      return obj.toNumber();
    }
    if (Array.isArray(obj)) {
      return obj.map(convertNeo4jTypes);
    }
    const newObj: any = {};
    for (const key of Object.keys(obj)) {
      newObj[key] = convertNeo4jTypes(obj[key]);
    }
    return newObj;
  }
  return obj;
}

export class KnowledgeGraphClient {
  private driver: Driver | null = null;

  private async ensureConnected() {
    if (this.driver) return;
    
    const uri = process.env.NEO4J_URI || 'bolt://127.0.0.1:7687';
    const user = process.env.NEO4J_USER || 'neo4j';
    const password = process.env.NEO4J_PASSWORD || 'password123';
    
    this.driver = neo4j.driver(uri, neo4j.auth.basic(user, password));
  }

  private async runQuery(query: string, params?: any): Promise<any[]> {
    await this.ensureConnected();
    const session = this.driver!.session();
    try {
      const result = await session.run(query, params);
      const records = result.records.map((record: any) => {
        const obj: any = {};
        record.keys.forEach((key: any) => {
          obj[key] = record.get(key);
        });
        return obj;
      });
      return convertNeo4jTypes(records);
    } finally {
      await session.close();
    }
  }

  async queryForStrategy(
    userIntent: string,
    datasetProfile: any
  ): Promise<RAGContext> {
    // 1. Detect relevant domains
    const domains = this.inferDomains(datasetProfile);

    // 2. Retrieve concepts
    const conceptsResult = await this.runQuery(`
      MATCH (c:Concept)-[:BELONGS_TO]->(d:Domain)
      WHERE d.name IN ${JSON.stringify(domains)}
      RETURN c.name AS name, 
             c.definition AS definition,
             c.category AS category,
             c.token_estimate AS tokens,
             c.formula AS formula,
             c.target_column AS target_column
      ORDER BY c.token_estimate ASC
      LIMIT 10
    `);

    const concepts = conceptsResult.map(r => ({
      name: r.name,
      definition: r.definition,
      category: r.category,
      formula: r.formula || undefined,
      target_column: r.target_column || undefined
    }));

    // 3. Retrieve decision rules
    const decisionsResult = await this.runQuery(`
      MATCH (dt:DecisionTree)-[:HAS_BRANCH]->(b:DecisionBranch)
      WHERE dt.context IN ${JSON.stringify(domains)}
      RETURN dt.question AS question,
             collect({
               condition: b.condition,
               action: b.action,
               confidence: b.confidence
             }) AS branches
    `);

    const decisionRules = decisionsResult.map(r => ({
      question: r.question,
      branches: r.branches
    }));

    // 4. Retrieve procedures
    const proceduresResult = await this.runQuery(`
      MATCH (p:Procedure)-[:HAS_STEP]->(s:Step)
      WHERE p.domain IN ${JSON.stringify(domains)}
      WITH p, s ORDER BY s.order
      RETURN p.title AS title,
             collect(s.action) AS steps
      LIMIT 3
    `);

    const procedures = proceduresResult.map(r => ({
      title: r.title,
      steps: r.steps
    }));

    return { relevantConcepts: concepts, decisionRules, procedures };
  }

  async queryForGovernanceRules(): Promise<any> {
    const result = await this.runQuery(`
      MATCH (dt:DecisionTree {id: 'agentic-human-supervision'})-[:HAS_BRANCH]->(b:DecisionBranch)
      RETURN dt.question AS question,
             collect({
               condition: b.condition,
               action: b.action,
               order: b.order
             }) AS rules
    `);

    if (result.length === 0) return null;

    const record = result[0];
    return {
      question: record.question,
      rules: record.rules
    };
  }

  private inferDomains(profile: any): string[] {
    const domains = ['data_engineering']; // Always relevant

    const taskType = (profile.suggested_task_type || '').toLowerCase();

    // Exact mapping of task types to Domain node names in Neo4j
    const taskTypeMap: Record<string, string> = {
      'timeseries': 'time_series',
      'time_series': 'time_series',
      'clustering': 'clustering',
      'unsupervised': 'clustering',
      'classification': 'classification',
      'regression': 'supervised_learning',
      'anomaly_detection': 'anomaly_detection',
      'survival_analysis': 'survival',
      'survival': 'survival',
      'recommender_system': 'recommendation',
      'recommendation': 'recommendation',
      'causal_inference': 'causal_inference',
      'ab_testing': 'ab_testing',
      'optimization': 'optimization',
      'semi_supervised': 'semi_supervised',
      'reinforcement_learning': 'reinforcement_learning',
      'association_rules': 'association_rules',
      'graph_analysis': 'graph_analysis',
      'nlp': 'nlp',
      'computer_vision': 'computer_vision'
    };

    const domain = taskTypeMap[taskType];
    if (domain && !domains.includes(domain)) {
      domains.push(domain);
    }

    // Additional automatic detection
    if (profile.features?.some((f: any) => f.type === 'datetime') && !domains.includes('time_series')) {
      domains.push('time_series');
    }

    if (profile.total_rows > 50000 && !domains.includes('supervised_learning')) {
      domains.push('supervised_learning');
    }

    // Add MLOps if in production
    if (process.env.MLOPS_ENABLED === 'true') {
      domains.push('mlops');
    }

    return domains;
  }

  async saveRunMetadata(
    runId: string,
    datasetName: string,
    domainName: string,
    taskType: string,
    championModel: string,
    metrics: any,
    strategy: any,
    options?: {
      status?: 'SUCCESS' | 'PARTIAL';
      alerts?: Array<{type: string; severity: string; message?: string}>;
      nRows?: number;
      nCols?: number;
    }
  ): Promise<void> {
    const status = options?.status || 'SUCCESS';
    const alerts = options?.alerts || [];
    const nRows = options?.nRows || 0;
    const nCols = options?.nCols || 0;

    // Extract key metrics only (not full JSON) to avoid context bloat
    const metricsObj = typeof metrics === 'string' ? JSON.parse(metrics) : metrics;
    const compactMetrics = JSON.stringify({
      accuracy: metricsObj?.accuracy,
      macro_f1: metricsObj?.macro_f1,
      rmse: metricsObj?.rmse,
      r2: metricsObj?.r2,
      silhouette: metricsObj?.silhouette_score,
      cv_mean: metricsObj?.cv_mean_f1,
      score: metricsObj?.score
    });

    // Extract action names only (not full strategy JSON)
    const strategyObj = typeof strategy === 'string' ? JSON.parse(strategy) : strategy;
    const compactStrategy = JSON.stringify({
      task_type: strategyObj?.task_type,
      steps: (strategyObj?.steps || []).map((s: any) => s.action).slice(0, 5)
    });

    const query = `
      MERGE (ds:Dataset {name: $datasetName})
      SET ds.n_rows = $nRows, ds.n_cols = $nCols
      MERGE (dom:Domain {name: $domainName})
      MERGE (ds)-[:BELONGS_TO]->(dom)
      MERGE (m:Model {name: $championModel})
      MERGE (run:Run {id: $runId})
      SET run.timestamp = $timestamp,
          run.taskType = $taskType,
          run.status = $status,
          run.metrics = $metrics,
          run.strategy = $strategy,
          run.domain = $domainName
      MERGE (ds)-[:HAS_RUN]->(run)
      MERGE (run)-[:ON_DATASET]->(ds)
      MERGE (run)-[:USED_MODEL]->(m)
      MERGE (m)-[:CHAMPION_OF]->(ds)
    `;
    await this.runQuery(query, {
      datasetName, domainName, championModel, runId,
      timestamp: Date.now(), taskType, status,
      nRows, nCols,
      metrics: compactMetrics,
      strategy: compactStrategy
    });

    // Create Alert nodes and link them to the Run
    for (const alert of alerts.slice(0, 10)) { // Max 10 alerts per run
      const alertId = `alert-${runId}-${alert.type}`;
      const alertQuery = `
        MATCH (run:Run {id: $runId})
        MERGE (a:Alert {id: $alertId})
        SET a.type = $type, a.severity = $severity, a.timestamp = $timestamp
        MERGE (run)-[:RAISED]->(a)
      `;
      await this.runQuery(alertQuery, {
        runId, alertId,
        type: alert.type,
        severity: alert.severity,
        timestamp: Date.now()
      });
    }
  }

  /**
   * Retrieves the 3 most similar runs with a COMPACT summary (~30 tokens/run)
   * to avoid LLM context bloat.
   */
  async getTopSimilarRuns(domain: string, taskType: string, nRows?: number): Promise<string> {
    const records = await this.runQuery(`
      MATCH (dom:Domain {name: $domain})<-[:BELONGS_TO]-(ds:Dataset)-[:HAS_RUN]->(r:Run)
      WHERE r.taskType = $taskType AND r.status = 'SUCCESS'
      MATCH (r)-[:USED_MODEL]->(m:Model)
      OPTIONAL MATCH (r)-[:RAISED]->(a:Alert)
      WITH r, ds, m, collect(DISTINCT a.type) AS alertTypes
      RETURN ds.name AS dataset, m.name AS model,
             r.metrics AS metrics, r.timestamp AS ts,
             alertTypes AS alerts
      ORDER BY r.timestamp DESC
      LIMIT 3
    `, { domain, taskType });

    if (records.length === 0) {
      // Fallback: any domain with the same task_type
      const fallback = await this.runQuery(`
        MATCH (ds:Dataset)-[:HAS_RUN]->(r:Run {taskType: $taskType, status: 'SUCCESS'})
        MATCH (r)-[:USED_MODEL]->(m:Model)
        RETURN ds.name AS dataset, m.name AS model, r.metrics AS metrics
        ORDER BY r.timestamp DESC LIMIT 2
      `, { taskType });
      if (fallback.length === 0) return '';
      records.push(...fallback);
    }

    // COMPACT summary — max 150 tokens total
    const lines = records.map((r: any, i: number) => {
      const m = r.metrics ? JSON.parse(r.metrics) : {};
      const score = m.accuracy ?? m.macro_f1 ?? m.r2 ?? m.score ?? '?';
      const scoreStr = typeof score === 'number' ? `${(score * 100).toFixed(1)}%` : score;
      const alerts = (r.alerts || []).filter(Boolean).join(', ') || 'no alerts';
      return `  ${i+1}. [${r.dataset}] → ${r.model} (score: ${scoreStr}) | alerts: ${alerts}`;
    });

    return `\n📜 SIMILAR RUNS (episodic memory, domain: ${domain}/${taskType}) :\n${lines.join('\n')}\n`;
  }

  async queryPastRuns(domain: string, taskType: string): Promise<Array<{
    dataset: string;
    model: string;
    metrics: string;
    strategy: string;
  }>> {
    const query = `
      MATCH (d:Domain {name: $domain})<-[:BELONGS_TO]-(ds:Dataset)-[:HAS_RUN]->(r:Run {taskType: $taskType})
      MATCH (r)-[:CHAMPION_MODEL]->(m:Model)
      RETURN ds.name AS dataset, m.name AS model, r.metrics AS metrics, r.strategy AS strategy
      ORDER BY r.timestamp DESC
      LIMIT 2
    `;
    const records = await this.runQuery(query, { domain, taskType });
    if (records.length > 0) return records;

    const fallbackQuery = `
      MATCH (ds:Dataset)-[:HAS_RUN]->(r:Run {taskType: $taskType})
      MATCH (r)-[:CHAMPION_MODEL]->(m:Model)
      RETURN ds.name AS dataset, m.name AS model, r.metrics AS metrics, r.strategy AS strategy
      ORDER BY r.timestamp DESC
      LIMIT 2
    `;
    return this.runQuery(fallbackQuery, { taskType });
  }

  async queryRemediationRules(errorType: string): Promise<{
    name: string;
    description: string;
    action: string;
    code_snippet: string;
  } | null> {
    const query = `
      MATCH (rem:Remedy)
      WHERE rem.name =~ $pattern
      RETURN rem.name AS name, rem.description AS description, rem.action AS action, rem.code_snippet AS code_snippet
      LIMIT 1
    `;
    const records = await this.runQuery(query, { pattern: '(?i).*' + errorType + '.*' });
    if (records.length === 0) return null;
    return records[0];
  }

  async queryInterpretationRules(domain: string): Promise<Array<{
    name: string;
    description: string;
    guideline: string;
    business_impact: string;
  }>> {
    const query = `
      MATCH (rule:InterpretationRule)-[:BELONGS_TO]->(d:Domain)
      WHERE d.name = $domain
      RETURN rule.name AS name, rule.description AS description, rule.guideline AS guideline, rule.business_impact AS business_impact
    `;
    return this.runQuery(query, { domain });
  }

  async queryBusinessCosts(domain: string): Promise<{
    cost_FP: number;
    cost_FN: number;
    gain_TP: number;
    currency: string;
  } | null> {
    const query = `
      MATCH (bc:BusinessCost)
      WHERE bc.domain = $domain
      RETURN bc.cost_FP AS cost_FP, bc.cost_FN AS cost_FN, bc.gain_TP AS gain_TP, bc.currency AS currency
      LIMIT 1
    `;
    const records = await this.runQuery(query, { domain });
    if (records.length === 0) {
      if (domain !== 'general') {
        return this.queryBusinessCosts('general');
      }
      return null;
    }
    return records[0];
  }

  async queryConstraintsForColumn(columnName: string): Promise<Array<{
    type: string;
    value: any;
    description: string;
  }>> {
    const query = `
      MATCH (col:ColumnMapping {name: $columnName})-[:MAPS_TO]->(sc:SemanticConcept)-[:HAS_CONSTRAINT]->(c:Constraint)
      RETURN c.type AS type, c.value AS value, c.description AS description
    `;
    return this.runQuery(query, { columnName });
  }

  async queryFairnessThreshold(domain: string): Promise<{
    min_disparate_impact: number;
    max_disparate_impact: number;
    metric: string;
  } | null> {
    const query = `
      MATCH (d:Domain {name: $domain})-[:HAS_FAIRNESS_THRESHOLD]->(f:FairnessThreshold)
      RETURN f.min_disparate_impact AS min_disparate_impact, f.max_disparate_impact AS max_disparate_impact, f.metric AS metric
      LIMIT 1
    `;
    const records = await this.runQuery(query, { domain });
    if (records.length === 0) {
      if (domain !== 'general') {
        return this.queryFairnessThreshold('general');
      }
      return null;
    }
    return {
      min_disparate_impact: records[0].min_disparate_impact,
      max_disparate_impact: records[0].max_disparate_impact,
      metric: records[0].metric
    };
  }

  async queryPerformanceThreshold(domain: string): Promise<{
    min_f1: number;
    min_r2: number;
    max_overfitting_gap: number;
  } | null> {
    const query = `
      MATCH (d:Domain {name: $domain})-[:HAS_PERFORMANCE_THRESHOLD]->(t:PerformanceThreshold)
      RETURN t.min_f1 AS min_f1, t.min_r2 AS min_r2, t.max_overfitting_gap AS max_overfitting_gap
      LIMIT 1
    `;
    const records = await this.runQuery(query, { domain });
    if (records.length === 0) {
      if (domain !== 'general') {
        return this.queryPerformanceThreshold('general');
      }
      return null;
    }
    return records[0];
  }


  async saveFailedRun(
    runId: string,
    datasetName: string,
    domainName: string,
    taskType: string,
    errorType: string,
    detail: string
  ): Promise<void> {
    const query = `
      MERGE (ds:Dataset {name: $datasetName})
      MERGE (dom:Domain {name: $domainName})
      MERGE (ds)-[:BELONGS_TO]->(dom)
      MERGE (run:Run {id: $runId})
      SET run.timestamp = $timestamp,
          run.taskType = $taskType,
          run.status = "FAILED"
      MERGE (ds)-[:HAS_RUN]->(run)
      
      MERGE (a:Alert {id: "alert-" + $runId})
      SET a.type = $errorType,
          a.detail = $detail,
          a.timestamp = $timestamp
      MERGE (run)-[:FAILED_WITH]->(a)
    `;
    await this.runQuery(query, {
      runId,
      datasetName,
      domainName,
      taskType,
      errorType,
      detail,
      timestamp: Date.now()
    });
  }

  async saveResolutionRelation(failedRunId: string, successfulRunId: string): Promise<void> {
    const query = `
      MATCH (failedRun:Run {id: $failedRunId})-[:FAILED_WITH]->(a:Alert)
      MATCH (successRun:Run {id: $successfulRunId})
      MERGE (a)-[:RESOLVED_BY]->(successRun)
    `;
    await this.runQuery(query, { failedRunId, successfulRunId });
  }

  async queryPastRunFailures(domain: string, taskType: string): Promise<Array<{
    dataset: string;
    errorType: string;
    errorDetail: string;
    resolvedStrategy: string;
    resolvedModel: string;
  }>> {
    const query = `
      MATCH (d:Domain {name: $domain})<-[:BELONGS_TO]-(ds:Dataset)-[:HAS_RUN]->(failedRun:Run {taskType: $taskType})-[:FAILED_WITH]->(a:Alert)
      MATCH (a)-[:RESOLVED_BY]->(successRun:Run)-[:CHAMPION_MODEL]->(m:Model)
      RETURN ds.name AS dataset, a.type AS errorType, a.detail AS errorDetail, successRun.strategy AS resolvedStrategy, m.name AS resolvedModel
      ORDER BY failedRun.timestamp DESC
      LIMIT 3
    `;
    return this.runQuery(query, { domain, taskType });
  }



  async queryColumnMappings(columnName: string): Promise<{
    concept: string;
    definition: string;
    action: string;
  } | null> {
    const query = `
      MATCH (col:ColumnMapping {name: $columnName})-[:MAPS_TO]->(sc:SemanticConcept)-[:RECOMMENDS_ACTION]->(act:Action)
      RETURN sc.name AS concept, sc.definition AS definition, act.name AS action
      LIMIT 1
    `;
    const records = await this.runQuery(query, { columnName });
    if (records.length === 0) return null;
    return records[0];
  }

  async exportAnonymizedKnowledge(outputFilePath: string): Promise<void> {
    const query = `
      MATCH (d:Domain)<-[:BELONGS_TO]-(ds:Dataset)-[:HAS_RUN]->(r:Run)
      MATCH (r)-[:CHAMPION_MODEL]->(m:Model)
      RETURN d.name AS domain, ds.name AS dataset, r.taskType AS taskType, r.metrics AS metrics, r.strategy AS strategy, m.name AS model
    `;
    const records = await this.runQuery(query, {});
    
    const crypto = require('crypto');
    const anonymized = records.map(r => {
      const hash = crypto.createHash('sha256').update(r.dataset || '').digest('hex').substring(0, 16);
      return {
        domain: r.domain,
        datasetHash: `dataset_hash_${hash}`,
        taskType: r.taskType,
        model: r.model,
        metrics: typeof r.metrics === 'string' ? JSON.parse(r.metrics) : r.metrics,
        strategy: typeof r.strategy === 'string' ? JSON.parse(r.strategy) : r.strategy
      };
    });

    const fs = require('fs');
    fs.writeFileSync(outputFilePath, JSON.stringify(anonymized, null, 2), 'utf8');
  }

  async importSharedKnowledge(jsonFilePath: string): Promise<number> {
    const fs = require('fs');
    if (!fs.existsSync(jsonFilePath)) {
      throw new Error(`Shared knowledge file not found at: ${jsonFilePath}`);
    }

    const data = JSON.parse(fs.readFileSync(jsonFilePath, 'utf8'));
    let importedCount = 0;

    for (const item of data) {
      const runId = `run-shared-${item.datasetHash}-${item.taskType}`;
      const query = `
        MERGE (dom:Domain {name: $domain})
        MERGE (ds:Dataset {name: $datasetHash})
        MERGE (ds)-[:BELONGS_TO]->(dom)
        MERGE (m:Model {name: $model})
        MERGE (run:Run {id: $runId})
        SET run.taskType = $taskType,
            run.metrics = $metrics,
            run.strategy = $strategy,
            run.timestamp = $timestamp,
            run.shared = true
        MERGE (ds)-[:HAS_RUN]->(run)
        MERGE (run)-[:CHAMPION_MODEL]->(m)
      `;
      await this.runQuery(query, {
        domain: item.domain,
        datasetHash: item.datasetHash,
        model: item.model,
        runId,
        taskType: item.taskType,
        metrics: typeof item.metrics === 'object' ? JSON.stringify(item.metrics) : item.metrics,
        strategy: typeof item.strategy === 'object' ? JSON.stringify(item.strategy) : item.strategy,
        timestamp: Date.now()
      });
      importedCount++;
    }

    return importedCount;
  }

  async close() {
    if (this.driver) {
      await this.driver.close();
    }
    this.driver = null;
  }
}
