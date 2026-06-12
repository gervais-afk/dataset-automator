---
title: agentic-human-supervision
domain: agentic_ai
type: decision_tree
---

# Decision: Quel niveau d'intervention humaine est requis pour cette action de l'agent ?

**Root Consideration**: Niveau de risque et de réversibilité de l'action

**Branches**:
- IF Action automatisée à faible risque et réversible THEN Niveau 1 : Exécution 100% automatisée sans supervision
- IF Action modérée nécessitant un contrôle qualité THEN Niveau 2 : Supervision avec fenêtre de révision humaine (ex: validation avant de lancer un pipeline ML coûteux)
- IF Action irréversible ou à forts enjeux business/sécurité THEN Niveau 3 : Approbation humaine stricte obligatoire (ex: déploiement en production, suppression de base de données)

## Implémentation via LangGraph
Pour implémenter ce modèle de gouvernance dans `ts-orchestrator` :

```typescript
// Exemple de configuration d'un checkpointer LangGraph pour le Niveau 3
import { MemorySaver } from "@langchain/langgraph";

const memory = new MemorySaver();

// L'agent s'arrêtera ('interrupt_before') juste avant d'exécuter le noeud "deploy_model"
const app = workflow.compile({ 
    checkpointer: memory,
    interrupt_before: ["deploy_model"] // Gouvernance de Niveau 3 !
});
```

Cette structure garantit que les IA ne prennent jamais d'actions destructrices sans qu'un humain n'approuve formellement le changement d'état.
