# M2 — Motor de Entrega del Día · Madre del Motor

> **El corazón diario de la app.** Cada día, a tu hora, elige **una** carta y te la
> entrega. Toma de M1 tu horario y aviso; toma de M0 las cartas (los 6 pilares ×
> las 4 acciones iniciales); aprende de lo que puntuás en M3; y le pasa la entrega a
> M3 (ritual) y M4 (Baúl). Se rige por el [`Documento Madre`](../00_Documento_Madre.md)
> y el storytelling del [`canon de cartas §0`](../M0_Motor_de_Contenido/canon_cartas.md).
>
> La **lógica** vive acá. La **implementación canónica** vive en
> [`apps/api/mindful_api/services/seleccion.py`](../apps/api/mindful_api/services/seleccion.py)
> (tests en `apps/api/tests/test_seleccion.py`).

---

## 1. Qué hace M2 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Elegir **una** carta por día | Inventar cartas (eso es M0) |
| Recorrer **los 6 pilares, todas las semanas** (rotación 6+1) | Dejar que el usuario recorte pilares o acciones (nada se elige — WS17/WS22) |
| No repetir en la semana **ni carta ni concepto** | Garantizar no-repetición de meses (no hace falta) |
| Aprender qué **acción inicial** te llega más e inclinarse | Mostrar el ritual (eso es M3) |
| Avisarte (push) a tu horario local | Encerrarte en una sola acción (siempre deja variedad) |
| Dejar la carta vigente 24h o hasta completarla | |

**El norte de M2:** que tu semana sea **el recorrido completo del crecimiento** — los
6 pilares, uno por día — sin que jamás se sienta repetido ni predecible.

---

## 2. La idea: la semana del usuario ES la rotación

El motor trabaja en **dos niveles**:

1. **El recorrido (nuestro): los 6 pilares, cada semana.** Cada día se sirve un pilar
   que no apareció en los últimos 6 días, **en orden mezclado** (la semana sorprende:
   el lunes no es siempre gratitud). Cuando los 6 ya pasaron, el 7º día es **comodín**:
   cualquier pilar salvo el de ayer. Después del comodín la rotación se auto-corrige
   sola. El usuario **no elige pilares** — el círculo completo es la promesa.
2. **La forma (del motor): las 4 acciones iniciales, con afinidad aprendida (WS22).**
   Dentro del pilar del día, el pool son **todas sus cartas** (las 4 acciones
   iniciales viables — el usuario ya no recorta nada). El motor aprende de las ⭐
   cuál acción le llega más e **inclina** la balanza. No manda: **empuja**. El azar
   siempre tiene la última palabra. La válvula del "hoy no quiero moverme" no es un
   menú: es el **cambio de carta** (v2 premium) que cruza el eje
   movimiento↔quietud.

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
3. Armo el pool del pilar → TODAS sus cartas (las 4 acciones iniciales — WS22)
4. Saco las repetidas     → ni carta NI concepto vistos en los últimos 7 días
5. Le doy un peso a cada candidata:
      • + afinidad de acción     (las que venís puntuando alto pesan más)
      • − repetir lo de ayer     (castigo chico si la acción es la de ayer)
      • piso para todas          (ninguna acción llega a peso 0)
6. Sorteo ponderado       → a más peso, más chance. El azar decide.
7. Entrego                → vigencia 24h; aviso (push) a tu horario, según M1
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
> sigue. Nunca se queda sin carta. Con el pool completo del pilar (WS22: nada se
> recorta; objetivo 12 cartas por pilar) el borde es aún más holgado que antes:
> la promesa se cumple siempre.

---

## 5. La puntuación (estrellas) y cómo aprende el motor

Al cerrar el ritual (M3), aparece un **"¿cuánto te llegó?" de 1 a 5 ⭐**. Es **opcional
y salteable** — la app nunca insiste (*invitar, nunca exigir*). Pero le contamos al
usuario, con todas las letras, **para qué sirve**: *"puntuá si querés; con eso la app
va aprendiendo qué te llega más"* (*intimidad como producto*: nada a escondidas).

- La señal que extraemos es **la afinidad por acción inicial** (los pilares van
  todos, no se afinan en v1). Si puntuás alto las cartas de *pasear*, el motor
  empuja un poco más esa acción.
- Cada acción tiene un **dial de afinidad** que arranca **neutro** y se mueve con
  el promedio de tus estrellas. Sin puntuaciones, todo neutro → el motor es humilde
  y sortea parejo.
- **Siempre hay un piso:** por más que adores una acción, las demás nunca llegan
  a probabilidad cero.

**Dos usos de la estrella:** afinar la entrega (acá) y ordenar el Baúl por mejores
puntuadas (handoff M2→M4).

---

## 6. La evolución: v1 humilde → v2 con criterio

| | **v1 — inclinación suave** | **v2 — concentra, pero no encierra** |
|---|---|---|
| **Cuándo** | desde el día 1 | cuando ya **recibiste y puntuaste las 4 acciones varias veces** |
| **Qué hace** | la preferencia empuja apenas | se apoya **fuerte** en tus favoritas… |
| **El guardarraíl** | — | …pero ≈1 vez/semana entra una acción *descuidada* |

**Por qué el comodín de acción es innegociable:** anti eco-cámara (*menos consumo,
más presencia*) y porque **la acción que evitás suele ser la más valiosa**.

**v2 también afina el comodín de pilar:** el 7º día deja de ser puro azar y pondera
por las ⭐ del usuario (su pilar favorito vuelve más seguido) — ver `ROADMAP_v2_PREMIUM.md`,
junto con "cambiar la carta 1×/día" (premium).

> Lema: **"el motor te conoce, pero no te subestima."**

---

## 7. Qué lee y qué escribe M2

**Lee** (privado, todo con `user_id`):
- `usuarios` → horario, zona horaria, aviso on/off (de M1)
  *(`usuario_acciones` quedó obsoleta — WS22: nada se elige, nada debe leerla;
  se elimina en el paso 3, canon §Transición)*
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

- **← M0:** las cartas (pilar, acción inicial, **concepto**, frase, prompt). El pool y
  las ventanas de no-repetición salen de acá.
- **← M1:** horario, zona horaria, aviso. (Nada más: ni pilares ni acciones se
  eligen — WS17/WS22.)
- **→ M3:** M2 entrega la carta del día; M3 corre el ritual y **devuelve** estrella +
  si la completó.
- **→ M4 (Baúl):** las entregas completadas son el historial, ordenable por estrella.

---

## 9. Decisiones canónicas vigentes

- **Rotación 6+1 (WS17):** los 6 pilares van todos, cada semana, en orden mezclado +
  día comodín. El usuario no elige pilares. La semana del usuario ES la rotación.
- **Doble ventana de no-repetición = 7 días, por carta Y por concepto (WS17).**
- **Nada se elige (WS22):** el pool del día es el pilar completo — las 4 acciones
  iniciales viables. La válvula del "hoy no" es el cambio de carta v2 cruzando el
  eje movimiento↔quietud (mismo pilar, concepto distinto, ventanas intactas).
- **Primera carta = random**, sin rama especial.
- **Sorteo ponderado, no "elegir la mejor":** la preferencia inclina, el azar decide.
- **Puntuación = 1-5 ⭐, opcional y transparente.** Alimenta la afinidad por acción.
- **Piso para todas las acciones:** nunca probabilidad cero.
- **Evolución v1 suave → v2 fuerte con comodines** (de actividad y de pilar),
  disparada por el historial, no por fecha. v1 es lo que está en producción.

---

## 10. Historial (derogado — solo contexto, no usar)

- **v1 original (WS04):** las categorías se elegían en M1 (2-6) y eran filtro duro del
  pool. **Derogado en WS17** por la rotación completa: los pilares son la tesis, no
  una preferencia.
- **WS10:** sumó las actividades como segundo filtro duro y el "piso garantizado" de
  escribir. **Todo derogado:** las categorías en WS17, el "piso" reformulado en WS18,
  y el filtro de actividades en **WS22** (la pausa de dos tiempos: el pool es el
  pilar completo, escribir es el cierre universal, `usuario_acciones` obsoleta).
- **Castigo por repetir categoría de ayer:** existía en v1; la rotación lo volvió
  innecesario y se eliminó.
- **Ventana de no-repetición de ~60 días adaptativa:** idea pre-WS04, nunca se
  construyó; 7 días alcanza (*Simpleza*).
- **`entrega.py` (sandbox v1 de esta carpeta):** eliminado en WS18; queda en el
  historial de git. La única implementación es la de `apps/api`.

---

## 11. Diferido a v2

- **Concentración fuerte + comodín de acción** (§6) con datos reales de uso.
- **Comodín de pilar aprendido** (el 7º día pondera por ⭐) — `ROADMAP_v2_PREMIUM.md`.
- **Cambiar la carta del día (1×/día, premium)** — cruza el eje movimiento↔quietud
  (WS22); respeta rotación y conceptos.
- Señales **implícitas** (completó, subió foto) como afinidad además de la estrella.
