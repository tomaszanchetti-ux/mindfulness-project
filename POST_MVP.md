# Post-MVP · Dwellia v2 — lo que queda para después

> Nace en la WS27 (07/09/2026). Acá se anota todo lo que decidimos NO hacer ahora
> pero no queremos olvidar. Una línea por idea: qué, por qué, de dónde salió y qué
> necesita para entrar. Se ordena por valor, no por fecha. Cuando algo entra a un
> bloque del `ROADMAP_v2_PREMIUM.md`, se mueve allá y acá queda tachado.

## 1. Producto

| # | Qué | Por qué | Origen | Qué necesita |
|---|---|---|---|---|
| P1 | **Reparto ponderado por puntaje de carta.** El motor sirve menos las cartas con peor promedio de estrellas y más las mejores; nuestras y de la comunidad por igual. | No se puede "sacar" una carta ya entregada; esto la va apagando sola y empuja a la comunidad a escribir buenas cartas. Es el mismo dial que hoy inclina por actividad, aplicado por carta. | Tomás, WS27 | Volumen real de estrellas (para no castigar por dos puntuaciones); definir el piso (ninguna carta llega a 0) y desde cuántas puntuaciones empieza a pesar. |
| P2 | **Comodín aprendido por estrellas** y **atenuar un pilar** que el usuario no quiere. | El motor "te conoce pero no te subestima" (WS04). | Roadmap WS17 | Datos reales de uso; hoy la rotación 6+1 es pareja. |
| P3 | **Carta inactiva** (`cartas.activa=false`): retirar del reparto sin borrar nada; el Baúl de quien la recibió no cambia. | Hoy una carta entregada no se puede borrar (`entregas.carta_id`). | Q/A B1.3, WS27 | Migración chica + filtro en el pool + botón en el adminland. Candidata a entrar en el Bloque C. |
| P4 | **Dos rituales por día** (mañana/noche, estilo diario guiado). | Palanca premium pensada desde el arranque. | Documento Madre | Orden compuesto del Baúl (fecha → estrella) y aviso doble. |
| P5 | **Fotos en el regalo** (link `/c/{token}`) y **compresión de imágenes** al subir. | Hoy el link muestra la ficha sin fotos y las fotos van tal cual (cap 8 MB). | WS16 | Redimensión en el backend (Pillow) o en el navegador antes de subir. |
| P6 | **Métricas suaves para el autor**: "se abrió tu carta", "tu Pausa se reenvió". | Impacto sin likes ni contadores públicos. | M5, WS06 | Que exista reenviar (Bloque C). |

## 2. Técnico / infra

| # | Qué | Por qué | Origen | Qué necesita |
|---|---|---|---|---|
| T1 | **`pytest` en el CI.** Hoy el CI solo despliega Hosting; el gate del backend es local. | Un merge sin correr la suite puede romper prod. | Fase 0 WS27 | Job de GitHub Actions con Postgres de servicio (`services: postgres`) + `make api-migrate api-seed api-test`. |
| T2 | **`MINDFUL_DATABASE_URL` y las keys a Secret Manager** (hoy env vars en Cloud Run). | Endurecer. | WS09 | Cambiar `--set-env-vars` por `--set-secrets` en el deploy. |
| T3 | **Email branded** para el magic link (dominio propio). | Sale de un remitente genérico de Firebase. | WS13 | Dominio + verificación en Firebase Auth. |
| T4 | **OG dinámico por token** en el link compartido (imagen de la carta real). | Hoy una sola imagen de marca para todos los links (SPA sin render server-side). | WS09 | Render server-side por token (Cloud Run) o pre-render. |
| T5 | **Zona horaria hacia el este duplica la carta del día** (caso borde del cambio de TZ). | Anotado en WS24 como deuda. | WS24 | Reproducir y decidir (probablemente comparar por fecha local guardada). |
| T6 | **Una suscripción de Stripe por usuario**: la baja de una vieja apaga la nueva. | Aceptable en v1. | WS24 | Guardar `subscription_id` y comparar en el webhook. |
| T7 | **Limpieza de fotos huérfanas** en Storage (entregas nunca completadas). | Costo y prolijidad. | WS16 | Job periódico (está en la ola C3 del roadmap). |
| T9 | **`GET /api/fichas/descubrir` hace ~6 queries por ficha** (183 para 30: persona, fotos, guardada, carta enriquecida por ítem). | Con cientos de usuarios no se nota; con miles, sí. | Q/A C1.2, WS29 | Cargar personas/fotos/guardadas en 3 queries por lote (`IN`) y `_carta_enriquecida` con las categorías/acciones cacheadas. |
| T8 | **Esfuerzo del juez** (`output_config.effort`) si el costo por carta molesta: hoy ≈ 4-6 ¢ porque Sonnet 5 piensa 3-6k tokens por veredicto. | Volumen premium lo hace irrelevante por ahora. | WS27 | Medir calidad con `medium`/`low` sobre cartas reales antes de bajarlo. |

## 3. Bloque D (promoción) — vive en `Flipbook/` y en el roadmap §5b
Sin entradas acá: el flipbook tiene su propio plan (D0-D3).
