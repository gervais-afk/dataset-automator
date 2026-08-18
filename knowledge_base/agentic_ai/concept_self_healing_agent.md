---
type: concept
title: Self-Healing Agents
domain: agentic_ai
generated: { by: "reference_agent/gemini-3.5-flash", at: "2026-08-14T14:00:00Z" }
verified:
  - { by: "human: Nelly Gervais (@gervais-afk)", at: "2026-08-14T15:00:00Z" }
status: stable
stale_after: 2027-08-14
---

# Self-Healing Agents

**Definition**: Le Self-Healing (ou auto-correction) est un patron de conception (design pattern) d'IA agentique où un agent apprend à corriger ses propres erreurs. Lorsqu'une action ou une sortie générée par l'agent échoue face à un validateur strict (comme un validateur de schéma JSON Zod ou un interpréteur de code), l'erreur de validation est interceptée, formatée de manière explicite et réinjectée dans le prompt de l'agent lors d'un nouvel essai. Cela permet à l'agent de corriger son formatage ou ses paramètres de manière itérative sans interrompre le pipeline.

**Related Tools**: Genkit, Zod, ts-orchestrator

**Quand l'utiliser** :
- Lors de la génération de structures de données strictes (schémas JSON complexes) par un LLM (Phase 2 - Strategizing).
- Pour réparer automatiquement le code ou les arguments d'exécution physique avant de lancer des calculs lourds.

**Code Snippet** :
```typescript
// Structure simplifiée du self-healing de l'orchestrateur
export async function generateWithSelfHealing(ai, model, context, maxRetries = 3) {
  let lastError = '';
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const prompt = buildPrompt(context, lastError);
      const response = await ai.generate({
        model: model,
        prompt: prompt,
        output: { format: "json", schema: StrategySchema }
      });
      return response.output; // Validation Zod réussie
    } catch (error) {
      // Capture de l'erreur de validation Zod pour le prochain essai
      lastError = error.message;
      if (attempt === maxRetries) {
        return getFallbackStrategy(); // Repli de sécurité
      }
    }
  }
}
```
