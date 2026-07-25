import * as fs from 'fs';
import * as path from 'path';

function ingestAll() {
  const baseDir = path.join(__dirname, '..', 'knowledge_base');
  
  if (!fs.existsSync(baseDir)) {
    fs.mkdirSync(baseDir, { recursive: true });
  }

  // 1. Ingest Concepts
  const conceptsPath = path.join(__dirname, '..', 'knowledge_base', 'raw_sources', 'concepts.json');
  if (fs.existsSync(conceptsPath)) {
    const rawData = JSON.parse(fs.readFileSync(conceptsPath, 'utf8'));
    rawData.concepts.forEach((concept: any) => {
      const domainDir = path.join(baseDir, concept.category);
      if (!fs.existsSync(domainDir)) fs.mkdirSync(domainDir, { recursive: true });

      const mdContent = `---
title: ${concept.name}
domain: ${concept.category}
type: concept
---

# ${concept.name}

**Definition**: ${concept.definition}

**Related Tools**: ${concept.related_tools ? concept.related_tools.join(', ') : 'None'}

**Sources**:
${concept.source_references ? concept.source_references.map((s: string) => `- ${s}`).join('\n') : ''}
`;
      const fileName = `concept_${concept.name.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()}.md`;
      const filePath = path.join(domainDir, fileName);
      if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, mdContent);
        console.log(`[INGEST] Created ${concept.category}/${fileName}`);
      } else {
        console.log(`[INGEST] Skipped (already exists) ${concept.category}/${fileName}`);
      }
    });
  }

  // 2. Ingest Decisions
  const decisionsPath = path.join(__dirname, '..', 'knowledge_base', 'raw_sources', 'decisions.json');
  if (fs.existsSync(decisionsPath)) {
    const rawData = JSON.parse(fs.readFileSync(decisionsPath, 'utf8'));
    rawData.decisions.forEach((decision: any) => {
      const domainDir = path.join(baseDir, decision.context);
      if (!fs.existsSync(domainDir)) fs.mkdirSync(domainDir, { recursive: true });

      let branchesText = '';
      if (decision.decision_tree && decision.decision_tree.branches) {
         branchesText = decision.decision_tree.branches.map((b: any) => `- IF ${b.condition} THEN ${b.action}`).join('\n');
      }

      const mdContent = `---
title: ${decision.id}
domain: ${decision.context}
type: decision_tree
---

# Decision: ${decision.question}

**Root Consideration**: ${decision.decision_tree?.root || ''}

**Branches**:
${branchesText}
`;
      const fileName = `decision_${decision.id.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()}.md`;
      const filePath = path.join(domainDir, fileName);
      if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, mdContent);
        console.log(`[INGEST] Created ${decision.context}/${fileName}`);
      } else {
        console.log(`[INGEST] Skipped (already exists) ${decision.context}/${fileName}`);
      }
    });
  }

  // 3. Ingest Procedures
  const proceduresPath = path.join(__dirname, '..', 'knowledge_base', 'raw_sources', 'procedures.json');
  if (fs.existsSync(proceduresPath)) {
    const rawData = JSON.parse(fs.readFileSync(proceduresPath, 'utf8'));
    rawData.procedures.forEach((proc: any) => {
      const domainDir = path.join(baseDir, proc.domain);
      if (!fs.existsSync(domainDir)) fs.mkdirSync(domainDir, { recursive: true });

      const stepsText = proc.steps ? proc.steps.map((s: any) => 
        `### Step ${s.order}: ${s.action}\n\`\`\`python\n${s.code_snippet || ''}\n\`\`\`\n**Tools**: ${s.tools_required ? s.tools_required.join(', ') : 'N/A'}`
      ).join('\n\n') : '';

      const mdContent = `---
title: ${proc.title}
domain: ${proc.domain}
type: procedure
---

# Procedure: ${proc.title}

**Objective**: ${proc.objective || ''}

## Steps
${stepsText}

**Validation/Pitfalls**: ${proc.validation || proc.pitfalls || ''}
`;
      const fileName = `procedure_${proc.title.replace(/[^a-zA-Z0-9]/g, '_').toLowerCase()}.md`;
      const filePath = path.join(domainDir, fileName);
      if (!fs.existsSync(filePath)) {
        fs.writeFileSync(filePath, mdContent);
        console.log(`[INGEST] Created ${proc.domain}/${fileName}`);
      } else {
        console.log(`[INGEST] Skipped (already exists) ${proc.domain}/${fileName}`);
      }
    });
  }
}

ingestAll();
