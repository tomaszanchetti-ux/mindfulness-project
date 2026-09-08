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
- **Principio "Sin City" (Tomás, 06/09): todo simplón, salvo UN elemento con detalle por hoja.**
  Como en la película, donde todo es blanco y negro y un detalle va en color, acá todo es
  línea simple y **un solo elemento lleva detalle** fino: el que carga el chiste o la emoción.
  La cara de Pipo con sus arrugas, la mirada triste en el espejo, las fotitos del feed pasando
  una atrás de otra, el vapor del café. El resto se queda en línea de palito. El detalle es
  un presupuesto: si dos cosas tienen detalle, ninguna se ve.
- **Dos capas de dibujo (Tomás, 07/09, WS31): "que no parezca algo así nomás".**
  **Capa de detalle (ilustrada):** Teo, Pipo (sus 6 caras), los personajes que vayan
  apareciendo y **el elemento clave de cada historieta** se dibujan UNA vez como piezas
  ilustradas con fondo transparente (cabeza, cuerpo, poses), se limpian y se registran como
  partes del motor; después el motor las usa en todas las hojas con temblor y registro
  imperfecto, así que es el mismo personaje en las 60 hojas. **Capa simple (programada):**
  fondos, extras, props, formas del cartel, taco de hojas: línea de palito, ahí se ahorra y
  el contraste hace que el personaje detallado se vea más. Lo que se genera es el ASSET,
  nunca la hoja (la regla de §6 sigue). Los activos que se repiten se hacen en D1.1/D1.2;
  los elementos puntuales de cada historieta, en la WS de ese volumen.

## 2. El ritmo del flipbook
- **10 hojas por segundo** (30 fps, cada hoja dura 3 cuadros).
- **1 cuadro en vuelo** por hoja: la hoja anterior levantándose desde la esquina del pulgar,
  con el dorso más claro y una sombra sobre la nueva. Aprobado por Tomás; no exagerar.
- La hoja entera **salta 1-3 px** al pasar (registro imperfecto).
- Taco de hojas al pie y a la derecha que se **achica** a medida que avanza; **número de
  página** abajo a la derecha; **pulgar fijo** en la esquina.
- Movimiento por hoja: poco. Un paso, un gesto, un cambio de mirada. Si algo tiene que moverse
  mucho, se mueve el fondo (parallax) y el personaje camina "en el lugar".
- **El zoom es un recurso del libro.** Una hoja puede ser un primer plano (la mano con el
  teléfono, las fotitos pasando, el ojo de Pipo). Se entra al detalle en 2-3 hojas (la hoja
  "acerca") y se vuelve al plano simple. Es donde vive el elemento con detalle del principio
  Sin City. Nunca se muestra una marca ni una interfaz real: fotitos una atrás de otra, no
  una app.

## 3. El libro (v2 · WS31)
- **Cartel de apertura** (2 s, respira sin pasar página): cartel retro de historieta,
  **distinto por volumen** (color de fondo, formas, título) con **lo fijo**: la imagen de Teo
  y Pipo a lo Tintín y el rótulo "TEO Y PIPO" en tipografía condensada grande. Título en el
  formato **"Teo y Pipo en [TÍTULO SATÍRICO] · Vol. N"**. El cartel es otro objeto, no una
  hoja: además de crema, tierra y salvia usa **una cuarta tinta reservada solo para carteles**,
  distinta por volumen. Es el gancho del feed: el título ya cuenta el chiste.
- **Historia** 20-24 s, 3 escenas (problema · espejo · magia), ver
  `guiones/00_FORMATO_Y_OPUESTOS.md` §2.
- **Cierre, siempre el mismo:** Pipo a cámara con alegría sarcástica → **el iris se cierra**
  sobre su cara al estilo Looney Tunes (~1,5 s) → la tapa se cierra (1 s) → **contratapa** 3 s:
  hoja salvia, "Dwellia", "una Pausa al día, fuera del teléfono", "Teo y Pipo volverán
  próximamente", "link en la bio". Dwellia **solo** aparece aquí. Se construye una vez (D1.2).
- TikTok repite en bucle: el libro cerrado vuelve solo al cartel. El cierre pide la apertura.

## 4. Los personajes
- **Uno principal (Teo)** y secundarios que entran de a uno por volumen (**Pipo** desde el 1).
- Cada personaje se define por **3 rasgos fijos** que se reconozcan en cualquier hoja y a
  cualquier tamaño. Se eligen mirando las fotos de referencia; el resto se simplifica a línea.
- Ficticios siempre: se inspiran en personas o animales reales, pero tienen nombre propio y no
  son esa persona. No se usan fotos reales en los videos.
- **Teo** con lo mínimo: boca plana / sonrisa; mirada abajo / frente / arriba / costado;
  postura encorvada (0) → erguida (1). Sin cejas ni expresiones complejas. Nunca mira a cámara.
- **Pipo es la excepción: su cara es el chiste.** Seis caras fijas (fastidio · resignación ·
  sospecha · ¿en serio? · alegría sarcástica · orgullo) con las herramientas del pug (arrugas
  como cejas, orejas, lengua, cabeza ladeada). **Pipo mira a cámara.** Teo lleva el arco,
  Pipo lleva la cara.
- Cada personaje es una **marioneta de piezas ilustradas** (`motor/partes.py` las dibuja como
  SVG y las renderiza a PNG transparente en `personajes/partes/`; `motor/marioneta.py` las
  compone con anclas y temblor): una cabeza por cara, un cuerpo por pose. Una pieza nueva se
  agrega una vez y sirve para todos los volúmenes. Se regenera todo con
  `python3 Flipbook/motor/partes.py`.

## 5. La historia
- Cada volumen sigue el **formato único de 5 escenas** de `guiones/00_FORMATO_Y_OPUESTOS.md`:
  cartel · el problema · el espejo de Pipo · la magia · el cierre. Un pilar y su opuesto
  moderno por volumen. **Chiste en las imágenes, mensaje lindo en los textos.** Las caras
  de Pipo y los gestos de Teo son la clave y se dibujan una vez para todos los volúmenes.
- **La sátira es de la situación, nunca de la persona.** Pipo trata a Teo con amor siempre.
- **Las situaciones son cosas MUY vividas, reconocibles en un segundo, y un poco grotescas.**
  No "Teo está triste": Teo pasa dos horas sacándose mil fotos con poses para verse bien, y
  después se mira al espejo con cara de tristeza. El grotesco es la exageración de algo que
  todos hicimos; ahí está la risa y el "sos vos". Cada guion arranca por encontrar ESA escena.
- Dwellia en la historia es **abstracta y mágica**: algo parecido a un teléfono se enciende de
  verde, el ruido mental se disuelve, el personaje hace la actividad, escribe, y se lo ve
  después con un **aura** distinta haciendo un acto que lo demuestra. Sin cartas, sin
  pantallas de la app, sin logo dentro de la historia.
- **Una temporada = 6 volúmenes**, uno por pilar en el orden del reloj del onboarding: amor
  propio · gratitud · vínculos · sentido · perspectiva · resiliencia. Cada volumen presenta un
  secundario ligado al pilar.
- Texto en pantalla = **la voz de Pipo** (el libro es su diario): primera persona,
  minúsculas, **hasta 6 palabras por hoja**, con punto si es una frase ("lunes. otra vez el
  espejo." · "yo me veo perfecto."). Una idea larga se reparte en 2-3 hojas. **Español
  neutro** en pantalla. Sin voz grabada. Georgia o serif parecida.
- Tono: sátira con ternura (Mafalda, Macanudo, Snoopy), humor de gesto, nunca sermón. Lo gracioso engancha; lo emocional hace volver.

## 6. Lo que no se hace
- Generar cada hoja con IA de imágenes (no mantiene el personaje entre hojas).
- Más de un color de acento, negro puro, fondos blancos, sombras realistas.
- Nombrar Dwellia dentro de la historia. Mostrar pantallas de la app.
- Personas reales reconocibles, fotos, voces.
