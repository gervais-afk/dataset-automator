/**
 * piiSanitizer.ts - Personal and sensitive data masking utility (DLP)
 * Secures prompts sent to Cloud LLMs (e.g., Gemini) during fallback switches.
 */

export interface SanitizeResult {
  sanitizedText: string;
  maskedCount: number;
}

export class PiiSanitizer {
  // Regex to detect emails, phone numbers, and API keys
  private static EMAIL_REGEX = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g;
  private static PHONE_REGEX = /(\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,4}/g;
  private static API_KEY_REGEX = /(sk-[a-zA-Z0-9]{20,}|AIzaSy[a-zA-Z0-9_-]{33})/g;

  /**
   * Masks PII data in a given text.
   */
  public static sanitize(text: string): SanitizeResult {
    if (!text) return { sanitizedText: text, maskedCount: 0 };

    let maskedCount = 0;
    let sanitized = text;

    // 1. Mask emails
    sanitized = sanitized.replace(this.EMAIL_REGEX, (match) => {
      maskedCount++;
      return '[EMAIL_MASKED]';
    });

    // 2. Mask phone numbers
    sanitized = sanitized.replace(this.PHONE_REGEX, (match) => {
      // Avoid masking simple short numbers
      if (match.replace(/\D/g, '').length >= 8) {
        maskedCount++;
        return '[PHONE_MASKED]';
      }
      return match;
    });

    // 3. Mask API keys
    sanitized = sanitized.replace(this.API_KEY_REGEX, (match) => {
      maskedCount++;
      return '[SECRET_KEY_MASKED]';
    });

    return {
      sanitizedText: sanitized,
      maskedCount
    };
  }
}
