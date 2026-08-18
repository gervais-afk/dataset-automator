import { MLMetrics, DatasetProfile } from '../schemas';

export interface PerformanceThresholds {
  min_f1?: number;
  min_r2?: number;
  max_overfitting_gap?: number;
}

export interface FairnessThresholds {
  min_disparate_impact?: number;
  max_disparate_impact?: number;
}

export class Guardrail {
  
  static validateTimeSeries(metrics: MLMetrics & { pValue?: number }): boolean {
    if (metrics.pValue !== undefined && metrics.pValue > 0.05) {
      this._lastError = `Stationarity check failed: p-value (ADF Test) is ${metrics.pValue.toFixed(4)}, which is greater than 0.05.`;
      return false; // ADF test failed (non-stationary)
    }
    return true;
  }

  static validateClustering(metrics: MLMetrics & { silhouetteScore?: number }): boolean {
    if (metrics.silhouetteScore !== undefined && metrics.silhouetteScore < 0.5) {
      this._lastError = `Insufficient cluster separation: Silhouette Score = ${metrics.silhouetteScore.toFixed(2)} (Expected > 0.5).`;
      return false; // Poor cluster separation
    }
    return true;
  }

  static validateClassification(metrics: MLMetrics & { per_class_recall?: Record<string, number> }, thresholds?: PerformanceThresholds): boolean {
    const minRecall = thresholds?.min_f1 !== undefined ? thresholds.min_f1 : 0.6;
    if (metrics.per_class_recall) {
      for (const [className, recall] of Object.entries(metrics.per_class_recall)) {
        if (recall < minRecall) {
          this._lastError = `Imbalance detected: Class '${className}' is poorly predicted (Recall = ${(recall * 100).toFixed(1)}% | Expected > ${(minRecall * 100).toFixed(1)}%). Requesting rebalancing via SMOTE or class_weight.`;
          return false;
        }
      }
    }
    return true;
  }

  static validateRegression(metrics: MLMetrics & { r2?: number }, thresholds?: PerformanceThresholds): boolean {
    const minR2 = thresholds?.min_r2 !== undefined ? thresholds.min_r2 : 0.5;
    if (metrics.r2 !== undefined && metrics.r2 < minR2) {
      this._lastError = `Insufficient performance: R² score is ${metrics.r2.toFixed(2)} (Expected > ${minR2.toFixed(2)}). The model does not explain enough variance.`;
      return false;
    }
    return true;
  }

  static validateIssues(issues: any[] | undefined): boolean {
    if (issues && issues.length > 0) {
      const issueMsgs = issues.map(i => `[${i.severity}] ${i.message}`).join(" | ");
      this._lastError = `Critical issues detected by Python Muscles: ${issueMsgs}. Re-generate a strategy to fix these issues (e.g., class_weight, SMOTE, regularization, etc).`;
      return false;
    }
    return true;
  }

  static validateFairness(metrics: any, fairnessThresholds?: FairnessThresholds): boolean {
    if (metrics && metrics.fairness) {
      const minDI = fairnessThresholds?.min_disparate_impact !== undefined ? fairnessThresholds.min_disparate_impact : 0.8;
      const maxDI = fairnessThresholds?.max_disparate_impact !== undefined ? fairnessThresholds.max_disparate_impact : 1.25;
      const ratio = metrics.fairness.disparate_impact_ratio;
      if (ratio !== undefined && (ratio < minDI || ratio > maxDI)) {
        this._lastError = `Discriminatory bias detected (Fairness Audit): Disparate impact on sensitive attribute '${metrics.fairness.sensitive_attribute}' is ${ratio.toFixed(2)} (Expected between ${minDI} and ${maxDI}).`;
        return false;
      }
    }
    return true;
  }

  private static _lastError: string = "Guardrail failure: Metrics did not pass strict threshold validation.";

  static validateEvaluation(evaluation: any, thresholds?: PerformanceThresholds, fairnessThresholds?: FairnessThresholds): boolean {
    if (!evaluation) {
      this._lastError = "Python evaluation empty or not found.";
      return false;
    }
    
    // Validate Issues raised by Python (Overfitting, Ignored Classes, Instability)
    if (!this.validateIssues(evaluation.issues)) return false;
    
    // Validate raw Metrics
    const metrics = evaluation.metrics || {};
    if (metrics.accuracy !== undefined && (metrics.accuracy < 0 || metrics.accuracy > 1)) return false;
    
    // Validation Overfitting
    const maxOverfit = thresholds?.max_overfitting_gap !== undefined ? thresholds.max_overfitting_gap : 0.15;
    if (metrics.overfitting_gap !== undefined && metrics.overfitting_gap > maxOverfit) {
      this._lastError = `Overfitting detected: Overfitting gap is ${(metrics.overfitting_gap * 100).toFixed(1)}% (Expected <= ${(maxOverfit * 100).toFixed(1)}%).`;
      return false;
    }

    if (!this.validateClustering(metrics)) return false;
    if (!this.validateTimeSeries(metrics)) return false;
    if (!this.validateClassification(metrics, thresholds)) return false;
    if (!this.validateRegression(metrics, thresholds)) return false;
    if (!this.validateFairness(metrics, fairnessThresholds)) return false;
    
    return true;
  }

  static getErrorReport(): string {
    return this._lastError;
  }
}

