# Port Forwarding and Router Configuration Guide

This guide provides comprehensive instructions for configuring your home router to enable external access to the Daily Scribe service. This includes port forwarding, static IP configuration, and network security setup.

## Overview

To make your Daily Scribe service accessible from the internet, you need to:

1. **Assign a static IP** to your server within your home network
2. **Forward ports 80 and 443** from your router to your server
3. **Configure router firewall** for security
4. **Test external connectivity** to verify setup
5. **Monitor for security issues** and unauthorized access

## Prerequisites

Before starting, ensure you have:
- Administrative access to your router
- The current IP address of your Daily Scribe server
- Your router's admin interface credentials
- Basic understanding of your network topology

## Step 1: Determine Network Information

### Find Your Server's Current IP

```bash
# On your Daily Scribe server, run:
ip addr show | grep "inet " | grep -v 127.0.0.1
# Or use:
hostname -I
# Or check with:
ifconfig | grep "inet " | grep -v 127.0.0.1
```

### Find Your Router's IP (Gateway)

```bash
# On your server:
ip route | grep default
# Or:
route -n | grep '^0.0.0.0'
```

### Common Network Ranges

Most home networks use one of these private IP ranges:
- `192.168.1.x` (most common)
- `192.168.0.x`
- `10.0.0.x`
- `172.16.x.x`

Example setup:
- **Router IP**: 192.168.1.1
- **Server IP**: 192.168.1.100 (what we'll configure)
- **Network Range**: 192.168.1.1-254

## Step 2: Configure Static IP for Server

### Method 1: Router DHCP Reservation (Recommended)

This method assigns the same IP to your server every time based on its MAC address.

1. **Find your server's MAC address**:
   ```bash
   # On your server:
   ip link show | grep -A1 "state UP"
   # Look for the line starting with "link/ether"
   ```

2. **Access your router's admin interface**:
   - Open browser and go to your router IP (usually `192.168.1.1`)
   - Login with admin credentials

3. **Navigate to DHCP settings**:
   - Look for "DHCP", "LAN", or "Network" settings
   - Find "DHCP Reservations", "Static DHCP", or "Reserved IPs"

4. **Add reservation**:
   - **MAC Address**: Your server's MAC address
   - **IP Address**: Choose an IP (e.g., 192.168.1.100)
   - **Description**: "Daily Scribe Server"

5. **Save and restart router** if required

### Method 2: Static IP on Server (Alternative)

Configure static IP directly on the server (Ubuntu/Debian example):

```bash
# Backup current network configuration
sudo cp /etc/netplan/01-netcfg.yaml /etc/netplan/01-netcfg.yaml.backup

# Edit network configuration
sudo nano /etc/netplan/01-netcfg.yaml
```

Example netplan configuration:
```yaml
network:
  version: 2
  renderer: networkd
  ethernets:
    eth0:  # Replace with your interface name
      dhcp4: false
      addresses:
        - 192.168.1.100/24  # Your chosen static IP
      gateway4: 192.168.1.1  # Your router IP
      nameservers:
        addresses:
          - 8.8.8.8
          - 1.1.1.1
```

Apply the configuration:
```bash
sudo netplan apply
```

## Step 3: Configure Port Forwarding

### Common Router Interface Locations

Port forwarding settings are typically found under:
- **Advanced** → **Port Forwarding**
- **NAT** → **Port Forwarding**
- **Firewall** → **Port Forwarding**
- **Gaming** → **Port Forwarding**
- **Virtual Server**

### Required Port Forwarding Rules

Configure these two rules:

#### Rule 1: HTTP (Port 80)
- **Service Name**: Daily Scribe HTTP
- **External Port**: 80
- **Internal IP**: 192.168.1.100 (your server's IP)
- **Internal Port**: 80
- **Protocol**: TCP
- **Enable**: Yes

#### Rule 2: HTTPS (Port 443)
- **Service Name**: Daily Scribe HTTPS
- **External Port**: 443
- **Internal IP**: 192.168.1.100 (your server's IP)
- **Internal Port**: 443
- **Protocol**: TCP
- **Enable**: Yes

### Router-Specific Instructions

#### Netgear Routers
1. Go to **Advanced** → **Dynamic DNS/Port Forwarding**
2. Click **Port Forwarding**
3. Add rules as specified above

#### Linksys Routers
1. Go to **Smart Wi-Fi Tools** → **Port Forwarding**
2. Add new forwarding rules

#### ASUS Routers
1. Go to **Advanced Settings** → **WAN** → **Port Forwarding**
2. Enable port forwarding and add rules

#### TP-Link Routers
1. Go to **Advanced** → **NAT Forwarding** → **Port Forwarding**
2. Add forwarding rules

#### Generic Steps
1. Access router admin interface (usually http://192.168.1.1)
2. Login with admin credentials
3. Navigate to port forwarding section
4. Add the two rules specified above
5. Save configuration
6. Restart router if prompted

## Step 4: Router Firewall Configuration

### Security Settings to Configure

1. **Enable SPI Firewall**: Stateful Packet Inspection
2. **Disable WPS**: If not needed for other devices
3. **Enable DoS Protection**: Protects against denial of service attacks
4. **Disable UPnP**: Unless specifically needed (security risk)
5. **Change default admin password**: Use strong password
6. **Update router firmware**: Ensure latest security patches

### Recommended Firewall Rules

#### Block Common Attack Ports
Consider blocking these ports if not needed:
- 22 (SSH) - Unless you need external SSH access
- 23 (Telnet)
- 135-139 (NetBIOS)
- 445 (SMB)
- 1433 (SQL Server)
- 3389 (RDP)

#### Allow Only Required Traffic
- **Port 80**: HTTP (will redirect to HTTPS)
- **Port 443**: HTTPS (main service)
- **Port 22**: SSH (optional, use non-standard port if enabled)

### Example Firewall Configuration

```
# Incoming Rules (from Internet to Server)
ALLOW: External Port 80 → Server:80 (HTTP)
ALLOW: External Port 443 → Server:443 (HTTPS)
BLOCK: All other unsolicited incoming traffic

# Outgoing Rules (from Server to Internet)
ALLOW: All outgoing traffic (for updates, DDNS, etc.)
```

## Step 5: Testing External Connectivity

### Automated Testing Script

Create this script to test your configuration:

```bash
#!/bin/bash
# save as test_connectivity.sh

# Test script for Daily Scribe external connectivity
echo "Daily Scribe External Connectivity Test"
echo "======================================"

# Get public IP
PUBLIC_IP=$(curl -s https://ipv4.icanhazip.com)
echo "Public IP: $PUBLIC_IP"

# Test if DDNS domain is set
if [ ! -z "$DDNS_DOMAIN" ]; then
    echo "Testing DDNS domain: $DDNS_DOMAIN"
    
    # Test HTTP redirect
    echo -n "HTTP redirect test: "
    HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://$DDNS_DOMAIN")
    if [ "$HTTP_RESPONSE" = "301" ] || [ "$HTTP_RESPONSE" = "302" ]; then
        echo "PASS (Redirects to HTTPS)"
    else
        echo "FAIL (Response: $HTTP_RESPONSE)"
    fi
    
    # Test HTTPS connectivity
    echo -n "HTTPS connectivity test: "
    HTTPS_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "https://$DDNS_DOMAIN/healthz")
    if [ "$HTTPS_RESPONSE" = "200" ]; then
        echo "PASS"
    else
        echo "FAIL (Response: $HTTPS_RESPONSE)"
    fi
else
    echo "DDNS_DOMAIN not set, testing with public IP"
    
    # Test direct IP access (if no domain configured)
    echo -n "Direct IP HTTP test: "
    HTTP_RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" "http://$PUBLIC_IP" --max-time 10)
    if [ "$HTTP_RESPONSE" = "301" ] || [ "$HTTP_RESPONSE" = "302" ] || [ "$HTTP_RESPONSE" = "200" ]; then
        echo "PASS (Response: $HTTP_RESPONSE)"
    else
        echo "FAIL (Response: $HTTP_RESPONSE)"
    fi
fi

# Test port accessibility
echo ""
echo "Port accessibility tests:"

# Test port 80
echo -n "Port 80 (HTTP): "
if timeout 5 bash -c "</dev/tcp/$PUBLIC_IP/80" 2>/dev/null; then
    echo "OPEN"
else
    echo "CLOSED/FILTERED"
fi

# Test port 443
echo -n "Port 443 (HTTPS): "
if timeout 5 bash -c "</dev/tcp/$PUBLIC_IP/443" 2>/dev/null; then
    echo "OPEN"
else
    echo "CLOSED/FILTERED"
fi

echo ""
echo "Test completed. If any tests fail, check:"
echo "1. Port forwarding configuration"
echo "2. Server firewall settings" 
echo "3. Daily Scribe service status"
echo "4. Router firewall settings"
```

### Manual Testing Methods

#### Test from External Network
1. **Use mobile hotspot**: Connect phone/laptop to mobile data
2. **Use external service**: Online port checkers
3. **Ask friend**: Test from different internet connection

#### Online Port Testing Tools
- **CanYouSeeMe.org**: Test specific ports
- **PortChecker.co**: Comprehensive port testing
- **YouGetSignal.com**: Port forwarding tester

#### Command Line Testing
```bash
# Test from external machine/VPS
curl -I http://your-public-ip
curl -I https://your-domain.duckdns.org

# Test specific ports
telnet your-public-ip 80
telnet your-public-ip 443
```

## Step 6: Network Security Monitoring

### Router Security Features to Enable

1. **Access Logging**: Enable logging of connection attempts
2. **Intrusion Detection**: If available on your router
3. **Automatic Firmware Updates**: Keep router security current
4. **Guest Network**: Isolate IoT devices from main network
5. **MAC Address Filtering**: For additional wireless security

### Monitoring Tools and Scripts

#### Log Analysis Script
```bash
#!/bin/bash
# analyze_router_logs.sh

# This script analyzes router logs for suspicious activity
LOG_FILE="/var/log/router.log"  # Adjust path as needed

echo "Router Security Log Analysis"
echo "============================"

# Check for common attack patterns
echo "Suspicious IP addresses (multiple connection attempts):"
grep -E "(DROP|BLOCK|DENY)" "$LOG_FILE" | awk '{print $4}' | sort | uniq -c | sort -nr | head -10

echo ""
echo "Port scan attempts:"
grep -i "port scan" "$LOG_FILE" || echo "No port scan attempts found"

echo ""
echo "Failed authentication attempts:"
grep -i "auth fail" "$LOG_FILE" || echo "No authentication failures found"

echo ""
echo "Recent blocked connections:"
grep -E "(DROP|BLOCK|DENY)" "$LOG_FILE" | tail -20
```

#### Network Monitoring with Simple Tools
```bash
# Monitor active connections to your server
sudo netstat -tnlp | grep :80
sudo netstat -tnlp | grep :443

# Monitor for unusual traffic patterns
sudo iftop -i eth0  # Replace eth0 with your interface

# Check for open ports
sudo nmap -sT localhost
```

## Step 7: ISP Considerations and Limitations

### Common ISP Restrictions

#### Residential Restrictions
- **Port 80 blocking**: Some ISPs block inbound port 80
- **Port 25 blocking**: SMTP port (doesn't affect Daily Scribe)
- **Dynamic IP changes**: Handled by DDNS
- **Bandwidth limits**: Monitor usage to avoid throttling

#### Business Considerations
- **Static IP service**: Consider for better reliability
- **Higher upload speeds**: Better for serving content
- **SLA guarantees**: Uptime commitments
- **No port restrictions**: All ports typically available

### Workarounds for Restrictions

#### If Port 80 is Blocked
1. **Use alternative port**: Forward external port 8080 to internal port 80
2. **HTTPS only**: Disable HTTP, use only port 443
3. **Cloudflare proxy**: Use Cloudflare's free proxy service

#### Configuration for Alternative Ports
```bash
# Update Caddyfile for non-standard port
yourdomain.duckdns.org:8080 {
    reverse_proxy app:8000
}

# Port forwarding rule
External Port: 8080 → Internal IP: 192.168.1.100, Port: 80
```

### Testing ISP Restrictions
```bash
# Test if port 80 is accessible from outside
# Run this from an external connection
curl -I http://your-public-ip:80

# Test alternative ports
curl -I http://your-public-ip:8080
```

## Step 8: Documentation and Maintenance

### Router Configuration Documentation Template

```markdown
# Daily Scribe Router Configuration

## Network Information
- Router Model: [Router Brand/Model]
- Router IP: 192.168.1.1
- Server IP: 192.168.1.100
- Network Range: 192.168.1.1-254

## DHCP Reservation
- MAC Address: [Server MAC Address]
- Reserved IP: 192.168.1.100
- Description: Daily Scribe Server

## Port Forwarding Rules
1. HTTP Traffic
   - External Port: 80
   - Internal IP: 192.168.1.100
   - Internal Port: 80
   - Protocol: TCP

2. HTTPS Traffic
   - External Port: 443
   - Internal IP: 192.168.1.100
   - Internal Port: 443
   - Protocol: TCP

## Security Settings
- SPI Firewall: Enabled
- DoS Protection: Enabled
- UPnP: Disabled
- WPS: Disabled
- Admin Password: [Changed from default]

## Backup Configuration
- Configuration backed up: [Date]
- Backup file location: [Path]

## Testing Results
- External HTTP test: [Pass/Fail]
- External HTTPS test: [Pass/Fail]
- Port 80 accessibility: [Open/Closed]
- Port 443 accessibility: [Open/Closed]
- Last tested: [Date]
```

### Maintenance Checklist

#### Monthly Tasks
- [ ] Test external connectivity
- [ ] Check router logs for suspicious activity
- [ ] Verify DDNS resolution
- [ ] Update router firmware if available

#### Quarterly Tasks
- [ ] Review and rotate admin passwords
- [ ] Backup router configuration
- [ ] Audit port forwarding rules
- [ ] Test failover procedures

#### Annual Tasks
- [ ] Complete security audit
- [ ] Review ISP service options
- [ ] Update network documentation
- [ ] Plan for hardware upgrades

## Troubleshooting Guide

### Common Issues and Solutions

#### "Cannot connect from external network"
**Possible Causes:**
1. Port forwarding not configured
2. Server firewall blocking connections
3. Router firewall too restrictive
4. ISP blocking ports
5. Server not running

**Solutions:**
1. Verify port forwarding rules
2. Check server firewall: `sudo ufw status`
3. Review router firewall settings
4. Test with alternative ports
5. Verify service status: `docker-compose ps`

#### "HTTPS not working"
**Possible Causes:**
1. Port 443 not forwarded
2. SSL certificate issues
3. Caddy not running
4. DNS not resolving

**Solutions:**
1. Add port 443 forwarding rule
2. Check Caddy logs: `docker-compose logs caddy`
3. Restart Caddy: `docker-compose restart caddy`
4. Test DNS: `dig yourdomain.duckdns.org`

#### "Intermittent connectivity"
**Possible Causes:**
1. Dynamic IP changes
2. Router stability issues
3. ISP throttling
4. Server resource constraints

**Solutions:**
1. Verify DDNS updates
2. Restart router
3. Monitor bandwidth usage
4. Check server resources: `htop`, `df -h`

### Emergency Access Procedures

If external access fails completely:

1. **Local Access**: Always ensure local access works
   ```bash
   curl http://192.168.1.100:8000/healthz
   ```

2. **VPN Access**: Set up VPN for emergency management
   ```bash
   # If OpenVPN is configured
   sudo openvpn client.ovpn
   ```

3. **Mobile Hotspot**: Use phone as internet source for testing

4. **Physical Access**: Direct console/keyboard access to server

5. **Recovery Mode**: Boot from USB if system issues

### Diagnostic Commands

```bash
# Network connectivity diagnostics
ping 8.8.8.8                    # Test internet connectivity
ping 192.168.1.1                # Test router connectivity
nslookup yourdomain.duckdns.org # Test DNS resolution
traceroute yourdomain.duckdns.org # Trace network path

# Port testing
sudo nmap -p 80,443 192.168.1.100      # Test local ports
nmap -p 80,443 your-public-ip           # Test external ports (from outside)

# Service status
docker-compose ps                        # Check container status
docker-compose logs app                  # Check application logs
curl -I http://localhost:8000/healthz   # Test local health endpoint
```

## Security Best Practices

### Router Security Hardening

1. **Change Default Credentials**
   - Use strong admin password
   - Change default username if possible
   - Enable two-factor authentication if available

2. **Firmware Management**
   - Enable automatic updates
   - Check for updates monthly
   - Monitor security advisories

3. **Network Segmentation**
   - Use guest network for IoT devices
   - Isolate server on separate VLAN if possible
   - Implement network access controls

4. **Monitoring and Logging**
   - Enable detailed logging
   - Set up log forwarding if possible
   - Monitor for anomalous traffic

### Ongoing Security Measures

1. **Regular Audits**
   - Review port forwarding rules quarterly
   - Audit connected devices monthly
   - Check for firmware updates weekly

2. **Incident Response**
   - Document response procedures
   - Have contact information ready
   - Plan for service isolation

3. **Backup and Recovery**
   - Backup router configuration
   - Document all settings
   - Test recovery procedures

This comprehensive guide should help you successfully configure port forwarding and router settings for your Daily Scribe deployment while maintaining security best practices.
