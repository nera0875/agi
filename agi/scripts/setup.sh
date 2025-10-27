#!/bin/bash

# =============================================================================
# AGI-V2 Docker Infrastructure Setup Script
# =============================================================================
# This script sets up the complete Docker infrastructure for AGI-v2
# Usage: ./scripts/setup.sh [--prod]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="AGI-v2"
COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"
ENV_EXAMPLE=".env.example"

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_requirements() {
    log_info "Vérification des prérequis..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker n'est pas installé. Veuillez installer Docker."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
        log_error "Docker Compose n'est pas installé. Veuillez installer Docker Compose."
        exit 1
    fi
    
    log_success "Prérequis vérifiés"
}

setup_environment() {
    log_info "Configuration de l'environnement..."
    
    if [ ! -f "$ENV_FILE" ]; then
        if [ -f "$ENV_EXAMPLE" ]; then
            cp "$ENV_EXAMPLE" "$ENV_FILE"
            log_warning "Fichier .env créé à partir de .env.example"
            log_warning "IMPORTANT: Veuillez configurer vos clés API dans le fichier .env"
        else
            log_error "Fichier .env.example introuvable"
            exit 1
        fi
    else
        log_info "Fichier .env existant trouvé"
    fi
}

create_directories() {
    log_info "Création des répertoires nécessaires..."
    
    # Create log directories
    mkdir -p backend/logs
    mkdir -p frontend/logs
    
    # Create data directories for volumes
    mkdir -p data/postgres
    mkdir -p data/neo4j
    mkdir -p data/redis
    
    log_success "Répertoires créés"
}

build_services() {
    log_info "Construction des services Docker..."
    
    if command -v docker-compose &> /dev/null; then
        docker-compose build --no-cache
    else
        docker compose build --no-cache
    fi
    
    log_success "Services construits"
}

start_infrastructure() {
    log_info "Démarrage de l'infrastructure..."
    
    # Start database services first
    log_info "Démarrage des bases de données..."
    if command -v docker-compose &> /dev/null; then
        docker-compose up -d postgres neo4j redis
    else
        docker compose up -d postgres neo4j redis
    fi
    
    # Wait for databases to be ready
    log