import { genkit, z } from 'genkit';
import axios from 'axios';
import neo4j from 'neo4j-driver';
import * as fs from 'fs';
import * as path from 'path';
import * as crypto from 'crypto';
import pino from 'pino';
import { OKFReader } from '../src/rag/okfReader';

const logger = pino({
  level: 'info',
  transport: {
    target: 'pino-pretty'
  }
});

import { getActiveModelName } from '../src/llm-utils';

const ai = genkit({});

// Définition du modèle Gemma connecté à LM Studio local (pour le fallback)
const localGemmaModel = ai.defineModel(
  {
    name: 'lmstudio/gemma-4-12b',
  },
  async (request) => {
    logger.info("🤖 Modèle Gemma appelé par Genkit pour l'extraction (fallback)");
    
    let promptText = "";
    if (request.messages) {
      for (const msg of request.messages) {
        if (msg.content) {
          for (const part of msg.content) {
            if (part.text) {
              promptText += part.text + "\n";
            }
          }
        }
      }
    }
    promptText = promptText.trim();
    logger.info(`📡 Envoi de la requête à LM Studio... Taille du prompt : ${promptText.length} caractères.`);

    try {
      const activeModel = await getActiveModelName();
      const response = await axios.post('http://127.0.0.1:1234/v1/chat/completions', {
        model: activeModel,
        messages: [{ role: 'user', content: promptText }],
        temperature: request.config?.temperature || 0.2,
        thinking: false,
        reasoning: false
      }, {
        timeout: 1800000, // 30 minutes
        headers: { 'Content-Type': 'application/json' }
      });

      const replyContent = response.data.choices[0].message.content || "";
      return {
        message: {
          role: 'model',
          content: [{ text: replyContent }]
        }
      };
    } catch (err: any) {
      logger.error("❌ Erreur lors de l'appel à LM Studio :", err.message || err);
      throw err;
    }
  }
);

// Schéma Zod rigoureux pour l'extraction de connaissances
const KnowledgeExtractionSchema = z.object({
  concepts: z.array(z.object({
    name: z.string().describe("Le nom du concept, ex: 'TimeSeriesSplit' ou 'Data Leakage'"),
    category: z.string().describe("La catégorie/domaine du concept, ex: 'time_series', 'validation', 'mlops'"),
    definition: z.string().describe("La définition précise du concept basée sur le document"),
    formula: z.string().optional().describe("La formule mathématique du concept, ex: 'Weight / (Height ** 2)'"),
    target_column: z.string().optional().describe("Le nom de la colonne cible pour le calcul de la formule")
  })),
  tools: z.array(z.object({
    name: z.string().describe("Le nom exact de l'outil, ex: 'scikit-learn', 'Pandera', 'MLflow'"),
    category: z.string().describe("La catégorie de l'outil, ex: 'supervised_learning', 'mlops', 'data_validation'"),
    definition: z.string().describe("La description de ce que fait l'outil")
  })),
  relations: z.array(z.object({
    sourceName: z.string().describe("Le nom de l'entité source"),
    sourceType: z.enum(['Concept', 'Tool']).describe("Le type de l'entité source"),
    targetName: z.string().describe("Le nom de l'entité cible"),
    targetType: z.enum(['Concept', 'Tool']).describe("Le type de l'entité cible"),
    type: z.enum(['ENABLES', 'PREVENTS', 'ALTERNATIVE_TO', 'REQUIRES', 'EVALUATES', 'COMPLEMENTS', 'IMPLEMENTS']).describe("Le type de relation"),
    strength: z.number().describe("La force de la relation entre 0.0 et 1.0"),
    evidence: z.string().describe("La justification de la relation tirée du document")
  })),
  procedures: z.array(z.object({
    title: z.string().describe("Le titre de la procédure"),
    domain: z.string().describe("Le domaine de la procédure"),
    objective: z.string().describe("L'objectif de la procédure"),
    steps: z.array(z.object({
      order: z.number().describe("L'ordre de l'étape (1-indexed)"),
      action: z.string().describe("L'action à accomplir"),
      code_snippet: z.string().optional().describe("Exemple de code ou commande associé à l'étape")
    }))
  }))
});

type KnowledgeExtraction = z.infer<typeof KnowledgeExtractionSchema>;

// Helper pour extraire le JSON brut du texte de réponse
function extractJsonFromText(text: string): string {
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (jsonMatch) return jsonMatch[0];
  return text;
}

// Prompt d'extraction
function buildExtractionPrompt(markdownContent: string, lastError?: string): string {
  return `Tu es un agent expert en extraction de connaissances scientifiques et MLOps.
Analyse le document Markdown suivant et extrais tous les Concepts, Outils (Tools), Relations causales et Procédures/Étapes mentionnés.

Contenu du document Markdown :
"""
${markdownContent}
"""

Tu DOIS répondre EXCLUSIVEMENT avec un JSON valide respectant STRICTEMENT ce schéma :
{
  "concepts": [
    {
      "name": "Nom du concept",
      "category": "validation",
      "definition": "définition du concept"
    }
  ],
  "tools": [
    {
      "name": "Nom de l'outil",
      "category": "mlops",
      "definition": "définition de l'outil"
    }
  ],
  "relations": [
    {
      "sourceName": "Nom de la source",
      "sourceType": "Concept",
      "targetName": "Nom de la cible",
      "targetType": "Concept",
      "type": "ENABLES",
      "strength": 0.9,
      "evidence": "justification tirée du document"
    }
  ],
  "procedures": [
    {
      "title": "Titre de la procédure",
      "domain": "time_series",
      "objective": "objectif de la procédure",
      "steps": [
        {
          "order": 1,
          "action": "action à faire",
          "code_snippet": "code_optionnel"
        }
      ]
    }
  ]
}

RÈGLES STRICTES :
- Ne rajoute aucune clé supplémentaire.
- Ne mets aucun texte ou markdown avant ou après le JSON. Réponds directement par le JSON.
- Les types de relations autorisés sont : ENABLES, PREVENTS, ALTERNATIVE_TO, REQUIRES, EVALUATES, COMPLEMENTS, IMPLEMENTS.
- Les types d'entités autorisés sont : Concept, Tool.
- Si une section (comme tools ou relations) n'a aucun élément correspondant dans le texte, renvoie un tableau vide [] pour cette clé.
- N'inclus aucune balise <think> ou chaîne de pensée. Réponds DIRECTEMENT avec le JSON valide.`;
}

// Extraction via LLM (Self-Healing)
async function extractKnowledgeWithLLM(
  markdownContent: string,
  maxRetries: number = 3
): Promise<KnowledgeExtraction | null> {
  let lastError = '';

  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      const promptText = buildExtractionPrompt(markdownContent, lastError || undefined);

      const response = await ai.generate({
        model: localGemmaModel,
        prompt: promptText,
        config: {
          temperature: attempt === 1 ? 0.2 : 0.1
        }
      });

      const rawText = response.text;
      const jsonString = extractJsonFromText(rawText);
      const data = JSON.parse(jsonString);

      return KnowledgeExtractionSchema.parse(data);
    } catch (error: any) {
      lastError = error.message || String(error);
      logger.warn(`❌ Tentative ${attempt}/${maxRetries} LLM - Erreur d'extraction : ${lastError}`);
    }
  }
  return null;
}

// Analyseur déterministe (Regex) pour les fiches Markdown standardisées du projet (Vitesse instantanée)
function parseMarkdownDeterministically(content: string, relPath: string): KnowledgeExtraction | null {
  try {
    // 1. Strip UTF-8 BOM if present and trim
    const cleanedContent = content.replace(/^\uFEFF/, '').trim();

    // 2. Match frontmatter
    const fmMatch = cleanedContent.match(/^---\r?\n([\s\S]*?)\r?\n---/);
    if (!fmMatch) return null;
    
    const fmText = fmMatch[1];
    const frontmatter: Record<string, string> = {};
    fmText.split('\n').forEach(line => {
      const parts = line.split(':');
      if (parts.length >= 2) {
        frontmatter[parts[0].trim()] = parts.slice(1).join(':').trim();
      }
    });

    let type = frontmatter['type'];
    const domain = frontmatter['domain'];
    const title = frontmatter['title'];

    if (!domain || !title) return null;

    // Infer type if missing
    if (!type) {
      if (/## Proc\u00e9dure:/i.test(cleanedContent) || /## Procedure:/i.test(cleanedContent) || /###\s+Step\s+\d+/i.test(cleanedContent) || /^\d+\.\s/m.test(cleanedContent)) {
        type = 'procedure';
      } else if (/^\s*-\s+IF\s+.*?\s+THEN\s+/im.test(cleanedContent)) {
        type = 'decision_tree';
      } else {
        type = 'concept';
      }
    }

    const result: any = {
      concepts: [],
      tools: [],
      relations: [],
      procedures: []
    };

    if (type === 'okf') {
      const okfFilePath = path.resolve(__dirname, '../../knowledge_base', relPath);
      const parsedOKF = OKFReader.parse(okfFilePath);
      result.concepts = parsedOKF.formulas.map(f => ({
        name: f.name,
        category: domain,
        definition: f.description,
        formula: f.formula,
        target_column: f.target_column
      }));
    } else if (type === 'concept') {
      let definition = "";
      const defMatch = cleanedContent.match(/\*\*Definition\*\*:\s*(.*)/i);
      if (defMatch) {
        definition = defMatch[1].trim();
      } else {
        // Fallback sur le premier paragraphe après le titre principal #
        const bodyWithoutFm = cleanedContent.replace(/^---\r?\n[\s\S]*?\r?\n---/, '');
        const bodyLines = bodyWithoutFm.split('\n').map(l => l.trim()).filter(l => l.length > 0);
        const headerIdx = bodyLines.findIndex(l => l.startsWith('# '));
        if (headerIdx !== -1 && bodyLines[headerIdx + 1] && !bodyLines[headerIdx + 1].startsWith('#') && !bodyLines[headerIdx + 1].startsWith('-')) {
          definition = bodyLines[headerIdx + 1];
        }
      }

      const conceptName = title;
      result.concepts.push({
        name: conceptName,
        category: domain,
        definition: definition || `Concept de validation et de modélisation pour ${domain}.`
      });

      // Outils liés
      const toolsMatch = cleanedContent.match(/\*\*Related Tools\*\*:\s*(.*)/i);
      if (toolsMatch) {
        const toolsList = toolsMatch[1].split(',').map(t => t.trim());
        toolsList.forEach(toolName => {
          if (toolName && toolName !== 'N/A' && toolName !== '[]' && toolName !== 'None') {
            result.tools.push({
              name: toolName,
              category: domain,
              definition: `Outil lié au concept ${conceptName}.`
            });
            result.relations.push({
              sourceName: toolName,
              sourceType: 'Tool',
              targetName: conceptName,
              targetType: 'Concept',
              type: 'IMPLEMENTS',
              strength: 0.9,
              evidence: `L'outil ${toolName} implémente ou supporte le concept ${conceptName}.`
            });
          }
        });
      }

      // Contexte du graphe (Requires, Related, Solves)
      const requiresMatch = cleanedContent.match(/-\s+\*\*Requires\*\*:\s*\[?(.*?)\]?$/m);
      if (requiresMatch) {
        const reqList = requiresMatch[1].split(',').map(t => t.replace(/['"\[\]]/g, '').trim()).filter(t => t.length > 0);
        reqList.forEach(reqName => {
          result.relations.push({
            sourceName: conceptName,
            sourceType: 'Concept',
            targetName: reqName,
            targetType: 'Concept',
            type: 'REQUIRES',
            strength: 0.9,
            evidence: `Le concept ${conceptName} requiert le concept ${reqName}.`
          });
        });
      }

      const relatedMatch = cleanedContent.match(/-\s+\*\*Related_Concepts\*\*:\s*\[?(.*?)\]?$/m);
      if (relatedMatch) {
        const relList = relatedMatch[1].split(',').map(t => t.replace(/['"\[\]]/g, '').trim()).filter(t => t.length > 0);
        relList.forEach(relName => {
          result.relations.push({
            sourceName: conceptName,
            sourceType: 'Concept',
            targetName: relName,
            targetType: 'Concept',
            type: 'COMPLEMENTS',
            strength: 0.8,
            evidence: `Le concept ${conceptName} est lié et complémentaire à ${relName}.`
          });
        });
      }

    } else if (type === 'decision_tree') {
      const branches: any[] = [];
      const lines = cleanedContent.split('\n');
      lines.forEach(line => {
        const branchMatch = line.trim().match(/^-\s+IF\s+(.*?)\s+THEN\s+(.*)/i);
        if (branchMatch) {
          const condition = branchMatch[1].trim();
          const actionText = branchMatch[2].trim();
          branches.push({
            condition,
            action: actionText,
            order: branches.length + 1
          });
        }
      });

      result.procedures.push({
        title: title,
        domain: domain,
        objective: `Arbre de décision pour ${title}`,
        steps: branches.map(b => ({
          order: b.order,
          action: `IF ${b.condition} THEN ${b.action}`,
          code_snippet: ""
        }))
      });

    } else if (type === 'procedure') {
      const steps: any[] = [];
      const lines = cleanedContent.split('\n');
      let currentStep: any = null;
      let inCodeBlock = false;
      let codeSnippet = "";

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();
        const stepHeaderMatch = line.match(/^###\s+Step\s+(\d+):\s*(.*)/i);
        const numberedStepMatch = !stepHeaderMatch && line.match(/^(\d+)\.\s+(.*)/);
        
        if (stepHeaderMatch) {
          if (currentStep) {
            currentStep.code_snippet = codeSnippet.trim();
            steps.push(currentStep);
          }
          currentStep = {
            order: parseInt(stepHeaderMatch[1], 10),
            action: stepHeaderMatch[2].trim()
          };
          codeSnippet = "";
          inCodeBlock = false;
        } else if (numberedStepMatch) {
          if (currentStep) {
            currentStep.code_snippet = codeSnippet.trim();
            steps.push(currentStep);
          }
          currentStep = {
            order: parseInt(numberedStepMatch[1], 10),
            action: numberedStepMatch[2].trim()
          };
          codeSnippet = "";
          inCodeBlock = false;
        } else if (line.startsWith('```')) {
          inCodeBlock = !inCodeBlock;
        } else if (inCodeBlock && currentStep) {
          codeSnippet += line + "\n";
        }
      }

      if (currentStep) {
        currentStep.code_snippet = codeSnippet.trim();
        steps.push(currentStep);
      }

      let objective = `Procédure pour ${title}`;
      const objMatch = cleanedContent.match(/\*\*Objective\*\*:\s*(.*)/i);
      if (objMatch && objMatch[1].trim().length > 0) {
        objective = objMatch[1].trim();
      }

      result.procedures.push({
        title: title,
        domain: domain,
        objective: objective,
        steps: steps
      });
    }

    // Valider la structure de retour contre le schéma Zod
    return KnowledgeExtractionSchema.parse(result);
  } catch (e) {
    logger.warn(`Analyseur déterministe échoué sur ${relPath} : ${e}`);
    return null;
  }
}

// Helpers de cache et fichiers
const cachePath = path.resolve(__dirname, '../.ingested_files.json');

function loadCache(): Record<string, string> {
  if (fs.existsSync(cachePath)) {
    try {
      return JSON.parse(fs.readFileSync(cachePath, 'utf8'));
    } catch {
      return {};
    }
  }
  return {};
}

function saveCache(cache: Record<string, string>) {
  fs.writeFileSync(cachePath, JSON.stringify(cache, null, 2), 'utf8');
}

function getMD5(content: string): string {
  return crypto.createHash('md5').update(content).digest('hex');
}

function getMarkdownFiles(dir: string): string[] {
  let results: string[] = [];
  if (!fs.existsSync(dir)) return results;
  const list = fs.readdirSync(dir);
  list.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    if (stat && stat.isDirectory()) {
      results = results.concat(getMarkdownFiles(filePath));
    } else if (file.endsWith('.md')) {
      results.push(filePath);
    }
  });
  return results;
}

// Injecteur dans Neo4j
async function injectIntoNeo4j(session: any, data: KnowledgeExtraction) {
  // 1. Injecter les Domaines et Concepts
  for (const concept of data.concepts) {
    logger.info(`💾 Ingestion Concept : ${concept.name} (${concept.category})`);
    
    await session.run(`
      MERGE (d:Domain {name: $category})
    `, { category: concept.category });

    await session.run(`
      MERGE (c:Concept {name: $name})
      SET c.definition = $definition, c.category = $category, c.token_estimate = 25, c.formula = $formula, c.target_column = $target_column
      WITH c
      MATCH (d:Domain {name: $category})
      MERGE (c)-[:BELONGS_TO]->(d)
    `, {
      name: concept.name,
      definition: concept.definition,
      category: concept.category,
      formula: concept.formula || null,
      target_column: concept.target_column || null
    });
  }

  // 2. Injecter les Outils
  for (const tool of data.tools) {
    logger.info(`💾 Ingestion Outil : ${tool.name} (${tool.category})`);

    await session.run(`
      MERGE (d:Domain {name: $category})
    `, { category: tool.category });

    await session.run(`
      MERGE (t:Tool {name: $name})
      SET t.definition = $definition, t.category = $category, t.token_estimate = 20
      WITH t
      MATCH (d:Domain {name: $category})
      MERGE (t)-[:BELONGS_TO]->(d)
    `, {
      name: tool.name,
      definition: tool.definition,
      category: tool.category
    });
  }

  // 3. Injecter les Relations causales
  for (const rel of data.relations) {
    logger.info(`🔗 Ingestion Relation : (${rel.sourceName}) -[:${rel.type}]-> (${rel.targetName})`);
    
    const allowedTypes = ['ENABLES', 'PREVENTS', 'ALTERNATIVE_TO', 'REQUIRES', 'EVALUATES', 'COMPLEMENTS', 'IMPLEMENTS'];
    if (!allowedTypes.includes(rel.type)) {
      continue;
    }

    const query = `
      MATCH (src:${rel.sourceType} {name: $sourceName})
      MATCH (tgt:${rel.targetType} {name: $targetName})
      MERGE (src)-[r:${rel.type}]->(tgt)
      SET r.strength = $strength, r.evidence = $evidence
    `;

    await session.run(query, {
      sourceName: rel.sourceName,
      targetName: rel.targetName,
      strength: rel.strength,
      evidence: rel.evidence
    });
  }

  // 4. Injecter les Procédures et Étapes
  for (const proc of data.procedures) {
    logger.info(`📋 Ingestion Procédure : ${proc.title}`);

    await session.run(`
      MERGE (d:Domain {name: $domain})
    `, { domain: proc.domain });

    await session.run(`
      MERGE (p:Procedure {title: $title})
      SET p.domain = $domain, p.objective = $objective
      WITH p
      MATCH (d:Domain {name: $domain})
      MERGE (p)-[:BELONGS_TO]->(d)
    `, {
      title: proc.title,
      domain: proc.domain,
      objective: proc.objective
    });

    for (const step of proc.steps) {
      await session.run(`
        MERGE (s:Step {action: $action})
        SET s.order = $order, s.code_snippet = $codeSnippet
        WITH s
        MATCH (p:Procedure {title: $title})
        MERGE (p)-[:HAS_STEP]->(s)
      `, {
        action: step.action,
        order: step.order,
        codeSnippet: step.code_snippet || "",
        title: proc.title
      });
    }
  }
}

// Fonction principale
async function main() {
  logger.info("⚡ Démarrage du pipeline d'ingestion automatique (Hybride)...");

  // 1. Initialiser le driver Neo4j
  const passwords = ['password123', 'password'];
  let driver;

  for (const pwd of passwords) {
    const tempDriver = neo4j.driver(
      'bolt://127.0.0.1:7687',
      neo4j.auth.basic('neo4j', pwd)
    );
    try {
      await tempDriver.verifyConnectivity();
      driver = tempDriver;
      break;
    } catch (e: any) {
      await tempDriver.close();
    }
  }

  if (!driver) {
    logger.error("❌ Impossible de se connecter à Neo4j. Le conteneur Docker est-il actif ?");
    process.exit(1);
  }
  logger.info(`✅ Connecté à Neo4j avec succès !`);

  // 2. Parcourir les fichiers Markdown
  const kbDir = path.resolve(__dirname, '../../knowledge_base');
  const files = getMarkdownFiles(kbDir);
  logger.info(`🔍 ${files.length} fichiers Markdown trouvés dans la base de connaissances.`);

  const cache = loadCache();
  const session = driver.session();

  try {
    let processedCount = 0;

    for (const file of files) {
      const relPath = path.relative(kbDir, file);
      const content = fs.readFileSync(file, 'utf8');
      const hash = getMD5(content);

      if (cache[relPath] === hash) {
        logger.info(`⏭️ Ignoré (déjà traité et inchangé) : ${relPath}`);
        continue;
      }

      logger.info(`\n📝 Traitement du fichier : ${relPath}`);
      
      // Tenter le parsing déterministe d'abord (ultra-rapide)
      let extraction = parseMarkdownDeterministically(content, relPath);

      if (!extraction) {
        // En cas d'échec de structure, on bascule sur le LLM
        logger.info(`🔄 Échec de la structure fixe. Inférence LLM locale en cours...`);
        extraction = await extractKnowledgeWithLLM(content);
      }

      if (extraction) {
        logger.info(`✅ Extraction réussie pour ${relPath}`);
        await injectIntoNeo4j(session, extraction);
        cache[relPath] = hash;
        processedCount++;
      } else {
        logger.error(`❌ Échec complet d'extraction pour ${relPath}`);
      }
    }

    saveCache(cache);
    logger.info(`\n🎉 Ingestion terminée. ${processedCount} fichier(s) traité(s) et mis à jour.`);
  } catch (error) {
    logger.error({ error }, "❌ Erreur pendant l'ingestion :");
  } finally {
    await session.close();
    await driver.close();
  }
}

main();
