# M2 — Motor de Entrega del Día · Madre del Motor

> **El corazón diario de la app.** Cada día, a tu hora, elige **una** carta y te la
> entrega. Toma de M1 tus categorías, horario y aviso; toma de M0 las cartas; aprende
> de lo que puntuás en M3; y le pasa la entrega a M3 (ritual) y M4 (Baúl). Se rige por
> el [`Documento Madre`](../00_Documento_Madre.md).
>
> La **lógica** vive acá. El **script** que la ejecuta vive aparte en
> [`entrega.py`](entrega.py) (hoy corre contra los JSON de M0; al construir se enchufa a Postgres).

> ## ⚠️ DEROGACIÓN WS17 (11/06/2026) — ROTACIÓN COMPLETA 6+1
>
> Lo de abajo describe la lógica v1 (WS04/WS10: categorías elegidas como filtro
> duro). **Desde WS17 las categorías YA NO se eligen ni filtran**: son la tesis de
> Dwellia (los 6 campos del crecimiento) y van **todas, todas las semanas**.
>
> - **Rotación 6+1:** cada día se sirve una categoría que no apareció en los
>   últimos 6 días (orden al azar → la semana sorprende); si las 6 ya pasaron,
>   día **comodín** (cualquiera salvo la de ayer; v2: ponderado por ⭐). La
>   rotación se auto-corrige sola tras el comodín.
> - **Doble ventana de no-repetición (7 días): por carta Y por `concepto`** —
>   campo nuevo en `cartas` (huella de dedup, [`canon_cartas.md`](../M0_Motor_de_Contenido/canon_cartas.md)
>   R5); las cartas "gemelas" comparten etiqueta y jamás caen en la misma semana.
> - El usuario elige solo la **forma** (modalidades, piso "escribir" — WS10 sigue
>   vigente). La capa blanda de ⭐ por acción sigue intacta; el castigo por
>   categoría de ayer desaparece (la rotación lo garantiza mejor).
> - Pool mínimo garantizado: 18 cartas (6 campos × 3 de "escribir") ≥ 7 días ✅.
>
> **Implementación canónica:** `apps/api/mindful_api/services/seleccion.py`
> (tests en `apps/api/tests/test_seleccion.py`). El `entrega.py` de esta carpeta
> queda como sandbox histórico de la v1.

---

## 1. Qué hace M2 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Elegir **una** carta por día, de tus categorías | Inventar cartas (eso es M0) |
| No repetir lo de la última semana | Garantizar no-repetición de 60 días (no hace falta) |
| Aprender qué **acción** te gusta más y inclinarse | Cambiar tus categorías o actividades (eso lo elegís vos en M1) |
| Avisarte (email/push) a tu horario local | Mostrar el ritual (eso es M3) |
| Dejar la carta vigente 24h o hasta completarla | Encerrarte en una sola modalidad (siempre deja variedad) |

**El norte de M2:** que cada día te llegue **algo distinto, de lo tuyo, que cada vez
te conozca un poco más** — sin volverse predecible ni un eco de vos mismo.

---

## 2. La idea en una imagen

Pensalo como un **sommelier de cartas**. Trabaja en **dos capas**:

1. **Lo que vos elegís (filtro duro): categoría Y actividad.** El pool del día son sólo
   las cartas que cruzan tus **categorías** (2-6) **y** tus **actividades** elegidas. Es
   sagrado: nunca te llega algo de fuera de tu menú. **"Escribir" está siempre en el pool**
   (piso garantizado), elijas lo que elijas.
2. **Lo que la app aprende (preferencia blanda): la afinidad de actividad.** *Dentro* de tu
   menú, va notando cuál de tus actividades te llega más (por las ⭐) y **inclina** la
   balanza hacia eso. No manda del todo: **empuja** las probabilidades. El azar siempre
   tiene la última palabra, para que el ritual no se vuelva predecible.

> Categoría y actividad las decidís **vos** (M1, *cambio WS10*). Dentro de tu menú, la app
> **descubre** con el tiempo cuál preferís. Antes la actividad no se elegía; ahora se
> elige para que nadie pierda el día por una modalidad que no hará.

---

## 3. El flujo de cada día

```
1. ¿Es tu PRIMERA carta?  → SÍ: 100% al azar dentro de tu menú.   ◄ el script lo sabe: tu historial está vacío
                            NO: seguí ↓
2. Armo el pool           → cartas que cruzan tus categorías Y tus actividades elegidas (+ "escribir" siempre)
3. Saco las repetidas     → las que ya viste en los últimos 7 días
4. Le doy un peso a cada candidata:
      • + afinidad de acción   (las modalidades que venís puntuando alto pesan más)
      • − repetir lo de ayer   (castigo chico si la acción o la categoría son las de ayer)
      • piso para todas        (ninguna modalidad llega a peso 0)
5. Sorteo ponderado       → entre las candidatas, a más peso más chance. El azar decide.
6. Entrego                → vigencia 24h; aviso (email/push) a tu horario, según M1
```

**Sin casos especiales.** La primera carta no es una rama aparte: simplemente, con el
historial vacío, los pasos 3 y 4 no tienen nada con qué trabajar y queda un sorteo
limpio. Todo sale del mismo motor.

---

## 4. La no-repetición: una semana alcanza

Regla única: **no repetir ninguna carta entregada en los últimos 7 días.** Con tener
una semana de contenido distinto, ya se siente fresco. (Antes pensábamos en ~60 días
con una ventana adaptativa: era complejidad que no aporta — *Simpleza*.)

> **Borde cubierto:** si alguien tuviera un pool minúsculo y los últimos 7 días lo
> vaciaran, el motor relaja la regla a *"que no sea la carta de ayer"* y sigue. Nunca
> se queda sin carta. **El filtro de actividad (WS10) achica el pool**, pero **"escribir"
> siempre presente** garantiza un piso de cartas, y la regla relajada cubre el resto.
> Aun el menú más chico (2 categorías + sólo "escribir") tiene cartas de sobra.

---

## 5. La puntuación (estrellas) y cómo aprende el motor

Al cerrar el ritual (M3), aparece un **"¿cuánto te llegó?" de 1 a 5 ⭐**. Es **opcional
y salteable** — la app nunca insiste (*invitar, nunca exigir*). Pero le contamos al
usuario, con todas las letras, **para qué sirve**: *"puntuá si querés; con eso la app
va aprendiendo qué te llega más"* (*intimidad como producto*: nada a escondidas).

**Cómo se convierte en preferencia:**

- La señal principal que extraemos es **la afinidad por acción** (no por categoría —
  esa ya la elegiste vos). Si puntuás alto las cartas de *caminar*, el motor entiende
  *"a esta persona le gusta caminar"* y empuja un poco más esa modalidad.
- Cada modalidad tiene un **dial de afinidad** que arranca **neutro** y se mueve con
  tus estrellas (promedio de lo que puntuaste en esa modalidad). Sin puntuaciones, todo
  queda neutro → el motor es humilde y sortea parejo.
- **Siempre hay un piso:** por más que adores una modalidad, las demás nunca llegan a
  probabilidad cero. Es lo que protege el balance que busca la app.

**Dos usos de la estrella:**
1. **Afinar la entrega** (esta sección, M2).
2. **Ordenar el Baúl:** por defecto el Baúl (M4) puede mostrar **las mejores puntuadas
   primero** (5⭐ arriba), además del orden cronológico. Handoff M2→M4.

---

## 6. La evolución: v1 humilde → v2 con criterio

El motor se gana el derecho a opinar con el rodaje. El gatillo no es una fecha mágica:
lo dispara **tu propio historial**.

| | **v1 — inclinación suave** | **v2 — concentra, pero no encierra** |
|---|---|---|
| **Cuándo** | desde el día 1 | cuando ya **recibiste y puntuaste las 5 modalidades varias veces** |
| **Qué hace** | la preferencia empuja apenas; mucha variedad y piso parejo | se apoya **fuerte** en tus favoritas… |
| **El guardarraíl** | — | …pero deja un **comodín** cada tanto (≈1 vez/semana entra una modalidad olvidada) |

**Por qué el comodín es innegociable, incluso en v2:**
1. **Anti eco-cámara** — encerrarte en tus 2 modalidades favoritas nos volvería un feed
   infinito de mindfulness. Es justo lo que la app combate (*menos consumo, más presencia*).
2. **La razón más linda:** en una app de presencia, **la modalidad que evitás suele ser
   la más valiosa.** Al que nunca quiere *escribir* es probablemente al que más le sirve
   escribir una vez por semana. Reducir del todo nos haría perder eso.

> Lema: **"el motor te conoce, pero no te subestima."** Concentra ~80% en lo tuyo,
> reserva ~20% para sorprenderte y hacerte crecer.

> **Ajuste WS10 (actividades elegibles):** el comodín opera **dentro del menú que el
> usuario eligió** — sorprende con una actividad *elegida pero descuidada*, nunca
> reintroduce una que el usuario sacó a propósito (*invitar, nunca exigir*). El menú es
> sagrado; la sorpresa vive adentro. Si alguien quiere volver a una modalidad que sacó, la
> re-agrega en Ajustes.

**v1 es lo que codeamos y lanzamos.** v2 queda especificada acá para cuando la app tenga
rodaje y datos reales; no la activamos hasta tener evidencia de uso.

---

## 7. Qué lee y qué escribe M2 (handoff al stack §5)

**Lee** (privado, todo con `user_id`):
- `usuario_categorias` → tus 2-6 categorías (de M1)
- `usuario_acciones` → tus actividades elegidas (de M1; "escribir" siempre cuenta) ◄ **WS10**
- `usuarios` → horario, zona horaria, aviso on/off (de M1)
- `entregas` → tu historial: qué cartas, qué días, con qué estrella (la última semana
  para no-repetir; todo el histórico para la afinidad)

**Escribe:**
- una fila nueva en `entregas` cada día (carta elegida, fecha, vigencia)
- la **estrella** se escribe sobre esa misma fila cuando M3 captura la puntuación

```
entregas  (privada, una fila por carta entregada)
  id · user_id
  carta_id        → FK a la tabla GLOBAL cartas (M0)
  categoria · accion   (copia para consultar rápido sin join; = las de la carta)
  fecha_entrega · vigente_hasta
  estrellas (1-5, NULL si no puntuó)   ◄ la escribe M3
  completada (bool)                    ◄ la escribe M3 (hizo el ritual)
```

> La carta en sí (frase, prompt, color, dibujo) **no se copia**: se joinea desde la
> tabla global `cartas` al renderizar. La entrega sólo guarda el puntero + lo tuyo.

---

## 8. Handoffs con los otros motores

- **← M0:** las cartas (categoría, acción, frase, prompt). El pool sale de acá.
- **← M1:** categorías, horario, zona horaria, aviso. Cambiar categorías en Ajustes
  **cambia el pool en el acto** (sacar una = sale; sumar una = entra ya).
- **→ M3:** M2 entrega la carta del día; M3 corre el ritual y **devuelve** estrella +
  si la completó, que M2 guarda en `entregas`.
- **→ M4 (Baúl):** las entregas completadas son el historial; el Baúl puede ordenarlas
  **por estrella** (mejores primero) además de por fecha.

---

## 9. Decisiones canónicas / pivots

- **No-repetición = 7 días** (no 60; no ventana adaptativa). *Simpleza.*
- **Dos capas (actualizado WS10):** filtro duro = categoría **Y** actividad (las dos las
  elige el user) · preferencia blanda = afinidad de actividad *dentro* del menú (la aprende
  la app de las ⭐). **"Escribir" = piso siempre en el pool.** El comodín de v2 sorprende
  sólo dentro del menú elegido.
- **Primera carta = random**, sin rama especial (el motor lo deduce del historial vacío).
- **Sorteo ponderado, no "elegir la mejor":** la preferencia inclina, el azar decide.
  Mantiene viva la sorpresa.
- **Puntuación = 1-5 ⭐, opcional y transparente.** Se explica en el slideshow (M1) y se
  practica en la carta de prueba. Alimenta sobre todo la **afinidad de acción**.
- **Piso para todas las modalidades** siempre: nunca probabilidad cero.
- **Evolución v1 suave → v2 fuerte con comodín**, disparada por el historial (haber
  probado+puntuado las 5 modalidades), no por fecha. v1 es lo que se lanza.
- **El Baúl se puede ordenar por estrella** (handoff M2→M4).

---

## 10. Diferido a v2 / más adelante

- Activar la **concentración fuerte + comodín** (§6) con datos reales de uso.
- Señales **implícitas** (completó el ritual, subió foto) como afinidad además de la
  estrella explícita.
- Preferencia por **categoría** dentro de las elegidas (hoy sólo afinamos acción).
- **Carta sorpresa semanal** de motivación (está en componentes v2 del Documento Madre).
