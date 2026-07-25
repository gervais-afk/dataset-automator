import { KnowledgeGraphClient } from '../src/rag/knowledge-graph-client';

async function main() {
  console.log("⚡ Démarrage du script de test pour l'expansion Neo4j...\n");

  const client = new KnowledgeGraphClient();

  try {
    // 1. Test des Mappings de Colonnes (Feature Store)
    console.log("🔍 Test 1 : Récupération des mappings de colonnes sémantiques...");
    const orderIdMapping = await client.queryColumnMappings("order_id");
    console.log("Mapping pour 'order_id' :", orderIdMapping);
    
    if (orderIdMapping && orderIdMapping.concept === "Identifier" && orderIdMapping.action === "drop") {
      console.log("✅ Test 1 Réussi !");
    } else {
      console.log("❌ Test 1 Échoué (Le mapping order_id -> Identifier -> drop n'est pas correct).");
    }
    console.log("--------------------------------------------------\n");

    // 2. Test des Remèdes (Self-Healing)
    console.log("🔍 Test 2 : Récupération des règles de remédiation (Overfitting)...");
    const overfittingRemedy = await client.queryRemediationRules("Overfitting");
    console.log("Remède Overfitting :", overfittingRemedy);

    if (overfittingRemedy && overfittingRemedy.name === "Overfitting" && overfittingRemedy.action.includes("Optuna")) {
      console.log("✅ Test 2 Réussi !");
    } else {
      console.log("❌ Test 2 Échoué.");
    }
    console.log("--------------------------------------------------\n");

    // 3. Test de la Mémoire Épisodique (Lecture de Run initial)
    console.log("🔍 Test 3 : Lecture des runs passés depuis Neo4j...");
    const pastRuns = await client.queryPastRuns("ecommerce", "clustering");
    console.log("Runs passés trouvés pour 'ecommerce'/'clustering' :", pastRuns);

    if (pastRuns && pastRuns.length > 0 && pastRuns.some(r => r.dataset === "ecommerce_sales_34500")) {
      console.log("✅ Test 3 Réussi !");
    } else {
      console.log("❌ Test 3 Échoué.");
    }
    console.log("--------------------------------------------------\n");

    // 4. Test d'Écriture de Run (Mémoire Épisodique)
    console.log("🔍 Test 4 : Écriture d'une nouvelle exécution (Run de test)...");
    const testRunId = "run-test-temp-" + Date.now();
    const testDataset = "test_dataset_mock";
    const testDomain = "finance";
    const testTask = "regression";
    const testModel = "XGBoost Regressor";
    const testMetrics = { r2: 0.92, rmse: 0.05 };
    const testStrategy = {
      target: "target_mock",
      steps: [
        { column: "mock_col", action: "scale", reasoning: "Test code" }
      ]
    };

    await client.saveRunMetadata(
      testRunId,
      testDataset,
      testDomain,
      testTask,
      testModel,
      testMetrics,
      testStrategy
    );
    console.log(`✅ Run '${testRunId}' écrit avec succès.`);

    // Vérifier l'écriture
    console.log("🔍 Vérification de l'écriture en relisant...");
    const financeRuns = await client.queryPastRuns(testDomain, testTask);
    console.log("Runs passés trouvés pour 'finance'/'regression' :", financeRuns);

    if (financeRuns && financeRuns.some(r => r.dataset === testDataset)) {
      console.log("✅ Test 4 Réussi ! Le run a été correctement sauvegardé et relu.");
    } else {
      console.log("❌ Test 4 Échoué (Le run sauvegardé est introuvable).");
    }
    console.log("--------------------------------------------------\n");

    console.log("🎉 Tous les tests de l'expansion Neo4j ont réussi !");

  } catch (error) {
    console.error("❌ Une erreur est survenue pendant les tests :", error);
  } finally {
    await client.close();
  }
}

main();
