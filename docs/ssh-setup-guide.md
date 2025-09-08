# Quick SSH Setup for Daily Scribe Deployment

Follow these steps to set up SSH access to your server before running the deployment script.

## Option 1: SSH Key Setup (Recommended)

### 1. Generate SSH key (if you don't have one)
```bash
# Generate a new SSH key pair
ssh-keygen -t rsa -b 4096 -C "your-email@example.com"

# Press Enter to accept default file location
# Enter a passphrase (optional but recommended)
```

### 2. Copy SSH key to server
```bash
# Copy your public key to the server
ssh-copy-id matheus@192.168.15.55

# You'll be prompted for the server password
```

### 3. Test SSH connection
```bash
# Test passwordless SSH login
ssh matheus@192.168.15.55 'echo "SSH key setup successful"'
```

## Option 2: Password Authentication (Less Secure)

If you prefer password authentication:

### 1. Test SSH connection with password
```bash
ssh matheus@192.168.15.55
# Enter password when prompted
```

### 2. Install rsync on your local machine (if not present)
```bash
# On macOS
brew install rsync

# On Ubuntu/Debian
sudo apt install rsync
```

## Deploy Daily Scribe

Once SSH access is working, deploy Daily Scribe:

### 1. Basic deployment
```bash
cd /Users/Matheus/daily-scribe
./scripts/deploy-to-server.sh
```

### 2. Production deployment with monitoring
```bash
./scripts/deploy-to-server.sh --production
```

### 3. Custom deployment options
```bash
# Skip Docker installation if already installed
./scripts/deploy-to-server.sh --skip-docker

# Deploy without monitoring
./scripts/deploy-to-server.sh --no-monitoring

# Skip firewall configuration
./scripts/deploy-to-server.sh --skip-firewall
```

### 4. Enable database administration (optional)
```bash
# Start CloudBeaver for database management
ssh matheus@192.168.15.55 'cd daily-scribe && docker-compose --profile admin up -d cloudbeaver'
```

## What the Deployment Script Does

1. **Tests SSH connectivity** to your server
2. **Checks server requirements** (OS, memory, disk space)
3. **Installs Docker and Docker Compose** (if not present)
4. **Configures firewall** (UFW) with proper ports
5. **Syncs application files** to the server
6. **Sets up environment configuration** (.env file)
7. **Creates necessary directories** and sets permissions
8. **Starts Daily Scribe services** (app, caddy, cron, etc.)
9. **Sets up monitoring** (Prometheus, Grafana, etc.)
10. **Validates the deployment** to ensure everything works

## After Deployment

### 1. Configure environment variables on server
```bash
ssh matheus@192.168.15.55
cd daily-scribe
nano .env
```

### 2. Set up your router
- Forward ports 80 and 443 to 192.168.15.55
- Configure static IP or DHCP reservation for your server

### 3. Configure DDNS (in .env file)
```bash
# Example for DuckDNS
DDNS_PROVIDER=duckdns
DDNS_DOMAIN=yourdomain.duckdns.org
DDNS_TOKEN=your-duckdns-token
```

### 4. Test the deployment
```bash
ssh matheus@192.168.15.55
cd daily-scribe
./scripts/validate-deployment.sh
```

### 5. Test external access
```bash
# On the server
./scripts/validate-port-forwarding.sh --domain yourdomain.duckdns.org
```

## Monitoring Access

After deployment with monitoring enabled:

- **Application**: http://daily-scribe.duckdns.org/
- **Grafana**: http://daily-scribe.duckdns.org:3000 (admin/admin)
- **Prometheus**: http://daily-scribe.duckdns.org:9092
- **Database Admin (CloudBeaver)**: http://daily-scribe.duckdns.org:8080
- **Status Page**: http://daily-scribe.duckdns.org/static/status.html

### Database Access with CloudBeaver

To access and manipulate your SQLite database:

1. **Start CloudBeaver** (if not already running):
   ```bash
   ssh matheus@192.168.15.55 'cd daily-scribe && docker-compose --profile admin up -d cloudbeaver'
   ```

2. **Open CloudBeaver** in your browser: http://daily-scribe.duckdns.org:8080

3. **Initial Setup** (first time only):
   - **Admin Username**: admin
   - **Admin Password**: admin
   - Complete the initial configuration wizard

4. **Add SQLite Database Connection**:
   - Click "**+ Add**" to create a new connection
   - Select "**SQLite**" as the database type
   - **Database path**: `/data/digest_history.db`
   - **Name**: Daily Scribe Database (or any name you prefer)
   - Click "**Create**" and then "**Connect**"

5. **Browse and edit** your database:
   - Navigate through database tables in the left panel
   - Run SQL queries in the SQL editor
   - View and edit data in a spreadsheet-like interface
   - Export data in various formats
   - Advanced features like query history, bookmarks, and more

6. **Stop CloudBeaver** when done (optional):
   ```bash
   ssh matheus@192.168.15.55 'cd daily-scribe && docker-compose stop cloudbeaver'
   ```

## Troubleshooting

### SSH Issues
```bash
# Check SSH service on server
ssh matheus@192.168.15.55 'sudo systemctl status ssh'

# Check firewall on server
ssh matheus@192.168.15.55 'sudo ufw status'
```

### Deployment Issues
```bash
# Check Docker status
ssh matheus@192.168.15.55 'docker --version && docker-compose --version'

# Check running services
ssh matheus@192.168.15.55 'cd daily-scribe && docker-compose ps'

# View logs
ssh matheus@192.168.15.55 'cd daily-scribe && docker-compose logs'
```

## Security Notes

- The firewall is configured to allow only necessary ports (22, 80, 443)
- Monitoring ports (3000, 9090) are restricted to local network access
- Consider changing default passwords for Grafana and other services
- Regularly update the system and Docker images

Ready to deploy? Run the deployment script!
