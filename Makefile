# Makefile for Bizio CRM

.PHONY: help install test run docker-up docker-down seed migrate clean

help: ## Show this help message
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Available targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-15s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Install dependencies
	cd backend && pip install -r requirements.txt

test: ## Run tests
	cd backend && pytest -v

test-cov: ## Run tests with coverage
	cd backend && pytest --cov=app --cov-report=html --cov-report=term

run: ## Run backend locally
	cd backend && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

worker: ## Run Celery worker
	cd backend && celery -A worker.worker worker --loglevel=info

docker-up: ## Start all services with Docker Compose
	docker-compose up --build

docker-down: ## Stop all Docker services
	docker-compose down

docker-logs: ## View Docker logs
	docker-compose logs -f

seed: ## Seed demo data
	cd backend && python seed_data.py

migrate: ## Run Alembic migrations
	cd backend && alembic upgrade head

migrate-create: ## Create new migration
	cd backend && alembic revision --autogenerate -m "$(msg)"

clean: ## Clean temporary files
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	find . -type f -name "*.pyo" -delete
	find . -type f -name "*.log" -delete
	rm -rf backend/htmlcov
	rm -rf backend/.pytest_cache
	rm -rf backend/.coverage
	rm -f backend/dev.db

format: ## Format code with black
	cd backend && black app/ tests/

lint: ## Lint code
	cd backend && flake8 app/ tests/

docs: ## Open API documentation
	open http://localhost:8000/docs

