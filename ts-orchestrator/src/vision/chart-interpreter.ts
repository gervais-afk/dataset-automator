import * as fs from 'fs';
import * as path from 'path';
import pino from 'pino';
import { execFile } from 'child_process';
import { promisify } from 'util';

const execFileAsync = promisify(execFile);
const logger = pino({ transport: { target: 'pino-pretty' } });

export class ChartInterpreter {
  /**
   * Analyse une Matrice de Confusion avec le script statistique Python
   */
  static async analyzeConfusionMatrix(imagePath: string, metricsContext: any): Promise<any> {
    return this.analyzeImage(imagePath, 'confusion_matrix', metricsContext);
  }

  /**
   * Analyse un graphe de Résidus avec le script statistique Python
   */
  static async analyzeResiduals(imagePath: string, metricsContext: any): Promise<any> {
    return this.analyzeImage(imagePath, 'residuals', metricsContext);
  }

  private static async analyzeImage(imagePath: string, chartType: string, metricsContext: any): Promise<any> {
    if (!fs.existsSync(imagePath)) {
      logger.error(`[Vision ERROR] Image introuvable : ${imagePath}`);
      return null;
    }

    logger.info(`[Vision RAG] Analyse du graphique ${chartType} par le script statistique Python...`);

    // Résolution du chemin vers l'interpréteur Python et le script de validation
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
      logger.info(`[Vision RAG] Analyse statistique terminée : ${parsed.confirmsMetrics ? 'Maths confirmées' : 'Conflit détecté !'}`);
      if (parsed.additionalIssues && parsed.additionalIssues.length > 0) {
        logger.warn(`[Vision RAG] Problèmes soulevés : ${parsed.additionalIssues.join(' | ')}`);
      }
      return parsed;
    } catch (err: any) {
      logger.error({ err }, "[Vision RAG ERROR] Échec de la validation du graphique par le script Python.");
      return null;
    }
  }
}
