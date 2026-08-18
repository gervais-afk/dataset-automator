#!/usr/bin/env bash
# ===============================================================================
# DATASET AUTOMATOR — GOOGLE CLOUD RUN 1-CLICK DEPLOYMENT SCRIPT (BASH)
# ===============================================================================

set -e

PROJECT_ID="${GCP_PROJECT_ID:-$1}"
REGION="${GCP_REGION:-europe-west1}"
SERVICE_NAME="dataset-automator"

echo "🚀 ==========================================================="
echo "   DATASET AUTOMATOR — DÉPLOIEMENT GOOGLE CLOUD RUN"
echo "==========================================================="

if [ -z "$PROJECT_ID" ]; then
    read -p "Entrez votre Google Cloud Project ID : " PROJECT_ID
fi

if [ -z "$PROJECT_ID" ]; then
    echo "❌ Erreur: Project ID requis pour déployer."
    exit 1
fi

echo "📌 Projet actif : $PROJECT_ID"
echo "📌 Région : $REGION"
echo "📌 Service : $SERVICE_NAME"

# 1. Configurer gcloud
echo ""
echo "[1/5] Configuration du projet GCP..."
gcloud config set project "$PROJECT_ID"

# 2. Activer les API requises
echo ""
echo "[2/5] Activation des APIs Google Cloud..."
gcloud services enable \
    run.googleapis.com \
    cloudbuild.googleapis.com \
    artifactregistry.googleapis.com \
    aiplatform.googleapis.com \
    bigquery.googleapis.com

# 3. Créer le Service Account Cloud Run si inexistant
SA_NAME="dataset-automator-runner"
SA_EMAIL="${SA_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"

echo ""
echo "[3/5] Configuration du compte de service IAM ($SA_EMAIL)..."
gcloud iam service-accounts create "$SA_NAME" \
    --display-name="Dataset Automator Cloud Run Service Account" 2>/dev/null || true

# 4. Attribuer les rôles Vertex AI & BigQuery
echo "   Attribution des rôles IAM (Vertex AI, BigQuery)..."
ROLES=(
    "roles/aiplatform.user"
    "roles/bigquery.jobUser"
    "roles/bigquery.dataViewer"
    "roles/storage.objectViewer"
)

for ROLE in "${ROLES[@]}"; do
    gcloud projects add-iam-policy-binding "$PROJECT_ID" \
        --member="serviceAccount:$SA_EMAIL" \
        --role="$ROLE" --condition=None --quiet >/dev/null
done

# 5. Build & Deploy sur Cloud Run
echo ""
echo "[4/5] Construction de l'image et déploiement sur Google Cloud Run..."
gcloud run deploy "$SERVICE_NAME" \
    --source . \
    --platform managed \
    --region "$REGION" \
    --allow-unauthenticated \
    --service-account "$SA_EMAIL" \
    --memory 2Gi \
    --cpu 2 \
    --min-instances 0 \
    --max-instances 5 \
    --port 8080 \
    --set-env-vars="GCP_PROJECT_ID=$PROJECT_ID,GCP_REGION=$REGION,GOOGLE_CLOUD_PROJECT=$PROJECT_ID,GOOGLE_CLOUD_LOCATION=$REGION,VERTEX_ACTIVE_MODEL=gemini-3.5-flash"

echo ""
echo "🎉 ==========================================================="
echo "   DÉPLOIEMENT RÉUSSI SUR GOOGLE CLOUD RUN !"
echo "==========================================================="
URL=$(gcloud run services describe "$SERVICE_NAME" --platform managed --region "$REGION" --format 'value(status.url)')
echo ""
echo "🌐 URL PUBLIQUE POUR LE JURY DEVPOST :"
echo "   $URL"
echo ""
echo "👉 Copiez cette URL dans votre dossier de soumission Devpost !"
