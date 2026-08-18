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
  task_type: z.enum([
    "regression", "classification", "clustering", "timeseries",
    "anomaly_detection", "survival_analysis", "recommender_system",
    "causal_inference", "association_rules", "ab_testing",
    "semi_supervised", "optimization", "graph_analysis",
    "reinforcement_learning", "nlp", "computer_vision"
  ]).optional(),
    steps: z.array(z.object({
      column: z.string(),
      action: z.enum(["drop", "impute_mean", "impute_median", "scale", "winsorize", "k_means", "encode", "sanitize_phone", "normalize_cam_geo", "clean_fcfa", "parse_momo", "pca", "add_time_features", "formula"]),
      formula: z.string().optional().describe("Mathematical expression to evaluate (e.g., 'Weight / (Height ** 2)')"),
      reasoning: z.string().optional().describe("Agent's justification for logging")
    }))
});

export type CleaningStrategy = z.infer<typeof CleaningStrategySchema>;

export const MLPipelineSchema = z.object({
  task: z.enum([
    "regression", "classification", "clustering", "timeseries",
    "anomaly_detection", "survival_analysis", "recommender_system",
    "causal_inference", "association_rules", "ab_testing",
    "semi_supervised", "optimization", "graph_analysis",
    "reinforcement_learning", "nlp", "computer_vision"
  ]),
  algorithm: z.enum(['RandomForest', 'LogisticRegression', 'XGBoost', 'LightGBM', 'CatBoost', 'KMeans']),
  test_size: z.number().min(0.1).max(0.4).default(0.2),
  hyperparameters: z.record(z.string(), z.any()).optional()
});

export type MLPipeline = z.infer<typeof MLPipelineSchema>;

export const MLMetricsSchema = z.object({
  accuracy: z.number().optional(),
  f1_score: z.number().optional(),
  mse: z.number().optional(),
  r2: z.number().optional()
});

export type MLMetrics = z.infer<typeof MLMetricsSchema>;
