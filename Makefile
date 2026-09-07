# Mindful — comandos comunes (espejo del Makefile de Arc One)

DB_URL ?= postgresql+psycopg://mindful:mindful@127.0.0.1:5432/mindful
API := apps/api
VENV := $(API)/.venv
PY := $(VENV)/bin/python
PIP := $(VENV)/bin/pip

.PHONY: db-up db-down api-setup api-migrate api-seed api-dev api-dev-admin api-test premium-demo free-demo demo-seed

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

api-dev-admin:        ## WS28 · como api-dev, pero dev|user y demo|a22 son admin (para ver /admin en local)
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) MINDFUL_ADMIN_UIDS='dev|user,demo|a22' .venv/bin/uvicorn mindful_api.main:app --port 8000 --reload

limpiar-fotos:        ## WS30 · C3 · Ensayo de fotos huérfanas (--borrar para aplicar): make limpiar-fotos ARGS='--borrar'
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/python -m mindful_api.services.limpieza $(ARGS)

api-test:             ## Corre los tests
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/pytest

# ── WS24/WS25/WS27 · Q/A visual local (Tomás) ────────────────────────────────
demo-seed:            ## Siembra 9 Pausas + 4 cartas de comunidad (una por estado) + avisos y comentarios en cada usuario demo|
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/python -m mindful_api.demo_seed

premium-demo:         ## Vuelve PREMIUM (1 año) a todos los usuarios demo| del navegador local
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/python -c "\
from datetime import datetime, timedelta, timezone; \
from sqlalchemy import select; \
from mindful_api.db.base import SessionLocal; \
from mindful_api.db.models import Usuario; \
from mindful_api.services.plan import activar_premium; \
s=SessionLocal(); us=s.scalars(select(Usuario).where(Usuario.firebase_uid.like('demo|%'))).all(); \
[activar_premium(u, datetime.now(timezone.utc)+timedelta(days=365)) for u in us]; s.commit(); \
print(f'{len(us)} usuario(s) demo ahora premium')"

free-demo:            ## Vuelve FREE a todos los usuarios demo| del navegador local
	cd $(API) && MINDFUL_DATABASE_URL=$(DB_URL) .venv/bin/python -c "\
from sqlalchemy import select; \
from mindful_api.db.base import SessionLocal; \
from mindful_api.db.models import Usuario; \
from mindful_api.services.plan import vencer_premium; \
s=SessionLocal(); us=s.scalars(select(Usuario).where(Usuario.firebase_uid.like('demo|%'))).all(); \
[vencer_premium(u) for u in us]; s.commit(); \
print(f'{len(us)} usuario(s) demo ahora free')"
