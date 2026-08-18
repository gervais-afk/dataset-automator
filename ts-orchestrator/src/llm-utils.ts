import axios from 'axios';
import pino from 'pino';
import { loadEnv } from './utils/envLoader';

const logger = pino({ transport: { target: 'pino-pretty' } });

export async function getActiveModelName(fallback: string = 'google/gemma-4-12b-qat'): Promise<string> {
  // Enforce environment variables are loaded
  loadEnv();
  
  const provider = process.env.LLM_PROVIDER || 'local';
  if (provider === 'openrouter') {
    const primaryModel = process.env.PRIMARY_MODEL || 'google/gemini-3.5-flash';
    logger.info(`🔍 [OpenRouter] Active model from env config: ${primaryModel}`);
    return primaryModel;
  }

  try {
    const res = await axios.get('http://127.0.0.1:1234/v1/models', { timeout: 5000 });
    if (res.data && res.data.data && res.data.data.length > 0) {
      // Filter models to ignore embedding models (e.g., nomic, embed, bge)
      const chatModels = res.data.data.filter((m: any) => {
        const id = (m.id || '').toLowerCase();
        return !id.includes('embed') && !id.includes('nomic') && !id.includes('bge');
      });

      if (chatModels.length > 0) {
        const activeModel = chatModels[0].id;
        logger.info(`🔍 Active chat model detected in LM Studio: ${activeModel}`);
        return activeModel;
      }
      
      const activeModel = res.data.data[0].id;
      logger.info(`🔍 Active model detected in LM Studio: ${activeModel}`);
      return activeModel;
    }
  } catch (e: any) {
    logger.warn(`⚠️ Unable to fetch models from LM Studio (${e.message}). Using fallback: ${fallback}`);
  }
  return fallback;
}
