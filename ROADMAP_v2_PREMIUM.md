# Roadmap v2 · Freemium y comunidad — Dwellia

> Reescrito en la WS24 (04/09/2026). Es el plan de salida a mercado: qué queda
> gratis, qué se paga, y las tres olas de construcción con sus cards, en el orden
> en que se despliegan. Toda decisión de producto de la v2 vive acá; los motores
> M0-M5 siguen siendo la fuente de la lógica que ya existe.
> El plan anterior (WS17) queda al final como historial.

## 0. Decisiones cerradas (Tomás · WS24 + WS25)

| Tema | Decisión |
|---|---|
| Free | **El método completo tal como está hoy**: 1 carta por día con acción inicial, rotación 6+1, diario fuera de la pantalla, reflexión ≤150 + 1 foto, Baúl, **compartir la ficha entera**. Más el **comentario de la carta**. |
| Premium | **8,99 € por año**, cobrado en la web con Stripe (sin tiendas). Incluye: escribir cartas para la comunidad · cambiar la carta del día hasta 3 veces · reflexión ≤500 y hasta 3 fotos · **compartir más contenido** (fichas de recomendación en el Baúl: libros, videos, podcasts, documentales). CTA siempre **"Quiero ser parte"**; premium: "Quiero dejar la comunidad". |
| Lo que NO cambia | Sigue llegando **1 carta por día** a todos. El diario personal nunca entra a la app. Sin feed, sin seguidores, sin likes, sin comentarios, sin contadores públicos. |
| Compartir (WS25) | **Todo o nada.** La ficha de una Pausa = carta + reflexión + fotos, y viaja entera tal como está al momento de enviar; nunca se elige qué parte. Desde el cierre hay dos CTAs, **Enviar** y **Guardar**: enviar sin reflexión (viaja la carta sola) · enviar con reflexión/foto sin guardar (viaja la ficha, no entra al Baúl) · guardar (ficha en el Baúl, reenviable las veces que se quiera). Cada uno pregunta por el otro después. Lo ya enviado no cambia. **Las estrellas nunca salen de tu cuenta.** Igual para free y premium. |
| Fichas y visibilidad (WS25) | Cada Pausa del Baúl es **privada por defecto** o **compartida**. Lo compartido es lo que ve tu comunidad y lo que puede reenviar. El Baúl propio y el perfil visto por otros son **la misma vista** (menos lo privado). Píldora "Pausa" en verde Dwellia; las fichas premium de **Recomendación** conviven en el mismo Baúl. |
| Perfil y comunidad (WS25) | **Perfil privado por defecto**, ajustable desde Perfil. Cualquiera te encuentra en Dwellia por email registrado, apodo, nombre o apellido. Privado = para ver tus fichas hay que mandarte una **solicitud** que aceptás (como Instagram). Público = cualquier usuario logueado ve tus fichas compartidas. |
| Reenviar (WS25) | La única acción sobre una ficha ajena: reenviarla a alguien de tu comunidad (in-app) o por WhatsApp (link). Quien la recibe la abre, ve la ficha y de quién es, y puede **guardarla en su Baúl** (privada) o **hacer la Pausa** ahora o programada para un día y hora (esa carta pasa a ser la del día). |
| Login (WS25) | **Siempre logueado**, también para abrir el link recibido por WhatsApp. Login simple: Google o enlace por email. |
| Estrellas | **Se mantienen** (alimentan la afinidad del motor). Debajo se pide un comentario opcional; con 1-2 estrellas la pregunta es "¿qué te hubiese gustado recibir?". Ese texto es feedback para Dwellia, no se publica. |
| Rotación de cartas | **Sin agente**. Determinística (M2). La API de Anthropic se usa fuera de línea para lotes nuevos y, en runtime, SOLO para juzgar cartas de usuarios. |
| Cartas de usuarios | Pestaña **Crear** (premium; free ve un pop-up + "Quiero ser parte"). Wizard: pilar → acción inicial → frase + prompt con la carta dibujándose en vivo → firma (anónima o apodo) + cesión → enviar. **Una carta en revisión a la vez**. **Frase ≤ 40** · **prompt 100-150** (Tomás, WS28; antes 60 / 220). |
| Validación | Capa 1 determinística → capa 2 juez LLM **Sonnet 5** con el canon cacheado (≈1 céntimo) → **Tomás aprueba** desde `/admin`. **Aprobar = cargado** (WS25): estados visibles "En proceso de evaluación" (gris) → "Cargado a la comunidad", más "Necesita un retoque" y "No aprobada". Cada cambio avisa al autor. |
| Distribución (WS27) | **Las aprobadas entran al mazo como iguales**: la carta se suma a su pilar y el motor la reparte con las mismas reglas que las nuestras (rotación 6+1, ventanas de 7 días), a todo el mundo. Sin día especial, sin tope y **sin interruptor: todos reciben cartas de la comunidad** (la comunidad hace crecer el sistema; el juez + Tomás son la puerta de calidad). El autor también puede recibir su propia carta (reconocimiento; si no la quiere, la cambia). Dorso: "de <apodo>" o "de alguien de la comunidad". Impacto = cuántas personas la recibieron, visible para el autor. **Adminland (solo la cuenta de Tomás)**: aprobación con el funnel completo (v1 redacción del usuario → v2 comentarios y sugerencia del juez → vFinal aprobar / rechazar / modificar) + tablero (cartas por pilar y origen; propuestas pendientes, aprobadas, rechazadas, retocadas) + termómetro general de usuarios (totales, premium, gratis, cuántos crearon cartas). **Nada por usuario individual** (decisión de Tomás: simple y útil). |
| Q/A visual (WS25) | El Q/A del backend de cada bloque **siembra datos reales** (`make demo-seed`: Pausas, reflexiones, fotos, fichas, estados, solicitudes) para que Tomás vea la app completa. Solo local. |

## 1. Modelo freemium (vista rápida)

| Capacidad | Free | Premium (8,99 €/año) |
|---|---|---|
| Carta del día con acción inicial, rotación 6+1 | ✅ | ✅ |
| Cambiar la carta del día | — | hasta 3 veces (cruza el eje quietud↔movimiento) |
| Reflexión | ≤150 | ≤500 |
| Fotos por Pausa | 1 | 3 |
| Compartir la ficha (carta + reflexión + fotos), por link o a la comunidad | ✅ | ✅ |
| Estrellas + comentario de la carta | ✅ | ✅ |
| Escribir cartas para la comunidad | — | ✅ (1 en revisión a la vez) |
| Recibir cartas de la comunidad (todos, sin interruptor) | ✅ | ✅ |
| Perfil público (opt-in) · comunidad con solicitudes · reenviar · guardar Pausas de otros | ✅ | ✅ |
| Fichas de recomendación en el Baúl (libros, videos, podcasts) | — | ✅ |

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
- **E2E (Tomás, WS28):** el Bloque B se validó con el contrato en navegador (Claude) + Q/A visual (Tomás) y se desplegó; el **E2E completísimo** se hace UNA vez, al cerrar el Bloque C (fin del desarrollo), antes del Bloque D. Regla original:  al terminar cada bloque, ANTES de mergear y desplegar, un recorrido completo en local con datos sembrados (`make demo-seed`, que crece con cada bloque: usuarios premium y free, cartas en todos los estados, avisos, comentarios; en C, vínculos y reenvíos) mirando el adminland con la cuenta admin local y la app con un usuario premium y uno free. Entra solo lo construido en ese bloque. Después del deploy, prueba real en producción con la cuenta de Tomás.
- Antes de desplegar: `gcloud auth login` (la sesión está vencida desde junio).

## 3. Bloque A — Base freemium (≈2 sesiones) · 🟢 CONSTRUIDO WS24 (branch, sin deploy)

Objetivo: cobrar y aplicar las compuertas. Al cerrar A, Dwellia ya se puede vender.
**Estado (WS24):** A0-A2 construidas y con Q/A adversarial del backend (209 tests ✓).
**WS25:** el Q/A visual de Tomás (`Pivot/Lectura_QA_Visual_WS24.md`) cambió el modelo
de compartir a **todo o nada** y sumó la **card A3** (contrato en `WS/WS25_04-09-2026.md` §2):
visibilidad por Pausa, compartir sin modos ni plan, login para el link, retoques de
onboarding/premium/perfil/Baúl y `make demo-seed`. Falta: Q/A visual de A3 · Stripe · deploy.

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

## 4. Bloque B — Crear: cartas de la comunidad (≈3 sesiones)

> **Estado (WS28, 07/09): BLOQUE B EN PRODUCCIÓN** (API rev 00018, migraciones aplicadas, merge a `main`). Q/A visual de Tomás hecho (admin "perfecto"). Falta la prueba real de Tomás en prod con su cuenta (admin = premium). Sigue el Bloque C.

Objetivo: la feature insignia del premium, con la pestaña **Crear** y el pipeline
juez + Tomás. Al cerrar B la barra tiene 4 pestañas (Hoy · Baúl · Crear · Perfil).

### Ola B0 (orquestador) — el contrato
- Tabla `cartas_comunidad` (Mundo 2): `usuario_id`, `categoria_slug`, `accion_slug`,
  `frase` ≤40, `prompt` 100-150 (WS28), `firma` (`anonima|apodo`), `estado`
  (`en_revision` juez corriendo → `revision_dwellia` | `a_revisar` (vuelve al autor con
  sugerencia) | `rechazada` → Tomás: `aprobada` (= cargada al mazo) | `rechazada`;
  `retirada` por el autor), `veredicto` (JSON del juez), `motivo`, `concepto`,
  `cesion_aceptada_at`, `carta_id` (la carta publicada), fechas.
- `cartas` (Mundo 1) suma `origen` (`dwellia|comunidad`), `autor_usuario_id` y `firma_publica`.
- `usuarios.recibe_comunidad` (bool, default false).
- Tabla `avisos` (Mundo 2): `usuario_id`, `tipo` (`carta_estado` hoy; `reenvio`,
  `solicitud` en C), `referencia_id`, `texto`, `leido`, `created_at`. Se muestra en
  la app y dispara el push web existente.
- Rótulos visibles (front): `en_revision`/`revision_dwellia` → "En proceso de
  evaluación" (gris) · `aprobada` → "Cargado a la comunidad" · `a_revisar` →
  "Necesita un retoque" · `rechazada` → "No aprobada".

### Ola B1 (3 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **B1.1 Propuestas (API)** | `POST /api/cartas-comunidad` (premium; 409 si ya hay una en revisión; valida límites y cesión) · `GET …/mias` · `PUT …/{id}` reenviar desde `a_revisar` · `DELETE …/{id}` retirar. Juez en `BackgroundTasks`. Crea `avisos` en cada cambio de estado. | `routers/cartas_comunidad.py`, `services/cartas_comunidad.py`, `services/avisos.py`, `schemas.py`, tests | estados y transiciones probados; aislamiento; free → 403 |
| **B1.2 Juez en runtime** | `services/canon.py` (capa 1, umbral 0,72) + `services/juez.py` (Sonnet 5, canon cacheado, structured output → `aprueba / requiere_revision + fix / rechaza` + concepto + safety). Sin key → `off` (todo a `revision_dwellia`). | `services/canon.py`, `services/juez.py`, `scripts/validar_cartas.py`, `config.py`, `requirements.txt`, tests | carta trampa → rechaza; buena → revision_dwellia; el CLI sigue 77/77 |
| **B1.3 Administración** | `GET /api/admin/cartas?estado=` · `POST …/aprobar` (publica en `cartas` con origen comunidad = cargada) · `…/rechazar` (motivo) · `…/a-revisar` (sugerencia) · `GET /api/admin/comentarios`. Admin = uid en `MINDFUL_ADMIN_UIDS`. | `routers/admin.py`, `services/admin.py`, `auth.py`, tests | no-admin → 403; aprobar crea la carta servible y avisa al autor |

### Ola B2 (2 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **B2.1 Distribución + impacto + tablero** | Las cartas `comunidad` ya están en el pool (B1.3 las publica en `cartas`): el motor las reparte como iguales a todos, **sin exclusiones** (el autor también puede recibir la suya). La columna `usuarios.recibe_comunidad` (B0) se elimina en la migración de B2.1: no hay interruptor. `GET …/mias` devuelve `personas_acompanadas` (entregas de esa carta). `GET /api/avisos` + `PUT …/{id}/leido` + no leídos. **Adminland (API):** `GET /api/admin/resumen` (por pilar: total / propias / comunidad · propuestas por estado · usuarios: totales, con onboarding, premium, free, crearon cartas · comentarios: total y últimos 7 días) · `cartas_comunidad.historial` (JSON, migración): cada redacción del usuario se guarda al enviar y al reenviar, así el funnel muestra v1 (lo que escribió), v2 (veredicto y sugerencia del juez o retoque de Dwellia) y vFinal (decisión). `GET /api/admin/cartas` devuelve `historial`. | `services/entrega.py`, `routers/avisos.py`, `services/avisos.py` (lectura), `services/admin.py` + `routers/admin.py` (resumen, historial), `services/cartas_comunidad.py` (historial al enviar/reenviar), `db/models.py`, migración (drop `recibe_comunidad`, add `historial`), tests | la carta se sirve a cualquiera; conteos y funnel correctos |
| **B2.2 Front: pestaña Crear + Admin** · 🟢 CONSTRUIDA WS28 (commit `8a0362d`; el autor premium ve además el **puntaje** de su carta: ★ promedio y valoraciones) | `Frame.tsx` con 4 pestañas · `/crear`: free → pop-up "Escribir cartas es parte de la comunidad" + "Quiero ser parte"; premium → CTA "Escribir una carta" + lista **"Tus cartas"** prolija (miniatura de la carta, frase, estado con rótulo y color, sugerencia del juez, editar y reenviar, impacto) · wizard `/crear/nueva` 4 pasos con preview en vivo · campana de avisos · `/admin` = **adminland solo para la cuenta de Tomás**: (1) cola de aprobación con el funnel de cada carta — v1 redacción del usuario (con la carta dibujada) → v2 comentarios del juez y su sugerencia → vFinal: Aprobar / Rechazar (motivo) / Modificar (sugerir el cambio al usuario) · (2) tablero: cartas por pilar y origen; propuestas pendientes, aprobadas, rechazadas, retocadas · (3) comentarios de las cartas **agrupados por carta** (frase, pilar, veces puntuada, promedio de estrellas, cuántos comentarios; ordenado por las que peor van; filtro único "1-2 estrellas"; tocar una abre sus comentarios con estrellas, apodo y fecha). Solo lectura: las cartas se cambian en el repo y viajan con el deploy de contenido. | `screens/Crear.tsx`, `screens/CartaNueva.tsx`, `screens/Admin.tsx`, `components/Frame.tsx`, `components/Card.tsx`, `lib/api.ts`, `app.css` | e2e en preview: proponer → juez simulado → admin aprueba → "Cargado" + aviso → llega el día 7 |

Seed B: `make demo-seed` suma 4 cartas del usuario demo, una por estado.

## 5. Bloque C — Comunidad (≈3-4 sesiones) · 🌅 EN PRODUCCIÓN (WS30 · merge `c9896ba` · API rev 00019) — la v2 (A+B+C) COMPLETA

Objetivo: la pestaña **Comunidad**, sin feed ni seguidores: personas, solicitudes,
reenvíos y las fichas de recomendación.

**Estado y decisiones de la WS29 (mandan sobre las tablas de abajo; el contrato
exacto vive en `WS/WS29_07-09-2026.md` §4):**
- **Barra de CUATRO: Hoy · Baúl · Comunidad · Crear.** Perfil (botón verde) y la
  campana van arriba a la derecha. Comunidad = tres personas; Crear = "+" verde.
- **Comunidad estilo Instagram:** buscador arriba (email, apodo, nombre, apellido)
  y debajo **Descubrir**: una grilla de fichas de Pausas compartidas (foto +
  reflexión, la persona visible), de perfiles públicos y de mi comunidad.
- **Foto de perfil** (`usuarios.foto_path`; se ve en búsqueda, comunidad y fichas).
- **Hacer la Pausa** (premium): "Hacer ahora" = una Pausa EXTRA hoy, no toca la
  diaria · "Programar" = tu PRÓXIMA carta del día (cola de una), sin fecha.
- **Una Pausa extra vivida y compartida es una ficha más** (Descubrir incluida).
- **Reenviar por WhatsApp una ficha ajena** = link in-app `/comunidad/ficha/{id}`
  (con login y la regla de lectura), nunca un token de un tercero.
- **La regla de lectura** es UNA (`services/comunidad.puede_ver`): compartida ∧
  vivida ∧ (dueño ∨ dueño público ∨ vínculo aceptado ∨ me la reenviaron) → si no, 404.
- T&C v3 = texto y fecha nuevos, sin re-aceptación. Q/A adversarial en Sonnet 5.
- Construido en la WS29: C0 (contrato + cableado del front) · C1.1 · C1.2 · C1.3 ·
  seed C · 3 Q/A adversariales (4 hallazgos, todos cerrados) · suite 751 ✓.
  WS30: C2.1 + C2.2 (2 Opus) · Q/A visual de Tomás → C2b (quitar de mi comunidad con
  CTA rojo · reenviar CON comentario ≤200 · perfil ajeno en pestañas · recomendación
  ajena en su pantalla con enlace rotulado · **Crear = la única puerta**, ambas premium) ·
  C3 (Términos v3 + fotos huérfanas en el barrido) · suite 758 ✓ · deploy. Fotos en
  recomendaciones → POST_MVP P7. **Sigue el Bloque D (§5b).**

### Ola C0 (orquestador) — el contrato
- `usuarios.perfil_publico` (bool, default false) · índices por `lower(email)`,
  `lower(apodo)`, `lower(nombre)`, `lower(apellido)`.
- Tabla `vinculos` (Mundo 2): `solicitante_id`, `destinatario_id`, `estado`
  (`pendiente|aceptada`), fechas; único por par. "Mi comunidad" = vínculos aceptados
  en cualquier dirección.
- Tabla `reenvios`: `de_usuario_id`, `a_usuario_id`, `entrega_id`, `leido`, `created_at`.
- Tabla `guardadas`: `usuario_id`, `entrega_id` (la ficha de otro), `created_at`;
  único por par. En el Baúl aparece como "Pausa de <apodo>", privada, y desaparece
  si el dueño la vuelve privada o la borra.
- Tabla `pausas_programadas`: `usuario_id`, `carta_id`, `de_usuario_id`,
  `programada_para` (fecha local), `servida`. El motor la sirve como carta de ese
  día (una por día se mantiene); el aviso diario la recuerda.
- Tabla `recomendaciones` (premium): `usuario_id`, `titulo` ≤80, `tipo`
  (`libro|video|podcast|documental|otro`), `texto` ≤500, `url` opcional (cualquier
  https), `visibilidad`, fechas. Máx. 30 por usuario. Es una ficha más del Baúl.
- Regla de lectura de una ficha ajena: visible si (dueño público) o (vínculo
  aceptado) y `visibilidad = compartida`; si no → 404. El link `/c/{token}` sigue
  siendo la excepción (el token es el permiso, con login).

### Ola C1 (3 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **C1.1 Personas y solicitudes** | `GET /api/comunidad/buscar?q=` (email exacto, apodo, nombre, apellido; devuelve apodo, público sí/no, estado del vínculo; nunca el email ajeno) · `POST /api/comunidad/solicitudes/{usuario_id}` · aceptar / rechazar / cancelar · `GET /api/comunidad` (mi gente + pendientes) · `DELETE` quitar de mi comunidad · `PUT /api/perfil` acepta `perfil_publico`. Avisos de solicitud. | `routers/comunidad.py`, `services/comunidad.py`, `routers/perfil.py`, tests | privado sin vínculo → solo apodo; duplicados → 409; aislamiento |
| **C1.2 Fichas ajenas, reenviar, guardar, hacer la Pausa** | `GET /api/comunidad/{usuario_id}/baul` (fichas compartidas según la regla) · `GET /api/comunidad/{usuario_id}/fotos/{id}` · `POST /api/reenvios` · `GET /api/reenvios/recibidos` · `POST /api/guardadas/{entrega_id}` · `POST /api/pausas/hacer` (`ahora` → entrega de hoy con esa carta · `programada_para`). Motor: la programada manda ese día. | `routers/reenvios.py`, `services/reenvios.py`, `services/guardadas.py`, `services/seleccion.py`, `services/baul.py` (guardadas en la lista), tests | ficha privada → 404 aunque haya vínculo; guardada desaparece si el dueño la vuelve privada; la programada llega ese día y solo ese día |
| **C1.3 Recomendaciones (API)** | CRUD `/api/recomendaciones` (premium; 30 máx.; visibilidad) y su inclusión en el Baúl propio y ajeno como ficha `tipo: recomendacion`. | `routers/recomendaciones.py`, `services/recomendaciones.py`, `schemas.py`, tests | free → 403; ajeno → 404; aparece en el Baúl ajeno solo si compartida |

### Ola C2 (2 agentes en paralelo)
| Card | Qué | Territorio | Acepta cuando |
|---|---|---|---|
| **C2.1 Pestaña Comunidad** | `Frame.tsx` con 5 pestañas · `/comunidad`: mi gente (buscador local), buscar en Dwellia, solicitudes pendientes (enviadas/recibidas), "Te enviaron" (reenvíos con la ficha y de quién) · perfil ajeno = **la misma vista del Baúl** (fichas Pausa y Recomendación) · ficha ajena: "Guardar en mi Baúl" y "Hacer la Pausa" (ahora / elegir día y hora). | `screens/Comunidad.tsx`, `screens/PerfilAjeno.tsx`, `screens/FichaAjena.tsx`, `components/Frame.tsx`, `lib/api.ts` | e2e en preview con dos usuarios demo: buscar → solicitud → aceptar → ver fichas → reenviar → guardar / programar |
| **C2.2 Baúl y Perfil** | Baúl: fichas "Recomendación" con su píldora, CTA "Agregar recomendación" + wizard (premium; free → pop-up "Quiero ser parte"), "Pausa de <apodo>" para las guardadas · EntryDetail: "Reenviar a alguien de tu comunidad" (lista) + "Enviar por WhatsApp" (link) · Perfil: toggle "Perfil público" con explicación. | `screens/Baul.tsx`, `screens/EntryDetail.tsx`, `screens/Recomendacion.tsx`, `screens/Profile.tsx`, `app.css` | toggles y wizard verificados e2e |

### Ola C3 (1 agente) — legal y cierre
- **TyC v3**: cesión de las cartas de la comunidad, moderación, perfil público y
  fichas compartidas como decisión del usuario, borrar la cuenta borra todo lo
  público, recomendaciones = opiniones de usuarios, +16.
- Limpieza de fotos huérfanas de Storage (WS16).

Seed C: `make demo-seed` crea un segundo y tercer usuario demo (uno público, uno
privado) con fichas, un vínculo aceptado, una solicitud pendiente, un reenvío
recibido y dos recomendaciones.

## 5b. Bloque D — Promoción en TikTok: el libro animado · 🟢 EN CURSO (D0 WS31 · D1.1 WS32 · D1.2 WS34 · **D2 EN CURSO: vol. 1 Vínculos HECHO WS35**)

Objetivo: dar a conocer Dwellia de forma indirecta, con una historia que la gente quiera
seguir. Formato: **libros animados para hojear (flipbook)** de 25-30 s, verticales. Un
protagonista (**Teo**) y su pug (**Pipo**) crecen capítulo a capítulo; Dwellia es la magia
abstracta que los impulsa (algo se enciende de verde) y solo se nombra en la contratapa.
**La definición principal es el formato v2 de 5 escenas** (cartel variable · problema ·
espejo · magia · cierre fijo con iris) en
[`Flipbook/guiones/00_FORMATO_Y_OPUESTOS.md`](Flipbook/guiones/00_FORMATO_Y_OPUESTOS.md).
Tomás abre y opera la cuenta; Claude deja cada volumen listo.

| Ola | Qué | Estado |
|---|---|---|
| **D0 · Definición principal** | Formato v2 (5 escenas), cartel de apertura variable por volumen con imagen fija de Teo y Pipo, cierre fijo (iris Looney Tunes + contratapa), banco de ideas y memes replicables por volumen, biblioteca de gestos, dónde va Dwellia en TikTok. | ✅ WS31 |
| **D1.1 · Activos principales: Pipo y Teo** | **Capa ilustrada** (piezas transparentes, una vez, registradas en el motor; hoy el motor solo dibuja palitos). Las **6 caras de Pipo** (fastidio · resignación · sospecha · ¿en serio? · alegría sarcástica · orgullo) + sus poses (a cámara, camina, panza arriba, plantado, cae del sofá) · pulir a Teo (pelo). Hoja de personajes v2 aprobada por Tomás mirando PNG. | ✅ **CERRADA WS32** (08/09): `motor/partes.py` + `personajes/partes/` + `marioneta.py` · hoja v2 aprobada por Tomás en 4 vueltas (v3 caricatura amigable · Teo sin anteojos · orejas separadas + detalles achuchables) |
| **D1.2 · La fábrica** | `motor/libro.py`: un guion YAML → el mp4 completo sin tocar código. **Cartel** desde plantilla (viñeta fija de Teo y Pipo corriendo a lo Tintín + tinta/formas/título por volumen) · **la escena de la magia** como paquete fijo de 4 imágenes con 3 huecos · **cierre fijo** (Pipo pícaro · iris · tapa · contratapa con la D) · **el tempo** validado en video (6-8 imágenes de 3-4 s, globos de ≤12 palabras, la vida del cuadro). La biblioteca de gestos de cada volumen se dibuja en su WS (≤2-3 poses nuevas). | ✅ **CERRADA WS34** (08/09): WS33 construyó (F la magia · A+B2+C+E el motor, por agente) y WS34 cerró (caras por cuadro, contratapa invertida, tempo, B1 el cartel) |
| **D2 · Píldoras** (era "Temporada 1") | 🔄 **Replanteada en la WS36 con los números del vol. 1** (183 views · 3,64 s de tiempo medio sobre 30,7 s · 1,7 % de completado · 0 seguidores). En vez de 6 volúmenes largos, **muchos mini-videos de 10-14 s**, un chiste y un mensaje cada uno, publicados seguido. Formato en `Flipbook/guiones/00_FORMATO_CORTO.md`: el mensaje general de la cuenta (vivir el presente · la Pausa · escribir), la regla de oro (**una escena, bien hecha**) y la gramática **conexión/desconexión** (Pipo contento + Teo con aura ⟷ Pipo enojado + Teo triste), metida en el motor. | 🟢 **2 hechas · WS36** (09/09): `p01_espejo` "EL DILEMA DEL ESPEJO" (10,9 s) y `p02_meditar` "CINCO MINUTOS DE PAZ" (12,8 s), con portada. Siguen 3-4 en la WS37 (el paseo · escribir · la caída · el café). |
| **D3 · Puerta de entrada** | Landing para el link de la bio, links con seguimiento (UTM) y tablero mínimo de cuánta gente llega desde TikTok y cuánta completa el onboarding. | — |

Límites: Claude no crea ni opera la cuenta ni publica; no se generan fotos realistas de
personas ni se usan las de referencia en los videos; la música se elige al subir; no se
generan hojas con IA de imágenes (no mantiene el personaje).

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

## 6b. Después del MVP
Todo lo que queda para la v2 (reparto ponderado por puntaje, carta inactiva, dos
rituales por día, deudas técnicas) vive en [`POST_MVP.md`](POST_MVP.md), una línea por idea.

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
