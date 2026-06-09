# apps/api — Mindful Backend

FastAPI · SQLAlchemy 2 · Alembic · psycopg3 · Postgres 16. Espejo del backend de
Arc One. Ver [`../../01_Stack_Arquitectura_Infraestructura.md`](../../01_Stack_Arquitectura_Infraestructura.md).

## Estructura

```
mindful_api/
  config.py        # Settings (pydantic-settings, env MINDFUL_*)
  db/
    base.py        # engine + sesión
    models.py      # las 8 tablas — los DOS MUNDOS (global vs user_id)
  seed.py          # carga el contenido global de M0 (idempotente)
  main.py          # app FastAPI: /health + /api/contenido/*
alembic/           # migraciones (la inicial crea las 8 tablas)
tests/             # smoke test
```

## Arranque local (desde la raíz del repo)

```bash
make db-up        # Postgres en docker
make api-setup    # venv + dependencias
make api-migrate  # crea las tablas
make api-seed     # carga 6 categorías · 5 acciones · 69 cartas (desde M0)
make api-dev      # API en http://localhost:8000
make api-test     # pytest
```

Todo se parametriza con `MINDFUL_DATABASE_URL` (default = Postgres local). El seed
lee los JSON maestros de `M0_Motor_de_Contenido/data/` — esa es la única fuente de
verdad del contenido.

## La regla de oro (codificada en `models.py`)

- **Mundo 1 · contenido global** (`categorias`, `acciones`, `cartas`): sin `user_id`,
  igual para todos.
- **Mundo 2 · datos del usuario** (`usuarios`, `usuario_categorias`, `entregas`,
  `fotos`, `compartidos`): **toda fila lleva `usuario_id`**; el filtro vive en el
  backend, nunca en el cliente.

## Estado del build (N4)

- ✅ **Paso 1 — Seed + esquema:** las 8 tablas + el contenido de M0 cargado y servido.
- ⏭️ **Paso 1b — Auth:** validar Firebase ID token (`MINDFUL_AUTH_MODE=firebase`) +
  endpoints de perfil (M1).
- ⏭️ **Paso 2 — Entrega + Ritual:** `elegir_carta()` (ya en `M2_Entrega_del_Dia/`) +
  worker RQ + cierre M3.
