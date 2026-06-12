# apps/api — Mindful Backend

FastAPI · SQLAlchemy 2 · Alembic · psycopg3 · Postgres 16. Espejo del backend de
Arc One. Ver [`../../01_Stack_Arquitectura_Infraestructura.md`](../../01_Stack_Arquitectura_Infraestructura.md).

> **⚠️ Transición WS22:** este README describe el código desplegado HOY. El canon
> de contenido se refundó (Sentido por Calma · 4 acciones iniciales · sin elección
> de acciones → `usuario_acciones` y sus endpoints quedan deprecados). La bajada a
> código es el paso 3 del plan — destino en
> [`canon_cartas.md §Transición`](../../M0_Motor_de_Contenido/canon_cartas.md).

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

## Auth (dos modos)

- `MINDFUL_AUTH_MODE=dev` (default local) → sin token. Se simula el usuario con headers
  `X-Debug-Sub` / `X-Debug-Email`. Para construir y testear sin Firebase.
- `MINDFUL_AUTH_MODE=firebase` → valida el `Authorization: Bearer <id_token>` de Firebase.

El aislamiento empieza en `auth.py:get_current_user`: cada request resuelve **un**
usuario (auto-provisión en el primer login) y el resto de la API filtra por su id.

## Endpoints

| Método | Ruta | Qué hace |
|--------|------|----------|
| GET | `/health` | Salud. |
| GET | `/api/contenido/categorias` | Las 6 categorías globales (Mundo 1). |
| GET | `/api/contenido/resumen` | Conteo de cartas (chequeo del seed). |
| GET | `/api/perfil` | Perfil del usuario logueado + sus actividades + `onboarding_completo` (= términos). |
| PUT | `/api/perfil` | Actualiza horario/TZ/aviso y acepta términos. |
| PUT | `/api/perfil/categorias` | **DEPRECADO (WS17):** lo que guarda no afecta la entrega; queda por compatibilidad. |
| GET | `/api/carta-del-dia` | La carta de hoy (M2: sortea + crea, o devuelve la ya entregada · 1/día por TZ). |
| PUT | `/api/entregas/{id}/cierre` | M3: cierra el ritual (estrellas/reflexión/completada). |
| GET | `/api/baul?orden=reciente\|valoradas` | M4: el historial vivido (carta + reflexión + fotos). |
| DELETE | `/api/baul/{id}` | M4: borrado real para siempre (+ apaga el link). |
| POST | `/api/compartir` | M5: crea un link (`carta_sola` o `ejercicio`) con nota. |
| DELETE | `/api/compartir/{id}` | M5: revoca un link. |
| GET | `/api/c/{token}` | **M5 público (sin login):** el regalo que abre el receptor. |

## Estado del build (N4)

- ✅ **Paso 1 — Seed + esquema:** las 8 tablas + el contenido de M0 cargado y servido.
- ✅ **Paso 1b — Auth + Perfil (M1):** dependency de auth (dev/firebase) + onboarding
  (actividades · horario/TZ/aviso · términos; onboarding_completo = términos). Aislamiento testeado.
- ✅ **Paso 2 — Entrega (M2) + Ritual (M3):** `elegir_carta()` portado fiel a
  `services/seleccion.py` (lee `cartas` global + `entregas` por user_id) + carta del día
  (1/día por TZ) + cierre del ritual.
- ✅ **Paso 3 — Baúl (M4) + Compartir (M5):** historial ordenable (Reciente/Más valoradas) +
  borrado real + links públicos `/c/{token}` (carta_sola sobrevive, ejercicio muere con la
  entrada). **Funnel backend M1→M5 completo.**
- ⏭️ **Falta (necesita GCP):** login real (Firebase) · aviso diario (worker RQ + Cloud
  Scheduler) · fotos del Baúl (Cloud Storage). Más el **front (Expo)**.
