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
| Cartas de usuarios | Pestaña **Crear** (premium; free ve un pop-up + "Quiero ser parte"). Wizard: pilar → acción inicial → frase + prompt con la carta dibujándose en vivo → firma (anónima o apodo) + cesión → enviar. **Una carta en revisión a la vez**. **Frase ≤ 60** · **prompt 100-220**. |
| Validación | Capa 1 determinística → capa 2 juez LLM **Sonnet 5** con el canon cacheado (≈1 céntimo) → **Tomás aprueba** desde `/admin`. **Aprobar = cargado** (WS25): estados visibles "En proceso de evaluación" (gris) → "Cargado a la comunidad", más "Necesita un retoque" y "No aprobada". Cada cambio avisa al autor. |
| Distribución (WS27) | **Las aprobadas entran al mazo como iguales**: la carta se suma a su pilar y el motor la reparte con las mismas reglas que las nuestras (rotación 6+1, ventanas de 7 días), a todo el mundo. Sin día especial, sin tope y **sin interruptor: todos reciben cartas de la comunidad** (la comunidad hace crecer el sistema; el juez + Tomás son la puerta de calidad). Dorso: "de <apodo>" o "de alguien de la comunidad". Impacto = cuántas personas la recibieron, visible para el autor. **Tablero de admin**: cartas por pilar, propias vs. de la comunidad, para emparejar a mano los pilares que queden desparejos. |
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
| Recibir cartas de la comunidad (opt-in) | ✅ | ✅ |
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

Objetivo: la feature insignia del premium, con la pestaña **Crear** y el pipeline
juez + Tomás. Al cerrar B la barra tiene 4 pestañas (Hoy · Baúl · Crear · Perfil).

### Ola B0 (orquestador) — el contrato
- Tabla `cartas_comunidad` (Mundo 2): `usuario_id`, `categoria_slug`, `accion_slug`,
  `frase` ≤60, `prompt` 100-220, `firma` (`anonima|apodo`), `estado`
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
| **B2.1 Distribución + impacto + tablero** | Las cartas `comunidad` ya están en el pool (B1.3 las publica en `cartas`): el motor las reparte como iguales a todos; la única exclusión es el propio autor (no recibe su carta). La columna `usuarios.recibe_comunidad` (B0) se elimina en la migración de B2.1: no hay interruptor. `GET …/mias` devuelve `personas_acompanadas` (entregas de esa carta). `GET /api/avisos` + `PUT …/{id}/leido` + no leídos. `GET /api/admin/resumen`: por pilar, total / propias / comunidad; propuestas en revisión; comentarios. | `services/entrega.py`, `routers/avisos.py`, `services/avisos.py` (lectura), `services/admin.py` (resumen), `db/models.py`, migración (drop `recibe_comunidad`), tests | la carta se sirve a cualquiera salvo a su autor; conteos correctos |
| **B2.2 Front: pestaña Crear + Admin** | `Frame.tsx` con 4 pestañas · `/crear`: free → pop-up "Escribir cartas es parte de la comunidad" + "Quiero ser parte"; premium → CTA "Escribir una carta" + lista **"Tus cartas"** prolija (miniatura de la carta, frase, estado con rótulo y color, sugerencia del juez, editar y reenviar, impacto) · wizard `/crear/nueva` 4 pasos con preview en vivo · campana de avisos · `/admin` = **adminland solo para la cuenta de Tomás**: tablero (cartas por pilar, propias vs. comunidad, pendientes) + cola de revisión (aprobar / retoque / rechazar) + comentarios. | `screens/Crear.tsx`, `screens/CartaNueva.tsx`, `screens/Admin.tsx`, `components/Frame.tsx`, `components/Card.tsx`, `lib/api.ts`, `app.css` | e2e en preview: proponer → juez simulado → admin aprueba → "Cargado" + aviso → llega el día 7 |

Seed B: `make demo-seed` suma 4 cartas del usuario demo, una por estado.

## 5. Bloque C — Comunidad (≈3-4 sesiones)

Objetivo: la pestaña **Comunidad** (5 pestañas: Hoy · Baúl · Comunidad · Crear ·
Perfil), sin feed ni seguidores: personas, solicitudes, reenvíos y las fichas de
recomendación.

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

## 5b. Bloque D — Promoción en TikTok: el libro animado (después de B y C · concepto cerrado WS26)

Objetivo: dar a conocer Dwellia de forma indirecta, con una historia que la gente quiera
seguir. Formato decidido en la WS26: **libros animados para hojear (flipbook)** de 15-30 s,
verticales. Un protagonista (**Teo**) y su pug (**Pipo**) crecen capítulo a capítulo; Dwellia
es la magia abstracta que los impulsa (algo se enciende de verde) y solo se nombra en la
contratapa. Todo el detalle vive en [`Flipbook/`](Flipbook/) (`CONCEPTO.md`, `REGLAS.md`,
fichas, guiones, motor). Tomás abre y opera la cuenta; Claude deja cada volumen listo.

| Ola | Qué |
|---|---|
| **D0 · Referencias + estrategia** | Tomás junta material en `Tiktok/` (estilos, ideas, personajes nuevos con foto + ficha). Se mira qué hacen apps parecidas en TikTok. Cadencia semanal, qué se mide. |
| **D1a · Personajes finales** | Pulir Teo (pelo) y Pipo con el material; secundarios de la temporada 1 (uno por pilar: padres, jefe, vecina, un desconocido…). Hoja de personajes aprobada por Tomás. |
| **D1b · La fábrica** | `Flipbook/motor/render.py` generaliza: guion en archivo → marionetas → hojas → mp4. Portada y contratapa desde plantilla. Un volumen nuevo cuesta minutos de render. |
| **D2 · Temporada 1** | 6 volúmenes, uno por pilar en el orden del reloj (amor propio · gratitud · vínculos · sentido · perspectiva · resiliencia). Guiones en `Flipbook/guiones/`, **todos desde cero, incluido el vol. 1** (el de la WS26 es un boceto de mecánica, no un guion). Descripciones y hashtags. |
| **D3 · Puerta de entrada** | Landing para el link de la bio, links con seguimiento (UTM) y tablero mínimo de cuánta gente llega desde TikTok y cuánta completa el onboarding. |

Límites: Claude no crea ni opera la cuenta ni publica; no se generan fotos realistas de
personas ni se usan las de referencia en los videos; la música se elige al subir; no se
generan hojas con IA de imágenes (no mantiene el personaje). Se hace DESPUÉS de B y C.

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
