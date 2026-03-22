# S3 File Manager Backend Makefile

.PHONY: help build up down restart logs shell test clean setup migrate

# Default target
help: ## Show this help message
	@echo "S3 File Manager Backend - Available Commands:"
	@echo "=============================================="
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

# Development commands
build: ## Build Docker image
	docker-compose build

up: ## Start the application
	docker-compose up -d

down: ## Stop the application
	docker-compose down

restart: ## Restart the application
	docker-compose restart

logs: ## View application logs
	docker-compose logs -f app

shell: ## Open shell in running container
	docker-compose exec app bash

# Database commands
migrate: ## Create and apply database migrations
	docker-compose exec app flask db migrate -m "Auto migration"
	docker-compose exec app flask db upgrade

migrate-create: ## Create a new migration (usage: make migrate-create MESSAGE="your message")
	docker-compose exec app flask db migrate -m "$(MESSAGE)"

migrate-upgrade: ## Apply pending migrations
	docker-compose exec app flask db upgrade

migrate-downgrade: ## Rollback last migration
	docker-compose exec app flask db downgrade

# Setup commands
setup: ## Run initial setup
	./setup.sh

init-db: ## Initialize database (first time only)
	docker-compose exec app flask db init
	docker-compose exec app flask db migrate -m "Initial migration"
	docker-compose exec app flask db upgrade

# Testing commands
test: ## Run tests
	docker-compose exec app python -m pytest

test-coverage: ## Run tests with coverage
	docker-compose exec app python -m pytest --cov=app

# Production commands (use FLASK_ENV=production in .env)
prod-build: ## Build production image
	docker-compose build

prod-up: ## Start production application
	docker-compose up -d

prod-down: ## Stop production application
	docker-compose down

prod-logs: ## View production logs
	docker-compose logs -f app

# Utility commands
clean: ## Clean up Docker resources
	docker-compose down -v
	docker system prune -f

status: ## Check application status
	@echo "Checking application status..."
	@curl -f http://localhost:5000/health && echo "✅ Application is healthy" || echo "❌ Application is not responding"

health: ## Check health endpoint
	curl -f http://localhost:5000/health | jq .

api-info: ## Get API information
	curl -f http://localhost:5000/api | jq .

# Development helpers
dev: ## Start development environment
	docker-compose up --build

dev-logs: ## View development logs
	docker-compose logs -f

# Backup commands
backup-db: ## Backup database
	docker-compose exec app mysqldump -u $(MYSQL_USER) -p$(MYSQL_PASSWORD) $(MYSQL_DB) > backup_$(shell date +%Y%m%d_%H%M%S).sql

# Environment commands
env-check: ## Check environment variables
	@echo "Checking environment variables..."
	@test -f .env && echo "✅ .env file exists" || echo "❌ .env file missing"
	@test -f .env && grep -q "SECRET_KEY" .env && echo "✅ SECRET_KEY is set" || echo "❌ SECRET_KEY is missing"
	@test -f .env && grep -q "MYSQL_HOST" .env && echo "✅ MYSQL_HOST is set" || echo "❌ MYSQL_HOST is missing"

# Quick start
quick-start: ## Quick start for new users
	@echo "🚀 Quick Start - S3 File Manager Backend"
	@echo "========================================"
	@echo "1. Copy environment file: cp env_example.txt .env"
	@echo "2. Edit .env with your configuration"
	@echo "3. Run setup: make setup"
	@echo "4. Check status: make status"
	@echo ""
	@echo "For more help, run: make help"
