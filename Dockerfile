# ===============================================================================
# DATASET AUTOMATOR — GOOGLE CLOUD RUN PRODUCTION DOCKERFILE
# ===============================================================================
FROM python:3.11-slim

# System dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    STREAMLIT_SERVER_PORT=8080 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0 \
    STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_BROWSER_GATHER_USAGE_STATS=false

# Copy requirements and install
COPY py-executors/requirements_cloud.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY py-executors/src ./py-executors/src
COPY data ./data
COPY workspace ./workspace
COPY ARCHITECTURE.md ./ARCHITECTURE.md
COPY roadmap_futur.md ./roadmap_futur.md

# Expose Cloud Run port
EXPOSE 8080

# Healthcheck
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8080/_stcore/health || exit 1

# Launch Streamlit Control Center
CMD ["streamlit", "run", "py-executors/src/app_dashboard.py", "--server.port=8080", "--server.address=0.0.0.0"]
