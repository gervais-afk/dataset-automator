import { MLMetrics, DatasetProfile } from '../schemas';

export class Guardrail {
  
  static validateTimeSeries(metrics: MLMetrics & { pValue?: number }): boolean {
    if (metrics.pValue !== undefined && metrics.pValue > 0.05) {
      this._lastError = `Échec de stationnarité : La p-value (Test ADF) est de ${metrics.pValue.toFixed(4)}, ce qui est supérieur à 0.05.`;
      return false; // ADF test failed (non-stationary)
    }
    return true;
  }

  static validateClustering(metrics: MLMetrics & { silhouetteScore?: number }): boolean {
    if (metrics.silhouetteScore !== undefined && metrics.silhouetteScore < 0.5) {
      this._lastError = `Séparation des clusters insuffisante : Silhouette Score = ${metrics.silhouetteScore.toFixed(2)} (Attendu > 0.5).`;
      return false; // Poor cluster separation
    }
    return true;
  }

  static validateClassification(metrics: MLMetrics & { per_class_recall?: Record<string, number> }): boolean {
    if (metrics.per_class_recall) {
      for (const [className, recall] of Object.entries(metrics.per_class_recall)) {
        if (recall < 0.6) {
          this._lastError = `Déséquilibre détecté : La classe '${className}' est mal prédite (Recall = ${(recall * 100).toFixed(1)}%). Demande de rééquilibrage via SMOTE ou class_weight.`;
          return false;
        }
      }
    }
    return true;
  }

  static validateRegression(metrics: MLMetrics & { r2?: number }): boolean {
    if (metrics.r2 !== undefined && metrics.r2 < 0.5) {
      this._lastError = `Performance insuffisante : Le score R² est de ${metrics.r2.toFixed(2)} (Attendu > 0.5). Le modèle n'explique pas assez la variance.`;
      return false;
    }
    return true;
  }

  static validateIssues(issues: any[] | undefined): boolean {
    if (issues && issues.length > 0) {
      const issueMsgs = issues.map(i => `[${i.severity}] ${i.message}`).join(" | ");
      this._lastError = `Problèmes critiques détectés par les Muscles Python : ${issueMsgs}. Re-générer une stratégie pour corriger ces problèmes (ex: class_weight, SMOTE, régularisation, etc).`;
      return false;
    }
    return true;
  }

  private static _lastError: string = "Guardrail failure: Metrics did not pass strict threshold validation.";

  static validateEvaluation(evaluation: any): boolean {
    if (!evaluation) {
      this._lastError = "Évaluation Python vide ou introuvable.";
      return false;
    }
    
    // Validation des Issues remontés par Python (Overfitting, Classes ignorées, Instabilité)
    if (!this.validateIssues(evaluation.issues)) return false;
    
    // Validation des Métriques brutes
    const metrics = evaluation.metrics || {};
    if (metrics.accuracy !== undefined && (metrics.accuracy < 0 || metrics.accuracy > 1)) return false;
    if (!this.validateClustering(metrics)) return false;
    if (!this.validateTimeSeries(metrics)) return false;
    if (!this.validateClassification(metrics)) return false;
    if (!this.validateRegression(metrics)) return false;
    
    return true;
  }

  static getErrorReport(): string {
    return this._lastError;
  }
}
