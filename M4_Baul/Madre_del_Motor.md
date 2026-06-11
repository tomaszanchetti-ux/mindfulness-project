# M4 — Motor del Baúl de Crecimiento Personal · Madre del Motor

> **El lugar para mirar atrás.** Acá vive todo lo que el usuario fue dejando: cada carta
> que cerró, con su reflexión, sus fotos y sus estrellas. M4 **no captura nada** (eso es M3);
> M4 **lee, ordena, muestra** — y deja borrar. Es la **retención** de la app: el rastro
> visible de la propia presencia. Se rige por el [`Documento Madre`](../00_Documento_Madre.md).
>
> M4 es **lógica + pantalla** (todavía no se codea). El front (React Native + Expo) y las
> consultas a Postgres/Cloud Storage se construyen en N4.

---

## 1. Qué hace M4 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Mostrar el historial de entregas cerradas (carta + reflexión + fotos + ⭐) | Capturar la reflexión / fotos / estrella (eso es M3) |
| Ordenar el historial en **dos modos** (Reciente · Más valoradas) | Elegir la carta del día (eso es M2) |
| Abrir una entrada al detalle (la carta tal cual la viviste) | Editar el contenido de una entrada (v2) |
| **Borrar** una entrada para siempre (con modal claro) | Empujar a compartir (Compartir es M5, secundario) |
| Ofrecer el botón **Compartir** sobre una entrada guardada | Mostrar nada de otros usuarios (no es red social) |

**El norte de M4:** que mirar atrás se sienta **cálido y propio**, nunca una métrica. No hay
rachas, ni contadores de vanidad, ni "te perdiste 3 días". Es tu cuaderno, no tu scoreboard.

---

## 2. La idea en una imagen

```
   BAÚL (lista)                         ENTRADA (detalle)
┌───────────────────────┐            ┌───────────────────────┐
│  [ Reciente ▼ ]       │  tocás     │      (la carta)        │
│ ┌───────────────────┐ │  ───────►  │   frase + micro-prompt │
│ │ 🎴 Gratitud  ⭐⭐⭐⭐│ │            │   ─────────────────    │
│ │ "mirá el amanecer"│ │            │   tu reflexión         │
│ │ hoy               │ │            │   📷 📷 (tus fotos)    │
│ ├───────────────────┤ │            │   ⭐⭐⭐⭐               │
│ │ 🎴 Calma     ⭐⭐⭐  │ │            │                        │
│ │ "respirá la luna" │ │            │   [ Compartir ]  (M5)  │
│ │ ayer              │ │            │   [ 🗑 Borrar ]  (rojo)│
│ └───────────────────┘ │            └───────────────────────┘
└───────────────────────┘
```

Cada **fila** es una entrega cerrada: el dibujo + nombre de la categoría, un pedazo de la
frase, las estrellas (si puntuó) y la fecha en lenguaje humano ("hoy", "ayer", "hace 3 días").
Al tocar, se abre la entrada **tal cual la viviste**: la carta, tu reflexión, tus fotos.

---

## 3. Los dos modos de orden

El Baúl se ordena de **dos maneras que el usuario alterna** con un toggle. No es un orden
compuesto: como hay **una carta por día**, "fecha y después estrellas" casi nunca tendría
varias entradas el mismo día para reordenar. Por eso son dos vistas:

- **Reciente** (default) — lo último arriba. El diario natural: bajás en el tiempo.
- **Más valoradas** — las de más estrellas arriba (4-5 ⭐ primero). "Tus mejores momentos."
  Las que no puntuaste van al final (estrella NULL = sin valorar, no = cero).

> El orden compuesto real (fecha → estrella dentro del día) recién tendría sentido con **dos
> rituales por día** (palanca premium v2). En v1 no hace falta.

**Qué se muestra en cada fila:** dibujo + categoría · fragmento de la frase · estrellas (o
nada si no puntuó) · fecha humana. Las entradas **a medias** (`completada=false`, autoguardadas
al vencer) también aparecen, marcadas con suavidad ("quedó a medias"), sin reproche.

---

## 4. Borrar una entrada — para siempre, con un modal claro

**Sí se puede borrar.** Es tu diario íntimo: no poder borrar tu propia entrada violaría
*intimidad como producto* (es 100% tuyo, incluido el derecho a que desaparezca). Pero se borra
**con plena conciencia y para siempre** — no hay papelera.

**El flujo (decisión Tomás, WS06):**

1. En el detalle de la entrada, **botón discreto** 🗑 (no compite con Compartir/Guardar).
2. Al tocarlo → **modal claro, botón rojo de confirmación:**

   > **¿Borrar esta entrada?**
   > Vas a perder para siempre **la carta, tu reflexión y tus fotos** de este día.
   > Esto **no se puede deshacer**.
   > [ Cancelar ]   [ **Borrar para siempre** ] ← rojo

3. Al confirmar → **borrado real**:
   - se borra la fila de `entregas`,
   - se borran las filas de `fotos` **y los archivos de Cloud Storage** (no sólo la fila — si
     no, las fotos quedan colgadas ocupando lugar y siendo un riesgo de privacidad),
   - **si esa entrada tenía un link compartido del ejercicio completo, el link se apaga**
     (ver §6 y [M5 §5](../M5_Compartir/Madre_del_Motor.md)). Tus datos íntimos no sobreviven a
     que los borres.

> **Por qué borrado real y no papelera:** una papelera contradice el "desaparece para siempre
> y ya". El **modal es la red de seguridad** — claro, explícito, con botón rojo. Reglas de UI
> canónicas: **acciones destructivas en rojo, modales que explican exactamente qué se pierde.**

**Editar** una entrada (cambiar la reflexión, sumar/sacar fotos) **queda para v2.** En v1 una
entrada cerrada es un recuerdo fijo; lo único que podés hacer es borrarla.

---

## 5. Seguridad y aislamiento — el Baúl es donde más importa

El Baúl es lo más íntimo de la app, así que repetimos acá la **regla de oro** del Documento
Madre §5, sin atajos:

> **No es una base de datos por usuario.** Es **una sola base con aislamiento por fila**: cada
> entrega y cada foto llevan su `user_id`, y **toda consulta del Baúl filtra por el usuario
> logueado, del lado del backend (Cloud Run) — nunca se confía en el cliente.**

Tres capas de seguridad:
1. **Firebase Auth** = la identidad. El backend sabe quién sos por el token, no porque el
   cliente lo diga.
2. **`WHERE user_id = <logueado>` en cada query**, aplicado en el servidor. Es imposible pedir
   el Baúl de otro: el filtro no es opcional ni viene del front.
3. **Cloud Storage con carpeta por usuario** para las fotos; la URL pública sólo existe para lo
   que el usuario eligió compartir (M5), y es un token opaco, no una ruta adivinable.

Esto es exactamente el modelo de aislamiento de **Arc One** (por `user_id`/workspace a nivel
fila), elegido porque **escala a +100.000 usuarios** y permite compartir el contenido global de
M0. Una-DB-por-usuario no escala y rompe ese contenido compartido.

---

## 6. Qué lee M4 (y qué no escribe)

M4 es casi **sólo lectura**. Su única escritura es el **borrado**.

**Lee** (privado, todo con `user_id`):
- `entregas` → todas las del usuario, ya cerradas (`completada=true`) o a medias
  (`completada=false`), con su `reflexion` y sus `estrellas`.
- `fotos` → las 0-3 de cada entrega (sus URLs en Cloud Storage).
- `cartas` (global, M0) → para renderizar cada entrada (color, dibujo, frase, prompt). La carta
  **no está copiada** en la entrega: se joinea al render, igual que en M3.

**Escribe** (lo único):
- **Borrado**: elimina la fila de `entregas`, sus filas de `fotos`, los archivos de Cloud
  Storage, y apaga el link compartido si existía (handoff a M5).

```
M4 lee:   entregas (privada) ⨝ fotos (privada) ⨝ cartas (global, M0)
M4 borra: entregas + fotos (DB) + archivos (Cloud Storage) + link compartido (M5)
```

> M3 **captura** el cierre del ritual; M4 **lo exhibe, lo ordena y lo borra**. División limpia.

---

## 7. Handoffs con los otros motores

- **← M3:** todo lo que muestra el Baúl lo escribió M3 al cerrar el ritual (reflexión, fotos,
  estrella, `completada`). M4 no captura nada nuevo.
- **← M2:** las filas de `entregas` nacen en M2 (la entrega del día). El Baúl es el acumulado
  histórico de esas filas.
- **← M0:** la carta de cada entrada se joinea de `cartas` (global) para renderizarla.
- **→ M5 (Compartir):** desde el detalle de una entrada, M4 ofrece el botón **Compartir**; la
  generación y el ciclo de vida del link son de **M5**. Y el **borrado en M4 apaga el link** de
  M5 si esa entrada estaba compartida como ejercicio completo.
- **↔ M1:** el Baúl es una de las pantallas explicadas en el slideshow del onboarding.

---

## 8. Decisiones canónicas / pivots (WS06)

- **Borrado real, para siempre** (no papelera). Modal claro + **botón rojo** + texto que dice
  exactamente qué se pierde. El modal es la red de seguridad. *(intimidad como producto)*
- **El borrado limpia todo:** fila `entregas` + filas `fotos` + archivos en Cloud Storage +
  link compartido del ejercicio (si existía). Nada queda colgado.
- **Dos modos de orden** (toggle): **Reciente** (default) y **Más valoradas**. No es un orden
  compuesto; el compuesto queda para v2 (dos rituales/día). Sin valorar = NULL → al final.
- **M4 es casi sólo lectura:** lee `entregas` ⨝ `fotos` ⨝ `cartas`; su única escritura es el
  borrado.
- **Aislamiento por fila reafirmado:** una sola base, `user_id` en cada fila, filtro en el
  backend, nunca en el cliente. **No** una base por usuario.
- **Sin métricas de vanidad:** no hay rachas ni contadores. Las entradas a medias se muestran
  sin reproche.

---

## 9. Diferido a v2 / más adelante

- **Editar** una entrada guardada (reflexión, fotos). En v1 una entrada cerrada es fija.
- **Buscar / filtrar** por pilar o por texto de la reflexión (cuando el Baúl crezca).
- **Orden compuesto** fecha → estrella, sólo si entran **dos rituales por día**.
- **Resumen / vista de crecimiento** (IA): "tu mes en una tarjeta", patrones de lo que más te
  llegó. Es componente v2 (IA creativa).
- **Exportar** el Baúl (PDF / respaldo) como palanca premium o derecho de portabilidad.
