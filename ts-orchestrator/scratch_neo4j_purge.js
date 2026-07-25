const neo4j = require('neo4j-driver');

const driver = neo4j.driver(
    'bolt://127.0.0.1:7687',
    neo4j.auth.basic('neo4j', 'password123')
);

async function purgeEpisodicMemory() {
    const session = driver.session();
    try {
        console.log("Connecté à Neo4j. Purge de la mémoire épisodique (nœuds Run)...");
        const result = await session.run(`
            MATCH (r:Run)
            DETACH DELETE r
        `);
        console.log(`Mémoire épisodique purgée : ${result.summary.counters.updates().nodesDeleted} nœud(s) Run supprimé(s).`);
    } catch (e) {
        console.error("Erreur :", e);
    } finally {
        await session.close();
        await driver.close();
        console.log("Déconnecté.");
    }
}

purgeEpisodicMemory();
