---
name: daily-scribe-observability
description: How to inspect the Daily Scribe monitoring stack — check Prometheus targets and alerts, query Loki logs, view cron job metrics, check container health, and diagnose observability issues. Use when debugging monitoring, checking if logs are flowing, verifying Prometheus scraping, or investigating cron job failures.
---

# Daily Scribe Observability

## Service URLs

| Service | URL | Notes |
|---------|-----|-------|
| Grafana | `http://192.168.15.55:3001` | admin / see `.env` |
| Prometheus | `http://192.168.15.55:9092` | no auth |
| Loki | `http://192.168.15.55:3100` | no auth |
| App metrics | `http://192.168.15.55:8000/metrics` | Prometheus text format |
| App health | `http://192.168.15.55:8000/healthz` | JSON |

All commands below run via SSH: `ssh matheus@192.168.15.55 "<command>"`

## Prometheus

### Check scrape targets (are they UP?)
```bash
curl -s http://localhost:9092/api/v1/targets | python3 -c "
import json,sys
for t in json.load(sys.stdin)['data']['activeTargets']:
    print(t['labels']['job'], '->', t['health'], t.get('lastError','')[:80])
"
```
Expected: `daily-scribe-app -> up` and `node-exporter -> up`

### Check firing alerts
```bash
curl -s http://localhost:9092/api/v1/alerts | python3 -c "
import json,sys
alerts = json.load(sys.stdin)['data']['alerts']
print('No alerts' if not alerts else '\n'.join(f\"{a['labels']['alertname']} [{a['state']}]\" for a in alerts))
"
```

### Query a metric
```bash
curl -s "http://localhost:9092/api/v1/query?query=daily_scribe_disk_usage_percent" | python3 -m json.tool
```

### Reload Prometheus config (after editing prometheus.yml or alert rules)
```bash
curl -X POST http://localhost:9092/-/reload
```

## Loki

### Check what log streams exist (labels)
```bash
curl -s "http://localhost:3100/loki/api/v1/labels"
curl -s "http://localhost:3100/loki/api/v1/label/job/values"
curl -s "http://localhost:3100/loki/api/v1/label/cronjob/values"
```

### Query recent logs from a cron job
```bash
curl -s "http://localhost:3100/loki/api/v1/query_range?query=%7Bjob%3D%22cronlogs%22%2Ccronjob%3D%22full-run%22%7D&limit=20&start=$(date -d '1 hour ago' +%s)000000000&end=$(date +%s)000000000" | python3 -c "
import json,sys
data=json.load(sys.stdin)
for stream in data['data']['result']:
    for ts,line in stream['values']:
        print(line)
"
```

### Query recent errors
```bash
curl -s "http://localhost:3100/loki/api/v1/query?query=%7Blevel%3D%22ERROR%22%7D&limit=10" | python3 -m json.tool
```

## Container Logs

```bash
# App container
docker logs --tail 50 daily-scribe-app

# Cron container (supercronic output)
docker logs --tail 50 daily-scribe-cron

# Promtail (check if it's scraping correctly)
docker logs --tail 30 daily-scribe-promtail

# Prometheus
docker logs --tail 30 daily-scribe-prometheus

# Follow live
docker logs -f daily-scribe-app
```

## Cron Log Files (inside cron container)

```bash
docker exec daily-scribe-cron ls -lh /var/log/cron/
docker exec daily-scribe-cron tail -50 /var/log/cron/full-run.log
docker exec daily-scribe-cron tail -50 /var/log/cron/send-digest.log
docker exec daily-scribe-cron tail -20 /var/log/cron/db-backup-cleanup.log
docker exec daily-scribe-cron tail -20 /var/log/cron/sanity-check.log
docker exec daily-scribe-cron cat /var/log/cron/cron_metrics.prom   # Prometheus textfile metrics
```

## Cron Job Metrics (Prometheus textfile)

After cron jobs run, they write to `/var/log/cron/cron_metrics.prom`. Node-exporter picks this up. Query:
```bash
curl -s "http://localhost:9092/api/v1/query?query=daily_scribe_cronjob_last_success_timestamp" | python3 -c "
import json,sys,time
data=json.load(sys.stdin)
for r in data['data']['result']:
    age = time.time() - float(r['value'][1])
    print(r['metric'].get('cronjob'), f'last success {age/3600:.1f}h ago')
"
```

## Common Diagnostics

### "Prometheus can't scrape app"
Check the app is on `daily-scribe-network`:
```bash
docker network inspect daily-scribe-network --format '{{range .Containers}}{{.Name}} {{end}}'
```
`daily-scribe-app` must appear. If not, the app compose file is missing the network — see `docker-compose.yml`.

### "cronlogs missing from Loki"
1. Check Promtail is running: `docker ps | grep promtail`
2. Check the volume is mounted: `docker exec daily-scribe-promtail ls /mnt/cron-logs/`
3. Check Promtail logs for errors: `docker logs --tail 20 daily-scribe-promtail`
4. If a log file is huge (>100MB), Promtail may be overwhelmed — trim it:
   ```bash
   docker exec daily-scribe-cron python3 -c "
   import os; path='/var/log/cron/full-run.log'; f=open(path,'rb'); f.seek(-2*1024*1024,2); d=f.read(); f.close(); f=open(path,'wb'); f.write(d)
   "
   docker compose -f docker-compose.monitoring.yml restart promtail
   ```

### "ServiceDown alerts firing"
Check `prometheus.yml` doesn't reference ghost services (caddy, docker-exporter). Only `daily-scribe-app` and `node-exporter` should be configured.

## Grafana Dashboard

Main dashboard: `http://192.168.15.55:3001` → folder "Daily Scribe" → "Daily Scribe"

Dashboard is provisioned from `monitoring/dashboards/daily-scribe-overview.json`. Changes to this file are picked up automatically on Grafana restart (no redeploy needed for JSON-only changes after an rsync).
