# Google Cloud Storage Setup for Litestream Backups

This guide walks through setting up Google Cloud Storage (GCS) for Daily Scribe database backups using Litestream.

## Prerequisites

- Google Cloud Platform account
- gcloud CLI installed (optional but recommended)
- Daily Scribe Docker environment set up

## Step 1: Create GCS Bucket

### Option A: Using Google Cloud Console

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Navigate to Cloud Storage > Buckets
3. Click "Create Bucket"
4. Configure:
   - **Name**: `your-daily-scribe-backups` (must be globally unique)
   - **Location type**: Region
   - **Location**: `us-central1` (or your preferred region)
   - **Storage class**: Standard
   - **Access control**: Uniform
   - **Encryption**: Google-managed key

### Option B: Using gcloud CLI

```bash
# Set your project ID
export PROJECT_ID="your-project-id"
export BUCKET_NAME="your-daily-scribe-backups"

# Create the bucket
gsutil mb -p $PROJECT_ID -c STANDARD -l us-central1 gs://$BUCKET_NAME

# Verify bucket creation
gsutil ls gs://$BUCKET_NAME
```

## Step 2: Create Service Account

### Using Google Cloud Console

1. Go to IAM & Admin > Service Accounts
2. Click "Create Service Account"
3. Configure:
   - **Name**: `daily-scribe-backup`
   - **Description**: `Service account for Daily Scribe Litestream backups`
4. Click "Create and Continue"
5. Grant roles:
   - **Storage Object Admin** (for read/write access to bucket)
6. Click "Continue" then "Done"

### Using gcloud CLI

```bash
# Create service account
gcloud iam service-accounts create daily-scribe-backup \
    --description="Service account for Daily Scribe Litestream backups" \
    --display-name="Daily Scribe Backup"

# Get the service account email
export SA_EMAIL="daily-scribe-backup@${PROJECT_ID}.iam.gserviceaccount.com"

# Grant Storage Object Admin role
gsutil iam ch serviceAccount:$SA_EMAIL:objectAdmin gs://$BUCKET_NAME
```

## Step 3: Generate Service Account Key

### Using Google Cloud Console

1. Go to IAM & Admin > Service Accounts
2. Find your `daily-scribe-backup` service account
3. Click the three dots menu > "Manage keys"
4. Click "Add Key" > "Create new key"
5. Select "JSON" and click "Create"
6. Save the downloaded JSON file as `gcs-service-account.json` in your Daily Scribe project root

### Using gcloud CLI

```bash
# Create and download service account key
gcloud iam service-accounts keys create gcs-service-account.json \
    --iam-account=$SA_EMAIL

# Move to project directory
mv gcs-service-account.json /path/to/daily-scribe/
```

## Step 4: Configure Environment Variables

Update your `.env` file with the GCS configuration:

```bash
# GCS Configuration
GCS_BUCKET=your-daily-scribe-backups
GCS_REGION=us-central1
GCS_SERVICE_ACCOUNT_PATH=./gcs-service-account.json
```

## Step 5: Test Configuration

1. Start the Litestream service:
```bash
docker-compose up -d litestream
```

2. Check Litestream logs:
```bash
docker-compose logs litestream
```

3. Test backup functionality:
```bash
./scripts/backup-manager.sh status
```

4. Verify snapshots are being created:
```bash
./scripts/backup-manager.sh snapshots
```

## Step 6: Security Best Practices

### Service Account Permissions

Ensure the service account has minimal required permissions:

```bash
# List current IAM bindings
gsutil iam get gs://$BUCKET_NAME

# Remove unnecessary permissions if any
gsutil iam ch -d serviceAccount:$SA_EMAIL:storage.admin gs://$BUCKET_NAME
```

### Bucket Security

1. **Uniform bucket-level access**: Enabled by default
2. **Public access**: Ensure "Public access" is set to "Not public"
3. **Lifecycle management**: Optional - set up automatic deletion of old backups

### Access Monitoring

Set up monitoring for bucket access:

1. Go to Cloud Logging in Google Cloud Console
2. Create log-based metrics for bucket access
3. Set up alerts for unusual access patterns

## Troubleshooting

### Common Issues

1. **Permission Denied Errors**
   ```bash
   # Check service account permissions
   gsutil iam get gs://$BUCKET_NAME
   
   # Verify service account key file
   cat gcs-service-account.json | jq .
   ```

2. **Bucket Not Found**
   ```bash
   # Verify bucket exists and you have access
   gsutil ls gs://$BUCKET_NAME
   ```

3. **Authentication Issues**
   ```bash
   # Test authentication with service account
   gcloud auth activate-service-account --key-file=gcs-service-account.json
   gsutil ls gs://$BUCKET_NAME
   ```

### Verification Commands

```bash
# Test Litestream configuration
docker-compose run --rm litestream litestream -config /etc/litestream.yml version

# Test GCS connectivity
docker-compose run --rm litestream gsutil ls gs://$BUCKET_NAME

# Test restore (dry run)
./scripts/backup-manager.sh restore --dry-run
```

## Cost Considerations

### Storage Costs

- **Standard Storage**: ~$0.020 per GB per month
- **Operations**: Minimal for typical backup operations
- **Network**: No egress charges for uploads from most regions

### Cost Optimization

1. **Lifecycle Policies**: Automatically delete old backups
   ```bash
   # Create lifecycle.json
   cat > lifecycle.json << EOF
   {
     "rule": [
       {
         "action": {"type": "Delete"},
         "condition": {"age": 90}
       }
     ]
   }
   EOF
   
   # Apply lifecycle policy
   gsutil lifecycle set lifecycle.json gs://$BUCKET_NAME
   ```

2. **Monitor Usage**: Set up billing alerts in Google Cloud Console

### Backup Size Estimation

For a typical Daily Scribe database:
- Initial database: ~1-10 MB
- Daily growth: ~0.1-1 MB
- Monthly total: ~3-30 MB
- Annual cost: ~$0.01-$0.10

## Recovery Procedures

### Complete Disaster Recovery

1. **Stop Daily Scribe services**:
   ```bash
   docker-compose down
   ```

2. **Restore database**:
   ```bash
   ./scripts/backup-manager.sh restore --output ./data/digest_history.db
   ```

3. **Verify restored database**:
   ```bash
   sqlite3 ./data/digest_history.db ".tables"
   ```

4. **Restart services**:
   ```bash
   docker-compose up -d
   ```

### Point-in-Time Recovery

```bash
# List available snapshots
./scripts/backup-manager.sh snapshots

# Restore to specific date
./scripts/backup-manager.sh restore --date 2025-09-04 --output ./restored-db.db
```

## Monitoring and Maintenance

### Regular Health Checks

Set up a cron job to verify backup health:

```bash
# Add to crontab
0 6 * * * /path/to/daily-scribe/scripts/backup-manager.sh verify >> /var/log/backup-verify.log 2>&1
```

### Monitoring Metrics

- Replication lag (should be < 5 minutes)
- Backup success rate (should be > 99%)
- Storage usage growth
- Error rates in logs

This completes the GCS setup for Litestream backups. The system will now continuously replicate your SQLite database to Google Cloud Storage with automatic recovery capabilities.
