---
name: daily-scribe-project
description: Reference for the Daily Scribe project architecture, service topology, Docker networks, volumes, and key file locations. Use when exploring the codebase, understanding how services connect, diagnosing network issues, or when unsure where a piece of configuration lives.
---

# Daily Scribe Project Architecture

## Service Map

Two separate Docker Compose stacks that share a network:

```
docker-compose.yml          (app stack)
  daily-scribe-app          FastAPI, port 8000
  daily-scribe-cron         Supercronic cron jobs
  daily-scribe-elasticsearch  port 9200
  daily-scribe-kibana         port 5601
  daily-scribe-cloudbeaver    port 8080 (profile: admin)

docker-compose.monitoring.yml  (monitoring stack)
  daily-scribe-prometheus     port 9092 (→ internal 9090)
  daily-scribe-grafana        port 3001 (→ internal 3000)
  daily-scribe-loki           port 3100
  daily-scribe-promtail       (no exposed port)
  daily-scribe-node-exporter  port 9100
```

## Networks

| Network | Who uses it |
|---------|------------|
| `daily_scribe_internal` | app, cron, elasticsearch, kibana, cloudbeaver |
| `daily-scribe-network` (external) | all monitoring stack services + app (dual-homed) |

**Critical**: The app is on BOTH networks so Prometheus can scrape it. Prometheus targets the app by container name `daily-scribe-app:8000`.

## Volumes

| Volume | Mounted in | Purpose |
|--------|-----------|---------|
| `daily_scribe_logs` | app, cron → `/var/log/daily-scribe` | API logs |
| `daily_scribe_cron_logs` | cron → `/var/log/cron`, promtail → `/mnt/cron-logs`, node-exporter → `/mnt/cron-metrics` | Cron logs + `.prom` metrics file |
| `prometheus-data` | prometheus | Metrics TSDB |
| `grafana-data` | grafana | Dashboards, users |
| `loki-data` | loki | Log chunks |

## Key File Locations

| What | Path |
|------|------|
| App entrypoint | `src/api.py` |
| CLI commands (full-run, send-digest, sanity-check) | `src/main.py` |
| Cron schedule | `cron/crontab` |
| Cron Python scripts | `cron/daily_cleanup_and_backup.py`, `cron/disk_cleanup_only.py` |
| Cron metrics writer | `cron/cron_metrics.py` (writes `/var/log/cron/cron_metrics.prom`) |
| Prometheus config | `monitoring/config/prometheus.yml` |
| Promtail config | `monitoring/config/promtail.yml` |
| Loki config | `monitoring/config/loki.yml` |
| Alert rules | `monitoring/alerts/daily-scribe.yml` |
| Grafana dashboard JSON | `monitoring/dashboards/daily-scribe-overview.json` |
| Grafana datasource provisioning | `monitoring/grafana/datasources/prometheus.yml` |

## App Metrics (exposed at `/metrics`)

Custom Prometheus metrics — all prefixed `daily_scribe_`:
- `requests_total`, `errors_total` — counters
- `requests_by_endpoint_total{method, path}` — per-endpoint counter
- `database_health` — gauge (1 = healthy)
- `database_last_query_duration_seconds` — gauge
- `disk_usage_percent`, `disk_free_bytes` — gauges
- `uptime_seconds` — gauge
- `articles_processed_total`, `digests_generated_total` — counters

Cron metrics (via node-exporter textfile collector, file `/var/log/cron/cron_metrics.prom`):
- `daily_scribe_cronjob_last_success_timestamp{cronjob}` — unix timestamp
- `daily_scribe_cronjob_last_duration_seconds{cronjob}` — gauge
- `daily_scribe_cronjob_runs_total{cronjob, status}` — counter

## Server

- SSH: `ssh matheus@192.168.15.55`
- Project root on server: `/home/matheus/daily-scribe`
- Server is NOT a git repo — files are deployed via rsync
