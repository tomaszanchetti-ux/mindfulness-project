# M3 — Motor del Ritual · Madre del Motor

> **El único momento en que el usuario toca el teléfono.** Recibe la carta que eligió M2,
> la gira, hace el ejercicio **afuera**, y vuelve a cerrar el ritual: una reflexión, fotos
> y estrellas. Tiene que sentirse como cerrar un cuaderno, no como usar una app. Devuelve a
> M2 la estrella y el "completada", y deja el rastro que mira M4 (Baúl). Se rige por el
> [`Documento Madre`](../00_Documento_Madre.md).
>
> M3 es **lógica + pantalla** (todavía no se codea). Acá vive el modelo; el front (React
> Native + Expo) y el guardado a Postgres/Cloud Storage se construyen en N4.

---

## 1. Qué hace M3 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Mostrar la carta del día (frente → dorso al tocar) | Elegir la carta (eso es M2) |
| Invitar a hacer el ejercicio **fuera del teléfono** | Acompañar/temporizar la actividad — el teléfono se calla |
| Capturar al cerrar: **reflexión** + fotos + estrellas | Exigir nada para que llegue la próxima carta |
| Devolver a M2 la **estrella** y **completada** | Mostrar el historial (eso es M4) |
| Dejar el rastro (reflexión + fotos) para el Baúl | Empujar a compartir (Compartir es secundario, M5) |

**El norte de M3:** que el contacto con la pantalla sea **mínimo, cálido y sin culpa**.
Entrás, soltás el teléfono, volvés y dejás un rastro tuyo. Nada más.

---

## 2. La idea en una imagen: el ritual en 3 estados

```
ESTADO 1 — La carta espera        ESTADO 2 — La carta abierta        ESTADO 3 — Cerrar el ritual
┌─────────────┐                   ┌─────────────┐                    ┌─────────────┐
│  (frente)   │   tocás / girás   │   (dorso)   │   tocás "Terminé"  │   (dorso)   │
│  color +    │  ───────────────► │  frase +    │  ────────────────► │  reflexión  │
│  dibujo     │                   │  micro-     │   (volviste de     │  + fotos    │
│  categoría  │                   │  prompt     │    hacerlo afuera) │  + estrellas│
└─────────────┘                   └─────────────┘                    │  + Guardar  │
   llega a tu hora (M2)              "andá y hacelo                   └─────────────┘
   y espera, sin ruido               afuera" → soltás
```

**Una sola superficie.** Todo pasa en la misma carta: gira, y la zona de cierre aparece
**scrolleando hacia abajo en el dorso** — no una ventana nueva. Que se sienta *un solo
objeto*, "mi ritual de hoy", no una secuencia de pantallas de app.

**El botón "Terminé" marca el corte.** El dorso muestra primero sólo la frase + el
micro-prompt (para que te vayas a hacerlo sin que la app te apure a reflexionar). Cuando
volvés, tocás **"Terminé"** y recién ahí se despliega la zona de cierre. El orden natural
queda protegido: *hacé afuera → volvé → cerrá.*

---

## 3. El flujo del ritual

```
1. Llega la carta      → a tu hora (M2). Ves el FRENTE. La app no insiste.
2. Tocás → gira        → ves el DORSO: frase + micro-prompt. Primera interacción.
3. Hacés el ejercicio  → AFUERA. El teléfono no participa. (Podés volver cuando quieras dentro de las 24h.)
4. Volvés y tocás      → "Terminé" despliega la zona de cierre ↓
      "Terminé"
5. Cerrás el ritual:
      • Reflexión   → recuadro ≤250 caracteres. PROTAGONISTA (el cursor te espera),
                      pero NO bloquea Guardar (invitar, nunca exigir).
      • Fotos       → hasta 3, opcional. Tomar o subir.
      • Estrellas   → 1-5, opcional. "¿cuánto te llegó?" (alimenta M2).
6. Guardar            → va al Baúl. (Al lado, discreto: Compartir → M5.)
```

> **Lo que ves al volver depende de si ya cerraste.** Si ya guardaste hoy, la carta se ve
> en modo "hecho" (tu reflexión y fotos a la vista, en calma). No hay nada más que hacer
> hasta mañana.

---

## 4. La reflexión: protagonista, pero nunca un peaje

- **Recuadro de hasta 250 caracteres.** Corto a propósito: una interacción *sutil* con la
  app, no un editor de texto. No hay mínimo — una línea, una palabra, lo que salga.
- **Es el paso protagonista del cierre:** visualmente es lo primero y lo más prominente, el
  cursor te espera. La app *invita con todo el peso* a dejar una línea.
- **Pero Guardar nunca se bloquea por ella.** Podés guardar sin escribir nada. Esa es la
  única opcionalidad canónica del Motor de Contenido ("guardar sin hacer nada"), y la
  respetamos. *Invitar, nunca exigir.*
- Es **tuya y privada** (*intimidad como producto*). Vive en el Baúl; nadie más la ve salvo
  que vos compartas esa carta.

> **Por qué "soft" y no obligatoria:** si forzáramos a escribir para poder guardar, la app
> dejaría de invitar y empezaría a exigir — justo lo que el norte rechaza. La fricción que
> crea ritual la pone el *diseño* (el cursor esperándote), no un candado.

---

## 5. Las fotos: hasta 3, opcional

- **Hasta 3 fotos**, tomar en el momento o subir de la galería. Opcional.
- Por qué 3 y no 1: una caminata o un "hacer" puede dejar 2-3 rastros, y el
  almacenamiento cuesta centavos. **No cobramos por cantidad de fotos** — sería mezquino y
  va contra *intimidad como producto*. Las palancas premium son otras (2×/día, Baúl más
  rico). El límite puede subir en premium, no es el muro.
- Van a **Cloud Storage**, en carpeta por usuario (aislamiento de datos, §7 del Documento
  Madre). En el Baúl se ven junto a la carta y la reflexión.

---

## 6. Las estrellas: opcional y transparente (handoff a M2)

- Al cerrar aparece **"¿cuánto te llegó?" de 1 a 5 ⭐**. Opcional y salteable — la app nunca
  insiste.
- Le contamos al usuario para qué sirve: *"puntuá si querés; con eso la app va aprendiendo
  qué te llega más"*. Ya lo vio en el slideshow (M1) y lo practicó en la carta de prueba.
- M3 **escribe la estrella** sobre la entrega del día; **M2 la lee** para afinar la
  afinidad de acción. Es el mismo dato que M2 ya está esperando. (Lógica completa en
  [M2 §5](../M2_Entrega_del_Dia/Madre_del_Motor.md).)

---

## 7. Guardar y Compartir

- **Guardar** es el botón protagonista. Al tocarlo: la entrega queda `completada=true`, se
  escriben reflexión + fotos + estrella, y la carta pasa a modo "hecho". Va al **Baúl** (M4).
- **Compartir** es un CTA **discreto al lado** de Guardar (no debajo, no protagonista).
  Genera un link de esa carta. Es **secundario y latente** — se ofrece, nunca se empuja.
  La lógica del link es **M5**; M3 sólo expone el botón.

---

## 8. Qué pasa si NO completás (sin gate, sin culpa)

**La próxima carta llega siempre, completes o no.** No hay peaje. (Decisión Tomás, WS05.)

- **Por qué no gateamos:** un candado generaría culpa y ansiedad de racha — *ansiedad de
  consumo*, lo contrario del norte. Y en la vida real un día te tapás o te enfermás; la app
  que sigue ahí mañana genera confianza, la que te castiga genera abandono. Además, M2
  entrega por **tiempo** (a tu hora), sin depender de que M3 se complete.
- **La carta vieja vence a las 24h** (canon: "vigencia 24h o hasta completarla"). Cuando
  llega la nueva, la de ayer ya está cerrada.
- **Al vencer, qué pasa con lo que dejaste a medias:**
  - Si **escribiste reflexión y/o subiste fotos** pero no apretaste Guardar → se
    **autoguarda** en el Baúl con `completada=false`. No perdemos tus palabras
    (*intimidad como producto*); queda como un rastro "a medias", sin reproche.
  - Si **no tocaste nada** (ni giraste, ni escribiste) → se cierra **en silencio, sin
    dejar rastro**. Sin notificación de culpa, sin racha rota.

> `completada=true` significa **"cerré el ritual a conciencia"** (apreté Guardar).
> `completada=false` es **"quedó a medias"** (autoguardado al vencer, con algo de contenido).

---

## 9. Qué lee y qué escribe M3 (handoff al stack §5)

**Lee** (privado, todo con `user_id`):
- `entregas` → la carta del día (su `carta_id`, vigencia, estado), creada por M2.
- `cartas` (global, M0) → para renderizar frente/dorso (color, dibujo, frase, prompt). La
  carta **no se copia**: se joinea al render.

**Escribe** (sobre la entrega del día):
- `estrellas` (1-5, NULL si no puntuó) ◄ lo espera M2
- `completada` (bool) ◄ lo espera M2
- `reflexion` (texto ≤250, NULL si no escribió) ◄ **columna nueva, la agrega M3**
- una o varias filas en `fotos` (0-3) ◄ **tabla nueva, la agrega M3**

```
entregas  (privada · M2 la crea · M3 le escribe el cierre)
  id · user_id
  carta_id        → FK a cartas (global, M0)
  categoria · accion · fecha_entrega · vigente_hasta
  estrellas (1-5, NULL)        ◄ M3
  completada (bool)            ◄ M3   (true = guardó · false = autoguardado a medias)
  reflexion (varchar 250, NULL) ◄ M3  ← columna NUEVA respecto de M2

fotos     (privada · 0-3 por entrega · la agrega M3)
  id · user_id
  entrega_id      → FK a entregas
  url             → ruta en Cloud Storage (carpeta por usuario)
  orden (1-3)
```

> M3 **escribe** el cierre del ritual; **M4 (Baúl) lo lee y lo muestra**. La división es
> clara: M3 captura, M4 exhibe y ordena.

---

## 10. Handoffs con los otros motores

- **← M0:** la carta a renderizar (frente/dorso) se joinea de `cartas`.
- **← M2:** la entrega del día (`entregas`) ya creada, con su vigencia de 24h.
- **→ M2:** M3 devuelve **estrella** + **completada**, que afinan la entrega futura.
- **→ M4 (Baúl):** reflexión + fotos + estrella + carta = el rastro que el Baúl muestra y
  ordena (por fecha o por estrella).
- **→ M5 (Compartir):** M3 expone el botón "Compartir"; la generación del link es de M5.
- **↔ M1:** la mecánica del ritual (girar, reflexión, foto, guardar) es lo que enseña la
  **carta de prueba** del onboarding. La carta de prueba **no guarda** en el Baúl.

---

## 11. Decisiones canónicas / pivots (WS05)

- **Sin gate:** la próxima carta llega siempre, completes o no. La entrega es por tiempo
  (M2), no por mérito. *(invitar, nunca exigir · menos consumo, más presencia)*
- **Reflexión soft:** protagonista del cierre y de hasta 250 caracteres, pero **no bloquea
  Guardar** y no tiene mínimo. La fricción de ritual la pone el diseño, no un candado.
- **Hasta 3 fotos**, opcional, sin cobrar por cantidad en v1.
- **Estrellas 1-5 opcional**, transparente; M3 las escribe, M2 las usa (mismo dato ya
  esperado).
- **Una sola superficie:** el cierre aparece scrolleando en el dorso, no en ventana nueva.
  El botón **"Terminé"** separa "hacelo afuera" de "cerrá el ritual".
- **Autoguardado al vencer** si hay contenido (`completada=false`); silencio total si no se
  tocó nada. Nunca se pierden las palabras del usuario; nunca hay reproche.
- **Guardar protagonista · Compartir discreto al lado** (Compartir = M5, secundario).
- **Datos:** M3 agrega `reflexion` a `entregas` y la tabla `fotos`. Fotos en Cloud Storage,
  carpeta por usuario.

---

## 12. Diferido a v2 / más adelante

- **Subir el límite de fotos** o el largo de la reflexión como palanca premium.
- **Reescritura de tono / tarjeta visual** de la reflexión (IA creativa, componentes v2).
- Señales **implícitas** del ritual (que lo completó, que subió foto) como afinidad para M2,
  además de la estrella explícita (ya anotado como diferido en M2 §10).
- **Editar/borrar** una entrada ya guardada (probablemente vive en M4, a definir ahí).
