import axios from 'axios';
import pino from 'pino';

const logger = pino({ transport: { target: 'pino-pretty' } });

export async function getActiveModelName(fallback: string = 'google/gemma-4-12b-qat'): Promise<string> {
  try {
    const res = await axios.get('http://127.0.0.1:1234/v1/models', { timeout: 5000 });
    if (res.data && res.data.data && res.data.data.length > 0) {
      // Filtrer les modèles pour ignorer ceux qui servent aux embeddings (ex: nomic, embed, bge)
      const chatModels = res.data.data.filter((m: any) => {
        const id = (m.id || '').toLowerCase();
        return !id.includes('embed') && !id.includes('nomic') && !id.includes('bge');
      });

      if (chatModels.length > 0) {
        const activeModel = chatModels[0].id;
        logger.info(`🔍 Modèle actif de chat détecté dans LM Studio : ${activeModel}`);
        return activeModel;
      }
      
      const activeModel = res.data.data[0].id;
      logger.info(`🔍 Modèle actif détecté dans LM Studio : ${activeModel}`);
      return activeModel;
    }
  } catch (e: any) {
    logger.warn(`⚠️ Impossible de récupérer les modèles depuis LM Studio (${e.message}). Utilisation du fallback : ${fallback}`);
  }
  return fallback;
}
