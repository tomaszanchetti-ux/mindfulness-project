# Teo — ficha de personaje (protagonista)

- **Quién es en la historia:** el protagonista. Un tipo joven con la cabeza llena de ruido que
  aprende, capítulo a capítulo, a hacer una Pausa. Ficticio, inspirado en Tomás como referencia
  de rasgos (no es Tomás).
- **Entra en el volumen:** 1 (y en todos).
- **Qué aporta al arco:** él ES el arco: encorvado (0) → erguido (1) a lo largo de la temporada.
- **Referencias:** `Tiktok/teo/tomas.jpg` (de frente, fondo blanco).
- **Lo que lo hace reconocible (3 rasgos fijos):**
  1. **Pelo ondulado con volumen hacia un lado** (3 bucles; relleno arena).
  2. ~~Anteojos de sol sobre el pelo~~ **Sin anteojos (decisión de Tomás, WS32: "sacamos las gafas y queda 10 puntos").** El segundo rasgo pasa a ser la **cara alargada con la mandíbula marcada**.
  3. **Barba de pocos días** en puntitos taupe sobre la mandíbula.
- **Cómo se mueve / qué gesto lo define:** cuerpo delgado de línea; postura como termómetro
  (encorvado sobre el teléfono → erguido con aura). Gesto que lo define: levantar la vista.
- **Acento salvia:** no lleva; el acento de sus hojas es el objeto que se enciende o el aura.
- **Estado en el motor (WS32 · D1.1):** **piezas ilustradas** en `personajes/partes/teo/`
  (`motor/partes.py`): 20 cabezas = 4 miradas (abajo · frente · arriba · costado) × 5 bocas
  (plana · sonrisa · abierta · fruncida · triste), con el pelo rehecho como mechones
  desparejos con volumen a la derecha (ya no parece gorro), anteojos sobre el pelo y barba
  de puntitos; 4 cuerpos base (`parado` · `encorvado` · `sentado` · `sentado_erguido`) con
  remera, pantalón y zapatillas. Los gestos de cada volumen (Spiderman, selfie, escribir con
  burbuja…) se construyen en el acto, en la WS de cada historieta (Tomás, WS32: "con Teo
  alcanza con tener un boceto claro de su cara y cuerpo"). La marioneta v1 de palitos queda en `render.py` hasta entonces.
- **La escena de la magia (WS33 · D1.2 · F):** piezas nuevas que se repiten en todos los
  volúmenes: la mirada `cerrada` (ojos cerrados, la cara de calma; × las 5 bocas), el cuerpo
  `medita` (piernas cruzadas de frente, manos en las rodillas, ancla `pecho` para la
  respiración) y `camina_0..3` (el paseo erguido de perfil en 4 fases, ancla `mano`). Los
  props de la escena viven en `personajes/partes/props/`: `telefono_0..3` (apagado · se
  enciende · pantalla entera salvia · salvia respirando) y `cuadernito_0..3` (el lápiz
  avanza). El **aura** no es una pieza: `Marioneta.pegar(..., aura=1, pulso=p)` la saca de
  la silueta del personaje ya compuesto, así sirve para cualquier pose. Guion de prueba en
  `motor/magia.py` (hoja fija `personajes/hoja_magia.png` + `pruebas/magia.mp4`).
