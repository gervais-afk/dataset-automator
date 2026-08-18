import * as fs from 'fs';
import * as path from 'path';
import pino from 'pino';

const logger = pino({ transport: { target: 'pino-pretty' } });

export function loadEnv() {
  const envPath = path.resolve(__dirname, '../../.env');
  if (fs.existsSync(envPath)) {
    const lines = fs.readFileSync(envPath, 'utf-8').split('\n');
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith('#')) continue;
      const index = trimmed.indexOf('=');
      if (index > 0) {
        const key = trimmed.substring(0, index).trim();
        const val = trimmed.substring(index + 1).trim().replace(/^['"]|['"]$/g, ''); // strip quotes
        process.env[key] = val;
      }
    }
    logger.info(`✅ Loaded environment variables from: ${envPath}`);
  } else {
    logger.warn(`⚠️ Warning: .env file not found at: ${envPath}`);
  }
}
