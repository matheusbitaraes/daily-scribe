# Check the main cron logs (inside the cron container)
docker exec daily-scribe-cron ls -la /var/log/cron/

# View individual cron job logs
docker exec daily-scribe-cron tail -f /var/log/cron/send-digest.log
docker exec daily-scribe-cron tail -f /var/log/cron/full-run.log
docker exec daily-scribe-cron tail -f /var/log/cron/cleanup.log