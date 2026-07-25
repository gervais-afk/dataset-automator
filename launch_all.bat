@echo off
TITLE SOVEREIGN.BI — Dataset Automator Full Launcher
COLOR 0A
cls
echo ===============================================================================
echo                🧠 SOVEREIGN.BI — DATASET AUTOMATOR LAUNCHER
echo ===============================================================================
echo.

echo 1. Verification du conteneur Docker Neo4j...
docker ps | findstr "neo4j" > nul
if %errorlevel% neq 0 (
    echo [!] Neo4j n'est pas encore demarre dans Docker. Démarrage de Neo4j...
    docker run -d --name neo4j -p 7474:7474 -p 7687:7687 -e NEO4J_AUTH=neo4j/password123 neo4j:latest
) else (
    echo [OK] Conteneur Docker Neo4j actif sur les ports 7474/7687.
)

echo.
echo 2. Verification de l'environnement Python (.venv)...
if not exist "py-executors\.venv\Scripts\python.exe" (
    echo [!] Environnement virtuel .venv non trouve. Installation avec uv...
    cd py-executors
    uv sync
    cd ..
) else (
    echo [OK] Environnement Python .venv pret.
)

echo.
echo 3. Lancement des 5 Services dans des Terminaux Dédiés...

echo    [1/5] Lancement de Firebase Emulators (Port 4000 / 8080)...
start "🔥 Firebase Emulators" cmd /k "firebase emulators:start"

echo    [2/5] Lancement de MLflow UI (Port 5000)...
start "📈 MLflow UI" cmd /k "cd workspace && ..\py-executors\.venv\Scripts\mlflow.exe ui --backend-store-uri sqlite:///mlflow.db --default-artifact-root file:///mlruns"

echo    [3/5] Lancement de Genkit Developer UI (Port 4000)...
start "🧠 Genkit Developer UI" cmd /k "cd ts-orchestrator && npx genkit start"

echo    [4/5] Lancement du Dashboard Streamlit (Port 8501)...
start "📊 Streamlit Control Center" cmd /k "cd py-executors && .venv\Scripts\streamlit.exe run src/app_dashboard.py"

echo    [5/5] Lancement de l'Orchestrateur TypeScript (Cerveau)...
start "⚡ TS Orchestrator Pipeline" cmd /k "cd ts-orchestrator && npm run dev"

echo.
echo ===============================================================================
echo [SUCCESS] TOUS LES SERVICES SONT DÉMARRÉS ET LEURS TERMINAUX SONT OUVERTS !
echo.
echo - Dashboard Streamlit  : http://localhost:8501
echo - MLflow UI (Tracking) : http://localhost:5000
echo - Genkit UI (Traces)   : http://localhost:4000
echo - Neo4j Browser        : http://localhost:7474
echo.
echo Vos terminaux restent ouverts pour afficher les logs et erreurs en temps reel.
echo ===============================================================================
pause
