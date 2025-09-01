# Makefile

.PHONY: dev dev-attach down logs lint test db-migrate create-admin-token hash-password \
        f-db-init f-db-migrate f-db-upgrade seed-admin user-cli restart-frontend

# --- Comandos Principais do Ambiente ---
dev:
	@echo "Starting up development environment (detached)..."
	docker compose --project-directory . -f infra/docker-compose.yml up -d --build

dev-attach:
	@echo "Starting up development environment (attached, shows logs)..."
	docker compose --project-directory . -f infra/docker-compose.yml up --build

down:
	@echo "Stopping development environment..."
	docker compose --project-directory . -f infra/docker-compose.yml down

logs:
	@echo "Tailing logs for api and frontend services..."
	# Ajuste aqui se existir 'worker' no seu docker-compose
	docker compose --project-directory . -f infra/docker-compose.yml logs -f api frontend

restart-frontend:
	@echo "Recreating frontend service to load new .env variables..."
	docker compose --project-directory . -f infra/docker-compose.yml up -d --force-recreate frontend

# --- Comandos da API ---
db-migrate:
	@echo "Creating API database tables (scans, tokens)..."
	docker compose --project-directory . -f infra/docker-compose.yml run --rm api python -c "from api.db.models import Base; from api.db.session import engine; Base.metadata.create_all(bind=engine)"

create-admin-token:
	@echo "Creating API token for the admin panel..."
	docker compose --project-directory . -f infra/docker-compose.yml run --rm api python -m scripts.create_admin_token

# --- Comandos do Frontend ---
f-db-init:
	@echo "Initializing Flask-Migrate for the frontend (idempotent)..."
	@if [ ! -d frontend/migrations ]; then \
		docker compose --project-directory . -f infra/docker-compose.yml run --rm frontend flask db init; \
	else \
		echo "frontend/migrations já existe, pulando 'flask db init'."; \
	fi

f-db-migrate:
	@echo "Generating frontend database migration..."
	docker compose --project-directory . -f infra/docker-compose.yml run --rm frontend flask db migrate -m "$(M)"

f-db-upgrade:
	@echo "Applying frontend database migration..."
	docker compose --project-directory . -f infra/docker-compose.yml run --rm frontend flask db upgrade

seed-admin:
	@echo "Seeding Super Admin user into the database..."
	docker compose --project-directory . -f infra/docker-compose.yml run --rm frontend flask seed-admin

user-cli:
	@echo "Running user management command..."
	@docker compose --project-directory . -f infra/docker-compose.yml run --rm frontend flask user $(CMD)

hash-password:
	@echo "Generating admin password hash..."
	docker compose --project-directory . -f infra/docker-compose.yml run --rm api python -m scripts.hash_password
