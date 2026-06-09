# Documento Madre — Mindfulness App

> **Documento rector. Se lee primero, siempre.** Corto a propósito: la idea, los
> principios y lo que vendrá después. Todo lo demás se rige por esto.

---

## 1. La idea

Una app de **micro-rituales diarios de presencia, gratitud y conexión humana**. El
**fin último**: que el usuario **escriba, al menos una vez por día, en su diario
físico** lo que sintió — **fuera del teléfono**. La **actividad** (caminar,
respirar, contemplar, hacer… o simplemente escribir) es el **medio** que se lo
provoca; así nadie queda afuera por no tener tiempo o ganas de una actividad
puntual. El teléfono es **guía** (le trae la consigna) y **baúl** (guarda el
rastro: foto + una nota corta de ayuda-memoria), nunca el destino.

La unidad de contenido es la **carta del día**: una **frase** breve que invita a
frenar + un **micro-prompt** que la vuelve acción concreta ("salí, mirá la luna,
guardá lo que viste"). Frase + micro-prompt, inseparables.

**Qué es / qué no es**

| Sí es | No es |
|-------|-------|
| Un ritual diario corto, fuera de la pantalla | Una red social / un feed infinito |
| Un espacio íntimo y privado | Una plataforma de likes y followers |
| Un gesto hacia personas concretas | Una app de productividad o fitness |

**Alcance v1:** ritual individual + compartir por link.
- **Entra:** onboarding-compromiso · carta del día · foto y reflexión opcionales · Baúl de Crecimiento Personal · compartir por link · perfil.
- **Queda para después:** círculos, IA generativa, dos rituales por día, packs.

**Stack:** Google Cloud + PostgreSQL + app móvil (React Native), nivel Arc One
(NO Vercel/Supabase). Mapa completo en §5. *Simple = la ingeniería, no el stack.*

---

## 2. Cómo funciona la app

El usuario hace el **onboarding una sola vez**. Después, **cada día a su hora**
recibe una **carta** (con un aviso opcional). La abre cerrada, la **gira**, lee la
frase y el micro-prompt, **hace el ejercicio afuera del teléfono**, **escribe en su
diario lo que sintió** (el cierre siempre invita a eso) y, si quiere, vuelve y sube
una **foto + una reflexión corta ≤250 de ayuda-memoria**. Todo se guarda en el **Baúl**.
Puede compartir la carta por link si le nace. Y la app **se apaga**.

**Los tres loops**
1. **Diario:** aviso → carta del día → se ejecuta afuera → (opcional) foto + reflexión → al Baúl → la app se apaga.
2. **Gesto (secundario, latente):** compartir una carta por link con una nota; el receptor la abre sin instalar nada. Único canal de crecimiento, pero **no se empuja**.
3. **Baúl:** mirar atrás lo vivido. Es la retención.

**Los motores de la app** (cada uno puede volverse su propia carpeta, como M0)

| Motor | Qué hace | Estado |
|-------|----------|--------|
| **M0 · Contenido** | La materia prima: las 6 categorías y las cartas (frase + micro-prompt + dibujo). | ✅ cerrado v1 (69 cartas) |
| **M1 · Onboarding y Perfil** | La entrada y las preferencias: login sin contraseña; elegir categorías (2-6), **actividades** y horario; activar (o no) el aviso; aceptar términos; explicar la app y el compromiso (diario a mano, 10-15 min). Editable después. | ✅ lógica cerrada v1 ([M1](M1_Onboarding_y_Perfil/Madre_del_Motor.md)) |
| **M2 · Entrega del día** | Elige la carta del día (azar ponderado: filtro duro por tus categorías **y tus actividades elegidas** — con **"escribir" siempre disponible** como piso — + preferencia blanda de acción que aprende de tus estrellas; sin repetir la última semana) y avisa (push/email opcional). Vigencia 24h o hasta completarla. | ✅ lógica cerrada v1 ([M2](M2_Entrega_del_Dia/Madre_del_Motor.md)) |
| **M3 · Ritual** | El momento: recibís la carta, la girás, hacés el ejercicio afuera y volvés a cerrarlo — **reflexión** ≤250 (protagonista, no bloquea Guardar), **hasta 3 fotos** y **estrellas** 1-5 (opcionales). Una sola superficie (scroll en el dorso). **Sin gate:** la próxima carta llega siempre; lo dejado a medias se autoguarda sin culpa. | ✅ lógica cerrada v1 ([M3](M3_Ritual/Madre_del_Motor.md)) |
| **M4 · Baúl de Crecimiento Personal** | El historial de todo lo vivido (carta + foto + reflexión). Dos modos de orden: **Reciente** (default) y **Más valoradas**. Se puede **borrar** una entrada para siempre (modal claro + botón rojo; limpia DB + fotos + link). Casi sólo lectura. | ✅ lógica cerrada v1 ([M4](M4_Baul/Madre_del_Motor.md)) |
| **M5 · Compartir** | Link público con nota personal. **Carta sola** (sin datos tuyos) o **ejercicio completo** (con reflexión + fotos → aviso de privacidad). El que recibe lo abre **sin instalar ni loguear**; un CTA suave al final. El link **muere si borrás la entrada**. Secundario y latente: se ofrece, no se empuja. | ✅ lógica cerrada v1 ([M5](M5_Compartir/Madre_del_Motor.md)) |

---

## 3. Principios rectores

**El Norte: _menos consumo, más presencia._**

### 🤝 Cómo trabajamos (nuestros)
1. **Simpleza** — claro, corto, sin jerga (Tomás no es técnico). Soluciones simples en la ingeniería, pero realizables y escalables. *Simple ≠ barato.*
2. **Eficacia** — decidir en pocas interacciones; y que todo funcione, escale (100.000 usuarios), sea seguro (datos de un usuario jamás se mezclan) y perfectamente usable.
3. **Integralidad** — la app es **un todo interconectado**: cada motor toma cosas del anterior y resuelve cosas para el o los siguientes. Cada visión y definición se hace **completa e integral**, nunca aislada (como trabajamos Arc One).

### 📿 Cómo se comporta la app
1. **El ritual vive fuera de la pantalla** — el teléfono manda a hacer algo afuera, **invita a escribirlo en tu diario** (el fin) y guarda el rastro. La actividad es el medio: que escribas es el objetivo.
2. **Simpleza con apagado** — interacción mínima; la mejor sesión es la que termina y te devuelve a tu vida.
3. **Intimidad como producto** — 100% tuyo, privado por defecto; no estás obligado a cargar nada; compartir es decisión explícita.
4. **Invitar, nunca exigir** — sin push de nada salvo el aviso (opcional) de la carta del día. Sin rachas ni métricas de vanidad.

> **El gesto de compartir es secundario y latente:** se ofrece, nunca se empuja. No es lo que validamos.

---

## 4. Posibles componentes v2 (más adelante)

No entran en la v1; son la zanahoria del roadmap.

- **Círculos privados** — compartir recurrente con un grupo chico + reacciones emocionales (no likes).
- **IA creativa** — reescritura de tono, transformar la reflexión en tarjeta visual, resumen semanal, recomendaciones suaves.
- **Dos rituales por día** — mañana y noche, estilo diario guiado (palanca premium).
- **Cartas propias por el usuario** — armar cartas vía integración con Claude Design (API).
- **Carta sorpresa semanal** — una frase de motivación que llega de sorpresa (engagement suave, a evaluar).
- **Freemium completo** — más categorías, almacenamiento de fotos, personalización, packs temáticos.

---

## 5. Stack y datos (N3)

Espejo del stack probado de **Arc One**, pensado para escalar a **+100.000 usuarios**
con los datos de cada persona **aislados** (sobre todo el Baúl).

| Pieza | Servicio | Para qué |
|-------|----------|----------|
| **App móvil** | React Native + Expo | El front: app real de celular (notificación diaria, cámara, ritual). Misma familia React que Arc One. |
| **Backend / API** | Cloud Run (Python) | Sirve la carta del día (acá vivirá el motor M2) y guarda el Baúl. |
| **Base de datos** | Cloud SQL (PostgreSQL) | Todo el dato estructurado. Escala a +100k sin despeinarse. |
| **Login / cuentas** | Firebase Authentication | Una cuenta por persona. Donde **empieza** el aislamiento. |
| **Imágenes** | Cloud Storage | Dibujos de las cartas + fotos del Baúl (carpetas por usuario). |

**Dos mundos de datos** (la regla de oro del aislamiento):
- **Contenido (compartido):** las cartas son iguales para todos. Tablas **globales**. Acá vive **M0**.
- **Datos del usuario (privados):** perfil, categorías elegidas y Baúl son tuyos. Cada fila lleva su `user_id` y **toda consulta filtra por el usuario logueado**, así el Baúl de uno jamás toca el de otro. *(No es "una base por usuario" — eso no escala.)*

**Las tablas:**

```
categorias  (6)   ┐
acciones    (5)   ├─ GLOBALES, compartidas  →  M0 vive acá
cartas      (69)  ┘     (seed = los 3 JSON de M0_Motor_de_Contenido/data/)
──────────────────────────────────────────────────────────
usuarios               ┐
usuario_categorias     │
usuario_acciones       │   ← actividades elegidas (M1; "escribir" siempre cuenta)
entregas / Baúl        ├─ PRIVADAS, todo con user_id
fotos                  │     (entregas+fotos: M2/M3 · compartidos: M5)
compartidos            ┘
```

Los **JSON del repo son el seed maestro**: un script los carga una vez a las 3 tablas
globales (y re-seedea si sumamos cartas). Las fotos del Baúl van a Cloud Storage; la
DB guarda solo la ruta.

> Confianza sobre Arc One: alta en *Google Cloud · PostgreSQL · Cloud Run · React+TS · Firebase*. Pendiente menor: confirmar versiones/servicios exactos contra el repo de Arc One antes de codear.

> **Pivot de secuencia (WS03):** salimos **primero como PWA instalable** (Expo for Web)
> y después el **nativo a las stores**, desde el **mismo proyecto Expo**. El stack no
> cambia; cambia el orden de salida. Consecuencia: el **aviso principal es email**
> (el push web en iPhone sólo anda con la app instalada al inicio). Detalle en M1 §7.
