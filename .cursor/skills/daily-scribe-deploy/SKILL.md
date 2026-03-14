---
name: daily-scribe-deploy
description: How to deploy Daily Scribe to the production server. Use when deploying changes, restarting services, pushing config updates, rebuilding containers, or when asked about the deploy process or deploy-to-server.sh.
---

# Daily Scribe Deployment

## Server Details

- Host: `192.168.15.55`
- User: `matheus`
- Project path: `/home/matheus/daily-scribe`
- Server is NOT a git repo — all deploys are via rsync

## Full Deploy (all changes)

```bash
./scripts/deploy-to-server.sh
```

This script does, in order:
1. SSH connectivity check
2. `rsync` entire project (excluding `.git/`, `venv/`, `data/`, `__pycache__/`, etc.)
3. Copies `.env.production` → `.env` on server
4. Creates Docker network if missing (`docker network create daily-scribe-network`)
5. Builds app + cron images (`docker compose build`)
6. Recreates app/cron/elasticsearch containers (`docker compose up -d`)
7. Runs `./scripts/setup-monitoring.sh --all` then `docker compose -f docker-compose.monitoring.yml up -d`
8. Health check validation

**When to use**: Any time you rebuild images (Dockerfile changes, new Python deps, new files added to image).

## Partial Deploys (config-only, no rebuild needed)

For changes to monitoring config, dashboard JSON, alert rules, or promtail config — no image rebuild required. Just rsync the specific files and restart the relevant container:

```bash
# Monitoring configs (prometheus, promtail, loki, alerts, dashboard)
rsync -av monitoring/ matheus@192.168.15.55:/home/matheus/daily-scribe/monitoring/
ssh matheus@192.168.15.55 "cd /home/matheus/daily-scribe && docker compose -f docker-compose.monitoring.yml restart prometheus promtail"

# Just the dashboard (Grafana picks it up automatically via provisioning — no restart needed)
rsync -av monitoring/dashboards/ matheus@192.168.15.55:/home/matheus/daily-scribe/monitoring/dashboards/

# docker-compose.yml or docker-compose.monitoring.yml changes
rsync -av docker-compose*.yml matheus@192.168.15.55:/home/matheus/daily-scribe/
ssh matheus@192.168.15.55 "cd /home/matheus/daily-scribe && docker compose up -d"
```

## When Image Rebuild Is Required

Rebuild is needed when:
- `Dockerfile` or `cron/Dockerfile` changed
- New files are `COPY`'d into the image (e.g., new cron scripts)
- `requirements.txt` changed

Use full deploy (`./scripts/deploy-to-server.sh`) or manually:
```bash
rsync -av --exclude='.git/' --exclude='venv/' --exclude='data/' --exclude='__pycache__/' \
  /Users/Matheus/daily-scribe/ matheus@192.168.15.55:/home/matheus/daily-scribe/
ssh matheus@192.168.15.55 "cd /home/matheus/daily-scribe && docker compose build && docker compose up -d"
```

## Restarting Individual Services

```bash
# App only
ssh matheus@192.168.15.55 "cd /home/matheus/daily-scribe && docker compose restart app"

# Cron only  
ssh matheus@192.168.15.55 "cd /home/matheus/daily-scribe && docker compose restart cron"

# Monitoring stack
ssh matheus@192.168.15.55 "cd /home/matheus/daily-scribe && docker compose -f docker-compose.monitoring.yml restart"

# Single monitoring service
ssh matheus@192.168.15.55 "cd /home/matheus/daily-scribe && docker compose -f docker-compose.monitoring.yml restart promtail"
```

## Post-Deploy Checks

After any deploy, verify:
```bash
# All containers healthy
ssh matheus@192.168.15.55 "docker ps --format 'table {{.Names}}\t{{.Status}}'"

# App health
ssh matheus@192.168.15.55 "curl -s http://localhost:8000/healthz | python3 -m json.tool"

# Prometheus targets (should show both targets as "up")
ssh matheus@192.168.15.55 "curl -s http://localhost:9092/api/v1/targets | python3 -c \"import json,sys; [print(t['labels']['job'],'->', t['health']) for t in json.load(sys.stdin)['data']['activeTargets']]\""
```

## Known Quirks

- The deploy script's `validate_deployment` checks Grafana on port 3000 and Prometheus on port 9090 — both will show "not healthy" because they're actually on 3001 and 9092. This is a false alarm in the script output.
- The `setup-monitoring.sh` script prints `unbound variable` on one line — this is a known bug in the script and doesn't affect the outcome.
- Grafana dashboard UIDs are hardcoded in the JSON (`"uid": "daily-scribe-main"`). The original dashboard had a different UID (`ae71c249-c94b-43e4-bc29-98da885c8417`). Access the new dashboard via the provisioned folder in Grafana UI or use `http://192.168.15.55:3001`.
