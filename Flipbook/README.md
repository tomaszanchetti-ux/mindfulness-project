# Flipbook — el libro animado de Dwellia (Bloque D)

Serie de **libros animados para hojear** de 25-30 s, verticales, para TikTok: **"El diario de
Pipo"**. Pipo (el pug) narra con humor cómo Teo (el héroe) se pierde en la vida moderna y
crece con cada Pausa; Dwellia es la magia que lo impulsa y solo se nombra en la contratapa. El concepto completo está en [`CONCEPTO.md`](CONCEPTO.md); las
reglas de dibujo y animación, en [`REGLAS.md`](REGLAS.md).

Estado (WS31 · 07/09/2026): **Bloque D en curso.** D0 cerrada: el formato v2 (5 escenas,
cartel variable, cierre fijo con iris, banco de ideas por volumen) es la definición
principal y vive en `guiones/00_FORMATO_Y_OPUESTOS.md`. Sigue **D1.1** (las 6 caras y poses
de Pipo, pulir a Teo) y **D1.2** (la fábrica: cartel, cierre, biblioteca de gestos, guion en
archivo). Contrato en `WS/WS31_07-09-2026.md` §3.

## Carpetas

| Carpeta | Qué hay |
|---|---|
| `CONCEPTO.md` | El concepto (estructura del volumen, arco por pilares, decisiones). |
| `REGLAS.md` | La gramática visual: cómo se dibuja y se anima para que se lea como flipbook Dwellia. |
| `personajes/` | Una **ficha** por personaje (`teo.md`, `pipo.md`) + la hoja de personajes dibujada. La plantilla para uno nuevo es `_plantilla.md`. |
| `guiones/` | **`00_FORMATO_Y_OPUESTOS.md` = el componente central (v2)**: las 5 escenas, el cartel y el cierre, los 6 pilares con su banco de ideas y memes replicables, las caras de Pipo, la biblioteca de gestos de Teo y dónde va Dwellia en TikTok. Después, un archivo por volumen (`vol01_lunes.md` es solo el boceto de mecánica de la WS26). |
| `motor/` | `render.py` renderiza un volumen (hojas → ffmpeg → mp4). `inventario.py` lista qué personajes tienen fotos y ficha. |
| `pruebas/` | Las pruebas de la WS26 (mp4 fuera del repo, hojas de contacto dentro). |
| `../Tiktok/` | **La bandeja de entrada de Tomás** (fuera del repo): una subcarpeta por personaje (`teo/`, `pipo/`) y `Ideas/` para material general de estilo (portadas, auras, viñetas que gusten). |

## Cómo cargar un personaje nuevo (el "producto", versión simple)

1. Creá `Tiktok/<nombre>/` y dejá ahí 2-4 fotos o dibujos de referencia (de frente y de
   costado si se puede). Sirven también recortes de estilo que te gusten.
2. Copiá `personajes/_plantilla.md` a `personajes/<nombre>.md` y completá lo que sepas:
   quién es en la historia, en qué volumen entra, qué lo hace reconocible. Si no sabés,
   dejalo en blanco: se completa en la sesión.
3. En la siguiente sesión, Claude mira las fotos, saca **3 rasgos fijos** siguiendo
   `REGLAS.md`, dibuja la marioneta en `motor/render.py`, y agrega el personaje a la hoja de
   personajes para que lo apruebes. Recién entonces entra a un guion.

Así funcionó con Teo y Pipo: fotos en `Tiktok/teo/` y `Tiktok/pipo/` → rasgos → marioneta →
hoja de personajes (`personajes/hoja_de_personajes_v1.png`) → Volumen 1.

Corrección clara: la transformación foto → dibujo la hace Claude en la sesión leyendo la
imagen; no hay un botón que lo haga solo. Lo que sí queda automático es lo caro: una vez
dibujada la marioneta, cada volumen nuevo se renderiza en minutos.

## Cómo se renderiza un volumen

```bash
python3 Flipbook/motor/render.py Flipbook/salida/vol01.mp4 Flipbook/personajes/hoja_de_personajes.png
```

Sale un mp4 1080×1920 a 30 fps (10 hojas por segundo, cada hoja con su cuadro en vuelo) más
la hoja de personajes actualizada. La música se elige al subir a TikTok.

## Cómo se ve el inventario

```bash
python3 Flipbook/motor/inventario.py
```

Lista cada personaje con sus fotos de referencia, si tiene ficha y si ya está dibujado en el motor.
