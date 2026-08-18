import * as fs from 'fs';
import * as path from 'path';
import pino from 'pino';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);
const logger = pino({ transport: { target: 'pino-pretty' } });

export class ChartInterpreter {
  /**
   * Analyzes a Confusion Matrix with the Python statistical script
   */
  static async analyzeConfusionMatrix(imagePath: string, metricsContext: any): Promise<any> {
    return this.analyzeImage(imagePath, 'confusion_matrix', metricsContext);
  }

  /**
   * Analyzes a Residuals graph with the Python statistical script
   */
  static async analyzeResiduals(imagePath: string, metricsContext: any): Promise<any> {
    return this.analyzeImage(imagePath, 'residuals', metricsContext);
  }

  private static async analyzeImage(imagePath: string, chartType: string, metricsContext: any): Promise<any> {
    if (!fs.existsSync(imagePath)) {
      logger.error(`[Vision ERROR] Image not found: ${imagePath}`);
      return null;
    }

    logger.info(`[Vision RAG] Analyzing ${chartType} chart with Python statistical script...`);

    // Resolve path to Python interpreter and validation script
    const pythonExe = path.resolve(__dirname, '..', '..', '..', 'py-executors', '.venv', 'Scripts', 'python.exe');
    const validatorScript = path.resolve(__dirname, '..', '..', '..', 'py-executors', 'src', 'tools', 'chart_validator.py');
    const metricsStr = JSON.stringify(metricsContext);

    try {
      const { stdout } = await execFileAsync(pythonExe, [
        validatorScript,
        '--image_path', imagePath,
        '--chart_type', chartType,
        '--metrics', metricsStr
      ], {
        maxBuffer: 1024 * 1024 * 10 // 10MB
      });

      const parsed = JSON.parse(stdout.trim());
      logger.info(`[Vision RAG] Statistical analysis complete: ${parsed.confirmsMetrics ? 'Math confirmed' : 'Conflict detected!'}`);
      if (parsed.additionalIssues && parsed.additionalIssues.length > 0) {
        logger.warn(`[Vision RAG] Issues raised: ${parsed.additionalIssues.join(' | ')}`);
      }
      return parsed;
    } catch (err: any) {
      logger.error({ err }, "[Vision RAG ERROR] Chart validation by Python script failed.");
      return null;
    }
  }
}
