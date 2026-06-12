# M1 — Motor de Onboarding y Perfil · Madre del Motor

> **La entrada a la app.** Define cómo la persona crea su cuenta, entiende la tesis de
> Dwellia (la pausa de dos tiempos + los 6 pilares en anillos), configura su horario y
> queda lista para recibir su carta diaria. Entrega a M2 (entrega) y M3 (ritual) un
> usuario configurado. Se rige por el [`Documento Madre`](../00_Documento_Madre.md) y el
> storytelling del [`canon de cartas §0`](../M0_Motor_de_Contenido/canon_cartas.md).

---

## 1. Qué hace M1 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Login sin contraseña (Google + magic link) | Manejar pagos / planes (eso es v2) |
| Contar el storytelling: la pausa de dos tiempos + los pilares | Elegir la carta del día (eso es M2) |
| Configurar el perfil: nombre, apodo, horario, aviso | Elegir pilares o acciones (no se eligen — WS17/WS22) |
| Dejar el perfil **editable** después | Mezclar datos de un usuario con otro (aislamiento) |

**El norte de M1:** que en pocos toques la persona pase de "no tengo cuenta" a
"mañana a mi hora me llega mi primera carta", entendiendo qué es Dwellia, por qué
escribe en un diario físico y qué recorrido la espera.

---

## 2. El embudo (storytelling WS18)

```
1. Bienvenida + Login    →  Google / Magic link
2. Slideshow STORYTELLING (educativo, deslizable · re-diseño WS22 pendiente, paso UX):
     a. Una pausa al día      → espacio de crecimiento personal, lejos de las distracciones.
                                MUCHO hincapié: diario físico + 15-30 min diarios disponibles.
     b. Los 6 pilares         → el curriculum del crecimiento: la persona al centro, la
                                calma como suelo, TRES ANILLOS de a dos pilares (adentro:
                                amor propio · sentido / la experiencia: gratitud ·
                                perspectiva / afuera y adelante: vínculos · resiliencia).
                                Se presentan, NO se eligen: cada semana se recorren todos
                                (rotación 6+1 de M2).
     c. La pausa de dos tiempos → una acción te lleva a la calma (contemplar, respirar,
                                pasear, hacer); en calma, escribes lo que sentiste en tu
                                diario físico — escribir es el motor del crecimiento.
     d. Los 5 pasos del ritual → recibe la carta · vive tu pausa · escribe lo que sentiste ·
                                guárdala en tu Baúl · compártela si quieres.
     e. ¿Comenzamos?          → "Sin feed ni likes. Solo una pausa al día."
3. Configurar la cuenta  →  nombre/apellido/apodo · horario · aviso →
                            check de términos al cerrar (las acciones NO se eligen — WS22)
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
| **Horario de la carta** | Hora local a la que quiere recibir la carta. *(Guarda también su zona horaria — M2 entrega en hora local.)* |
| **Aviso** | Un solo interruptor **sí/no**. Si **sí**: push donde se pueda (WS21). Si **no**: la carta aparece en silencio al abrir la app. |

> **Las acciones no se configuran (WS22).** El motor sirve las 4 acciones iniciales;
> "pasear" (no "caminar") resuelve la accesibilidad sin preguntas, y el cambio de
> carta (v2 premium) cruza el eje movimiento↔quietud para quien ese día no quiere
> moverse. Menos opciones, menos fricción, más control del outcome.

**Al cerrar la configuración, el check de términos/privacidad** — explica que **no es
red social**, que **el contenido es 100% suyo** y que **compartir depende sólo de él**.
**`onboarding_completo` = términos aceptados** (no exige nada más).

> **Los pilares no se configuran.** Son la tesis de Dwellia (slideshow b) y M2 los
> recorre todos, cada semana. En Perfil se *muestran* como el recorrido, no como opción.

---

## 5. Notificaciones y "descargar como App" (arranque PWA)

Arrancamos como **PWA instalable** (Expo for Web, mismo código que el futuro nativo).

- **Push web = el aviso (WS21; email descartado, `services/email.py` dormido)** —
  Web Push estándar + VAPID, suscripción por dispositivo, barrido cada 15 min.
- En **Android/Chrome** anda directo; **en iPhone sólo con la PWA instalada al
  inicio** (iOS 16.4+) → el copy empuja a instalar (instructivo en Perfil, WS19).
- Botón **"descargar como App"** y aviso trabajan juntos: *"instalá la app en tu inicio
  para recibir el aviso en el celular"*. **Instalar = desbloquear el push.**

> **Pivot de secuencia (no de stack):** el canon es React Native + Expo. Sale **primero
> la web/PWA** y después el **nativo a las stores**, desde el **mismo proyecto Expo**.

---

## 6. Perfil editable (Ajustes)

Editable después: apodo, nombre/apellido, horario, aviso.

- **Cambiar horario/aviso** redefine cuándo y cómo avisa M2.
- **Los pilares se muestran** ("Los pilares que recorres") con la leyenda de la
  rotación semanal — informativos, no editables. Las acciones tampoco se editan
  (WS22): no hay menú que mantener.
- **Teoría in-app** ("el método Dwellia"): sección breve y serena que explica la
  pausa de dos tiempos y los pilares — derivada de
  [`fundamentos_pilares.md`](../M0_Motor_de_Contenido/fundamentos_pilares.md)
  (pendiente, paso UX WS22).

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
```

> **Tablas obsoletas:** `usuario_acciones` (las acciones ya no se eligen — WS22) y
> `usuario_categorias` (los pilares no se eligen — WS17) existen en la DB pero
> **nada debe leerlas**. Los endpoints `PUT /api/perfil/acciones` y
> `PUT /api/perfil/categorias` quedan deprecados. Todo se elimina en la bajada a
> código del paso 3 (canon §Transición).

---

## 8. Decisiones canónicas vigentes

- **Login passwordless** (Google + magic link), sin paso de verificación extra.
- **Aviso diario = SOLO push web (WS21):** email descartado como canal de aviso.
  (El email branded queda solo como mejora futura del magic link de login.)
- **PWA primero, nativo después** desde el mismo Expo.
- **Aviso = un solo interruptor**; si está off, la carta aparece en silencio.
- **Orden del embudo:** login → slideshow storytelling → configuración → carta real.
- **Ni pilares ni acciones se eligen (WS17/WS22):** la pantalla de pilares es
  educativa (tres anillos, persona en el centro, calma como suelo); M2 rota los 6
  cada semana y sirve las 4 acciones iniciales. "Pasear" resuelve la accesibilidad
  sin configuración; el cambio de carta v2 cruza el eje movimiento↔quietud.
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
- **Elegir actividades de desconexión (WS10-WS18):** menú de complementos en el
  onboarding y Perfil, filtraba el pool de M2 (`usuario_acciones`). **Derogado en
  WS22:** la pausa es de dos tiempos — el motor sirve las 4 acciones iniciales,
  escribir es el cierre universal y nada se elige.
- **Carta de prueba / tutorial de 11 pop-ups (WS03-WS13):** derogado en WS14 por los
  2 nudges sobre la carta real.
- **Selector de "tono" del onboarding:** eliminado cuando M0 canonizó español neutro.

---

## 10. Diferido a v2

- Planes / pagos / freemium (`ROADMAP_v2_PREMIUM.md`).
- Más de un horario / dos rituales por día.
- Login con Apple (lo agrega Firebase fácil cuando salga el nativo a la App Store).
