# Flipbook — el libro animado de Dwellia (Bloque D)

Serie de **libros animados para hojear** de 25-30 s, verticales, para TikTok: **"El diario de
Pipo"**. Pipo (el pug) narra con humor cómo Teo (el héroe) se pierde en la vida moderna y
crece con cada Pausa; Dwellia es la magia que lo impulsa y solo se nombra en la contratapa. El concepto completo está en [`CONCEPTO.md`](CONCEPTO.md); las
reglas de dibujo y animación, en [`REGLAS.md`](REGLAS.md).

Estado (WS36 · 09/09/2026): **D2 son PÍLDORAS.** El vol. 1 se publicó y midió **3,64 s de
tiempo medio sobre 30,7 s** (11,8 % de retención, 1,7 % de completado): la gente se iba
durante el cartel, antes del primer chiste. De ahí salió todo lo de la WS36 — el envase del
feed (el cartel pasa a ser PORTADA y el título va de rótulo sobre la primera imagen; el
cierre baja a 3,7 s), la **ley del movimiento** (ningún cuadro quieto), y el cambio de plan:
**muchos mini-videos de 10-14 s, un chiste cada uno**, en vez de seis volúmenes largos. El
formato largo no se tira: queda para cuando una historia lo merezca.

**Leer primero [`guiones/00_FORMATO_CORTO.md`](guiones/00_FORMATO_CORTO.md)**: el mensaje
general de la cuenta, la regla de oro (**una escena, bien hecha**), la gramática
conexión/desconexión y el banco de píldoras. La gramática visual sigue en
[`REGLAS.md`](REGLAS.md) y el formato largo en `guiones/00_FORMATO_Y_OPUESTOS.md`.

Hechas: **`p01_espejo`** ("EL DILEMA DEL ESPEJO", 10,9 s) y **`p02_meditar`** ("CINCO MINUTOS
DE PAZ", 12,8 s), cada una con su portada. El vol. 1 largo sigue en `vol01_vinculos`.
El detalle de cómo se llegó está en `WS/WS31` a `WS/WS36`.

## Cómo se hace un volumen nuevo (D2, una WS por historieta)

1. **El guion, en papel primero:** título satírico, el problema en 2 imágenes (la escena y
   el zoom que delata), el espejo en 1, los tres huecos de la magia (la acción · la burbuja
   · el resultado) y los globos de Pipo (≤12 palabras cada uno). Banco de ideas por pilar en
   `00_FORMATO_Y_OPUESTOS.md` §5.
2. **Lo que rodea a esa historia se dibuja en la WS:** ≤2-3 poses nuevas de Teo o Pipo, el
   elemento clave del volumen y los secundarios con detalle (todo en `motor/partes.py`, se
   regenera con `python3 Flipbook/motor/partes.py`). Fondos y props simples van en
   `motor/libro.py` (`FONDOS`, `PROPS_SIMPLES`, `DIBUJOS`).
3. **El guion en YAML** (`guiones/volNN_nombre.yaml`, vocabulario en `REGLAS.md` §7) →
   `--solo-cuadros` para revisar la lectura → el video → Tomás valida mirando el mp4.
4. La descripción del video, el comentario fijado y los hashtags van al final del guion.

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `CONCEPTO.md` | El concepto (estructura del volumen, arco por pilares, decisiones). |
| `REGLAS.md` | La gramática visual: cómo se dibuja y se anima para que se lea como flipbook Dwellia. |
| `personajes/` | Una **ficha** por personaje (`teo.md`, `pipo.md`) + la hoja de personajes dibujada (`hoja_de_personajes_v2.png`). **`partes/`** = las piezas ilustradas (SVG + PNG transparente + `partes.json` con las anclas), generadas por `motor/partes.py`. La plantilla para un personaje nuevo es `_plantilla.md`. |
| `guiones/` | **`volNN.yaml` = el guion de cada volumen, lo que lee `motor/libro.py`** (`vol00_prueba.yaml` es el de prueba de la fábrica). **`00_FORMATO_Y_OPUESTOS.md` = el componente central (v2)**: las 5 escenas, el cartel y el cierre, los 6 pilares con su banco de ideas y memes replicables, las caras de Pipo, la biblioteca de gestos de Teo y dónde va Dwellia en TikTok. Después, un archivo por volumen (`vol01_lunes.md` es solo el boceto de mecánica de la WS26). |
| `motor/` | **`libro.py` = la fábrica: lee un guion YAML y escribe el mp4 completo** (cartel · hojas · magia · cierre; los globos, la vida del cuadro, los fondos y props simples) · `partes.py` dibuja las piezas ilustradas (capa de detalle: caras, cuerpos, props) · `marioneta.py` las compone en una hoja (anclas, temblor, aura, cabeceo, cabeza delante o detrás) · `hoja.py` arma la hoja de personajes y el video de prueba · `magia.py` = guion de prueba de la escena de la magia (referencia de dibujo) · `render.py` = los helpers de papel, línea y libro de la v1 · `fuentes/` = Fraunces Italic (la D de la contratapa) · `inventario.py` lista qué personajes tienen fotos y ficha. |
| `pruebas/` | Las salidas del motor: `<nombre>.mp4` (fuera del repo) y `<nombre>_cuadros.png` (la hoja de revisión, dentro) · `cartel_vol00.png` (la viñeta del cartel) · `caras_pipo.mp4` y `magia.mp4` (pruebas de las piezas). |
| `cuenta_tiktok.md` | **Cómo abrir la cuenta de Teo y Pipo** y qué poner (handle, nombre, bio, avatar, los pasos), con las reglas de TikTok verificadas el 08/09/2026. |
| `../Tiktok/` | **La bandeja de entrada de Tomás** (fuera del repo): una subcarpeta por personaje (`teo/`, `pipo/`) y `Ideas/` para material general de estilo (portadas, auras, viñetas que gusten). |

## Cómo cargar un personaje nuevo (el "producto", versión simple)

1. Creá `Tiktok/<nombre>/` y dejá ahí 2-4 fotos o dibujos de referencia (de frente y de
   costado si se puede). Sirven también recortes de estilo que te gusten.
2. Copiá `personajes/_plantilla.md` a `personajes/<nombre>.md` y completá lo que sepas:
   quién es en la historia, en qué volumen entra, qué lo hace reconocible. Si no sabés,
   dejalo en blanco: se completa en la sesión.
3. En la siguiente sesión, Claude mira las fotos, saca **3 rasgos fijos** siguiendo
   `REGLAS.md`, dibuja las piezas en `motor/partes.py` (SVG parametrizado → PNG), y agrega el
   personaje a la hoja de personajes para que lo apruebes. Recién entonces entra a un guion.

Así funcionó con Teo y Pipo: fotos en `Tiktok/teo/` y `Tiktok/pipo/` → rasgos → piezas →
hoja de personajes (`personajes/hoja_de_personajes_v2.png`), aprobada en 4 vueltas.

Corrección clara: la transformación foto → dibujo la hace Claude en la sesión leyendo la
imagen; no hay un botón que lo haga solo. Lo que sí queda automático es lo caro: una vez
dibujada la marioneta, cada volumen nuevo se renderiza en minutos.

## Cómo se renderiza un volumen

Un volumen se escribe en un **guion YAML** (`guiones/volNN.yaml`) y se renderiza sin tocar
código. El vocabulario del guion está en [`REGLAS.md`](REGLAS.md) §7.

```bash
python3 Flipbook/motor/libro.py Flipbook/guiones/vol00_prueba.yaml
python3 Flipbook/motor/libro.py Flipbook/guiones/vol00_prueba.yaml --solo-cuadros
```

Salen `pruebas/<nombre>.mp4` (1080×1920 a 30 fps, 10 hojas por segundo, cada hoja con su
cuadro en vuelo, cartel de apertura y cierre fijo) y `pruebas/<nombre>_cuadros.png`, la hoja
fija con un cuadro clave de cada cuadro para revisar la lectura sin abrir el video. La música
se elige al subir a TikTok.

El motor v1 de palitos (`motor/render.py`) queda solo como biblioteca de helpers (papel,
línea, temblor, taco de hojas, cuadro en vuelo); sus escenas y personajes ya no se usan.

## Lo que el motor sabe hacer hoy (D1.2 · WS33-34)

- **Piezas:** Pipo = 6 caras + 12 cuerpos (sentado · camina ×4 · panza arriba · plantado ·
  cae · corre · buda · buda con la V) · Teo = 25 caras + 2 con el pelo caído + 11 cuerpos
  (parado · encorvado · sentado · sentado erguido · medita · camina ×4 · corre · **spiderman**)
  · props ilustrados: el teléfono en 4 niveles (se pone verde a nivel pantalla) y el
  cuadernito · **grupos** (piezas compuestas que se pegan con `piezas:`): la familia del
  vol. 1 en dos estados (living y mesa) y las chicas que pasan de largo.
- **La escena de la magia** como paquete fijo de 4 imágenes con 3 huecos (`accion` ·
  `burbuja` · `resultado`). El aura sale de la silueta, sirve en cualquier pose. El teléfono
  se enciende con zoom o **en la mano, sobre la misma imagen** (con resplandor salvia).
- **Los globos de Pipo:** hasta 12 palabras, uno o varios sobre la misma imagen, entran 0,5 s
  después de la imagen. **Van ABAJO de la escena** (caja apaisada con la colita subiendo a
  Pipo), y la escena sube 220 px para quedar en la zona segura de TikTok.
- **La vida del cuadro:** cabeceo automático, el globo flota, temblor de línea, props con ciclo.
- **Cartel** (cuarta tinta + formas + título, viñeta fija a lo Tintín) y **cierre fijo** (Pipo
  pícaro · iris · tapa · contratapa con la D de la app).
- **Hoja de revisión** con un cuadro clave por globo, para leer un volumen sin abrir el video.

## Cómo se ve el inventario

```bash
python3 Flipbook/motor/inventario.py
```

Lista cada personaje con sus fotos de referencia, si tiene ficha y si ya está dibujado en el motor.
