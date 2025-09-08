# HTTPS SSL Certificate Setup Tasks

## Current Status
- ✅ Domain `daily-scribe.duckdns.org` resolves to public IP `179.98.209.77`
- ✅ DDNS service updated to point to correct public IP
- ✅ Caddy configured for automatic HTTPS with Let's Encrypt
- ❌ Port forwarding not configured on router (blocking SSL certificate validation)
- ❌ SSL certificate acquisition failing due to inaccessible server from internet

## Issue
Let's Encrypt cannot reach the server to validate the domain because ports 80 and 443 are not forwarded from the router to the server (192.168.15.55).

## Router Port Forwarding Configuration

### Step 1: Access Router Admin Interface
1. **Find router IP address** (try these common addresses):
   - `192.168.1.1`
   - `192.168.0.1` 
   - `10.0.0.1`

2. **Open web browser** and navigate to router IP
3. **Login** with admin credentials (check router label for defaults)

### Step 2: Locate Port Forwarding Settings
Look for menu options (varies by router brand):
- **Port Forwarding**
- **Virtual Server**
- **NAT Forwarding**
- **Applications & Gaming** → **Port Forwarding**
- **Advanced** → **Port Forwarding**

### Step 3: Create Port Forwarding Rules

#### Rule 1 - HTTP (Port 80)
- **Service Name**: `Daily-Scribe-HTTP`
- **External Port**: `80`
- **Internal IP**: `192.168.15.55`
- **Internal Port**: `80`
- **Protocol**: `TCP`
- **Enable**: `Yes`

#### Rule 2 - HTTPS (Port 443)
- **Service Name**: `Daily-Scribe-HTTPS`
- **External Port**: `443`
- **Internal IP**: `192.168.15.55`
- **Internal Port**: `443`
- **Protocol**: `TCP`
- **Enable**: `Yes`

### Step 4: Save and Apply
- **Save** configuration
- **Restart** router if prompted
- Wait 1-2 minutes for changes to take effect

### Router-Specific Locations:
- **TP-Link**: `Advanced` → `NAT Forwarding` → `Virtual Servers` → `Add`
- **Netgear**: `Dynamic DNS` → `Port Forwarding/Port Triggering` → `Port Forwarding`
- **Linksys**: `Smart Wi-Fi Settings` → `Security` → `Apps and Gaming` → `Single Port Forwarding`
- **ASUS**: `Adaptive QoS` → `Traditional QoS` → `Port Forwarding`

## Next Steps After Port Forwarding

### Step 5: Test Port Forwarding
```bash
# SSH into server and test external access
ssh matheus@192.168.15.55 "curl -I http://daily-scribe.duckdns.org"
```

### Step 6: Restart Caddy to Retry SSL Certificate
```bash
# Restart Caddy service to trigger new certificate request
ssh matheus@192.168.15.55 "cd /home/matheus/daily-scribe && docker-compose --env-file .env.production restart caddy"
```

### Step 7: Monitor Certificate Acquisition
```bash
# Watch Caddy logs for certificate acquisition progress
ssh matheus@192.168.15.55 "docker logs daily-scribe-caddy --tail 20 -f"
```

### Step 8: Verify HTTPS Connection
```bash
# Test HTTPS connection from server
ssh matheus@192.168.15.55 "curl -I https://daily-scribe.duckdns.org"

# Test from local machine
curl -I https://daily-scribe.duckdns.org
```

## Expected Results
- Ports 80 and 443 should be accessible from internet
- Let's Encrypt should successfully validate domain ownership
- SSL certificate should be automatically issued and installed
- Site should be accessible at `https://daily-scribe.duckdns.org` without warnings

## Troubleshooting Commands

### Check DNS Resolution
```bash
nslookup daily-scribe.duckdns.org 8.8.8.8
```

### Check Port Accessibility
```bash
# Test if ports are open from external tool like:
# https://www.yougetsignal.com/tools/open-ports/
# Or use: nc -zv daily-scribe.duckdns.org 80
# And: nc -zv daily-scribe.duckdns.org 443
```

### View Caddy Certificate Logs
```bash
ssh matheus@192.168.15.55 "docker logs daily-scribe-caddy | grep -i certificate"
```

### Manual DDNS Update (if needed)
```bash
ssh matheus@192.168.15.55 "curl 'https://www.duckdns.org/update?domains=daily-scribe&token=a0aa6e32-209e-49c4-ae84-b1d2249f84ce&ip=179.98.209.77'"
```

## Important Notes
- The server public IP is: `179.98.209.77`
- The server private IP is: `192.168.15.55`
- DuckDNS domain: `daily-scribe.duckdns.org`
- Let's Encrypt rate limits may apply if too many failed attempts occur
- Port forwarding is essential for Let's Encrypt domain validation

## Success Criteria
- [ ] Router port forwarding configured for ports 80 and 443
- [ ] External port connectivity verified
- [ ] SSL certificate successfully obtained from Let's Encrypt
- [ ] HTTPS site accessible without browser warnings
- [ ] Both HTTP and HTTPS working correctly with automatic redirect
