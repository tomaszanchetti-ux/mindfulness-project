# M1 — Motor de Onboarding y Perfil · Madre del Motor

> **La entrada a la app.** Define cómo la persona crea su cuenta, entiende la tesis de
> Dwellia (los 6 pilares, escribir como pausa), configura su forma de pausar y queda
> lista para recibir su carta diaria. Entrega a M2 (entrega) y M3 (ritual) un usuario
> configurado. Se rige por el [`Documento Madre`](../00_Documento_Madre.md) y el
> storytelling del [`canon de cartas §0`](../M0_Motor_de_Contenido/canon_cartas.md).

---

## 1. Qué hace M1 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Login sin contraseña (Google + magic link) | Manejar pagos / planes (eso es v2) |
| Contar el storytelling: pilares + escribir como pausa | Elegir la carta del día (eso es M2) |
| Configurar el perfil: nombre, apodo, actividades, horario, aviso | El ritual en sí (girar/foto/reflexión real es M3) |
| Dejar el perfil **editable** después | Mezclar datos de un usuario con otro (aislamiento) |

**El norte de M1:** que en pocos toques la persona pase de "no tengo cuenta" a
"mañana a mi hora me llega mi primera carta", entendiendo qué es Dwellia, por qué
escribe en un diario físico y qué recorrido la espera.

---

## 2. El embudo (storytelling WS18)

```
1. Bienvenida + Login    →  Google / Magic link
2. Slideshow STORYTELLING (educativo, deslizable):
     a. Una pausa al día      → espacio de crecimiento personal, lejos de las distracciones.
                                MUCHO hincapié: diario físico + 15-30 min diarios disponibles.
     b. Los 6 pilares         → el curriculum del crecimiento, interconectados, con la
                                persona en el centro (círculo). Se presentan, NO se eligen:
                                cada semana se recorren todos (rotación 6+1 de M2).
     c. Escribir es tu pausa  → por qué escribir a mano, fuera del teléfono, es el motor
                                del crecimiento. Las actividades de desconexión (contemplar,
                                respirar, caminar, hacer) son disparadores que la preparan
                                (círculo alrededor de escribir).
     d. Los 5 pasos del ritual → recibe la carta · vive tu pausa · escribe lo que sentiste ·
                                guárdala en tu Baúl · compártela si quieres.
     e. ¿Comenzamos?          → "Sin feed ni likes. Solo una pausa al día."
3. Configurar la cuenta  →  nombre/apellido/apodo · actividades de desconexión
                            ("¿Cómo te gustaría complementar tu pausa?" — escribir NO es
                            opción: es el núcleo, siempre presente) · horario · aviso →
                            check de términos al cerrar
4. Carta real del día    →  M2 la entrega en el momento; 2 nudges contextuales la 1ª vez
```

El **slideshow va antes de configurar** a propósito: el compromiso (diario físico +
15-30 min) enmarca el horario que se elige justo después.

---

## 3. Login — passwordless prolijo

Dos vías, las dos **sin contraseña** y con el mail ya verificado (Firebase Auth):

- **Google** — un toque; trae su propio 2FA. Vuelve logueado.
- **Magic link** — escribe su mail → pantalla *"te mandamos un link a tu correo"* →
  toca el link → vuelve logueado. **El link es la verificación**, no hay paso extra.

**La regla de oro (aprendizaje del prode):** el mail tiene que **llegar siempre y
verse real**. Por eso el correo es **branded, desde dominio propio y por buen
proveedor de envío** (no el mail por defecto de Firebase, que es feo y cae en spam).

> Sin verificación adicional tipo código: agregaría fricción y rompe *Simpleza con
> apagado*. Lo passwordless, bien hecho, ya es la seguridad.

---

## 4. Configurar la cuenta (el wizard, sólo la 1ª vez)

| Campo | Detalle |
|-------|---------|
| **Nombre y apellido** | Identificación básica. |
| **Apodo** | Cómo lo llama la app ("Hola, {apodo}"). |
| **Actividades de desconexión** | *"¿Cómo te gustaría complementar tu pausa?"* — elige cuáles quiere recibir (contemplar, respirar, caminar, hacer). **Escribir no aparece como opción: es el núcleo de toda pausa** (canon §0) y las cartas de escritura pura siempre llegan. El menú filtra el pool de M2; la app aprende dentro de él con las ⭐. |
| **Horario de la carta** | Hora local a la que quiere recibir la carta. *(Guarda también su zona horaria — M2 entrega en hora local.)* |
| **Aviso** | Un solo interruptor **sí/no**. Si **sí**: email siempre + push donde se pueda. Si **no**: la carta aparece en silencio al abrir la app. |

**Al cerrar la configuración, el check de términos/privacidad** — explica que **no es
red social**, que **el contenido es 100% suyo** y que **compartir depende sólo de él**.
**`onboarding_completo` = términos aceptados** (no exige nada más).

> **Los pilares no se configuran.** Son la tesis de Dwellia (slideshow b) y M2 los
> recorre todos, cada semana. En Perfil se *muestran* como el recorrido, no como opción.

---

## 5. Notificaciones y "descargar como App" (arranque PWA)

Arrancamos como **PWA instalable** (Expo for Web, mismo código que el futuro nativo).

- **Email = aviso principal** — llega a cualquier teléfono (reusa la infra del magic link).
- **Push web = bonus** — Android/Chrome anda bien; **en iPhone sólo si instalan la app
  al inicio** (iOS 16.4+).
- Botón **"descargar como App"** y aviso trabajan juntos: *"instalá la app en tu inicio
  para recibir el aviso en el celular"*. **Instalar = desbloquear el push.**

> **Pivot de secuencia (no de stack):** el canon es React Native + Expo. Sale **primero
> la web/PWA** y después el **nativo a las stores**, desde el **mismo proyecto Expo**.

---

## 6. Perfil editable (Ajustes)

Editable después: apodo, nombre/apellido, **actividades**, horario, aviso.

- **Cambiar actividades** acá **cambia el pool de M2 en el acto**. (La escritura pura
  no se puede sacar: es la pausa misma.)
- **Cambiar horario/aviso** redefine cuándo y cómo avisa M2.
- **Los pilares se muestran** ("Los pilares que recorres") con la leyenda de la
  rotación semanal — informativos, no editables.

---

## 7. Datos que escribe M1 (handoff al stack §5)

Tablas **privadas** (cada fila con `user_id`, jamás se cruzan entre usuarios):

```
usuarios
  user_id (= Firebase UID, PK)
  email · nombre · apellido · apodo
  horario_carta · zona_horaria
  aviso_on (bool)
  terminos_aceptados_en
  creado_en

usuario_acciones          (0 a 4 filas por usuario + "escribir" siempre presente)
  user_id · accion_id      → FK a la tabla GLOBAL acciones (M0)
```

> **"Escribir" se guarda siempre** en `usuario_acciones` (el backend la fuerza), aunque
> en la UI ya no sea una opción: garantiza el invariante del pool de M2.
>
> **Tabla legacy:** `usuario_categorias` existe en la DB por compatibilidad (v1
> pre-WS17) pero **nada la lee**. El endpoint `PUT /api/perfil/categorias` queda
> deprecado por compatibilidad de clientes viejos. Se eliminan en una limpieza futura.

---

## 8. Decisiones canónicas vigentes

- **Login passwordless** (Google + magic link), sin paso de verificación extra.
- **Email branded por dominio propio + buen proveedor** (aprendizaje del prode).
- **PWA primero, nativo después** desde el mismo Expo.
- **Aviso = un solo interruptor**; si está off, la carta aparece en silencio.
- **Orden del embudo:** login → slideshow storytelling → configuración → carta real.
- **Los pilares se presentan, no se eligen (WS17/WS18):** la pantalla de pilares es
  educativa (círculo, persona en el centro); M2 rota los 6 cada semana.
- **Escribir no es opción del menú (WS18):** es el núcleo de toda pausa; las
  actividades de desconexión la complementan (*"¿Cómo te gustaría complementar tu
  pausa?"*).
- **`onboarding_completo` = términos aceptados** (WS17).
- **Privacidad en dos toques:** cierre del slideshow + check de términos.
- **Sin carta de ensayo (WS14):** al terminar la configuración cae la carta REAL del
  día con 2 nudges contextuales la primera vez. El storytelling vive en el slideshow.
- **Español de España neutro** en toda la UI (sin selector de "tono").

---

## 9. Historial (derogado — solo contexto, no usar)

- **Elegir categorías 2-6 (WS03-WS16):** el usuario elegía sus categorías como filtro
  duro de M2. **Derogado en WS17** (rotación completa) y reformulado en WS18 (pilares
  = tesis educativa del onboarding).
- **"Escribir" como opción bloqueada del menú (WS10-WS17):** se mostraba incluida y
  bloqueada ("piso garantizado"). **Reformulado en WS18:** ya no es opción — es el
  núcleo; el menú solo lista los complementos.
- **Carta de prueba / tutorial de 11 pop-ups (WS03-WS13):** derogado en WS14 por los
  2 nudges sobre la carta real.
- **Selector de "tono" del onboarding:** eliminado cuando M0 canonizó español neutro.

---

## 10. Diferido a v2

- Planes / pagos / freemium (`ROADMAP_v2_PREMIUM.md`).
- Más de un horario / dos rituales por día.
- Login con Apple (lo agrega Firebase fácil cuando salga el nativo a la App Store).
