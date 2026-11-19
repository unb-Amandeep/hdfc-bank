# Production Dockerfile for HDFC Bank Cyclical Accumulation Engine
FROM python:3.11-slim

# System setup & curl for container healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    sqlite3 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Set production environment flags
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8501 \
    HDFC_DATA_DIR=/app/data

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY . .

# Create persistent data & backup directories
RUN mkdir -p /app/data /app/data/backups /app/hdfc_predictor/logs /app/hdfc_predictor/reports

# Declare persistent SQLite volume
VOLUME ["/app/data"]

# Expose default dashboard port
EXPOSE 8501

# Health check endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8501/healthz || exit 1

# Default execution: start dashboard and scheduler
CMD ["python3", "-m", "hdfc_predictor.dashboard", "--port", "8501"]
