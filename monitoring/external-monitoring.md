# External Monitoring Configuration

## UptimeRobot Setup

1. Create account at https://uptimerobot.com
2. Get API key from account settings
3. Add to .env file:
   ```
   UPTIMEROBOT_API_KEY=ur123456789-abcdef
   UPTIMEROBOT_MONITOR_URL=https://yourdomain.duckdns.org/healthz
   UPTIMEROBOT_ALERT_CONTACTS=email_contact_id
   ```
4. Run: `./scripts/external-monitor.sh uptimerobot`

## Healthchecks.io Setup

1. Create account at https://healthchecks.io
2. Create new check and get UUID
3. Add to .env file:
   ```
   HEALTHCHECKS_UUID=12345678-1234-5678-9012-123456789abc
   ```
4. Run: `./scripts/external-monitor.sh healthchecks`

## StatusCake Setup

1. Create account at https://www.statuscake.com
2. Get API key from account settings
3. Add to .env file:
   ```
   STATUSCAKE_API_KEY=your-api-key
   STATUSCAKE_TEST_URL=https://yourdomain.duckdns.org/healthz
   ```
