#!/bin/bash

# Health Check Script for AGI-V2 Services
# This script checks the health of all services in the Docker Compose setup

set -e

echo "🔍 AGI-V2 Health Check Starting..."
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to check service health
check_service() {
    local service_name=$1
    local health_url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service_name... "
    
    if curl -s -f -o /dev/null -w "%{http_code}" "$health_url" | grep -q "$expected_status"; then
        echo -e "${GREEN}✓ Healthy${NC}"
        return 0
    else
        echo -e "${RED}✗ Unhealthy${NC}"
        return 1
    fi
}

# Function to check Docker service status
check_docker_service() {
    local service_name=$1
    echo -n "Checking Docker service $service_name... "
    
    if docker-compose ps "$service_name" | grep -q "Up"; then
        echo -e "${GREEN}✓ Running${NC}"
        return 0
    else
        echo -e "${RED}✗ Not Running${NC}"
        return 1
    fi
}

# Check if Docker Compose is running
if ! docker-compose ps > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker Compose is not running${NC}"
    exit 1
fi

echo "📊 Docker Services Status:"
echo "-------------------------"

# Check Docker services
DOCKER_SERVICES=("postgres" "neo4j" "redis" "agi-backend" "agi-frontend")
docker_healthy=0

for service in "${DOCKER_SERVICES[@]}"; do
    if check_docker_service "$service"; then
        ((docker_healthy++))
    fi
done

echo ""
echo "🌐 HTTP Health Checks:"
echo "----------------------"

# Wait a moment for services to be ready
sleep 2

# Check HTTP endpoints
http_healthy=0
total_http_checks=0

# Backend health check
((total_http_checks++))
if check_service "Backend API" "http://localhost:8000/health/"; then
    ((http_healthy++))
fi

# Backend detailed health check
((total_http_checks++))
if check_service "Backend Detailed" "http://localhost:8000/health/detailed"; then
    ((http_healthy++))
fi

# Frontend health check
((total_http_checks++))
if check_service "Frontend" "http://localhost:3000/health"; then
    ((http_healthy++))
fi

# Neo4j health check
((total_http_checks++))
if check_service "Neo4j" "http://localhost:7474/"; then
    ((http_healthy++))
fi

echo ""
echo "📈 Summary:"
echo "----------"
echo "Docker Services: $docker_healthy/${#DOCKER_SERVICES[@]} healthy"
echo "HTTP Endpoints: $http_healthy/$total_http_checks healthy"

# Overall health status
total_services=$((${#DOCKER_SERVICES[@]} + total_http_checks))
total_healthy=$((docker_healthy + http_healthy))

if [ $total_healthy -eq $total_services ]; then
    echo -e "${GREEN}🎉 All services are healthy! ($total_healthy/$total_services)${NC}"
    exit 0
elif [ $total_healthy -gt $((total_services / 2)) ]; then
    echo -e "${YELLOW}⚠️  Some services are unhealthy ($total_healthy/$total_services)${NC}"
    exit 1
else
    echo -e "${RED}❌ Most services are unhealthy ($total_healthy/$total_services)${NC}"
    exit 2
fi