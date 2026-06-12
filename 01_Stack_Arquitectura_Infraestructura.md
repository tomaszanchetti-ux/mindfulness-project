# Stack · Arquitectura · Infraestructura (N4)

> **Documento de referencia técnica. Se confirma una vez, antes de codear.**
> Espejo del stack **probado y en producción** de Arc One, adaptado de una
> plataforma B2B (web) a una **app de consumo móvil para +100.000 usuarios**.
> Versiones verificadas contra `arc-one-sandbox` el 09/06/2026.
>
> Manda el [Documento Madre §5](00_Documento_Madre.md). Esto lo baja a detalle.

---

## 0. La idea en una frase

Tomamos **el mismo stack que ya funciona en Arc One** (Google Cloud + Postgres +
Cloud Run + React/TS + Firebase), porque está probado, escala y Mati ya lo conoce.
**Cambia una sola pieza grande** (el front: en vez de web, app móvil) y **se suma
una pieza nueva** (el email transaccional, que Arc One no necesita por ser B2B).
Todo lo demás es calcado.

---

## 1. El stack, pieza por pieza

| Pieza | Servicio | Versión exacta (Arc One) | ¿Igual que Arc One? | Para qué en mindfulness |
|-------|----------|--------------------------|---------------------|--------------------------|
| **Front** | React Native + **Expo** | React 19 · TS 6 (familia) | 🟡 **Misma familia, distinto target** | La app real del celular: carta del día, cámara, girar la carta, Baúl. Arc One es web (Vite); nosotros móvil (Expo). |
| **API / Backend** | **Cloud Run** (Python) | FastAPI 0.115 · Uvicorn 0.34 | ✅ Idéntico | Sirve la carta del día (motor M2), guarda el Baúl, arma los links de M5. |
| **ORM / Migraciones** | SQLAlchemy + Alembic | SQLAlchemy 2.0.41 · Alembic 1.15.2 · psycopg 3.2.9 | ✅ Idéntico | Define las tablas y versiona los cambios de esquema. |
| **Validación de datos** | Pydantic | Pydantic 2.11.4 · pydantic-settings 2.9.1 | ✅ Idéntico | Contratos de entrada/salida de la API. |
| **Base de datos** | **Cloud SQL (PostgreSQL)** | Postgres **16** | ✅ Idéntico | Todo el dato estructurado. Escala a +100k sin despeinarse. |
| **Login / cuentas** | **Firebase Authentication** | firebase-admin 6.6.0 (API) · firebase 11.6 (cliente) | ✅ Idéntico | Una cuenta por persona. Donde **empieza** el aislamiento. Passwordless (Google + magic-link). |
| **Imágenes** | **Cloud Storage** | — | ✅ Mismo patrón GCP | Dibujos de las cartas (M0) + fotos del Baúl (M3). Carpeta por `user_id`. |
| **Trabajos en segundo plano** | **Redis + RQ** | Redis 6.1 (lib) · RQ 2.3.3 · Memorystore Redis 7 | ✅ Idéntico | **El motor del aviso diario** (ver §3.2): calcular y disparar la carta de cada usuario a su hora. |
| **Hosting web (PWA + links)** | **Firebase Hosting** | — | ✅ Idéntico | Sirve la PWA y las **páginas públicas `/c/{token}`** de M5 (el receptor abre sin instalar). Rewrites `/api/**` → Cloud Run. |
| **Infra como código** | **Terraform** | GCP provider | ✅ Idéntico | Toda la infra reproducible: un comando levanta DB + Cloud Run + Redis + secretos + red. |
| **Secretos** | Secret Manager | — | ✅ Idéntico | DATABASE_URL, claves, tokens. Nunca en el código. |
| **Registro de imágenes** | Artifact Registry | — | ✅ Idéntico | Guarda la imagen Docker del backend que corre en Cloud Run. |
| **Push** | **FCM** (Firebase Cloud Messaging) | familia Firebase | ✅ Mismo patrón (lo usa prode) | Aviso a quien **instaló** la app. Igual que prode hoy. |
| **📧 Email del aviso diario** | **Resend** *(solo si hace falta · a confirmar en M2)* | — | 🆕 **Pieza nueva, NO bloqueante** | Fallback del aviso diario para quien **NO** instaló la PWA. Ver §2.2. |

> **Leyenda:** ✅ calcado de Arc One · 🟡 misma familia, otro target · 🆕 pieza nueva.
>
> **Ojo — el email de login NO necesita proveedor:** el magic-link de login lo manda
> **Firebase Auth solo** (`sendSignInLinkToEmail`), gratis y built-in. Es exactamente
> lo que hace **prode** hoy. El único caso que *podría* pedir un proveedor externo es
> el **aviso diario por email** (§2.2), y esa decisión recién aparece en M2.

---

## 2. Las dos divergencias (lo único que NO es calco)

### 2.1 🟡 El front: móvil en vez de web

Arc One es una **web** (React 19 + Vite + Tailwind, servida por Firebase Hosting).
Nosotros necesitamos una **app de celular** (notificación, cámara, sensación de
ritual). Por eso: **React Native + Expo**.

- **Misma familia React + TypeScript** → todo lo que Mati sabe de Arc One aplica.
- **PWA primero, nativo después** (decisión WS03): salimos con **Expo for Web**
  como PWA instalable, servida por el **mismo Firebase Hosting** que Arc One.
  Después, el **mismo proyecto Expo** compila a las stores. El stack no cambia;
  cambia el orden de salida.
- **Consecuencia (actualizada WS21):** el aviso diario es **SOLO push web**
  (Web Push estándar + VAPID, sin FCM; email descartado por decisión de Tomás —
  `services/email.py` quedó dormido). En iPhone el push solo anda con la PWA
  instalada (iOS 16.4+) → el copy empuja a "instalar como App".

### 2.2 El aviso diario (histórico WS07 — el canal cambió a push en WS21)

Lo que verificamos contra **prode** (09/06): prode **no usa ningún proveedor de email
transaccional**. Resuelve todo con Firebase:

- **Login** → magic-link que **manda Firebase Auth solo** (`sendSignInLinkToEmail` /
  `signInWithEmailLink`). Gratis, built-in. **No necesitamos proveedor.**
- **Notificaciones** → **FCM push**. Prode avisa por push, no por email.

El "aprendizaje de prode" sobre **email branded con dominio propio** es real pero
acotado: el magic-link de Firebase sale de un dominio `firebaseapp.com` que se ve feo
y cae en spam → para que llegue branded hay que configurar dominio propio. **No
bloquea nada para arrancar.**

**Dónde sí podría aparecer un proveedor externo:** el **aviso diario de la carta**.
Firebase Auth solo manda emails de *autenticación* — no puede mandar un "tu carta del
día te espera". Para ese aviso hay dos caminos:

- **Camino A (el de prode): FCM push como canal principal.** Cero pieza nueva. Cubre
  a quien instaló la app. Limitación WS03: en iPhone-PWA-no-instalada el push no
  llega.
- **Camino B: sumar un proveedor de email** (Resend / Postmark / SendGrid, o la
  Firebase Extension *Trigger Email* que igual usa un SMTP por debajo) para cubrir
  también a quien no instaló.

> **Decisión diferida a M2** — no bloquea el build inicial (seed + auth). Cuando
> lleguemos a la entrega diaria elegimos A, B o A+B. Recomendación tentativa: **A+B**
> (push para instalados + email para el resto), con **Resend** si vamos por B.

---

## 3. Arquitectura

### 3.1 Los dos mundos de datos (la regla de oro del aislamiento)

Idéntico a como Arc One aísla workspaces, pero a escala de usuario individual:

```
┌─────────────────────────────────────────────────────────────┐
│  MUNDO 1 · CONTENIDO (global, compartido por todos)          │
│  categorias (6) · acciones (5) · cartas (69)                 │
│  → seed maestro = los 3 JSON de M0_Motor_de_Contenido/data/  │
│  → un script los carga una vez; re-seed si sumamos cartas    │
├─────────────────────────────────────────────────────────────┤
│  MUNDO 2 · DATOS DEL USUARIO (privados, todo con user_id)    │
│  usuarios · entregas (Baúl) · fotos · compartidos ·          │
│  push_suscripciones · (usuario_acciones + usuario_categorias:│
│   OBSOLETAS — WS22/WS17, se eliminan en la limpieza)         │
│  → CADA fila lleva user_id                                    │
│  → TODA consulta filtra por el usuario logueado              │
└─────────────────────────────────────────────────────────────┘
```

> **⚠️ Transición WS22 (pendiente, paso 3):** el canon de contenido se refundó —
> categoría `sentido` reemplaza a `calma`, `acciones` queda en 4 acciones iniciales
> (escribir = cierre universal), display `caminar` → "pasear", y las tablas de
> elección (`usuario_acciones`, `usuario_categorias`) se eliminan. Lo de arriba
> describe la DB desplegada HOY; el destino está en
> [`canon_cartas.md §Transición`](M0_Motor_de_Contenido/canon_cartas.md).

**La regla que no se rompe nunca** (canon Arc One, macro de Mati): el filtro por
`user_id` vive **en el backend (Cloud Run), JAMÁS en el cliente**. El Baúl de uno no
puede tocar el de otro ni por error. **No es "una base por usuario"** (eso no escala
a 100k) — es **una sola base, filtrada server-side** + Firebase Auth + carpeta por
usuario en Cloud Storage.

### 3.2 El motor del aviso diario (el desafío de escala real)

Esto es lo **único que Arc One no tiene que resolver** (B2B no le dispara a 100k
consumidores a horario). Es el corazón operativo de la app y donde el Redis + RQ que
ya está en el stack gana su lugar:

```
Cloud Scheduler (cron, cada ~15 min)
        │
        ▼
Cloud Run: endpoint /jobs/tick
        │  "¿quién tiene su horario en esta ventana (según su hora + TZ)?"
        ▼
Encola en Redis (RQ) un trabajo por lote de usuarios "que toca avisar ahora"
        │
        ▼
Worker (Cloud Run): para cada usuario del lote
        │  1. elegir_carta()  ← motor M2 (ya escrito en M2_Entrega_del_Dia/)
        │  2. crear la fila en `entregas` (vigencia 24h)
        │  3. disparar el aviso (email · push si instalada)
        ▼
Idempotente: si un tick se repite, no manda dos veces (1 entrega/día/usuario)
```

- **Por qué escala:** no hacemos un cron gigante; partimos a 100k usuarios en
  ventanas de 15 min por su hora local. Cada ventana es un puñado de lotes cortos.
- **TZ autodetectada + editable** (canon M1): el cálculo "¿le toca ahora?" usa la TZ
  guardada del usuario, no el país.
- **El `elegir_carta()` ya existe** como función pura en `M2_Entrega_del_Dia/entrega.py`
  — el worker la invoca, no se reescribe.

### 3.3 Las capas (de afuera hacia adentro)

```
📱 Expo (PWA / nativo)          ← M1 onboarding · M3 ritual · M4 Baúl
        │ HTTPS (Firebase Auth ID token en cada request)
        ▼
🔥 Firebase Hosting             ← sirve la PWA + páginas públicas /c/{token} (M5)
        │ rewrite /api/** → Cloud Run
        ▼
☁️ Cloud Run (FastAPI)          ← API: valida token, filtra por user_id, motores
        │                          ↘ Redis + RQ (aviso diario · §3.2)
        ▼
🐘 Cloud SQL (Postgres 16)      ← Mundo 1 (contenido) + Mundo 2 (usuario)
🗄️ Cloud Storage                ← dibujos de cartas + fotos del Baúl
```

### 3.4 Cómo se mapea a los motores ya cerrados

| Motor | Dónde vive técnicamente |
|-------|--------------------------|
| **M0 · Contenido** | Tablas globales `categorias`/`acciones`/`cartas` + seed JSON + dibujos en Cloud Storage. |
| **M1 · Onboarding** | Firebase Auth (passwordless) + tablas `usuarios`/`usuario_categorias`. |
| **M2 · Entrega** | `elegir_carta()` corriendo en el worker RQ + tabla `entregas`. |
| **M3 · Ritual** | Endpoints de cierre (reflexión + estrellas) + subida de fotos a Cloud Storage (tabla `fotos`). |
| **M4 · Baúl** | Lectura `entregas ⨝ fotos ⨝ cartas` filtrada por `user_id` + borrado real (DB + Storage). |
| **M5 · Compartir** | Tabla `compartidos` (token opaco) + página pública server-side en Firebase Hosting. |

---

## 4. Infraestructura (GCP vía Terraform)

Todo se levanta con Terraform — mismos módulos que `arc-one-sandbox/infra/terraform/`:

| Recurso | Servicio GCP | Notas de escala (+100k) |
|---------|--------------|--------------------------|
| **Base de datos** | Cloud SQL Postgres 16, IP **privada** vía VPC | Cloud Run llega por IP privada (no proxy sidecar). Backups automáticos + **PITR** (point-in-time recovery) ya en el Terraform de Arc One. Pooling con `psycopg-pool` (Cloud SQL tiene límite de conexiones; el pool lo respeta). |
| **API** | Cloud Run (autoescala a 0..N) | Escala solo con el tráfico. La carga diaria es predecible (picos por ventana horaria). |
| **Cola / jobs** | Memorystore Redis 7 (tier BASIC) | Para RQ. El aviso diario es el consumidor principal. |
| **Disparador diario** | **Cloud Scheduler** *(nuevo vs Arc One)* | Cron que pega a `/jobs/tick` cada ~15 min. Único servicio que se suma a la lista de Arc One. |
| **Imágenes** | Cloud Storage (bucket, carpeta `/{user_id}/`) | Fotos del Baúl + dibujos. La DB guarda solo la ruta. |
| **Secretos** | Secret Manager | DATABASE_URL, ANTHROPIC (v2 IA), claves de email. |
| **Imagen Docker** | Artifact Registry | La build del backend. |
| **Red** | VPC + private services + VPC connector | Cloud Run ↔ Cloud SQL/Redis por red privada. |
| **CI/CD** | GitHub Actions + OIDC (sin claves) | Igual que Arc One (`github_oidc.tf`). |
| **Región** | `europe-west1` | Misma que Arc One (cercanía a Madrid/España). |

**APIs de GCP a habilitar** (las mismas de Arc One + Scheduler): run, sqladmin,
redis, secretmanager, artifactregistry, compute, servicenetworking, vpcaccess,
iam, sts, **cloudscheduler**.

---

## 5. Resumen ejecutivo — qué cambia respecto de Arc One

| | Arc One (probado) | Mindfulness (este doc) |
|---|---|---|
| Front | React 19 + **Vite** (web) | React 19 + **Expo** (móvil/PWA) 🟡 |
| API | FastAPI / Cloud Run | **Idéntico** ✅ |
| DB | Cloud SQL Postgres 16 | **Idéntico** ✅ |
| Auth | Firebase Auth / Auth0 (dual) | Firebase Auth passwordless ✅ |
| Storage | Cloud Storage | **Idéntico** ✅ |
| Jobs | Redis + RQ | **Idéntico** ✅ (lo usamos para el aviso diario) |
| Hosting | Firebase Hosting | **Idéntico** ✅ |
| Infra | Terraform / GCP | **Idéntico** ✅ |
| Disparador cron | — | **+ Cloud Scheduler** 🆕 |
| Email de login | (Firebase Auth) | **Idéntico patrón** ✅ (built-in, gratis) |
| Aviso diario | — | **FCM push** ✅ (como prode) **+ email opcional** 🆕 (decisión M2) |

**Confianza: muy alta.** Casi todo es calco directo de algo que ya está en producción
(Arc One para la infra/backend, prode para el patrón auth+push). El único cambio
estructural es el front móvil; el email es una decisión menor y diferida.

---

## 6. Decisiones abiertas antes de codear

1. **🟢 Email de login — RESUELTO:** Firebase Auth built-in, gratis, como prode. Sin
   proveedor. (Branding del dominio = pulido posterior, no bloquea.)
2. **🟡 Aviso diario — DIFERIDO A M2:** FCM push (camino A, como prode) y/o proveedor
   de email (camino B, recomendación Resend). No bloquea seed+auth. Ver §2.2.
3. **Confirmar con Mati (sign-off técnico, North Star = CTO)** — el stack es espejo
   del suyo, así que debería ser un sí rápido. Punto a validar: el patrón
   **Cloud Scheduler → RQ** para el aviso diario (es lo único que Arc One no tiene).

---

## 7. Próximo paso (plan WS06)

Con esto cerrado, el orden de build (N4) acordado:

1. **Seed + Auth** — tablas globales (M0) cargadas + Firebase Auth andando.
2. **Entrega + Ritual** — `elegir_carta()` en el worker + ciclo M2/M3.
3. **Baúl** — lectura M4.
4. **Compartir** — páginas públicas M5.

Antes del build, queda pendiente del plan WS06 el doc de UX/UI general
(`Madre_del_Diseno.md`, espejo del design-system de Arc One).
