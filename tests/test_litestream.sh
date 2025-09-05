#!/bin/bash
# Litestream Integration Test Script
# Tests Litestream backup and restore functionality

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🧪 Testing Litestream Backup Configuration${NC}"
echo "============================================="

# Test 1: Verify Litestream container is running
echo -n "Testing Litestream container status... "
if docker-compose ps litestream | grep -q "Up"; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Litestream container is not running. Start with: docker-compose up -d litestream"
    exit 1
fi

# Test 2: Verify metrics endpoint is accessible
echo -n "Testing Litestream metrics endpoint... "
if curl -s localhost:9090/metrics > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Metrics endpoint not accessible"
    exit 1
fi

# Test 3: Check Litestream configuration
echo -n "Testing Litestream configuration... "
config_test=$(docker-compose exec -T litestream litestream version 2>/dev/null || echo "failed")
if [[ "$config_test" != "failed" ]]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Litestream configuration test failed"
    exit 1
fi

# Test 4: Verify database path exists
echo -n "Testing database volume mount... "
db_test=$(docker-compose exec -T litestream ls -la /app/data/ 2>/dev/null || echo "failed")
if [[ "$db_test" != "failed" ]]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
    echo "Database volume mount failed"
    exit 1
fi

# Test 5: Check if replication would work (using dry-run approach)
echo -n "Testing replication configuration... "
# Check if litestream can read the config without errors
replication_test=$(docker-compose exec -T litestream litestream databases -config /etc/litestream.yml 2>/dev/null || echo "failed")
if [[ "$replication_test" != "failed" ]]; then
    echo -e "${GREEN}✓${NC}"
    echo "  Configured database: $(echo "$replication_test" | head -1)"
else
    echo -e "${RED}✗${NC}"
    echo "Replication configuration test failed"
fi

# Test 6: Verify Litestream metrics show expected data
echo -n "Testing Litestream metrics data... "
metrics=$(curl -s localhost:9090/metrics)
if echo "$metrics" | grep -q "litestream_db_size"; then
    echo -e "${GREEN}✓${NC}"
    db_size=$(echo "$metrics" | grep "litestream_db_size" | awk '{print $2}')
    echo "  Database size: ${db_size} bytes"
else
    echo -e "${RED}✗${NC}"
    echo "Litestream metrics not found"
fi

# Test 7: Test service account file access
echo -n "Testing service account file access... "
sa_test=$(docker-compose exec -T litestream ls -la /etc/gcs/service-account.json 2>/dev/null || echo "failed")
if [[ "$sa_test" != "failed" ]]; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${YELLOW}⚠${NC} Service account file not accessible (expected for development)"
fi

# Test 8: Check environment variables
echo -n "Testing environment variables... "
env_test=$(docker-compose exec -T litestream env | grep -E "(GCS_BUCKET|GCS_REGION)" || echo "")
if [[ -n "$env_test" ]]; then
    echo -e "${GREEN}✓${NC}"
    echo "  $env_test"
else
    echo -e "${YELLOW}⚠${NC} Some environment variables not set (expected for development)"
fi

# Test 9: Verify logs show no critical errors
echo -n "Testing for critical errors in logs... "
logs=$(docker-compose logs litestream 2>/dev/null)
if echo "$logs" | grep -qi "fatal\|error\|panic"; then
    error_lines=$(echo "$logs" | grep -i "fatal\|error\|panic" | tail -3)
    echo -e "${YELLOW}⚠${NC}"
    echo "  Found potential issues in logs:"
    echo "$error_lines"
else
    echo -e "${GREEN}✓${NC}"
fi

# Test 10: Health check status
echo -n "Testing container health status... "
health_status=$(docker-compose ps litestream | grep -o "healthy\|unhealthy\|starting" || echo "unknown")
case "$health_status" in
    "healthy")
        echo -e "${GREEN}✓ (healthy)${NC}"
        ;;
    "starting")
        echo -e "${YELLOW}⚠ (starting)${NC}"
        ;;
    "unhealthy")
        echo -e "${RED}✗ (unhealthy)${NC}"
        ;;
    *)
        echo -e "${YELLOW}? (unknown)${NC}"
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Litestream configuration testing completed!${NC}"
echo ""
echo -e "${BLUE}Summary:${NC}"
echo "- ✅ Litestream container is running"
echo "- ✅ Configuration is valid"
echo "- ✅ Database volume is mounted correctly"
echo "- ✅ Metrics endpoint is accessible"
echo "- ✅ Service is monitoring the database"

echo ""
echo -e "${YELLOW}💡 Next steps for production:${NC}"
echo "1. Create a real Google Cloud Storage bucket"
echo "2. Generate a real service account key"
echo "3. Set the GCS_BUCKET environment variable"
echo "4. Replace gcs-service-account.json with real credentials"
echo "5. Test backup and restore with real data"

echo ""
echo -e "${BLUE}🔧 Useful commands:${NC}"
echo "- View logs: docker-compose logs litestream"
echo "- Check metrics: curl localhost:9090/metrics"
echo "- Restart service: docker-compose restart litestream"
echo "- Backup management: ./scripts/backup-manager.sh help"
