import axios from 'axios';
import * as fs from 'fs';
import * as path from 'path';
import pino from 'pino';

const logger = pino({ transport: { target: 'pino-pretty' } });

export class ChartInterpreter {
  /**
   * Analyse une Matrice de Confusion avec Gemma 12B Vision (Local)
   */
  static async analyzeConfusionMatrix(imagePath: string, metricsContext: any): Promise<any> {
    return this.analyzeImage(imagePath, 'confusion_matrix', metricsContext);
  }

  /**
   * Analyse un graphe de Résidus avec Gemma 12B Vision (Local)
   */
  static async analyzeResiduals(imagePath: string, metricsContext: any): Promise<any> {
    return this.analyzeImage(imagePath, 'residuals', metricsContext);
  }

  private static async analyzeImage(imagePath: string, chartType: string, metricsContext: any): Promise<any> {
    if (!fs.existsSync(imagePath)) {
      logger.error(`[Vision ERROR] Image introuvable : ${imagePath}`);
      return null;
    }

    const base64Image = fs.readFileSync(imagePath, { encoding: 'base64' });
    const mimeType = imagePath.endsWith('.png') ? 'image/png' : 'image/jpeg';
    
    logger.info(`[Vision RAG] Envoi de l'image ${chartType} à LM Studio pour double-vérification...`);

    const promptText = `
You are a Senior ML Engineer performing visual quality control on a generated ML chart.
Chart Type: ${chartType}

AUTOMATED METRICS:
${JSON.stringify(metricsContext, null, 2)}

Analyze this image and answer strictly in JSON format:
1. "visualPatterns": What patterns do you see? (Array of strings)
2. "confirmsMetrics": Does the visual confirm the math? (Boolean)
3. "additionalIssues": Are there critical VISUAL problems the math missed? (Array of strings)

Format STRICT JSON expected:
{
  "visualPatterns": ["pattern 1", "pattern 2"],
  "confirmsMetrics": true,
  "additionalIssues": []
}
`;

    const payload = {
      model: "google/gemma-4-12b",
      messages: [
        {
          role: "user",
          content: [
            { type: "text", text: promptText },
            { type: "image_url", image_url: { url: `data:${mimeType};base64,${base64Image}` } }
          ]
        }
      ],
      temperature: 0.1
    };

    try {
      const response = await axios.post('http://127.0.0.1:1234/v1/chat/completions', payload);
      const responseText = response.data.choices[0].message.content;
      
      const match = responseText.match(/\{[\s\S]*\}/);
      if (match) {
        const parsed = JSON.parse(match[0]);
        logger.info(`[Vision RAG] Analyse Visuelle terminée : ${parsed.confirmsMetrics ? 'Maths confirmées' : 'Conflit détecté !'}`);
        if (parsed.additionalIssues && parsed.additionalIssues.length > 0) {
          logger.warn(`[Vision RAG] Problèmes visuels soulevés : ${parsed.additionalIssues.join(' | ')}`);
        }
        return parsed;
      }
      return null;
    } catch (err) {
      logger.error("[Vision RAG ERROR] Échec de l'appel vision LM Studio.", err);
      return null;
    }
  }
}
