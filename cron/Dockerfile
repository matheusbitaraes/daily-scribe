# Cron Container Dockerfile
# Extends the main Daily Scribe application image to run scheduled tasks

FROM daily-scribe:latest

# Switch to root to install supercronic
USER root

# Install supercronic for better Docker cron integration
# supercronic is more reliable than system cron in containers
RUN apt-get update && \
    apt-get install -y curl && \
    curl -fsSLO "https://github.com/aptible/supercronic/releases/download/v0.2.29/supercronic-linux-amd64" && \
    echo "cd48d45c4b10f3f0bfdd3a57d054cd05ac96812b supercronic-linux-amd64" | sha1sum -c - && \
    chmod +x supercronic-linux-amd64 && \
    mv supercronic-linux-amd64 /usr/local/bin/supercronic && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy cron configuration and entrypoint script
COPY cron/crontab /app/crontab
COPY cron/entrypoint.sh /app/entrypoint.sh

# Make entrypoint script executable and set proper ownership
RUN chmod +x /app/entrypoint.sh && \
    chown appuser:appuser /app/crontab /app/entrypoint.sh

# Create log directory for cron jobs with proper ownership
RUN mkdir -p /var/log/cron && \
    chown -R appuser:appuser /var/log/cron

# Switch back to the application user
USER appuser

# Set working directory
WORKDIR /app

# Use the cron entrypoint script
ENTRYPOINT ["/app/entrypoint.sh"]
