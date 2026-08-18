# ===============================================================================
# DATASET AUTOMATOR — GOOGLE CLOUD RUN 1-CLICK DEPLOYMENT SCRIPT (POWERSHELL)
# ===============================================================================
param(
    [string]$ProjectId = $env:GCP_PROJECT_ID,
    [string]$Region = "europe-west1",
    [string]$ServiceName = "dataset-automator"
)

Write-Host "🚀 ===========================================================" -ForegroundColor Cyan
Write-Host "   DATASET AUTOMATOR — DÉPLOIEMENT GOOGLE CLOUD RUN" -ForegroundColor Cyan
Write-Host "===========================================================" -ForegroundColor Cyan

if (-not $ProjectId) {
    $ProjectId = Read-Host "Entrez votre Google Cloud Project ID"
}

if (-not $ProjectId) {
    Write-Host "❌ Erreur: Project ID requis pour déployer." -ForegroundColor Red
    exit 1
}

Write-Host "📌 Projet actif : $ProjectId" -ForegroundColor Green
Write-Host "📌 Région : $Region" -ForegroundColor Green
Write-Host "📌 Service : $ServiceName" -ForegroundColor Green

# 1. Configurer gcloud
Write-Host "`n[1/5] Configuration du projet GCP..." -ForegroundColor Yellow
gcloud config set project $ProjectId

# 2. Activer les API requises
Write-Host "`n[2/5] Activation des APIs Google Cloud..." -ForegroundColor Yellow
gcloud services enable `
    run.googleapis.com `
    cloudbuild.googleapis.com `
    artifactregistry.googleapis.com `
    aiplatform.googleapis.com `
    bigquery.googleapis.com

# 3. Créer le Service Account Cloud Run si inexistant
$SaName = "dataset-automator-runner"
$SaEmail = "$SaName@$ProjectId.iam.gserviceaccount.com"

Write-Host "`n[3/5] Configuration du compte de service IAM ($SaEmail)..." -ForegroundColor Yellow
gcloud iam service-accounts create $SaName `
    --display-name="Dataset Automator Cloud Run Service Account" 2>$null

# 4. Attribuer les rôles Vertex AI & BigQuery
Write-Host "   Attribution des rôles IAM (Vertex AI, BigQuery)..." -ForegroundColor Yellow
$Roles = @(
    "roles/aiplatform.user",
    "roles/bigquery.jobUser",
    "roles/bigquery.dataViewer",
    "roles/storage.objectViewer"
)

foreach ($Role in $Roles) {
    gcloud projects add-iam-policy-binding $ProjectId `
        --member="serviceAccount:$SaEmail" `
        --role=$Role --condition=None --quiet >$null
}

# 5. Build & Deploy sur Cloud Run
Write-Host "`n[4/5] Construction de l'image et déploiement sur Google Cloud Run..." -ForegroundColor Yellow
gcloud run deploy $ServiceName `
    --source . `
    --platform managed `
    --region $Region `
    --allow-unauthenticated `
    --service-account $SaEmail `
    --memory 2Gi `
    --cpu 2 `
    --min-instances 0 `
    --max-instances 5 `
    --port 8080 `
    --set-env-vars="GCP_PROJECT_ID=$ProjectId,GCP_REGION=$Region,GOOGLE_CLOUD_PROJECT=$ProjectId,GOOGLE_CLOUD_LOCATION=$Region,VERTEX_ACTIVE_MODEL=gemini-3.5-flash"

if ($LASTEXITCODE -eq 0) {
    Write-Host "`n🎉 ===========================================================" -ForegroundColor Green
    Write-Host "   DÉPLOIEMENT RÉUSSI SUR GOOGLE CLOUD RUN !" -ForegroundColor Green
    Write-Host "===========================================================" -ForegroundColor Green
    $Url = gcloud run services describe $ServiceName --platform managed --region $Region --format 'value(status.url)'
    Write-Host "`n🌐 URL PUBLIQUE POUR LE JURY DEVPOST :" -ForegroundColor Cyan
    Write-Host "   $Url" -ForegroundColor Yellow
    Write-Host "`n👉 Copiez cette URL dans votre dossier de soumission Devpost !" -ForegroundColor Green
} else {
    Write-Host "`n❌ Échec du déploiement. Vérifiez vos permissions Google Cloud." -ForegroundColor Red
}
