# M2 — Motor de Entrega del Día · Madre del Motor

> **El corazón diario de la app.** Cada día, a tu hora, elige **una** carta y te la
> entrega. Toma de M1 tus categorías, horario y aviso; toma de M0 las cartas; aprende
> de lo que puntuás en M3; y le pasa la entrega a M3 (ritual) y M4 (Baúl). Se rige por
> el [`Documento Madre`](../00_Documento_Madre.md).
>
> La **lógica** vive acá. El **script** que la ejecuta vive aparte en
> [`entrega.py`](entrega.py) (hoy corre contra los JSON de M0; al construir se enchufa a Postgres).

---

## 1. Qué hace M2 (y qué no)

| Sí hace | No hace |
|---------|---------|
| Elegir **una** carta por día, de tus categorías | Inventar cartas (eso es M0) |
| No repetir lo de la última semana | Garantizar no-repetición de 60 días (no hace falta) |
| Aprender qué **acción** te gusta más y inclinarse | Cambiar tus categorías (eso lo elegís vos en M1) |
| Avisarte (email/push) a tu horario local | Mostrar el ritual (eso es M3) |
| Dejar la carta vigente 24h o hasta completarla | Encerrarte en una sola modalidad (siempre deja variedad) |

**El norte de M2:** que cada día te llegue **algo distinto, de lo tuyo, que cada vez
te conozca un poco más** — sin volverse predecible ni un eco de vos mismo.

---

## 2. La idea en una imagen

Pensalo como un **sommelier de cartas**. Trabaja en **dos capas**:

1. **Lo que vos elegís (filtro duro): la categoría.** El pool del día son sólo las
   cartas de tus categorías elegidas (2-6). Es sagrado: nunca te llega algo de fuera.
2. **Lo que la app aprende (preferencia blanda): la acción.** Dentro de ese pool, va
   notando si te gusta más *escribir*, *caminar*, *contemplar*, *respirar* o *hacer*,
   y **inclina** la balanza hacia eso. No manda del todo: **empuja** las probabilidades.
   El azar siempre tiene la última palabra, para que el ritual no se vuelva predecible.

> La categoría la decidís **vos** (M1). La acción la **descubre la app** con el tiempo.

---

## 3. El flujo de cada día

```
1. ¿Es tu PRIMERA carta?  → SÍ: 100% al azar dentro de tus categorías.   ◄ el script lo sabe: tu historial está vacío
                            NO: seguí ↓
2. Armo el pool           → todas las cartas de tus categorías elegidas
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
> se queda sin carta. Con 2 categorías el pool es ~21 cartas, así que en la práctica
> esto casi nunca pasa.

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

**v1 es lo que codeamos y lanzamos.** v2 queda especificada acá para cuando la app tenga
rodaje y datos reales; no la activamos hasta tener evidencia de uso.

---

## 7. Qué lee y qué escribe M2 (handoff al stack §5)

**Lee** (privado, todo con `user_id`):
- `usuario_categorias` → tus 2-6 categorías (de M1)
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
- **Dos capas:** categoría = filtro duro (la elige el user) · acción = preferencia
  blanda (la aprende la app).
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
