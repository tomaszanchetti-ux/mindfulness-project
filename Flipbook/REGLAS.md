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

## 3. El libro (v2.1 · WS31, revisado en la WS36 con los números del vol. 1)

> **Por qué cambió.** El vol. 1 se publicó y midió **3,64 s de tiempo medio sobre 30,7 s**
> (11,8 % de retención, 1,7 % de completado, 183 visualizaciones, 0 seguidores nuevos).
> El espectador promedio se iba **durante el cartel**, antes del primer chiste. En el feed,
> una pantalla fija al principio se lee como "esto va lento". La regla que sale de ahí:
> **el video abre con la historia; todo lo que no es historia se acorta o se saca.**

- **El arranque: rótulo, no pantalla.** El video **abre con la primera imagen y su globo ya
  puesto** (`globo_desde: 0` automático en el primer cuadro). El título viaja como **rótulo
  superpuesto arriba** ("TEO Y PIPO EN / [TÍTULO] · Vol. N", en la cuarta tinta del volumen),
  2,4 s y se va con un fundido. La banda vive entre y=150 y y=390: debajo de la barra
  "Para ti" de TikTok y encima de la escena, que ya sube 220 px por los globos de abajo.
- **El cartel sigue existiendo, como PORTADA.** Se guarda siempre en
  `pruebas/<nombre>_portada.png` y se sube a TikTok como portada del video: ahí es donde de
  verdad trabaja, en la grilla del perfil, que es la que decide si alguien mira los otros
  cinco. Mismo dibujo de antes (Tintín, cuarta tinta, formas por volumen). `cartel: {modo:
  apertura}` recupera la pantalla fija de 2 s del vol. 1, por si alguna vez conviene.
- **Historia 16-20 s**, 3 escenas (problema · espejo · magia), ver
  `guiones/00_FORMATO_Y_OPUESTOS.md` §2. Más corto que el vol. 1 a propósito: con 1,7 % de
  completado, cada segundo de más resta.
- **Cierre, siempre el mismo, pero de 3,7 s** (era 6,1 s): Pipo a cámara con alegría
  sarcástica (0,5 s) → **el iris se cierra** sobre su cara al estilo Looney Tunes (0,9 s) →
  la tapa se cierra (0,5 s) → **contratapa** 1,8 s. Dwellia **solo** aparece aquí. Los cuatro
  tiempos se mueven por guion (`cierre:`). El branding largo no vive en el video: vive en la
  descripción, el comentario fijado y la bio, que sí se leen sin pagar segundos.
- TikTok repite en bucle: **la última imagen de la historia y la primera tienen que
  poder empalmar**, para que el rebobinado sume como visualización nueva.

### La ley del movimiento (WS36, Tomás)

> El vol. 1 salió con la escena **congelada**: el papel pasaba, pero adentro no se movía
> nada. Las chicas eran una estampa pegada y Teo una pose fija. En el feed eso se lee como
> una lámina, no como un video, y el pulgar sigue de largo.

**Ningún cuadro se queda quieto.** Cada cuadro tiene que tener al menos UNA de estas cuatro,
y el primero del volumen tiene que tenerla **desde la hoja 0**:

1. **Alguien se desplaza** (`hacia`) — entra, sale, cruza, se acerca.
2. **Alguien cambia de pose** (`cuerpo` como lista, `ciclo`) — el chiste que se repite.
3. **La cámara se mueve** (`camara`) — el recurso comodín: no hay que dibujar nada y sirve
   en cualquier cuadro. Cuando no se te ocurre qué mover, empujá la cámara.
4. **El mundo se mueve** (`parallax`, `flash`, `sacude`) — la calle que corre, el fogonazo.

El cabeceo y el temblor de línea NO cuentan: son la textura del dibujo, no movimiento.
La regla de costo no cambia (≤2-3 poses nuevas por volumen); el movimiento se saca del
guion, no de dibujar más.

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
- Texto en pantalla = **la voz de Pipo, y va en un GLOBO DE DIÁLOGO a la audiencia**
  (Tomás, WS33: Pipo rompe la cuarta pared, formato Deadpool). Nunca suelto sobre la hoja:
  globo de historieta con relleno marfil, borde tierra, temblor, y la **colita apuntando a
  la cabeza de Pipo**. Georgia, minúsculas, primera persona, con punto si es una frase.
  **El tempo (Tomás, WS34): hasta 12 palabras por globo, en 3-4 líneas cortas, y el globo
  queda ≥3 s en pantalla** (se lee cómodo a ~3 palabras por segundo). Una idea más larga va
  en **dos globos sobre la MISMA imagen** (`pipo_dice` como lista), nunca en otra imagen.
  **La imagen entra sola 0,5 s y recién después aparece el globo** (`globo_desde`): el ojo
  ve el chiste antes de leerlo. **Español neutro** en pantalla (nunca voseo). Sin voz grabada.
- **La vida del cuadro (WS34):** una imagen que dura 3-4 s no puede estar quieta. El motor
  la mueve solo: la cabeza de Pipo cabecea (±4°, un ciclo por segundo), la de Teo apenas y
  lento, el globo flota, y siguen el temblor de línea y los ciclos de props (la pantalla que
  respira, el lápiz que avanza). `vida: false` en un personaje lo deja quieto.
- **Si Pipo no está en el cuadro, Pipo ASOMA:** se pega su cabeza sola por un borde lateral
  o inferior de la hoja para que el globo tenga de dónde salir. El motor lo hace solo
  (derecha abajo, con la cara de la escena) o el guion lo dice con `pipo_asoma`.
- **El globo vive ABAJO de la escena (Tomás, WS35):** en vertical, la escena ocupa la franja
  del medio y el globo va debajo, como una caja redondeada apaisada (2-3 líneas anchas) con
  la colita subiendo al mentón de Pipo; así nunca tapa la imagen. Para que quede en la zona
  segura de TikTok (la app tapa la franja de abajo con la descripción y el usuario, y la
  columna derecha con los íconos), **la escena entera sube 220 px** (`subir_escena`), y entre el piso y la caja quedan 130 px para la colita: nace en el borde superior de la caja con base angosta y sube en dos curvas hasta justo debajo de la silueta de Pipo, sin tocarlo. El
  modo viejo (óvalo arriba, como en la historieta) sigue con `globos: arriba` en el guion o
  `globo_lado: arriba` en un cuadro.
- El globo **nunca tapa una cara** ni el objeto que el personaje sostiene: el motor mide las
  cajas reales y elige dónde ponerlo (ver §7).
- Tono: sátira con ternura (Mafalda, Macanudo, Snoopy), humor de gesto, nunca sermón. Lo gracioso engancha; lo emocional hace volver.

## 6. Lo que no se hace
- Generar cada hoja con IA de imágenes (no mantiene el personaje entre hojas).
- Más de un color de acento, negro puro, fondos blancos, sombras realistas.
- Nombrar Dwellia dentro de la historia. Mostrar pantallas de la app.
- Personas reales reconocibles, fotos, voces.

## 7. El guion (v2 · WS33)

Un volumen se escribe en **un archivo YAML** en `guiones/` y se renderiza sin tocar código:

```bash
python3 Flipbook/motor/libro.py Flipbook/guiones/vol00_prueba.yaml
python3 Flipbook/motor/libro.py Flipbook/guiones/vol00_prueba.yaml --solo-cuadros
```

Salen `pruebas/<nombre>.mp4` (1080×1920, 30 fps) y `pruebas/<nombre>_cuadros.png`, la hoja
fija con un cuadro clave de cada cuadro **para revisar la lectura sin abrir el video**. El
motor imprime hojas, cuadros de video y segundos.

### La estructura

```yaml
volumen: 0
titulo: LA PRUEBA               # el título satírico, va en el cartel
cartel:
  tinta: ocre                   # ocre | ladrillo | azul_cartel (la cuarta tinta, §3)
  formas: diagonales            # diagonales | rayos | circulo | franja | marco
  vineta: tintin                # la imagen fija: tintin (los dos corriendo, la de la serie) | iluminado
escenas:
  - tipo: problema              # problema | espejo | magia
    fondo: rincon
    cuadros:
      - hojas: 34               # o `duracion: 3.4` (10 hojas = 1 s)
        teo:  {cuerpo: sentado, cara: abajo_plana, x: 430, y: 1100, escala: 1.6,
               prop: {nombre: telefono_0, dx: 12, dy: -34, rot: -24}}
        pipo: {cuerpo: sentado, cara: fastidio, x: 890, y: 1300, escala: 0.6}
        props: [{nombre: nube_garabatos, x: 610, y: 545, escala: 2.0, hacia_disolucion: 1.0}]
        pipo_dice: otra vez en el rincón. dos horas mirando nada.
      - hojas: 28               # la hoja "acerca"
        zoom: {pieza: props/telefono_0, escala: 2.7, rot: -12, manos: true}
        pipo_asoma: {lado: izquierda, cara: en_serio}
        pipo_dice: y el pulgar sube y sube, sin parar.
  - tipo: magia                 # bloque fijo de 4 momentos, tres huecos
    accion: medita              # medita | pasea
    burbuja: abuelos            # el descubrimiento del volumen
    resultado:
      fondo: mesa_familiar
      teo: {cuerpo: sentado_erguido, cara: costado_sonrisa}
      secundarios: [{tipo: abuela, x: 720, y: 900}, {tipo: abuelo, x: 930, y: 890}]
      pipo_dice: y ahora se le nota, ¿no?
```

El **cierre fijo** (Pipo · iris · tapa · contratapa) lo pone el motor: no se declara. Desde
la WS36 dura **3,7 s** y sus cuatro tiempos se pueden mover, en segundos:

```yaml
cartel:
  modo: rotulo                  # rotulo (por defecto: banda sobre la primera imagen) | apertura (pantalla fija de 2 s)
  rotulo_seg: 2.4               # cuánto se queda el rótulo antes del fundido
cierre:
  pipo: 0.5                     # Pipo a cámara
  iris: 0.9                     # el iris Looney Tunes
  tapa: 0.5                     # la tapa que se cierra
  contratapa: 1.8               # la hoja salvia con la D
```

El cartel se dibuja igual siempre y se guarda como `pruebas/<nombre>_portada.png` para subirlo
a TikTok como **portada** del video.

### Qué puede llevar un cuadro

| Clave | Qué es |
|---|---|
| `hojas` / `duracion` | cuántas hojas dura el cuadro (10 hojas por segundo). |
| `fondo` | `habitacion` · `rincon` · `banco_plaza` · `mesa_familiar` · `sofa` · `living` (el sofá corrido a la derecha y el rincón con banquito y lámpara a la izquierda, vol. 1) · `espejo_bano` · `calle` · `ninguno`. Cada uno declara anclas (`ventana`, `banquito`, `banco`, `mesa`, `sofa`, `espejo`, `repisa`…). |
| `teo` / `pipo` | `cuerpo`, `cara`, `x`, `y`, `escala`, `rot`, `espejo`, `aura` (0..1 o `sube`), `pulso`, `ciclo: true` (usa `cuerpo_0..3`, una fase por hoja), `prop` (una pieza o una lista; `ancla`, `dx`, `dy`, `rot`, `ciclo`), `hacia: {x, y}` (se interpola dentro del cuadro), `en: <ancla del fondo>`. |
| `props` | props simples: `nube_garabatos` (con `disolucion` 0..1), `burbuja_pensamiento` (con `dibujo` y `punta`), `correa`, `plato_croquetas`, `globo`. Cualquier opción admite `hacia_<opcion>` para interpolarla dentro del cuadro. `delante: true` los pone adelante del personaje. |
| `piezas` | piezas ilustradas compuestas (WS35): `pieza` (`familia/familia_living`, `familia/familia_mesa`, `extras/chicas_pasan`), `x`, `y`, `escala`, `rot`, `espejo`. Se pegan por su ancla `centro`, entre los secundarios y la capa delantera del fondo (la mesa tapa a la familia de la cintura para abajo); el globo las esquiva. |
| `secundarios` | gente de línea simple: `tipo` (`abuela`, `abuelo`, `chica`, `senor`), `x`, `y`, `escala`. |
| `zoom` | la hoja "acerca": `pieza` (`teo/cara_…`, `pipo/…`, `props/…`) o `prop`, con `escala`, `rot`, `ciclo`, `manos: true`. |
| `pipo_dice` | el texto del globo (≤12 palabras, 3-4 líneas), o una **lista** de textos = varios globos seguidos sobre la misma imagen. |
| `globo_desde` | hojas que la imagen está sola antes del primer globo (5 por defecto = 0,5 s). **En el PRIMER cuadro del volumen el motor lo pone en 0**: al principio del video, medio segundo sin texto es medio segundo para irse. |
| `globo_lado` | `abajo` (por defecto desde la WS35) o `arriba`, por cuadro. A nivel guion: `globos: abajo \| arriba` y `subir_escena: 220` (píxeles que sube la escena entera; 220 con globos abajo, 0 con arriba). |
| `pipo_asoma` | `lado` (`izquierda`, `derecha`, `abajo`) y `cara`, para cuando Pipo no está en el cuadro. |
| `parallax` | píxeles que corre el fondo por hoja (árboles de `calle` y `banco_plaza`). |
| `camara` | **el movimiento más barato (WS36)**: `empuje` (zoom 1→1,12) · `empuje_fuerte` (1→1,28) · `retroceso` (1,12→1) · o `{desde, hasta, x, y}` con el paneo en píxeles. Mueve la ESCENA, no el globo ni el libro. |
| `flash` | el fogonazo de una foto: `{desde, cada, dura, fuerza}` en hojas (por defecto uno cada 8 hojas desde la 3ª). |
| `hacia` | en `teo`, `pipo`, `piezas` y `secundarios`: `{x, y}` de destino; la posición se interpola dentro del cuadro. **Ya existía y el vol. 1 no lo usó: por eso las chicas no se movían.** |
| `hacia_escala` / `hacia_rot` | la escala o la inclinación al final del cuadro (se acerca, se inclina). |
| `sacude` | vibración corta en píxeles (el remate de un chiste, el nervio). |
| `vida` | multiplica el cabeceo del personaje (`0` lo apaga, `1.8` lo exagera). |
| `estado` | **la gramática de la serie (WS36)**: `conexion` (Teo con aura verde y boca sonriendo · Pipo contento) o `desconexion` (Teo triste y sin aura · Pipo enojado). Se puede poner en la escena entera. `boca_libre: true` en Teo deja su boca como está. |
| `pipo_dice` con ventana | cada globo puede ser un mapa `{texto, desde, hasta, cara, lado}`: **entre ventanas no hay globo y Pipo desaparece de escena**. La `cara` del globo manda sobre la de `pipo_asoma`. |
| `piezas` sueltas que se encienden | `brillo` (0..1, o `sube`/`baja`) y `brillo_color` (`salvia` \| `blanco`) también en `piezas` y en `prop`. **El teléfono que desconecta usa `props/telefono_4`, la pantalla blanca fría**: el salvia es el color del presente. |
| `cierre: {dice, pipo, textos}` | el globo de Pipo a cámara antes del iris (ahí va el mensaje de la cuenta), cuánto dura, y los cinco renglones de la contratapa si alguna vez hiciera falta cambiarlos. |
| `cuerpo` / `cara` como **lista** | poses o caras que **alternan** dentro del mismo cuadro cada `ritmo` hojas (3 por defecto): la sesión de fotos, el que gesticula. Distinto de `ciclo: true`, que es el ciclo de caminata `_0..3`. |

**Regla del guion (el tempo, WS34):** pocas imágenes, **6-8 por volumen**, cada una **30-45
hojas (3-4,5 s)**: ≥30 con un globo, ≥40 con dos. Si algo tiene que moverse mucho, se mueve
el fondo (§2); lo demás lo mueve la vida del cuadro (§5).

### La escena de la magia

Es un **paquete fijo** (WS33, recortado en la WS34): (1) el teléfono se enciende = SOLO la
hoja "acerca" del teléfono poniéndose verde, Pipo asoma con duda · (2) Teo carga el aura con
la acción del menú · (3) Teo escribe y la burbuja muestra el descubrimiento del volumen ·
(4) **el resultado**: Teo con el aura desplegada haciendo la acción que muestra el cambio.
Cuatro imágenes, 13,2 s. Solo se declaran los tres huecos: `accion`, `burbuja` y
`resultado` (antes `final`, sigue aceptado). `textos:` y `hojas:` (claves `enciende`,
`accion`, `escribe`, `resultado`) permiten ajustar los globos y las duraciones fijas. Un dibujo
nuevo para la burbuja se agrega como función en `motor/libro.py` y se registra en `DIBUJOS`
(hay: `abuelos`, `familia_riendo`, `corazon`).

**El momento 1, dos modos (WS35):** `enciende: zoom` (por defecto, la hoja "acerca" del
teléfono grande) o **`enciende: en_mano`**, que clona el cuadro ANTERIOR y le pone verde el
teléfono que el personaje ya tiene en la mano (el prop `telefono_*` pasa a `telefono_2/3`,
1,45× más grande y con **resplandor salvia + rayitos**: a la escala de la mano el verde solo
no se lee). No corta la escena: es la misma imagen, y es lo que pidió Tomás para el vol. 1.

**El momento 2 puede llevar SU burbuja** (`burbuja_accion`, `burbuja_accion_pos`) y su cara
de Pipo (`cara_accion`): en el vol. 1, meditando ve a la familia riéndose y Pipo se
sorprende. El hueco `resultado` hereda `teo`, `pipo`, `props`, `piezas`, `secundarios`,
`hojas` y `globo_desde`.
