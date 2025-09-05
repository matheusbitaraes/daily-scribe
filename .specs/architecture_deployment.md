# Daily Scribe — Minimal Production Architecture and Deployment Guide

This document outlines a low-cost, low-complexity path to run your API and database 24/7, keep the background jobs reliable, and enable a simple frontend for visualization and user settings.

## Goals

- Keep costs very low and ops simple.
- Keep SQLite (good enough for low traffic) with durability and backups.
- Run FastAPI 24/7 and expose a stable base URL for a future frontend.
- Run scheduled jobs reliably without depending on your laptop.

## Current State (summary)

- Monorepo with CLI and FastAPI in `src/`.
- Jobs live in `src/main.py` (Typer CLI) and run via local cron.
- Data stored in `data/digest_history.db` (SQLite) via `DatabaseService`.
- API layer at `src/api.py`.
- Simple frontend

## Target Architecture (MVP)

Single small server with Docker Compose, using:

- App container: FastAPI (Uvicorn) + your existing code. SQLite DB on a mounted volume. WAL mode for better concurrency.
- Cron/worker container: Runs your CLI (`fetch-news`, `summarize-articles`, `full-run`, or `send-digest`) on a schedule.
- Reverse proxy: Caddy (or Nginx) for TLS and domain routing. Caddy is simpler and auto-issues Let’s Encrypt certificates.
- Backup/replication: Litestream to S3-compatible storage (e.g., Backblaze B2) for continuous, low-cost backups of SQLite.
- Static frontend: Deployed to Cloudflare Pages or Netlify (free), pointing at your API domain with CORS enabled.

This keeps everything on one tiny host, with a single SQLite file and automated backups.

### Why this?

- Lowest monthly cost: 1x small VPS ($4–$6/mo typical) + pennies for object storage.
- Low cognitive load: Docker Compose + Caddy + cron container.
- SQLite is fine for small concurrent usage; WAL mode and a single writer pattern are sufficient.

## Hosting Option: Home server

Using a home server is an excellent choice for Daily Scribe, offering complete control and zero hosting costs. Here's how to set it up effectively:

### Advantages of Home Server Hosting

- **Zero monthly costs:** No VPS fees, only electricity (~$1-5/month for a small server)
- **Complete control:** Full access to hardware, logs, and configuration
- **Learning opportunity:** Hands-on experience with production deployment
- **Scalability:** Easy to upgrade hardware as needed
- **Privacy:** Data stays on your premises

### Network and Domain Setup

**Dynamic DNS Configuration:**
- Use a DDNS service (No-IP, DuckDNS, Cloudflare) to handle changing home IP addresses
- Set up automatic IP updates via router or a simple cron job
- Example: `daily-scribe.yourname.duckdns.org`

**Port Forwarding:**
- Forward ports 80 and 443 from router to your server's internal IP
- Ensure your server has a static internal IP (DHCP reservation recommended)
- Document the internal IP for troubleshooting

**Firewall Configuration:**
```bash
# Enable UFW and configure basic rules
sudo ufw enable
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw default deny incoming
sudo ufw default allow outgoing
```

### Hardware Recommendations

**Minimum specs for Daily Scribe:**
- **CPU:** 2 cores (Raspberry Pi 4 or Intel NUC work great)
- **RAM:** 2GB (1GB for containers + 1GB for OS)
- **Storage:** 32GB+ SSD/SD card (faster I/O benefits SQLite)
- **Network:** Stable broadband with reasonable upload speed

**Optimal setup:**
- Use SSD over HDD for better SQLite performance
- Ensure good ventilation/cooling for 24/7 operation
- Consider UPS for power stability
- Monitor disk space and set up log rotation

### Home Server Specific Considerations

**Power and Uptime:**
- Set BIOS to auto-restart after power loss
- Consider a small UPS for brief outages
- Monitor system health with basic scripts

**ISP and Connectivity:**
- Verify your ISP allows hosting (most residential do)
- Consider bandwidth limits if any
- Set up monitoring for connection drops

**Security Hardening:**
- Change default SSH port: `Port 2222` in `/etc/ssh/sshd_config`
- Use SSH keys instead of passwords
- Set up fail2ban for brute force protection
- Keep OS and Docker updated regularly
- Consider VPN access for remote management

**Local Access:**
- Keep local access available: `http://server-local-ip:8000`
- Useful for debugging when external access is down
- Consider local DNS entry for convenience

### Backup Strategy for Home Server

Since you control the hardware, implement multiple backup layers:

**Primary: Litestream to Cloud**
- Same GCS/S3 setup as VPS deployment
- Continuous replication of SQLite database
- Zero-cost with GCP free tier

**Secondary: Local Backups**
- Daily automated backups to external USB drive
- Weekly full system snapshots
- Keep copies of Docker volumes and configs

**Example backup script:**
```bash
#!/bin/bash
# /home/user/backup-daily-scribe.sh
DATE=$(date +%Y%m%d)
docker exec daily-scribe-app sqlite3 /data/digest_history.db ".backup /data/backup-$DATE.db"
cp /data/backup-$DATE.db /mnt/external-backup/
find /mnt/external-backup -name "backup-*.db" -mtime +30 -delete
```

### Monitoring and Maintenance

**Health Checks:**
- Set up simple uptime monitoring (UptimeRobot free tier)
- Internal health checks via cron
- Email alerts for service failures

**Log Management:**
- Configure log rotation to prevent disk filling
- Set up centralized logging if running multiple services
- Monitor Docker container logs

**Updates and Maintenance:**
- Schedule monthly system updates during low-usage hours
- Automate Docker image updates with Watchtower (optional)
- Keep documentation of configuration changes

### Example Home Server docker-compose.yml Additions

```yaml
version: '3.8'
services:
  # ... existing services ...
  
  # Optional: Monitoring
  watchtower:
    image: containrrr/watchtower
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
    environment:
      - WATCHTOWER_POLL_INTERVAL=86400  # Check daily
      - WATCHTOWER_CLEANUP=true
    restart: unless-stopped

  # Optional: System monitoring
  portainer:
    image: portainer/portainer-ce:latest
    ports:
      - "9000:9000"
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - portainer_data:/data
    restart: unless-stopped

volumes:
  portainer_data:
```

### Troubleshooting Common Home Server Issues

**External access not working:**
1. Check port forwarding configuration
2. Verify DDNS is updating correctly
3. Test with online port checkers
4. Check ISP blocking (rare but possible)

**Performance issues:**
1. Monitor Docker stats: `docker stats`
2. Check disk I/O with `iotop`
3. Verify SQLite isn't being overwhelmed
4. Review log files for errors

**Security concerns:**
1. Regular security scans with `nmap` from external network
2. Monitor auth logs: `tail -f /var/log/auth.log`
3. Check for unusual network activity
4. Keep software updated

## Containerization (app + cron)

- App service runs FastAPI: `uvicorn src.api:app --host 0.0.0.0 --port 8000`.
- Cron service runs your Typer CLI on schedule using system `crond` or `supercronic`. Example schedules:
  - Fetch multiple times each morning: `0 7-11 * * *` for hourly runs at 7,8,9,10,11.
  - Or one daily pipeline: `0 08 * * *` for a single run.
- Both services share a named volume `data/` for `digest_history.db`.

Notes for SQLite:
- Use WAL mode and sane timeouts to reduce lock contention: `PRAGMA journal_mode=WAL;` and set `sqlite3.connect(..., timeout=30)`.
- Ensure all paths point to the shared `/data/digest_history.db`.

## Backups and Durability

Use **Litestream** to replicate the SQLite database to **Google Cloud Storage (GCS)**. This is the ideal solution as it leverages the GCP free tier and keeps your infrastructure consolidated.

- **Continuous Replica:** Litestream will continuously stream database changes to a GCS bucket, providing near real-time backups.
- **Disaster Recovery:** On startup, Litestream can restore the database from GCS if the local file is missing or corrupted. This gives you robust, near-zero-downtime recovery without needing to migrate to a more complex database like Postgres.
- **Cost:** Fits within the GCP free tier (5 GB-months of storage), making it free for this project's scale.

## Frontend

- Build a small SPA (Vite/React) and deploy to Cloudflare Pages or Netlify.
- Point it to `https://api.yourdomain.com` and keep CORS permissive (already configured in `src/api.py`).
- Don’t expose the DB; all access via API.

## Security/Basics

- Reverse proxy terminates TLS (Caddy auto HTTPS). Expose only ports 80/443 publicly.
- Put the app on an internal Docker network. Only Caddy binds to the internet.
- Store secrets (SMTP creds, API keys) as env vars in a `.env` used by Compose (never commit them).
- Keep the server firewalled (UFW allow 80,443,22; deny everything else).

## Observability

- Log to stdout/stderr (Docker captures) and to `digest.log` for local tails.
- Add `/healthz` to FastAPI for uptime checks.
- Optionally add basic request logging and a lightweight metrics endpoint.

## Minimal docker-compose.yml (concept)

- app: FastAPI + your code
- cron: runs CLI on schedules (uses the same image)
- caddy: reverse proxy with automatic HTTPS
- litestream: replicates `data/digest_history.db` to object storage

All share a named `data` volume for the SQLite file.

## Scheduling strategy

- Keep schedules in the cron container to avoid mixing API uptime and job timing.
- For your earlier ask, example entry for hourly 7–11:
  - `0 7-11 * * * /app/run-daily-scribe.sh send-digest >> /var/log/cron.log 2>&1`
- Alternatively, run the full pipeline once daily:
  - `0 8 * * * python -m src.main full-run`

## Small code hardening (optional, low-risk)

- Database path via env var: let `DatabaseService` accept `DB_PATH` (`/data/digest_history.db`) so the same code works locally and in containers.
- Enable WAL mode on startup once.
- Add a simple `/healthz` to `api.py`:
  - Checks a quick DB query `SELECT 1` and returns 200.
- Add `--force` guardrails already present for `send-digest` to avoid double sends.

## Migration Steps

1) Containerize
- Add a Dockerfile for the app (python:3.11-slim), install `requirements.txt`, run as non-root.
- Ensure working directory contains `src/` and `run-daily-scribe.sh`.

2) Compose stack
- Create `docker-compose.yml` with services: app, cron, caddy, litestream, and a named volume `data`.
- Mount `data` to `/data` in app and cron.
- Map Caddy 80/443 to host.

3) Domain + TLS
- Point `api.yourdomain.com` A record to the server IP.
- Provide a simple Caddyfile reverse-proxying to `app:8000`.

4) Backups
- Create a bucket (B2/S3). Add keys to `.env`.
- Configure Litestream to replicate `/data/digest_history.db`.

5) Schedules
- Put your cron entries into the cron container image or mount a crontab file.
- Start the stack and verify logs.

6) Frontend (later)
- Build and deploy SPA to Cloudflare Pages.
- Point to `https://api.yourdomain.com` with CORS.

## Costs Comparison

### Option 1: Cloud VPS (with GCP Free Tier)

- **VPS:** $0/month (using the `e2-micro` instance included in the GCP free tier).
- **Object Storage for Backups:** $0/month (the first 5GB-months of standard storage are free, which is more than enough for Litestream backups).
- **Static Frontend:** $0/month (Cloudflare Pages or Netlify free tiers are sufficient).

Total estimated cost: **$0/month**, assuming usage stays within the free tier limits.

### Option 2: Home Server (Recommended for Learning)

**One-time costs:**
- Hardware: $50-200 (Raspberry Pi 4 to Intel NUC)
- UPS (optional): $50-100
- Total initial: $50-300

**Monthly costs:**
- Electricity: ~$1-5/month (depending on hardware and local rates)
- Dynamic DNS: $0-2/month (many free options available)
- Object Storage for Backups: $0/month (within free tier limits)
- Static Frontend: $0/month

**Total ongoing cost: ~$1-7/month**

### Cost Analysis Summary

- **Home server** pays for itself in 2-6 months vs. paid VPS options
- **Learning value** is significantly higher with home server
- **Control and customization** is complete with home server
- **Reliability** can be higher with proper UPS and monitoring
- **Scalability** is easier (just upgrade hardware vs. changing hosting plans)

If you ever outgrow SQLite (traffic, concurrency): migrate to a managed Postgres (Supabase, Neon, RDS) and swap the DB layer; your FastAPI + cron layout stays the same.

## Appendix — Example cron matrix

- Fetch and summarize every hour between 7–11:
  - `0 7-11 * * * python -m src.main fetch-news`
  - `15 7-11 * * * python -m src.main summarize-articles`
- Send digest at 11:30 with force safety off:
  - `30 11 * * * python -m src.main send-digest`

This staggers CPU/network use and avoids lock contention.

---

## Next Steps for Home Server Deployment

**Immediate actions:**
1. **Hardware setup:** Ensure your home server meets minimum requirements
2. **Network configuration:** Set up DDNS and port forwarding
3. **Security hardening:** Configure firewall and SSH properly
4. **Domain setup:** Choose and configure your DDNS domain

**Implementation priority:**
1. **Containerize the application** (Docker + docker-compose.yml)
2. **Set up reverse proxy** (Caddy for auto-HTTPS)
3. **Configure backups** (Litestream to GCS/S3)
4. **Deploy and test** (local and external access)
5. **Set up monitoring** (uptime checks and health monitoring)

**Optional enhancements:**
- UPS for power stability
- Local backup strategy
- System monitoring (Portainer, Grafana)
- Automated updates (Watchtower)

Questions to decide next:
- What hardware are you planning to use for the home server?
- Do you have a preference for DDNS provider (DuckDNS, No-IP, etc.)?
- What domain name pattern would you like for the API?
- Should we start with the basic Docker setup or include monitoring from the start?