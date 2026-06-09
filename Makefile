# Mindful — comandos comunes (espejo del Makefile de Arc One)

DB_URL ?= postgresql+psycopg://mindful:mindful@127.0.0.1:5432/mindful
API := apps/api
VENV := $(API)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: db-up db-down api-setup api-migrate api-seed api-dev api-test

db-up:                ## Levanta Postgres local
	docker compose up -d postgres

db-down:              ## Apaga Postgres local
	docker compose down

api-setup:            ## Crea venv e instala dependencias
	python3 -m venv $(VENV)
	$(PIP) install -U pip
	$(PIP) install -r $(API)/requirements.txt

api-migrate:          ## Aplica migraciones (crea las tablas)
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/alembic upgrade head

api-seed:             ## Carga el contenido global de M0 (categorías/acciones/cartas)
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/python -m mindful_api.seed

api-dev:              ## Levanta la API en :8000 con reload
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/uvicorn mindful_api.main:app --port 8000 --reload

api-test:             ## Corre los tests
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/pytest
