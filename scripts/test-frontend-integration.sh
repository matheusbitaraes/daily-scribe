#!/bin/bash

# Frontend Docker Integration Test Script
# This script tests the Docker Compose setup for the frontend integration

set -e

echo "🧪 Testing Daily Scribe Frontend Docker Integration"
echo "=================================================="

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test functions
test_docker_compose_syntax() {
    echo "📋 Testing docker-compose.yml syntax..."
    docker-compose config > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ docker-compose.yml syntax is valid${NC}"
    else
        echo -e "${RED}❌ docker-compose.yml syntax error${NC}"
        exit 1
    fi
}

test_frontend_dockerfile() {
    echo "🐳 Testing frontend Dockerfile..."
    cd frontend
    docker build --target build -t daily-scribe-frontend-test . > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Frontend Dockerfile builds successfully${NC}"
        docker rmi daily-scribe-frontend-test > /dev/null 2>&1 || true
    else
        echo -e "${RED}❌ Frontend Dockerfile build failed${NC}"
        exit 1
    fi
    cd ..
}

test_nginx_config() {
    echo "🌐 Testing Nginx configuration..."
    docker run --rm -v "$(pwd)/frontend/nginx.conf:/etc/nginx/nginx.conf:ro" nginx:alpine nginx -t > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Nginx configuration is valid${NC}"
    else
        echo -e "${RED}❌ Nginx configuration error${NC}"
        exit 1
    fi
}

test_caddy_config() {
    echo "🎯 Testing Caddy configuration..."
    docker run --rm -v "$(pwd)/Caddyfile:/etc/caddy/Caddyfile:ro" caddy:2.7-alpine caddy validate --config /etc/caddy/Caddyfile > /dev/null 2>&1
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}✅ Caddyfile configuration is valid${NC}"
    else
        echo -e "${RED}❌ Caddyfile configuration error${NC}"
        exit 1
    fi
}

test_environment_files() {
    echo "🔧 Testing environment configuration..."
    if [ -f "frontend/.env.production" ]; then
        if grep -q "REACT_APP_API_URL" frontend/.env.production; then
            echo -e "${GREEN}✅ Frontend environment configuration found${NC}"
        else
            echo -e "${YELLOW}⚠️  Frontend environment missing REACT_APP_API_URL${NC}"
        fi
    else
        echo -e "${YELLOW}⚠️  Frontend .env.production file not found${NC}"
    fi
}

test_service_dependencies() {
    echo "🔗 Testing service dependencies..."
    
    # Check if frontend service exists
    if docker-compose config | grep -q "frontend:"; then
        echo -e "${GREEN}✅ Frontend service defined${NC}"
    else
        echo -e "${RED}❌ Frontend service not found${NC}"
        exit 1
    fi
    
    # Check if caddy depends on frontend
    if docker-compose config | grep -A 10 "caddy:" | grep -q "frontend"; then
        echo -e "${GREEN}✅ Caddy service depends on frontend${NC}"
    else
        echo -e "${YELLOW}⚠️  Caddy service dependency on frontend not found${NC}"
    fi
}

# Main test execution
echo "Starting tests..."
echo

test_docker_compose_syntax
test_frontend_dockerfile
test_nginx_config
test_caddy_config
test_environment_files
test_service_dependencies

echo
echo -e "${GREEN}🎉 All tests passed! Frontend Docker integration is ready.${NC}"
echo
echo "📝 Next steps:"
echo "1. Set DOMAIN environment variable: export DOMAIN=daily-scribe.duckdns.org"
echo "2. Start services: docker-compose up -d"
echo "3. Check services: docker-compose ps"
echo "4. Access frontend: http://daily-scribe.duckdns.org/"
echo
echo "🔍 Troubleshooting:"
echo "- Check logs: docker-compose logs frontend"
echo "- Check Caddy: docker-compose logs caddy"
echo "- View service status: docker-compose ps"
