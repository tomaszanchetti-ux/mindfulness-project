# M5 — Motor de Compartir · Madre del Motor

> **El único canal de crecimiento — y el más delicado.** El usuario puede regalar por link una
> carta (sola) o un ejercicio completo (con su reflexión y fotos). Quien recibe **abre el link
> sin instalar nada, sin login, en la web abierta** y vive el momento al instante; recién
> después se le ofrece, suave, tener el suyo. Es **secundario y latente**: se ofrece, **nunca se
> empuja**. Se rige por el [`Documento Madre`](../00_Documento_Madre.md).
>
> M5 es **lógica + pantalla** (todavía no se codea). El link público se sirve desde la web
> (Expo for Web / dominio propio) en N4.

---

## 1. Qué hace M5 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Generar un **link público** de una carta sola o de un ejercicio completo | Empujar a compartir (es secundario y latente) |
| Mostrar a quien recibe un **momento completo** sin instalar ni loguearse | Pedirle al receptor que se registre para ver |
| Dejar que el que comparte sume una **nota personal** | Crear círculos / chat / respuestas (eso es v2) |
| Avisar con claridad qué se vuelve **público** al compartir el ejercicio | Exponer IDs, `user_id` o datos de otras entradas |
| Ofrecer **un solo CTA suave** al receptor: "¿querés una así cada día?" | Ser el destino de la app (el destino es el ritual afuera) |

**El norte de M5:** el link es un **regalo completo en sí mismo**, no un embudo a la app. El
que recibe gana el momento gratis; instalar es sólo para quien quiere el suyo a diario.

---

## 2. El desafío real (y cómo lo resolvemos)

> *"Hay muchos pasos hasta que el que recibe llegue a la carta."*

Esos pasos **sólo existen si obligamos a instalar para recibir.** No lo hacemos.
**Recibir = abrir la URL = listo.** Instalar es para quien quiere **crear/recibir a diario.**
Invertimos el marco:

```
   ❌ Embudo (lo que NO hacemos)        ✅ Regalo (lo que hacemos)
   link → "descargá la app" →           link → la carta, AL INSTANTE →
   instalá → registrate → ...           viviste el momento →
   → recién ves la carta                → (abajo, suave) "¿querés una así?"
```

El **motor de engagement es la calidad de la carta** (M0): el cuidado del dibujo, la frase, el
gesto de girar. Compartir sólo lo **expone**. Por eso el receptor no necesita más que abrir.

**Tres palancas de engagement en quien recibe** (v1, simples):
1. **Una nota personal del que comparte**, arriba de todo (*"me acordé de vos con esta"*). Es lo
   que hace que la abran: es de **una persona**, no de una marca.
2. **La carta es interactiva y bella** — mismo gesto de girar que en la app, mismo cuidado. Un
   momento de calma de 10 segundos, no un aviso.
3. **Un solo CTA suave abajo**, emocional, nunca un muro: *"Una carta así, cada día, para vos"*
   → abre el onboarding (M1). Sin modal, sin pared de "descargá la app".

---

## 3. Los dos modos de compartir

Al tocar **Compartir** (desde M3 al cerrar, o desde M4 sobre una entrada guardada), se elige:

### A) La carta sola
- Comparte sólo la **carta**: frase + micro-prompt + dibujo de la categoría. **Sin datos tuyos.**
- Es una **invitación hermosa al contenido**. Es contenido **global de M0** — no expone nada
  privado.
- Por eso puede vivir como invitación genérica y **no se ve afectada si después borrás tu
  entrada** (no hay datos tuyos adentro).

### B) El ejercicio completo
- Comparte la **carta + tu reflexión + tus fotos**. Íntimo: el que recibe ve **lo que vos
  viviste** ese día.
- Como expone datos privados, exige **aviso de privacidad explícito** (§4) y **muere si borrás
  la entrada** (§5).

```
        ┌─ Compartir ─────────────────────┐
        │  ¿Qué querés regalar?            │
        │   ○ La carta sola               │ → invitación, sin datos tuyos
        │   ○ El ejercicio completo       │ → con tu reflexión + fotos (privado→público)
        │   [ nota personal opcional... ] │
        └─────────────────────────────────┘
```

---

## 4. Privacidad — compartir el ejercicio vuelve lo íntimo público (por link)

Compartir el **ejercicio completo** convierte tu reflexión y tus fotos en algo **visible para
cualquiera que tenga el link**. Hay que decirlo clarísimo **antes** de generarlo, coherente con
*intimidad como producto* y con *compartir es decisión explícita*:

> **Vas a compartir tu reflexión y tus fotos.**
> Cualquiera con este link va a poder verlas. Compartilo sólo con quien quieras.
> [ Cancelar ]   [ Crear link ]

- El que comparte **decide y entiende** lo que expone. Nunca compartimos por default.
- La **carta sola** no necesita este aviso (no hay datos privados).
- El link es **"unlisted", no indexable** (sin buscadores), pero **público para quien lo tenga**:
  lo dejamos explícito para que el usuario no asuma que es secreto.

---

## 5. El link: cómo es por dentro, y su ciclo de vida

**Anatomía del link:**
- URL pública tipo `https://<dominio>/c/{token}`.
- **`token` = aleatorio y opaco** (string largo no adivinable). **Jamás** el `entrega_id`, el
  `user_id` ni nada secuencial — no se exponen IDs internos.
- Se sirve **server-side desde la web** (Expo for Web / dominio propio), **mobile-first, sin
  login, sin cookies**. Quien recibe ve la carta en < 2 segundos en cualquier navegador.
- Para el **ejercicio completo**, las fotos se sirven por una **URL pública/firmada de Cloud
  Storage** atada a ese token (no se expone la carpeta privada del usuario).

**Ciclo de vida (decisión Tomás, WS06):**
- **El link muere con la entrada.** Si borrás en M4 el ejercicio que compartiste, **el link se
  apaga** y muestra *"esta carta ya no está disponible"*. Tus datos íntimos **no sobreviven** a
  que los borres → coherente con el "para siempre" de M4.
- La **carta sola** (sin datos tuyos) puede seguir viva como invitación aunque borres la
  entrada, porque no contiene nada privado.
- v1: el link **no expira por tiempo** y **no se puede revocar a mano** (más allá de borrar la
  entrada). Expiración/revocación explícita = mejora anotada para v2.

**Tabla nueva `compartidos`** (privada · `user_id` · la agrega M5):

```
compartidos  (privada · la agrega M5)
  id · user_id
  token            → string aleatorio opaco (lo que va en la URL /c/{token})
  entrega_id       → FK a entregas (NULL si es "carta sola" desde una carta no guardada)
  carta_id         → FK a cartas (global, M0) — para la "carta sola"
  modo             → 'carta_sola' | 'ejercicio_completo'
  nota             → texto opcional del que comparte (la nota personal)
  activo           → bool (false = link apagado; M4 lo apaga al borrar la entrada)
  creado           → timestamp
```

> Para resolver un link, el backend toma el `token` → si `activo=true`, joinea `cartas`
> (+ `entregas`/`fotos` si es ejercicio completo) y arma la página pública. Si `activo=false`
> o no existe → "ya no está disponible".

---

## 6. Qué lee y qué escribe M5 (handoff al stack §5)

**Lee:**
- `entregas` + `fotos` (privadas) → para armar el ejercicio completo a compartir.
- `cartas` (global, M0) → la carta a renderizar (carta sola y completo).

**Escribe:**
- una fila en **`compartidos`** (tabla nueva) al generar un link.
- (vía M4) el `activo=false` cuando se borra la entrada asociada.

**Página pública (lo que ve el receptor):** se arma server-side resolviendo el `token`; **no
toca datos del receptor** (no hay receptor logueado). Sólo muestra lo que el `compartidos` +
sus joins permiten, y un CTA a M1.

---

## 7. Handoffs con los otros motores

- **← M3:** expone el botón **Compartir** al cerrar el ritual (carta recién vivida).
- **← M4:** expone **Compartir** sobre cualquier entrada guardada del Baúl; y **M4 apaga el
  link** (`activo=false`) al borrar la entrada.
- **← M0:** la carta a renderizar (sola o dentro del ejercicio) se joinea de `cartas`.
- **→ M1:** el CTA suave de la página pública lleva al **onboarding** (único canal de
  crecimiento). El que recibe entra por la misma puerta que cualquiera.
- **↔ M1 (slideshow):** "compartir" es una de las pantallas explicadas en el onboarding, donde
  también se canoniza que es **100% tuyo y opcional**.

---

## 8. Decisiones canónicas / pivots (WS06)

- **El link es un regalo completo, no un embudo.** Recibir no requiere instalar, loguear ni
  registrarse: se abre en la web, al instante. Instalar es para quien quiere el suyo a diario.
- **Dos modos:** **carta sola** (sin datos tuyos, invitación) y **ejercicio completo** (con
  reflexión + fotos, íntimo).
- **Aviso de privacidad explícito** antes de compartir el ejercicio completo (lo íntimo se
  vuelve público-por-link). La carta sola no lo necesita.
- **Engagement del receptor:** nota personal del que comparte + carta interactiva y bella + un
  solo CTA suave. La calidad de la carta (M0) es el verdadero motor.
- **El link muere con la entrada** (borrar en M4 lo apaga). La carta sola sobrevive (no tiene
  datos privados).
- **Token opaco y aleatorio** en la URL; jamás IDs internos. Link unlisted, no indexable, pero
  público para quien lo tenga (se dice claro).
- **Tabla nueva `compartidos`** (privada, `user_id`), con `activo` para apagar el link.
- **Secundario y latente:** se ofrece, nunca se empuja. No es lo que validamos.

---

## 9. Diferido a v2 / más adelante

- **Revocar / expirar** un link a mano (sin tener que borrar la entrada) y links con vencimiento.
- **Círculos privados:** compartir recurrente con un grupo + reacciones emocionales (no likes).
- **Responder** al que te compartió (mini-gesto de vuelta) — embrión de círculos.
- **Tarjeta visual** de la carta/ejercicio (IA creativa) optimizada para redes/WhatsApp.
- **Métricas suaves para el que comparte** ("se abrió tu carta") — con cuidado de no caer en
  vanidad.
