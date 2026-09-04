# Roadmap v2 · Freemium y comunidad — Dwellia

> Reescrito en la WS24 (04/09/2026). Es el plan de salida a mercado: qué queda
> gratis, qué se paga, y las tres olas de construcción con sus cards, en el orden
> en que se despliegan. Toda decisión de producto de la v2 vive acá; los motores
> M0-M5 siguen siendo la fuente de la lógica que ya existe.
> El plan anterior (WS17) queda al final como historial.

## 0. Decisiones cerradas (Tomás · WS24)

| Tema | Decisión |
|---|---|
| Free | **El método completo tal como está hoy**: 1 carta por día con acción inicial, rotación 6+1, diario fuera de la pantalla, reflexión ≤150 + 1 foto, Baúl, compartir la carta sola. Más el **comentario de la carta** (0.2). |
| Premium | **8,99 € por año**, cobrado en la web con Stripe (sin tiendas: sin comisión del 15-30 % ni revisión). Incluye: escribir cartas para la comunidad · cambiar la carta del día hasta 3 veces · reflexión ≤500 y hasta 3 fotos · compartir el ejercicio completo · recomendaciones en el perfil. |
| Lo que NO cambia | Sigue llegando **1 carta por día** a todos. El diario personal nunca entra a la app. Sin feed, sin seguidores, sin contadores públicos. |
| Perfil | **Privado por defecto**; el usuario lo hace público a elección. Lo público es la carta recibida y la reflexión posterior (frase y/o foto). Si el perfil es público se ven todas las entradas, y el usuario puede ocultar entradas sueltas. |
| Estrellas | **Se mantienen** (alimentan la afinidad del motor). Debajo se pide un comentario opcional; con 1-2 estrellas la pregunta es "¿qué te hubiese gustado recibir?". Ese texto es feedback para Dwellia, no se publica. |
| Rotación de cartas | **Sin agente**. Es determinística (M2) y con 77 cartas un usuario tarda 11 semanas en repetir una. La API de Anthropic se usa fuera de línea para lotes nuevos y, en runtime, SOLO para juzgar cartas de usuarios. |
| Cartas de usuarios | Wizard: pilar (uno de los 6) → acción inicial (una de las 4) → frase + prompt con la carta dibujándose en vivo → firma (anónima o apodo) + cesión → enviar. **Una carta en revisión a la vez** por usuario (sin tope mensual: la revisión ya regula el ritmo). Límites medidos sobre el mazo real: **frase ≤ 60 caracteres** (máx. actual 55) · **prompt 100-220** (máx. actual 207). |
| Validación | Capa 1 determinística (gratis) → capa 2 juez LLM **Sonnet 5** con el canon cacheado (≈1 céntimo por carta) → **Tomás aprueba** desde una pantalla mínima de administración. El juez sugiere, nunca publica. |
| Distribución | Las aprobadas entran al mazo como **cartas de la comunidad**; el receptor hace opt-in en su Perfil y las recibe el día 7 (comodín). Dorso: "de <apodo>" o "de alguien de la comunidad". Impacto = mensaje privado al autor. |

## 1. Modelo freemium (vista rápida)

| Capacidad | Free | Premium (8,99 €/año) |
|---|---|---|
| Carta del día con acción inicial, rotación 6+1 | ✅ | ✅ |
| Cambiar la carta del día | — | hasta 3 veces (cruza el eje quietud↔movimiento) |
| Reflexión | ≤150 | ≤500 |
| Fotos por Pausa | 1 | 3 |
| Compartir por link | carta sola | carta sola + ejercicio completo (con fotos) |
| Estrellas + comentario de la carta | ✅ | ✅ |
| Escribir cartas para la comunidad | — | ✅ (1 en revisión a la vez) |
| Recibir cartas de la comunidad (opt-in) | ✅ | ✅ |
| Perfil público (opt-in) con reflexiones | ✅ | ✅ |
| Recomendaciones en el perfil (libros, videos, podcasts) | — | ✅ |

Regla de ingeniería: **todos los límites viven en un solo lugar** (`services/plan.py`)
y el backend los aplica; el front solo los muestra. Un usuario free que manda 500
caracteres recibe 422, no importa qué diga la pantalla.

## 2. Método de construcción (orquestado, multiagente)

Espejo del método de CaliScan: **Claude orquesta** (contratos, criterio, Q/A,
commits, deploy tras el OK de Tomás) y **un agente Opus por card** con territorio
de archivos disjunto, sin git ni deploys. Circuito por card: hacer → commit →
Q/A adversarial por otro agente, con evidencia → correcciones al mismo agente →
verificación del orquestador → commit. Las cards de una misma ola corren en
paralelo; cada ola arranca cuando la anterior está commiteada.

- Branch: `epic/v2-freemium`. Merge a `main` y deploy solo con OK explícito de Tomás.
- Tests: cada card suma los suyos (suite hoy: 35 ✓). Front: `tsc` estricto + e2e en preview.
- Bitácora por sesión en `WS/`. Este roadmap se actualiza al cierre de cada bloque.
- Antes de desplegar: `gcloud auth login` (la sesión está vencida desde junio).

## 3. Bloque A — Base freemium (≈2 sesiones)

Objetivo: cobrar y aplicar las compuertas. Al cerrar A, Dwellia ya se puede vender.

### Ola A0 (orquestador, sin agente) — el contrato
- Migración única con TODAS las columnas del bloque: `usuarios.plan` (`free|premium`,
  default free) · `usuarios.plan_hasta` · `usuarios.stripe_customer_id` ·
  `entregas.comentario_carta` (Text) · `entregas.cambios` (int, default 0) ·
  `entregas.descartadas` (JSON, ids de cartas cambiadas).
- `services/plan.py`: `limites(usuario) -> Limites` (reflexion, fotos, compartir_ejercicio,
  cambios_carta, propone_cartas) y `es_premium(usuario)`.
- `PerfilOut` devuelve `plan`, `plan_hasta` y `limites` (el front lee de acá, nunca hardcodea).

### Ola A1 (3 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **A1.1 Compuertas** | Reflexión 150/500, fotos 1/3, compartir `ejercicio` solo premium. Los límites salen de `plan.py`. | `services/fotos.py`, `services/compartir.py`, `services/entrega.py` (cierre), `schemas.py`, tests | free → 422 al pasarse; premium pasa; aislamiento intacto |
| **A1.2 Stripe** | `POST /api/pagos/checkout` (Checkout anual 8,99 €, `client_reference_id`=usuario) · `POST /api/pagos/webhook` (firma verificada; `checkout.session.completed` e `invoice.paid` activan `plan_hasta`; `customer.subscription.deleted` lo vence) · `POST /api/pagos/portal`. Env `MINDFUL_STRIPE_*`. | `routers/pagos.py`, `services/stripe.py`, `config.py`, `requirements.txt`, tests con firma simulada | webhook sin firma válida → 400; evento repetido idempotente; plan se activa y vence |
| **A1.3 Comentario + cambiar carta** | `CierreRitual.comentario_carta` ≤150 · `POST /api/entregas/{id}/cambiar` (premium, máx. 3, mismo pilar, cruza el eje, respeta ventanas de carta y concepto, guarda descartada, nunca repite la de ayer). | `services/cambio.py` (nuevo), `services/seleccion.py` (función `cambiar`), `routers/entregas.py`, tests | free → 403; 4.º intento → 409; la carta nueva cumple el eje y las ventanas |

### Ola A2 (2 agentes en paralelo, front)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **A2.1 Pantalla Premium + Perfil** | `/premium` ("Apoya Dwellia", 8,99 €/año, qué incluye, botón que abre Checkout) · Perfil: bloque "Tu plan" (free → enlace; premium → hasta cuándo + "Gestionar suscripción") · vuelta de Stripe `/premium/gracias`. | `screens/Premium.tsx`, `screens/Profile.tsx`, `lib/api.ts` (pagos), `Frame.tsx` (ruta) | flujo de prueba Stripe e2e en preview con clave de test |
| **A2.2 Límites vivos + cambiar carta** | `Reflect.tsx` lee límites del perfil (contador, fotos) · comentario debajo de las estrellas con copy según puntuación · `Home.tsx` botón "Otra carta (quedan N)" solo premium · `Share.tsx` habilita modo ejercicio para premium. | `screens/Reflect.tsx`, `screens/Home.tsx`, `screens/Share.tsx`, `store.tsx`, `app.css` | free y premium verificados en preview; `tsc` ✓ |

Deploy A: migración (job `dwellia-migrate`) → API → Hosting. Stripe en modo test hasta
que Tomás active la cuenta real (lo único que hace él: crear cuenta Stripe + producto
8,99 €/año + pegar 3 secretos en Cloud Run).

## 4. Bloque B — Cartas de la comunidad (≈3 sesiones)

Objetivo: la feature insignia del premium, con el pipeline que ya existe.

### Ola B0 (orquestador) — el contrato
- Tabla `cartas_comunidad` (Mundo 2): `usuario_id`, `categoria_slug`, `accion_slug`,
  `frase` ≤60, `prompt` 100-220, `firma` (`anonima|apodo`), `estado`
  (`en_revision` juez corriendo → `revision_dwellia` | `a_revisar` (vuelve al autor con
  sugerencia) | `rechazada` (safety) → Tomás: `aprobada` | `rechazada`; `retirada` por el
  autor), `veredicto` (JSON del juez), `motivo`, `concepto`, `cesion_aceptada_at`,
  `carta_id` (la carta publicada), fechas.
- `cartas` (Mundo 1) suma `origen` (`dwellia|comunidad`, default dwellia), `autor_usuario_id`
  (atribución, no aislamiento) y `firma_publica` (apodo o null). Así motor, Baúl y compartir
  funcionan sin cambios.
- `usuarios.recibe_comunidad` (bool, default false).

### Ola B1 (3 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **B1.1 Propuestas (API)** | `POST /api/cartas-comunidad` (premium; 409 si ya hay una en revisión; valida límites y cesión) · `GET /api/cartas-comunidad/mias` · `PUT …/{id}` reenviar desde `a_revisar` · `DELETE …/{id}` retirar. Dispara el juez en `BackgroundTasks` (sin Redis). | `routers/cartas_comunidad.py`, `services/cartas_comunidad.py`, `schemas.py` (sección propia), tests | estados y transiciones probados; aislamiento; free → 403 |
| **B1.2 Juez en runtime** | Portar `scripts/validar_cartas.py` a `services/canon.py` (capa 1 importable, mismo umbral 0,72) + `services/juez.py` (Anthropic SDK, Sonnet 5, canon con prompt caching, structured output → `aprueba / requiere_revision + fix / rechaza` + concepto + safety). Sin key → modo `off` que deja todo en `revision_dwellia`. El script CLI pasa a usar los mismos módulos. | `services/canon.py`, `services/juez.py`, `scripts/validar_cartas.py`, `config.py`, `requirements.txt`, tests con cliente simulado | carta trampa → rechaza; carta buena → revision_dwellia; el CLI sigue dando 77/77 |
| **B1.3 Administración** | `GET /api/admin/cartas?estado=` · `POST /api/admin/cartas/{id}/aprobar` (publica en `cartas` con origen comunidad, sync de concepto) · `…/rechazar` (motivo) · `GET /api/admin/comentarios` (los comentarios de A1.3). Admin = uid en `MINDFUL_ADMIN_UIDS`. | `routers/admin.py`, `services/admin.py`, `auth.py` (`get_admin`), tests | no-admin → 403; aprobar crea la carta y la deja servible |

### Ola B2 (2 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **B2.1 Distribución + impacto** | Motor: el día comodín sirve una carta `comunidad` no vista si el usuario tiene opt-in y hay disponible; si no, comodín como hoy. Las de comunidad nunca desplazan la rotación de pilares. Dorso: firma. `GET /api/cartas-comunidad/mias` devuelve `personas_acompanadas` (conteo de entregas de esa carta). | `services/seleccion.py`, `services/entrega.py`, `services/cartas_comunidad.py` (impacto), `routers/perfil.py` (opt-in), tests | opt-in recibe el día 7; sin opt-in nunca; conteo correcto |
| **B2.2 Front: wizard + Mis cartas + Admin** | `/cartas/nueva` wizard 4 pasos con preview en vivo (reusa `Card.tsx`) y contadores de caracteres · Perfil › "Tus cartas" (estados, sugerencia del juez, editar y reenviar, impacto privado) · Perfil › toggle "Recibir cartas de la comunidad" · `/admin` (solo admins): cola con veredicto, aprobar/rechazar, comentarios. | `screens/CartaNueva.tsx`, `screens/MisCartas.tsx`, `screens/Admin.tsx`, `screens/Profile.tsx`, `components/Card.tsx` (firma en dorso), `lib/api.ts`, `Frame.tsx` | e2e en preview: proponer → juez simulado → admin aprueba → llega el día 7 |

## 5. Bloque C — Perfil público y recomendaciones (≈2-3 sesiones)

Objetivo: el loop de descubrimiento (link al perfil) sin feed ni seguidores.

### Ola C0 (orquestador) — el contrato
- `usuarios.handle` (único, 3-24, minúsculas y guiones; sugerido desde el apodo),
  `usuarios.perfil_publico` (default false), `usuarios.bio` ≤150.
- `entregas.oculta_perfil` (default false).
- Tabla `recomendaciones` (Mundo 2): `usuario_id`, `tipo` (`libro|video|podcast|otro`),
  `titulo` ≤80, `url` (dominios permitidos: youtube, vimeo, spotify, goodreads, amazon,
  casadellibro, apple podcasts; lista en `services/recomendaciones.py`), `nota` ≤150,
  `orden`, máx. 20 por usuario. Premium.

### Ola C1 (2 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **C1.1 Perfil público (API)** | `GET /api/u/{handle}` SIN login (404 si privado): apodo, bio, pilares, cartas de comunidad aprobadas con firma apodo, entradas completadas no ocultas (carta + reflexión + fotos) y recomendaciones · `GET /api/u/{handle}/fotos/{id}` público solo si la entrada es visible · `PUT /api/perfil` acepta handle/perfil_publico/bio · `PUT /api/baul/{id}/visibilidad`. | `routers/publico.py`, `services/perfil_publico.py`, `routers/perfil.py`, `routers/baul.py`, `services/fotos.py` (lectura pública), tests | privado → 404; oculta no aparece; foto de entrada oculta → 404; borrar cuenta borra lo público |
| **C1.2 Recomendaciones (API)** | CRUD `/api/recomendaciones` (premium; allowlist de dominios; 20 máx.; orden). | `routers/recomendaciones.py`, `services/recomendaciones.py`, `schemas.py` (sección propia), tests | dominio fuera de lista → 422; free → 403 |

### Ola C2 (2 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **C2.1 Front público** | `/u/:handle` con la estética del regalo (`PublicShare`): cabecera, pilares, cartas de la comunidad, entradas con foto y reflexión, recomendaciones · OG básico. | `screens/PerfilPublico.tsx`, `Frame.tsx`, `app.css` | perfil público navegable sin login en preview |
| **C2.2 Front privado** | Perfil › "Tu perfil público" (toggle, handle, bio, copiar link) · Baúl detalle › "Ocultar del perfil" · Perfil › "Tus recomendaciones" editor (premium). | `screens/Profile.tsx`, `screens/EntryDetail.tsx`, `screens/Recomendaciones.tsx`, `lib/api.ts` | toggles verificados e2e en preview |

### Ola C3 (1 agente) — legal y cierre
- **TyC v3**: cesión de las cartas de la comunidad (licencia a Dwellia, atribución por apodo o
  anónima, retiro a pedido), moderación, perfil público como decisión del usuario, borrar la
  cuenta borra todo lo público, recomendaciones = opiniones de usuarios, +16.
- Barrido "Pausa" con mayúscula pendiente de la WS23.
- Limpieza de fotos huérfanas de Storage (WS16).

## 6. Costos del MVP (mensual, estimado)

| Rubro | Hoy | Con la v2 |
|---|---|---|
| Cloud SQL `db-f1-micro` | ≈ 10 $ | igual |
| Cloud Run + Hosting + Storage | ≈ 0 | ≈ 0-2 $ |
| Anthropic (juez, Sonnet 5, canon cacheado) | 0 | ≈ 0,01 $ por carta enviada |
| Stripe | 0 | 0,25 € + 1,5 % por cobro (quedan ≈ 8,60 € de 8,99) |
| **Total** | ≈ 10 $ | **< 15 $** hasta miles de usuarios |

No se toca la infra. El costo real es el tiempo de moderación de Tomás, y por eso
proponer cartas es premium: el que paga casi nunca hace spam.

## 7. Lo que sigue abierto de la v1
- Tomás prueba el push en su iPhone (WS21).
- Email branded para el magic link (dominio propio).
- Compresión de imágenes (WS16).

---

## Historial — plan WS17 (11/06/2026), superado por este documento

Ola 1 "capacidad" (reflexión larga, 3-5 fotos, compartir completo, cambiar carta,
comodín aprendido, fotos en el regalo) y Ola 2 "UGC curado" (pool "Cartas de la
comunidad" opt-in, apodo en el dorso, impacto privado, pipeline validador + Tomás).
Todo eso sigue vigente y quedó repartido en los bloques A y B de arriba; lo nuevo
de la WS24 es el precio, el cobro por web, el comentario de la carta, el perfil
público opt-in y las recomendaciones. El comodín aprendido por ⭐ y "atenuar un
pilar" quedan para después del MVP, con feedback real.
