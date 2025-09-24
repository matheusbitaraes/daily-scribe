# Elasticsearch Migration Guide

This guide provides comprehensive instructions for migrating data from SQLite to Elasticsearch in the Daily Scribe application.

## Overview

The migration infrastructure provides:
- **Batch Processing**: Handles large datasets efficiently with configurable batch sizes
- **Progress Tracking**: Real-time progress monitoring with ETA calculations
- **Resume Capability**: Can resume interrupted migrations from the last checkpoint
- **Data Validation**: Validates migrated data integrity and counts
- **Rollback Support**: Ability to rollback migrations if needed
- **Comprehensive Logging**: Detailed logs for monitoring and debugging

## Prerequisites

1. **Elasticsearch Server**: Must be running and accessible
2. **Environment Configuration**: Required environment variables set
3. **Database Access**: SQLite database with existing data
4. **Python Dependencies**: All required packages installed

### Environment Variables

```bash
ELASTICSEARCH_ENABLED=true
ELASTICSEARCH_HOST=localhost
ELASTICSEARCH_PORT=9200
ELASTICSEARCH_INDEX_PREFIX=daily_scribe
SQLITE_DB_PATH=data/digest_history.db
```

## Migration Process

### 1. Pre-Migration Checklist

Before starting migration, verify:

```bash
# Check Elasticsearch health
curl -X GET "localhost:9200/_cluster/health"

# Verify database exists and has data
sqlite3 data/digest_history.db "SELECT COUNT(*) FROM articles;"

# Check available disk space (ES needs ~2-3x data size)
df -h
```

### 2. Running Migration

#### Option A: Full Migration (Recommended)

```bash
# Run complete migration with validation
python src/migrations/migrate_cli.py migrate-all --validate

# With custom batch size for performance tuning
python src/migrations/migrate_cli.py migrate-all --batch-size 200 --validate
```

#### Option B: Incremental Migration

```bash
# Migrate sources first (required for articles)
python src/migrations/migrate_cli.py migrate-sources

# Migrate articles (largest dataset)
python src/migrations/migrate_cli.py migrate-articles

# Migrate user preferences
python src/migrations/migrate_cli.py migrate-users
```

### 3. Monitoring Progress

```bash
# Check migration status
python src/migrations/migrate_cli.py status

# Monitor logs in real-time
tail -f migration.log
```

## Data Mapping

### Articles Migration

**SQLite → Elasticsearch Transformation:**

| SQLite Field | Elasticsearch Field | Transformation |
|--------------|-------------------|----------------|
| `id` | `id` | Direct mapping |
| `url` | `url` | Direct mapping |
| `title` | `title` | Direct mapping |
| `title_pt` | `title_pt` | Direct mapping |
| `summary` | `summary` | Direct mapping |
| `summary_pt` | `summary_pt` | Direct mapping |
| `keywords` | `keywords` | CSV → Array |
| `published_at` | `published_at` | ISO format |
| `processed_at` | `processed_at` | ISO format |
| `embedding` (BLOB) | `embedding` | Pickle → Array |

### User Preferences Migration

**SQLite → Elasticsearch Transformation:**

| SQLite Field | Elasticsearch Field | Transformation |
|--------------|-------------------|----------------|
| `enabled_sources` | `enabled_sources` | CSV → Integer Array |
| `enabled_categories` | `enabled_categories` | CSV → String Array |
| `keywords` | `keywords` | CSV → String Array |
| `updated_at` | `updated_at` | ISO format |

### Sources Migration

**SQLite → Elasticsearch Transformation:**

| SQLite Field | Elasticsearch Field | Transformation |
|--------------|-------------------|----------------|
| `id` | `id` | Direct mapping |
| `name` | `name` | Direct mapping |
| N/A | `description` | Generated |
| N/A | `category` | Default: "General" |
| N/A | `country` | Default: "BR" |
| N/A | `language` | Default: "pt" |
| N/A | `reliability_score` | Default: 0.8 |

## Performance Optimization

### Batch Size Tuning

| Data Size | Recommended Batch Size | Memory Usage |
|-----------|----------------------|--------------|
| < 10K records | 100 | Low |
| 10K - 100K | 500 | Medium |
| 100K - 1M | 1000 | High |
| > 1M | 2000 | Very High |

### Memory Considerations

- **Articles with Embeddings**: ~150KB per article (1536-dim vectors)
- **Batch Memory**: `batch_size × 150KB × 2` (processing buffer)
- **Recommended System Memory**: 8GB+ for large datasets

### Network Optimization

```bash
# For remote Elasticsearch clusters
export ELASTICSEARCH_TIMEOUT=60
export ELASTICSEARCH_MAX_RETRIES=5
export ELASTICSEARCH_RETRY_ON_TIMEOUT=true
```

## Troubleshooting

### Common Issues

#### 1. Out of Memory Errors

**Symptoms**: Java heap space errors, Python memory errors
**Solutions**:
- Reduce batch size: `--batch-size 50`
- Increase ES heap: `ES_JAVA_OPTS="-Xms2g -Xmx4g"`
- Monitor system memory usage

#### 2. Connection Timeouts

**Symptoms**: Connection timeout errors, network unreachable
**Solutions**:
- Increase timeout: `ELASTICSEARCH_TIMEOUT=120`
- Check network connectivity
- Verify Elasticsearch is running

#### 3. Index Creation Failures

**Symptoms**: Mapping conflicts, index already exists
**Solutions**:
```bash
# Delete existing indices and restart
python src/migrations/migrate_cli.py rollback --confirm

# Recreate with correct mappings
python src/migrations/migrate_cli.py migrate-all
```

#### 4. Data Validation Failures

**Symptoms**: Count mismatches, sample validation errors
**Solutions**:
```bash
# Check detailed validation
python src/migrations/migrate_cli.py validate

# Re-run specific migration
python src/migrations/migrate_cli.py migrate-articles --no-resume
```

### Recovery Procedures

#### Resume Interrupted Migration

```bash
# Migration automatically resumes from last checkpoint
python src/migrations/migrate_cli.py migrate-all

# Force restart from beginning
python src/migrations/migrate_cli.py migrate-all --no-resume
```

#### Complete Rollback

```bash
# Rollback all data
python src/migrations/migrate_cli.py rollback --confirm

# Reset migration state
python src/migrations/migrate_cli.py reset-state --confirm

# Start fresh migration
python src/migrations/migrate_cli.py migrate-all
```

#### Partial Rollback

```bash
# Rollback specific data types
python src/migrations/migrate_cli.py rollback --data-types articles,sources --confirm
```

## Validation and Testing

### Data Integrity Checks

```bash
# Run comprehensive validation
python src/migrations/migrate_cli.py validate

# Manual count verification
sqlite3 data/digest_history.db "SELECT COUNT(*) FROM articles;"
curl -X GET "localhost:9200/daily_scribe_articles/_count"
```

### Search Functionality Testing

```bash
# Test basic search
curl -X POST "localhost:9200/daily_scribe_articles/_search" \
  -H 'Content-Type: application/json' \
  -d '{"query": {"match": {"title": "technology"}}}'

# Test vector search (if embeddings migrated)
curl -X POST "localhost:9200/daily_scribe_articles/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "query": {
      "script_score": {
        "query": {"match_all": {}},
        "script": {
          "source": "cosineSimilarity(params.query_vector, '\''embedding'\'') + 1.0",
          "params": {"query_vector": [0.1, 0.2, ...]}
        }
      }
    }
  }'
```

## Monitoring and Maintenance

### Migration Logs

- **Location**: `migration.log`
- **Format**: Timestamp, component, level, message
- **Rotation**: Automatic rotation at 10MB

### Performance Metrics

Monitor during migration:
- **CPU Usage**: Should be moderate (50-70%)
- **Memory Usage**: Depends on batch size
- **Disk I/O**: High during bulk indexing
- **Network**: High if ES is remote

### Post-Migration Tasks

1. **Index Optimization**:
```bash
curl -X POST "localhost:9200/daily_scribe_*/_forcemerge?max_num_segments=1"
```

2. **Alias Creation**:
```bash
curl -X POST "localhost:9200/_aliases" \
  -H 'Content-Type: application/json' \
  -d '{
    "actions": [
      {"add": {"index": "daily_scribe_articles", "alias": "articles"}},
      {"add": {"index": "daily_scribe_users", "alias": "users"}}
    ]
  }'
```

3. **Backup Configuration**:
```bash
# Create repository
curl -X PUT "localhost:9200/_snapshot/backup_repo" \
  -H 'Content-Type: application/json' \
  -d '{"type": "fs", "settings": {"location": "/backup/elasticsearch"}}'

# Create snapshot
curl -X PUT "localhost:9200/_snapshot/backup_repo/migration_backup"
```

## Production Deployment

### Pre-Production Testing

1. **Load Testing**: Test with production data size
2. **Performance Benchmarking**: Measure search response times
3. **Failover Testing**: Test with ES unavailable
4. **Data Consistency**: Verify ongoing sync mechanisms

### Deployment Strategy

1. **Blue-Green Deployment**:
   - Keep SQLite as primary during initial ES deployment
   - Gradually shift read traffic to ES
   - Maintain dual-write until fully validated

2. **Gradual Migration**:
   - Migrate historical data first
   - Enable dual-write for new data
   - Validate consistency over time

3. **Rollback Plan**:
   - Document exact rollback procedures
   - Test rollback in staging environment
   - Maintain SQLite backup during transition

## API Integration

After successful migration, update application code:

```python
# Example: Search service integration
from components.search.elasticsearch_service import ElasticsearchService

es_service = ElasticsearchService()

# Search articles
results = es_service.search('articles', {
    'query': {
        'bool': {
            'must': [
                {'match': {'title': 'technology'}},
                {'range': {'published_at': {'gte': '2025-01-01'}}}
            ]
        }
    }
})

# Vector similarity search
similarity_results = es_service.search('articles', {
    'query': {
        'script_score': {
            'query': {'match_all': {}},
            'script': {
                'source': "cosineSimilarity(params.query_vector, 'embedding') + 1.0",
                'params': {'query_vector': user_embedding}
            }
        }
    }
})
```

## Support and Resources

### Log Analysis

```bash
# Common search patterns for logs
grep "ERROR" migration.log
grep "Failed to" migration.log
grep -E "Migration.*completed" migration.log
```

### Elasticsearch Cluster Monitoring

```bash
# Cluster health
curl -X GET "localhost:9200/_cluster/health?pretty"

# Index statistics
curl -X GET "localhost:9200/_cat/indices/daily_scribe_*?v"

# Node information
curl -X GET "localhost:9200/_cat/nodes?v"
```

### Performance Profiling

```bash
# Enable search profiling
curl -X POST "localhost:9200/daily_scribe_articles/_search" \
  -H 'Content-Type: application/json' \
  -d '{
    "profile": true,
    "query": {"match": {"title": "test"}}
  }'
```

This migration guide provides comprehensive coverage for successfully migrating from SQLite to Elasticsearch while maintaining data integrity and application performance.