# ==========================================
# ÉTAPE 1 : BUILDER (Compilation)
# ==========================================
FROM python:3.10-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# ==========================================
# ÉTAPE 2 : RUNNER (Image de production finale)
# ==========================================
FROM python:3.10-slim AS runner

WORKDIR /app

# Création et configuration d'un utilisateur système non-root sécurisé
RUN useradd -m appuser
USER appuser

# Récupération des dépendances compilées
COPY --from=builder /root/.local /home/appuser/.local
ENV PATH=/home/appuser/.local/bin:$PATH

# Copie du code de l'API et du modèle
COPY --chown=appuser:appuser app.py .
COPY --chown=appuser:appuser model.joblib .
COPY --chown=appuser:appuser streamlit_app.py .

EXPOSE 8000
EXPOSE 8501

# Lancement par défaut du backend FastAPI
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]