# K-Scan Security Audit System - Docker Management
# Usage: make <command>

.PHONY: help build up down logs shell test clean prod dev status backup

# Default target
help: ## Show this help message
	@echo "🔒 K-Scan Docker Management Commands"
	@echo ""
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "\033[36m%-15s\033[0m %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Development Commands
dev: ## Start development environment with hot reload
	@echo "🚀 Starting K-Scan in development mode..."
	docker-compose up -d
	@echo "✅ Development environment started"
	@echo "📖 API Docs: http://localhost:8000/docs"
	@echo "🏥 Health: http://localhost:8000/health"

build: ## Build the Docker image
	@echo "🔨 Building K-Scan Docker image..."
	docker-compose build --no-cache

up: ## Start the application
	@echo "⬆️ Starting K-Scan..."
	docker-compose up -d

down: ## Stop the application
	@echo "⬇️ Stopping K-Scan..."
	docker-compose down

restart: down up ## Restart the application

# Production Commands
prod: ## Start production environment
	@echo "🏭 Starting K-Scan in production mode..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
	@echo "✅ Production environment started"

prod-build: ## Build production image
	@echo "🔨 Building K-Scan production image..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml build --no-cache

prod-down: ## Stop production environment
	@echo "⬇️ Stopping K-Scan production..."
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml down

# Monitoring Commands
logs: ## Show application logs
	docker-compose logs -f k-scan

logs-all: ## Show all service logs
	docker-compose logs -f

status: ## Show service status
	@echo "📊 K-Scan Service Status:"
	docker-compose ps
	@echo ""
	@echo "🏥 Health Check:"
	@curl -s http://localhost:8000/health | jq '.' 2>/dev/null || curl -s http://localhost:8000/health

# Development Tools
shell: ## Access application shell
	docker-compose exec k-scan bash

test: ## Run tests inside container
	docker-compose exec k-scan python -m pytest tests/ -v

lint: ## Run code linting
	docker-compose exec k-scan python -m black src/
	docker-compose exec k-scan python -m isort src/

# Database Commands
db-shell: ## Access database shell
	docker-compose exec postgres psql -U k_scan_user -d k_scan

backup: ## Backup database
	@echo "💾 Creating database backup..."
	@mkdir -p backups
	@if docker-compose ps postgres | grep -q "Up"; then \
		docker-compose exec -T postgres pg_dump -U k_scan_user k_scan > backups/k_scan_$$(date +%Y%m%d_%H%M%S).sql; \
		echo "✅ PostgreSQL backup created in backups/"; \
	else \
		docker-compose exec k-scan cp /app/data/k_scan.db /tmp/backup.db 2>/dev/null && \
		docker cp $$(docker-compose ps -q k-scan):/tmp/backup.db backups/k_scan_$$(date +%Y%m%d_%H%M%S).db && \
		echo "✅ SQLite backup created in backups/"; \
	fi

# Maintenance Commands
clean: ## Clean up containers, images, and volumes
	@echo "🧹 Cleaning up Docker resources..."
	docker-compose down -v --remove-orphans
	docker system prune -f
	@echo "✅ Cleanup completed"

reset: clean ## Reset everything and start fresh
	@echo "🔄 Resetting K-Scan environment..."
	docker-compose up -d --build
	@echo "✅ Environment reset completed"

update: ## Update and restart application
	@echo "🔄 Updating K-Scan..."
	git pull origin main
	docker-compose down
	docker-compose build --no-cache
	docker-compose up -d
	@echo "✅ Update completed"

# Environment Setup
setup: ## Initial setup for new installation
	@echo "⚙️ Setting up K-Scan environment..."
	@if [ ! -f .env ]; then \
		echo "📝 Creating .env file..."; \
		echo "# K-Scan Environment Configuration" > .env; \
		echo "OPENAI_API_KEY=your-openai-api-key-here" >> .env; \
		echo "BROWSERLESS_TOKEN=" >> .env; \
		echo "DATABASE_URL=sqlite:///data/k_scan.db" >> .env; \
		echo "DEBUG=false" >> .env; \
		echo "⚠️  Please edit .env file and add your OpenAI API key"; \
	else \
		echo "✅ .env file already exists"; \
	fi
	@make build
	@echo "✅ Setup completed. Don't forget to configure your .env file!"

# Security Commands
security-scan: ## Run security scan on the application
	docker-compose exec k-scan python -m bandit -r src/ -f json -o /tmp/security-report.json
	docker-compose exec k-scan cat /tmp/security-report.json

audit: ## Quick security audit of example.com
	@echo "🔍 Running quick security audit..."
	@curl -s "http://localhost:8000/audit/quick?url=https://example.com" | jq '.'

# Utility Commands
check-deps: ## Check if required dependencies are installed
	@echo "✅ Checking dependencies..."
	@command -v docker >/dev/null 2>&1 || { echo "❌ Docker is required"; exit 1; }
	@command -v docker-compose >/dev/null 2>&1 || { echo "❌ Docker Compose is required"; exit 1; }
	@echo "✅ All dependencies are installed"

env-check: ## Validate environment configuration
	@echo "🔍 Checking environment configuration..."
	@if [ -f .env ]; then \
		echo "✅ .env file exists"; \
		if grep -q "your-openai-api-key-here" .env; then \
			echo "⚠️  Please set your OpenAI API key in .env"; \
		else \
			echo "✅ OpenAI API key is configured"; \
		fi; \
	else \
		echo "❌ .env file missing. Run 'make setup' first"; \
	fi

# Quick Start
quickstart: setup dev status ## Complete setup and start development environment
	@echo "🎉 K-Scan is ready!"
	@echo "📖 Visit: http://localhost:8000/docs"

# Documentation
docs: ## Open API documentation in browser
	@echo "📖 Opening API documentation..."
	@command -v open >/dev/null 2>&1 && open http://localhost:8000/docs || \
	command -v xdg-open >/dev/null 2>&1 && xdg-open http://localhost:8000/docs || \
	echo "Please visit: http://localhost:8000/docs" 