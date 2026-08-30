.PHONY: help up up-dev down build logs ps restart \
	migrate makemigrations superuser shell \
	test lint format check ci \
	dev-backend dev-frontend

help: ## Show available targets
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-18s\033[0m %s\n", $$1, $$2}'

# --- Docker ------------------------------------------------------------------

up: ## Start the full stack (build if needed)
	docker compose up --build -d
	@echo "Nexora is running at http://localhost"

up-dev: ## Start the stack with the backend on loopback :8000 (development)
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build -d
	@echo "Nexora is running at http://localhost (backend: http://localhost:8000)"

down: ## Stop the stack
	docker compose down

build: ## Build all images
	docker compose build

logs: ## Tail logs from all services
	docker compose logs -f --tail=100

ps: ## Show service status
	docker compose ps

restart: ## Restart backend + celery + frontend
	docker compose restart backend celery frontend

# --- Backend (inside Docker) -------------------------------------------------

migrate: ## Apply database migrations
	docker compose exec backend python manage.py migrate

makemigrations: ## Create migrations for a given app: make makemigrations APP=accounts
	docker compose exec backend python manage.py makemigrations $(APP)

superuser: ## Create a Django superuser
	docker compose exec backend python manage.py createsuperuser

shell: ## Open a Django shell in the backend container
	docker compose exec backend python manage.py shell

# --- Local development (without Docker) --------------------------------------

dev-backend: ## Run the Django dev server locally
	cd backend && ../../.venv/bin/python manage.py runserver || python3 manage.py runserver

dev-frontend: ## Run the Vite dev server locally
	cd frontend && npm run dev

# --- Quality gates ------------------------------------------------------------

test: ## Run the backend test suite
	cd backend && python -m pytest

lint: ## Lint backend and frontend
	cd backend && ruff check . && ruff format --check .
	cd frontend && npm run lint

format: ## Auto-format backend code
	cd backend && ruff check . --fix && ruff format .

check: ## Validate Django configuration (development settings)
	cd backend && python manage.py check

ci: lint test check build-fe ## Run everything CI runs
	@echo "CI gate passed."

build-fe: ## Type-check and build the frontend
	cd frontend && npm run build
