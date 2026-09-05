# El libro de Dwellia — concepto v1 (WS26 · 05/09/2026)

> Estado: **cerrado como base** por Tomás (05/09): el formato, los personajes y la manera de
> contar. **Los guiones NO están fijos**, ni el del Volumen 1: todo lo de esta sesión es
> conceptual y los volúmenes se trabajan desde cero para que sean representativos. Se ejecuta como Bloque D, después de B y C.
> Pruebas: `pruebas/flipbook_poc.mp4` (mecánica, 8 s) · `pruebas/flipbook_v2.mp4` (estructura de libro, 23 s) · **`pruebas/flipbook_v3.mp4` (Teo y Pipo + historia abstracta, 24 s · la vigente; motor en `motor/render.py`)**. Los mp4 no van al repo; se regeneran con el motor.

## 1. Qué es
Una serie de **libros animados para hojear** (flipbook) de 15-30 s, verticales, para TikTok.
Cada video es un **volumen** de la misma historieta: un personaje entrañable que va creciendo
capítulo a capítulo. Dwellia vive **dentro** de la historia como el elemento mágico que lo
impulsa (algo que se enciende de verde), y solo se nombra en la contratapa.

Lo que lo hace leerse como flipbook, y que cuesta poco: pocas hojas por segundo (10), la
línea que tiembla porque cada hoja está "redibujada", papel con número de página, taco de
hojas que se achica, el pulgar que las pasa, y una hoja en vuelo en cada pase.

## 2. Estructura de cada volumen (lo que muestran `pruebas/flipbook_v2.mp4` y `pruebas/flipbook_v3.mp4`)
| Parte | Duración | Qué pasa |
|---|---|---|
| **Portada** | 2 s | Tapa de cartón: "VOLUMEN N · Título", viñeta redonda con el personaje, "capítulo N · día". Es el gancho: la primera cosa que se ve en el feed. |
| **Historia** | 15-20 s | Hojas del flipbook. 4-6 escenas, texto mínimo en pantalla (sin voz). Algo se enciende de verde en algún momento y cambia el rumbo del día. |
| **Cierre** | 4 s | La última hoja se sostiene medio segundo, la tapa se cierra (1 s), contratapa: hoja salvia + "Dwellia · una Pausa al día, fuera del teléfono" + "continúa en el volumen N+1" + "link en la bio". |

## 3. La historia: arco del personaje sobre los 6 pilares
**Decisión de Tomás (05/09): sin carta ni objeto literal de la app.** Dwellia dentro de la
historia es abstracta y mágica: el personaje toma algo parecido a un teléfono, ese algo se
enciende de verde (salvia), el ruido mental se disuelve, hace la actividad, escribe, y después
se lo ve con un aura distinta haciendo un acto que lo demuestra (vol. 1: camina erguido y
saluda a alguien que pasa). Está en `pruebas/flipbook_v3.mp4`.

Una **temporada = 6 volúmenes**, uno por pilar de la app, en el orden del reloj del onboarding:
amor propio · gratitud · vínculos · sentido · perspectiva · resiliencia.
Cada volumen presenta un secundario nuevo ligado al pilar (el perro, los padres, el jefe, la
vecina, un desconocido) y deja al protagonista un poco distinto de como empezó.


Tono: suave, con humor de gesto (no de chiste), nunca sermón. Regla de oro de cada capítulo:
un problema chiquito y reconocible en la primera hoja, algo que se enciende, un gesto, un final abierto.

## 4. Personajes
**Referencias (05/09):** fotos en `Tiktok/` (Tomás + su pug). Rasgos tomados para el personaje
ficticio: pelo ondulado con volumen hacia un lado (3 bucles), cara alargada, barba de pocos
días (puntitos), anteojos de sol apoyados sobre el pelo como prop fijo, cuerpo delgado. El
perro es un **pug**: cuerpo redondo, máscara negra sólida, orejas negras plegadas, ojos
grandes, cola enrulada, **collar salvia** (el acento de color). Hoja de personajes:
`personajes/hoja_de_personajes_v1.png`. **Nombres (05/09): Teo y Pipo.** Pendiente: pulir el pelo de Teo (hoy parece un gorro) y una pasada de edición de ambos con material de referencia.

- **Uno principal**, diseñado con cuidado, con **3 rasgos fijos** que se reconozcan hoja a hoja
  (en la v3: el pelo con volumen, los anteojos de sol sobre el pelo, la barba de puntitos). Ficticio, con nombre propio;
  puede inspirarse en una foto real de Tomás y su perro como referencia de rasgos (silueta,
  pelo, lentes, barba, raza y orejas del perro), pero **no es Tomás**: es un personaje.
- **Secundarios** que entran de a uno por volumen: el pug (desde el vol. 1, collar salvia como
  marca), padres, jefe, vecina, etc.
- Estilo: línea tierra sobre papel crema, un solo acento de color salvia por hoja (el collar del
  pug, el sol, el objeto encendido, el aura, la hoja).

## 5. La fábrica (Bloque D1b, reescrito)
Pipeline ya probado en la Mac, sin instalar nada (Python + Pillow + ffmpeg):

1. **Guion** en texto: `volumen`, `título`, lista de escenas `(escena, duración, texto en pantalla, poses)`.
2. **Marionetas de partes** (personaje y secundarios dibujados una vez, por piezas) → cada hoja es
   una pose interpolada entre poses clave.
3. **Render hoja por hoja** con temblor de línea, papel, número, taco, pulgar, hoja en vuelo.
4. **Portada y contratapa** desde plantilla (título y número del volumen salen del guion).
5. **ffmpeg** → mp4 1080×1920 listo para subir. Música se elige al subir (TikTok).

Costo por volumen nuevo una vez diseñados los personajes: minutos de render, una sesión de
guion + ajuste de poses. Descartado generar cada hoja con IA de imágenes: no mantiene el
personaje idéntico entre 60 hojas y el flipbook lo delata.

## 6. Decisiones (05/09)
1. Peso del pase de página: **aprobado** (1 cuadro en vuelo por hoja).
2. Dwellia en la historia: **abstracta y mágica**, sin carta (ver §3).
3. Nombres: **Teo** (protagonista) y **Pipo** (el pug). Fotos de referencia recibidas y usadas solo para rasgos.
4. Portada: **aprobada** así; ideas conceptuales de referencia se trabajan después.
5. Orden confirmado: este boceto → Bloque B → Bloque C → Bloque D completo.
