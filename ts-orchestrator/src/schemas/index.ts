import { z } from 'zod';

export const DatasetProfileSchema = z.object({
  total_rows: z.number(),
  total_columns: z.number(),
  target_candidate: z.string().optional(),
  features: z.array(z.object({
    name: z.string(),
    type: z.enum(['numeric', 'categorical', 'datetime', 'text']),
    missing_percentage: z.number().min(0).max(100),
    cardinality: z.number().optional(),
    skewness: z.number().optional()
  }))
});

export type DatasetProfile = z.infer<typeof DatasetProfileSchema>;

export const CleaningStrategySchema = z.object({
  target: z.string(),
  steps: z.array(z.object({
    column: z.string(),
    action: z.enum([
      'drop', 'impute_mean', 'impute_median', 'impute_mode', 
      'one_hot_encode', 'label_encode', 'standardize'
    ]),
    reasoning: z.string().describe("Agent's justification for logging")
  }))
});

export type CleaningStrategy = z.infer<typeof CleaningStrategySchema>;

export const MLPipelineSchema = z.object({
  task: z.enum(['classification', 'regression', 'clustering']),
  algorithm: z.enum(['RandomForest', 'LogisticRegression', 'XGBoost', 'KMeans']),
  test_size: z.number().min(0.1).max(0.4).default(0.2),
  hyperparameters: z.record(z.any()).optional()
});

export type MLPipeline = z.infer<typeof MLPipelineSchema>;

export const MLMetricsSchema = z.object({
  accuracy: z.number().optional(),
  f1_score: z.number().optional(),
  mse: z.number().optional(),
  r2: z.number().optional()
});

export type MLMetrics = z.infer<typeof MLMetricsSchema>;
