# M2 — Motor de Entrega del Día · Madre del Motor

> **El corazón diario de la app.** Cada día, a tu hora, elige **una** carta y te la
> entrega. Toma de M1 tus actividades, horario y aviso; toma de M0 las cartas (los 6
> pilares); aprende de lo que puntuás en M3; y le pasa la entrega a M3 (ritual) y M4
> (Baúl). Se rige por el [`Documento Madre`](../00_Documento_Madre.md) y el
> storytelling del [`canon de cartas §0`](../M0_Motor_de_Contenido/canon_cartas.md).
>
> La **lógica** vive acá. La **implementación canónica** vive en
> [`apps/api/mindful_api/services/seleccion.py`](../apps/api/mindful_api/services/seleccion.py)
> (tests en `apps/api/tests/test_seleccion.py`).

---

## 1. Qué hace M2 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Elegir **una** carta por día | Inventar cartas (eso es M0) |
| Recorrer **los 6 pilares, todas las semanas** (rotación 6+1) | Dejar que el usuario recorte pilares (son la tesis de Dwellia) |
| No repetir en la semana **ni carta ni concepto** | Garantizar no-repetición de meses (no hace falta) |
| Aprender qué **actividad** te gusta más y inclinarse | Cambiar tus actividades (eso lo elegís vos en M1) |
| Avisarte (email/push) a tu horario local | Mostrar el ritual (eso es M3) |
| Dejar la carta vigente 24h o hasta completarla | Encerrarte en una sola actividad (siempre deja variedad) |

**El norte de M2:** que tu semana sea **el recorrido completo del crecimiento** — los
6 pilares, uno por día, cada uno en la forma que elegiste — sin que jamás se sienta
repetido ni predecible.

---

## 2. La idea: la semana del usuario ES la rotación

El motor trabaja en **dos niveles**:

1. **El recorrido (nuestro): los 6 pilares, cada semana.** Cada día se sirve un pilar
   que no apareció en los últimos 6 días, **en orden mezclado** (la semana sorprende:
   el lunes no es siempre gratitud). Cuando los 6 ya pasaron, el 7º día es **comodín**:
   cualquier pilar salvo el de ayer. Después del comodín la rotación se auto-corrige
   sola. El usuario **no elige pilares** — el círculo completo es la promesa.
2. **La forma (del usuario): sus actividades, con afinidad aprendida.** Dentro del
   pilar del día, el pool son las cartas de las **actividades de desconexión** que
   eligió (M1) — y las de **escritura pura siempre están** (escribir ES la pausa, §0
   del canon). El motor además aprende de las ⭐ cuál actividad le llega más e
   **inclina** la balanza. No manda: **empuja**. El azar siempre tiene la última
   palabra.

> Pensalo como un **guía de viaje con un sommelier adentro**: el guía garantiza que
> cada semana visites los 6 territorios; el sommelier elige, dentro de cada territorio,
> la copa que más va con vos.

---

## 3. El flujo de cada día

```
1. ¿Es tu PRIMERA carta?  → SÍ: 100% al azar dentro de tu pool.   ◄ el motor lo sabe: historial vacío
                            NO: seguí ↓
2. Pilar del día          → uno que NO apareció en los últimos 6 días (al azar entre los pendientes);
                            si los 6 ya pasaron → COMODÍN (cualquiera salvo el de ayer)
3. Armo el pool del pilar → sus cartas de tus actividades elegidas (+ escritura pura, siempre)
4. Saco las repetidas     → ni carta NI concepto vistos en los últimos 7 días
5. Le doy un peso a cada candidata:
      • + afinidad de actividad  (las que venís puntuando alto pesan más)
      • − repetir lo de ayer     (castigo chico si la actividad es la de ayer)
      • piso para todas          (ninguna actividad llega a peso 0)
6. Sorteo ponderado       → a más peso, más chance. El azar decide.
7. Entrego                → vigencia 24h; aviso (email/push) a tu horario, según M1
```

**Sin casos especiales.** La primera carta no es una rama aparte: con el historial
vacío, los pasos 2-5 no tienen con qué trabajar y queda un sorteo limpio.

---

## 4. La no-repetición: doble ventana de 7 días

Dos reglas, misma ventana:

- **Por carta:** ninguna carta entregada en los últimos 7 días vuelve.
- **Por concepto:** ningún **`concepto`** vivido en los últimos 7 días vuelve. Las
  cartas "gemelas" (misma experiencia con otra ropa) comparten etiqueta de concepto
  en M0 — así, aunque la carta sea otra, la *experiencia* no se repite en la semana.

> **Borde cubierto (sin drama):** si el pool del pilar se queda corto, el motor
> relaja primero el dedup de concepto, después el de carta (nunca la de ayer) y
> sigue. Nunca se queda sin carta. El pool mínimo posible es 18 cartas (6 pilares ×
> 3 de escritura pura) ≥ 7 días: la promesa se cumple en toda configuración.

---

## 5. La puntuación (estrellas) y cómo aprende el motor

Al cerrar el ritual (M3), aparece un **"¿cuánto te llegó?" de 1 a 5 ⭐**. Es **opcional
y salteable** — la app nunca insiste (*invitar, nunca exigir*). Pero le contamos al
usuario, con todas las letras, **para qué sirve**: *"puntuá si querés; con eso la app
va aprendiendo qué te llega más"* (*intimidad como producto*: nada a escondidas).

- La señal que extraemos es **la afinidad por actividad** (los pilares van todos,
  no se afinan en v1). Si puntuás alto las cartas de *caminar*, el motor empuja un
  poco más esa actividad.
- Cada actividad tiene un **dial de afinidad** que arranca **neutro** y se mueve con
  el promedio de tus estrellas. Sin puntuaciones, todo neutro → el motor es humilde
  y sortea parejo.
- **Siempre hay un piso:** por más que adores una actividad, las demás nunca llegan
  a probabilidad cero.

**Dos usos de la estrella:** afinar la entrega (acá) y ordenar el Baúl por mejores
puntuadas (handoff M2→M4).

---

## 6. La evolución: v1 humilde → v2 con criterio

| | **v1 — inclinación suave** | **v2 — concentra, pero no encierra** |
|---|---|---|
| **Cuándo** | desde el día 1 | cuando ya **recibiste y puntuaste las 5 actividades varias veces** |
| **Qué hace** | la preferencia empuja apenas | se apoya **fuerte** en tus favoritas… |
| **El guardarraíl** | — | …pero ≈1 vez/semana entra una actividad *elegida pero descuidada* |

**Por qué el comodín de actividad es innegociable:** anti eco-cámara (*menos consumo,
más presencia*) y porque **la actividad que evitás suele ser la más valiosa**. Sorprende
solo **dentro del menú elegido** — nunca reintroduce una actividad que el usuario sacó.

**v2 también afina el comodín de pilar:** el 7º día deja de ser puro azar y pondera
por las ⭐ del usuario (su pilar favorito vuelve más seguido) — ver `ROADMAP_v2_PREMIUM.md`,
junto con "cambiar la carta 1×/día" (premium).

> Lema: **"el motor te conoce, pero no te subestima."**

---

## 7. Qué lee y qué escribe M2

**Lee** (privado, todo con `user_id`):
- `usuario_acciones` → tus actividades elegidas (de M1; la escritura pura siempre cuenta)
- `usuarios` → horario, zona horaria, aviso on/off (de M1)
- `entregas` ⨝ `cartas` → tu historial: qué cartas, qué pilares, qué **conceptos**,
  qué días, con qué estrella (la última semana para las ventanas; todo el histórico
  para la afinidad)

**Escribe:**
- una fila nueva en `entregas` cada día (carta elegida, fecha, vigencia)
- la **estrella** y `completada` las escribe M3 sobre esa misma fila

> La carta en sí (frase, prompt, concepto, color, dibujo) **no se copia**: se joinea
> desde la tabla global `cartas` al renderizar. La entrega guarda el puntero + lo tuyo.

---

## 8. Handoffs con los otros motores

- **← M0:** las cartas (pilar, actividad, **concepto**, frase, prompt). El pool y las
  ventanas de no-repetición salen de acá.
- **← M1:** actividades elegidas, horario, zona horaria, aviso. Cambiar actividades en
  Ajustes **cambia el pool en el acto**.
- **→ M3:** M2 entrega la carta del día; M3 corre el ritual y **devuelve** estrella +
  si la completó.
- **→ M4 (Baúl):** las entregas completadas son el historial, ordenable por estrella.

---

## 9. Decisiones canónicas vigentes

- **Rotación 6+1 (WS17):** los 6 pilares van todos, cada semana, en orden mezclado +
  día comodín. El usuario no elige pilares. La semana del usuario ES la rotación.
- **Doble ventana de no-repetición = 7 días, por carta Y por concepto (WS17).**
- **El usuario elige solo la forma (WS10/WS17):** actividades de desconexión
  elegibles; la escritura pura siempre en el pool (escribir ES la pausa, canon §0).
- **Primera carta = random**, sin rama especial.
- **Sorteo ponderado, no "elegir la mejor":** la preferencia inclina, el azar decide.
- **Puntuación = 1-5 ⭐, opcional y transparente.** Alimenta la afinidad de actividad.
- **Piso para todas las actividades:** nunca probabilidad cero.
- **Evolución v1 suave → v2 fuerte con comodines** (de actividad y de pilar),
  disparada por el historial, no por fecha. v1 es lo que está en producción.

---

## 10. Historial (derogado — solo contexto, no usar)

- **v1 original (WS04):** las categorías se elegían en M1 (2-6) y eran filtro duro del
  pool. **Derogado en WS17** por la rotación completa: los pilares son la tesis, no
  una preferencia.
- **WS10:** sumó las actividades como segundo filtro duro y el "piso garantizado" de
  escribir. La parte de actividades sigue viva; la de categorías quedó derogada; el
  "piso" se reformuló como *escritura pura = la pausa misma* (canon §0, WS18).
- **Castigo por repetir categoría de ayer:** existía en v1; la rotación lo volvió
  innecesario y se eliminó.
- **Ventana de no-repetición de ~60 días adaptativa:** idea pre-WS04, nunca se
  construyó; 7 días alcanza (*Simpleza*).
- **`entrega.py` (sandbox v1 de esta carpeta):** eliminado en WS18; queda en el
  historial de git. La única implementación es la de `apps/api`.

---

## 11. Diferido a v2

- **Concentración fuerte + comodín de actividad** (§6) con datos reales de uso.
- **Comodín de pilar aprendido** (el 7º día pondera por ⭐) — `ROADMAP_v2_PREMIUM.md`.
- **Cambiar la carta del día (1×/día, premium)** — respeta rotación y conceptos.
- Señales **implícitas** (completó, subió foto) como afinidad además de la estrella.
