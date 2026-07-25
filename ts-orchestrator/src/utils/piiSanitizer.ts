/**
 * piiSanitizer.ts - Utilitaire de masquage des données personnelles et sensibles (DLP)
 * Sécurise les prompts envoyés aux LLM Cloud (ex: Gemini) lors des bascules de secours.
 */

export interface SanitizeResult {
  sanitizedText: string;
  maskedCount: number;
}

export class PiiSanitizer {
  // Regex pour détecter emails, numéros de téléphone et clés d'API
  private static EMAIL_REGEX = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  private static PHONE_REGEX = /(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}/g;
  private static API_KEY_REGEX = /(sk-[a-zA-Z0-9]{20,}|AIzaSy[a-zA-Z0-9_-]{33})/g;

  /**
   * Masque les données PII dans un texte donné.
   */
  public static sanitize(text: string): SanitizeResult {
    if (!text) return { sanitizedText: text, maskedCount: 0 };

    let maskedCount = 0;
    let sanitized = text;

    // 1. Masquer les emails
    sanitized = sanitized.replace(this.EMAIL_REGEX, (match) => {
      maskedCount++;
      return '[EMAIL_MASQUÉ]';
    });

    // 2. Masquer les téléphones
    sanitized = sanitized.replace(this.PHONE_REGEX, (match) => {
      // Éviter de masquer les simples nombres courts
      if (match.replace(/\D/g, '').length >= 8) {
        maskedCount++;
        return '[TÉLÉPHONE_MASQUÉ]';
      }
      return match;
    });

    // 3. Masquer les clés API
    sanitized = sanitized.replace(this.API_KEY_REGEX, (match) => {
      maskedCount++;
      return '[CLÉ_SECRET_MASQUÉE]';
    });

    return {
      sanitizedText: sanitized,
      maskedCount
    };
  }
}
