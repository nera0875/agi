# AGI-V2 Development Makefile
# Provides convenient commands for development workflow

.PHONY: help setup build up down restart logs health clean test lint format

# Default target
help: ## Show this help message
	@echo "AGI-V2 Development Commands"
	@echo "=========================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}'

setup: ## Initial setup of the development environment
	@echo "🚀 Setting up AGI-V2 development environment..."
	@bash scripts/setup.sh

build: ## Build all Docker images
	@echo "🔨 Building Docker images..."
	@docker-compose build

up: ## Start all services
	@echo "⬆️  Starting services..."
	@docker-compose up -d

down: ## Stop all services
	@echo "⬇️  Stopping services..."
	@docker-compose down

restart: ## Restart all services
	@echo "🔄 Restarting services..."
	@docker-compose restart

logs: ## Show logs from all services
	@docker-compose logs -f

logs-backend: ## Show backend logs only
	@docker-compose logs -f agi-backend

logs-frontend: ## Show frontend logs only
	@docker-compose logs -f agi-frontend

logs-db: ## Show database logs
	@docker-compose logs -f postgres neo4j redis

health: ## Run health check on all services
	@echo "🔍 Running health check..."
	@bash scripts/health-check.sh

clean: ## Clean up Docker resources
	@echo "🧹 Cleaning up Docker resources..."
	@docker-compose down -v
	@docker system prune -f

clean-all: ## Clean up everything including images
	@echo "🧹 Cleaning up all Docker resources..."
	@docker-compose down -v --rmi all
	@docker system prune -af

test-backend: ## Run backend tests
	@echo "🧪 Running backend tests..."
	@docker-compose exec agi-backend pytest

lint-backend: ## Lint backend code
	@echo "🔍 Linting backend code..."
	@docker-compose exec agi-backend black --check .
	@docker-compose exec agi-backend isort --check-only .
	@docker-compose exec agi-backend mypy .

format-backend: ## Format backend code
	@echo "✨ Formatting backend code..."
	@docker-compose exec agi-backend black .
	@docker-compose exec agi-backend isort .

shell-backend: ## Open shell in backend container
	@docker-compose exec agi-backend bash

shell-frontend: ## Open shell in frontend container
	@docker-compose exec agi-frontend sh

shell-db: ## Open PostgreSQL shell
	@docker-compose exec postgres psql -U agi_user -d agi_db

shell-neo4j: ## Open Neo4j shell
	@docker-compose exec neo4j cypher-shell -u neo4j -p password

shell-redis: ## Open Redis shell
	@docker-compose exec redis redis-cli

dev: ## Start development environment
	@echo "🚀 Starting development environment..."
	@make up
	@sleep 5
	@make health

prod: ## Start production environment
	@echo "🚀 Starting production environment..."
	@docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

status: ## Show status of all services
	@echo "📊 Service Status:"
	@docker-compose ps

backup-db: ## Backup PostgreSQL database
	@echo "💾 Backing up database..."
	@docker-compose exec postgres pg_dump -U agi_user agi_db > backup_$(shell date +%Y%m%d_%H%M%S).sql

restore-db: ## Restore PostgreSQL database (requires BACKUP_FILE variable)
	@echo "📥 Restoring database from $(BACKUP_FILE)..."
	@docker-compose exec -T postgres psql -U agi_user -d agi_db < $(BACKUP_FILE)

install-deps: ## Install development dependencies
	@echo "📦 Installing dependencies..."
	@cd backend && pip install -r requirements.txt
	@cd frontend && npm install

update-deps: ## Update dependencies
	@echo "🔄 Updating dependencies..."
	@cd backend && pip install -r requirements.txt --upgrade
	@cd frontend && npm update