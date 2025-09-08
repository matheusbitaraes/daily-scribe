# HTTPS Setup Guide for Daily Scribe

This guide explains how to set up HTTPS with Let's Encrypt certificates for Daily Scribe using DuckDNS.

## Prerequisites

1. **DuckDNS Account**: Sign up at [duckdns.org](https://www.duckdns.org)
2. **Router Access**: Access to configure port forwarding
3. **Public IP**: Your internet connection needs a public IP address

## Step 1: Configure DuckDNS

1. **Get your DuckDNS token**:
   - Visit [duckdns.org](https://www.duckdns.org) and sign in
   - Copy your token from the dashboard

2. **Update the domain** (if needed):
   - Ensure `daily-scribe.duckdns.org` points to your public IP
   - DuckDNS will automatically update this when we start the DDNS service

3. **Update server configuration**:
   ```bash
   ssh matheus@192.168.15.55
   cd daily-scribe
   nano .env
   ```
   
   Replace `YOUR_DUCKDNS_TOKEN_HERE` with your actual DuckDNS token:
   ```
   DDNS_PROVIDERS=duckdns:daily-scribe:YOUR_ACTUAL_TOKEN_HERE
   ```

## Step 2: Configure Router Port Forwarding

Configure your router to forward these ports to `192.168.15.55`:

- **Port 80 (HTTP)**: Required for Let's Encrypt challenge
- **Port 443 (HTTPS)**: Required for HTTPS traffic

### Router Configuration Steps:
1. Access your router's admin interface (usually http://192.168.1.1)
2. Find "Port Forwarding" or "Virtual Servers" section
3. Add these rules:
   - **Service**: HTTP, **External Port**: 80, **Internal IP**: 192.168.15.55, **Internal Port**: 80
   - **Service**: HTTPS, **External Port**: 443, **Internal IP**: 192.168.15.55, **Internal Port**: 443

## Step 3: Start DDNS Service

Start the Dynamic DNS service to keep your domain updated:

```bash
ssh matheus@192.168.15.55
cd daily-scribe
docker-compose --profile ddns up -d ddns
```

Check DDNS service status:
```bash
docker-compose logs ddns
```

## Step 4: Restart Caddy with HTTPS

Restart Caddy to enable HTTPS with the new configuration:

```bash
ssh matheus@192.168.15.55
cd daily-scribe
docker-compose restart caddy
```

Monitor Caddy logs for certificate acquisition:
```bash
docker-compose logs -f caddy
```

## Step 5: Verify HTTPS Setup

1. **Test domain resolution**:
   ```bash
   nslookup daily-scribe.duckdns.org
   ```

2. **Test external access**:
   ```bash
   curl -I https://daily-scribe.duckdns.org
   ```

3. **Check certificate**:
   - Visit https://daily-scribe.duckdns.org in your browser
   - Verify the SSL certificate is valid and issued by Let's Encrypt

## Troubleshooting

### Certificate Acquisition Issues

1. **Check Caddy logs**:
   ```bash
   docker-compose logs caddy | grep -i certificate
   ```

2. **Verify domain resolution**:
   ```bash
   # From an external source (like your phone's data connection)
   nslookup daily-scribe.duckdns.org
   ```

3. **Test port forwarding**:
   ```bash
   # From external network
   telnet daily-scribe.duckdns.org 80
   telnet daily-scribe.duckdns.org 443
   ```

### Common Issues

- **"no certificate available"**: Domain not resolving to server or ports not forwarded
- **"connection refused"**: Port forwarding not configured correctly
- **"invalid domain"**: DuckDNS token incorrect or domain not updated

### DDNS Service Issues

Check DDNS service logs:
```bash
docker-compose logs ddns
```

Force DDNS update:
```bash
docker-compose exec ddns /usr/local/bin/ddns-update.sh --force
```

## Security Considerations

1. **Firewall Rules**: The server firewall allows ports 80 and 443
2. **Token Security**: Keep your DuckDNS token secret
3. **Certificate Monitoring**: Monitor certificate expiration (auto-renewed by Caddy)

## Rollback to HTTP

If you need to temporarily disable HTTPS:

1. **Comment out HTTPS redirect** in Caddyfile:
   ```caddyfile
   # http://{$DOMAIN:localhost} {
   #     redir https://{host}{uri} permanent
   # }
   ```

2. **Restart Caddy**:
   ```bash
   docker-compose restart caddy
   ```

## Next Steps

After HTTPS is working:
1. Update any hardcoded HTTP URLs to use HTTPS
2. Configure HSTS headers (already included in Caddyfile)
3. Set up monitoring for certificate expiration
4. Consider adding additional security headers

## Support

- **DuckDNS Documentation**: https://www.duckdns.org/spec.jsp
- **Caddy Documentation**: https://caddyserver.com/docs/automatic-https
- **Let's Encrypt**: https://letsencrypt.org/docs/
