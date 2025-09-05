# Multi-stage build for Daily Scribe application
# Stage 1: Build dependencies
FROM python:3.11-slim as builder

# Install build dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy and install Python dependencies
COPY requirements.txt .
# Use minimal requirements for smaller image size during development/testing
# In production, use full requirements.txt
ARG REQUIREMENTS_FILE=requirements.txt
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r ${REQUIREMENTS_FILE} && \
    # Remove unnecessary files to reduce size
    find /opt/venv -type d -name "__pycache__" -exec rm -r {} + 2>/dev/null || true && \
    find /opt/venv -type f -name "*.pyc" -delete && \
    find /opt/venv -type d -name "tests" -exec rm -r {} + 2>/dev/null || true

# Stage 2: Production image
FROM python:3.11-slim as production

# Install minimal runtime dependencies
RUN apt-get update && apt-get install -y \
    --no-install-recommends \
    cron \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean \
    && apt-get autoremove -y

# Copy virtual environment from builder stage
COPY --from=builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Create non-root user
RUN useradd --create-home --shell /bin/bash --uid 1000 appuser

# Set working directory
WORKDIR /app

# Create necessary directories with proper permissions
RUN mkdir -p /app/data /var/log/daily-scribe && \
    chown -R appuser:appuser /app /var/log/daily-scribe

# Copy application code (minimal files only)
COPY --chown=appuser:appuser src/ ./src/
COPY --chown=appuser:appuser config.json.example ./config.json.example
COPY --chown=appuser:appuser run-daily-scribe.sh ./run-daily-scribe.sh

# Make scripts executable
RUN chmod +x run-daily-scribe.sh

# Copy crontab and configure cron (as root)
COPY crontab /etc/cron.d/daily-scribe-cron
RUN chmod 0644 /etc/cron.d/daily-scribe-cron && \
    crontab -u appuser /etc/cron.d/daily-scribe-cron

# Create log files
RUN touch /var/log/cron.log /var/log/daily-scribe/app.log && \
    chown appuser:appuser /var/log/cron.log /var/log/daily-scribe/app.log

# Switch to non-root user
USER appuser

# Set environment variables
ENV PYTHONPATH=/app \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DB_PATH=/app/data/digest_history.db \
    DB_TIMEOUT=30

# Expose port
EXPOSE 8000

# Add health check using built-in python instead of external requests
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/healthz', timeout=5)" || exit 1

# Default command (can be overridden in docker-compose.yml)
CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
