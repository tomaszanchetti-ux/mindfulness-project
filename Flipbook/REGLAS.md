# Reglas del flipbook Dwellia (gramática visual · v1 · WS26)

Estas reglas son lo que hace que cualquier volumen se lea como **un flipbook** y como
**Dwellia**, aunque lo dibuje otra persona u otra sesión. Se aplican al transformar una foto
en personaje y al escribir un guion.

## 1. El papel y la línea
- Fondo **papel crema** (`#f7f1e7`) con grano suave; nunca blanco puro.
- Línea principal **tierra** (`#2f2923`), 6-8 px a 1080 de ancho. Secundaria **taupe**
  (`#756b5e`) para el fondo, la correa, los que pasan. Divisores **arena** (`#d8cbb8`).
- **Un solo acento de color por hoja**, siempre **salvia** (`#8fa58a` / `#6f8a69`): el collar
  de Pipo, el sol, el objeto que se enciende, el aura, la hoja del cierre. Nunca dos colores.
- La línea **tiembla**: cada hoja se traza con su propio temblor (±2 px). Es lo que dice
  "esto está redibujado a mano".
- Relleno solo donde hace falta leer una forma: pelo, máscara y orejas del pug. El resto es línea.

## 2. El ritmo del flipbook
- **10 hojas por segundo** (30 fps, cada hoja dura 3 cuadros).
- **1 cuadro en vuelo** por hoja: la hoja anterior levantándose desde la esquina del pulgar,
  con el dorso más claro y una sombra sobre la nueva. Aprobado por Tomás; no exagerar.
- La hoja entera **salta 1-3 px** al pasar (registro imperfecto).
- Taco de hojas al pie y a la derecha que se **achica** a medida que avanza; **número de
  página** abajo a la derecha; **pulgar fijo** en la esquina.
- Movimiento por hoja: poco. Un paso, un gesto, un cambio de mirada. Si algo tiene que moverse
  mucho, se mueve el fondo (parallax) y el personaje camina "en el lugar".

## 3. El libro
- **Portada** (2 s, respira sin pasar página): tapa de cartón (`#c4b296`), doble marco, "VOLUMEN N",
  título de 1-2 palabras grande, viñeta redonda con el personaje, "un libro para hojear",
  "capítulo N". Es el gancho del feed.
- **Historia** 15-20 s, 4-6 escenas.
- **Cierre**: última hoja sostenida 0,5 s → la tapa se cierra en 1 s → **contratapa** 3 s: hoja
  salvia, "Dwellia", "una Pausa al día, fuera del teléfono", "continúa en el volumen N+1",
  "impulsado por Dwellia · link en la bio". Dwellia **solo** aparece aquí.

## 4. Los personajes
- **Uno principal (Teo)** y secundarios que entran de a uno por volumen (**Pipo** desde el 1).
- Cada personaje se define por **3 rasgos fijos** que se reconozcan en cualquier hoja y a
  cualquier tamaño. Se eligen mirando las fotos de referencia; el resto se simplifica a línea.
- Ficticios siempre: se inspiran en personas o animales reales, pero tienen nombre propio y no
  son esa persona. No se usan fotos reales en los videos.
- Estados de ánimo con lo mínimo: boca plana / sonrisa; mirada abajo / frente / arriba / costado;
  postura encorvada (0) → erguida (1). Sin cejas ni expresiones complejas.
- Cada personaje es una **marioneta de partes** en `motor/render.py`: cabeza, cuerpo, poses
  (sentado, camina, erguido). Una pose nueva se agrega una vez y sirve para todos los volúmenes.

## 5. La historia
- Regla de oro del capítulo: **un problema chiquito y reconocible en la primera hoja → algo se
  enciende → un gesto → un final abierto**.
- Dwellia en la historia es **abstracta y mágica**: algo parecido a un teléfono se enciende de
  verde, el ruido mental se disuelve, el personaje hace la actividad, escribe, y se lo ve
  después con un **aura** distinta haciendo un acto que lo demuestra. Sin cartas, sin
  pantallas de la app, sin logo dentro de la historia.
- **Una temporada = 6 volúmenes**, uno por pilar en el orden del reloj del onboarding: amor
  propio · gratitud · vínculos · sentido · perspectiva · resiliencia. Cada volumen presenta un
  secundario ligado al pilar.
- Texto en pantalla: **máximo 4 palabras por hoja**, minúsculas, con punto si es una frase
  ("lunes." · "algo se enciende." · "salir un rato"). Sin voz. Georgia o serif parecida.
- Tono suave, humor de gesto, nunca sermón. Pipo lleva el humor; Teo lleva el arco.

## 6. Lo que no se hace
- Generar cada hoja con IA de imágenes (no mantiene el personaje entre hojas).
- Más de un color de acento, negro puro, fondos blancos, sombras realistas.
- Nombrar Dwellia dentro de la historia. Mostrar pantallas de la app.
- Personas reales reconocibles, fotos, voces.
