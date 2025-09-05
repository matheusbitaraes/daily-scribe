# Router Configuration Checklist for Daily Scribe

This checklist helps ensure your router is properly configured for Daily Scribe external access.

## Pre-Configuration Checklist

### Network Information Gathering
- [ ] Current server IP address: `_________________`
- [ ] Router/Gateway IP address: `_________________`
- [ ] Server MAC address: `_________________`
- [ ] Network range (e.g., 192.168.1.x): `_________________`
- [ ] Router admin username: `_________________`
- [ ] Router admin password: `_________________`

### Access Requirements
- [ ] Router admin interface accessible
- [ ] Administrative privileges confirmed
- [ ] Router firmware version noted: `_________________`
- [ ] Router model documented: `_________________`

## Static IP Configuration

Choose one method:

### Method A: DHCP Reservation (Recommended)
- [ ] Access router admin interface (usually http://192.168.1.1)
- [ ] Navigate to DHCP settings
- [ ] Add DHCP reservation:
  - [ ] MAC Address: `_________________`
  - [ ] Reserved IP: `_________________`
  - [ ] Description: "Daily Scribe Server"
- [ ] Save configuration
- [ ] Restart router if required
- [ ] Verify server gets assigned IP

### Method B: Static IP on Server
- [ ] Backup current network configuration
- [ ] Configure static IP using netplan or network scripts
- [ ] Apply configuration: `sudo netplan apply`
- [ ] Verify connectivity after change
- [ ] Update any dependent systems

## Port Forwarding Configuration

### Required Port Forwarding Rules

#### Rule 1: HTTP (Port 80)
- [ ] Service Name: "Daily Scribe HTTP"
- [ ] External Port: 80
- [ ] Internal IP: `_________________`
- [ ] Internal Port: 80
- [ ] Protocol: TCP
- [ ] Status: Enabled

#### Rule 2: HTTPS (Port 443)
- [ ] Service Name: "Daily Scribe HTTPS"
- [ ] External Port: 443
- [ ] Internal IP: `_________________`
- [ ] Internal Port: 443
- [ ] Protocol: TCP
- [ ] Status: Enabled

### Optional: SSH Access (If Required)
- [ ] Service Name: "Daily Scribe SSH"
- [ ] External Port: 2222 (non-standard for security)
- [ ] Internal IP: `_________________`
- [ ] Internal Port: 22
- [ ] Protocol: TCP
- [ ] Status: Enabled (if needed)

## Router Security Configuration

### Firewall Settings
- [ ] SPI (Stateful Packet Inspection) enabled
- [ ] DoS protection enabled
- [ ] Port scan detection enabled
- [ ] Access logging enabled
- [ ] Intrusion detection enabled (if available)

### Security Features
- [ ] Default admin password changed
- [ ] WPS disabled (unless specifically needed)
- [ ] UPnP disabled (recommended for security)
- [ ] Remote management disabled (unless needed)
- [ ] Guest network configured (if using IoT devices)

### Access Control
- [ ] MAC address filtering configured (optional)
- [ ] Access time restrictions set (optional)
- [ ] VPN server configured (optional, for secure remote access)

## Testing and Verification

### Internal Testing
- [ ] Server accessible from local network
- [ ] Static IP assignment working
- [ ] DNS resolution working locally
- [ ] Services responding on expected ports

### External Testing
- [ ] Port forwarding rules working
- [ ] External connectivity test passed
- [ ] DDNS domain resolving correctly
- [ ] HTTPS certificate working
- [ ] Health check endpoint accessible

### Security Testing
- [ ] Only required ports accessible
- [ ] Unauthorized ports properly blocked
- [ ] Router admin interface not externally accessible
- [ ] No unexpected open services

## Documentation

### Configuration Record
- [ ] Router configuration exported/backed up
- [ ] Port forwarding rules documented
- [ ] Static IP assignments recorded
- [ ] Security settings documented
- [ ] Admin credentials securely stored

### Network Diagram
- [ ] Network topology documented
- [ ] IP address assignments mapped
- [ ] Service endpoints documented
- [ ] External access paths documented

## Maintenance Schedule

### Weekly Tasks
- [ ] Check router logs for suspicious activity
- [ ] Verify external connectivity
- [ ] Monitor bandwidth usage
- [ ] Check service availability

### Monthly Tasks
- [ ] Review and rotate admin passwords
- [ ] Check for router firmware updates
- [ ] Audit port forwarding rules
- [ ] Test backup/recovery procedures

### Quarterly Tasks
- [ ] Complete security audit
- [ ] Review and update documentation
- [ ] Test disaster recovery procedures
- [ ] Evaluate performance and capacity

## Troubleshooting Reference

### Common Issues

#### "External connectivity fails"
**Check:**
- [ ] Port forwarding rules correct
- [ ] Server firewall not blocking
- [ ] Router firewall not blocking
- [ ] ISP not blocking ports
- [ ] Services actually running

#### "Intermittent connectivity"
**Check:**
- [ ] DDNS updates working
- [ ] Router stability
- [ ] ISP throttling
- [ ] Server resource constraints
- [ ] Network congestion

#### "HTTPS not working"
**Check:**
- [ ] Port 443 forwarded
- [ ] SSL certificate valid
- [ ] Caddy running properly
- [ ] DNS resolving correctly
- [ ] Certificate not expired

### Emergency Contacts
- ISP Support: `_________________`
- Network Administrator: `_________________`
- Daily Scribe Support: `_________________`

### Emergency Procedures
- [ ] Local access method documented
- [ ] VPN fallback configured
- [ ] Mobile hotspot procedure documented
- [ ] Physical access instructions documented

## Sign-off

### Configuration Completed By
- Name: `_________________`
- Date: `_________________`
- Signature: `_________________`

### Configuration Verified By
- Name: `_________________`
- Date: `_________________`
- Signature: `_________________`

### Review Schedule
- Next Review Date: `_________________`
- Review Frequency: Quarterly
- Responsible Person: `_________________`

---

**Note:** Keep this checklist with your router documentation and update it whenever configuration changes are made. This checklist should be reviewed during any network troubleshooting or when planning network changes.
