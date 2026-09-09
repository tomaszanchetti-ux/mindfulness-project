# El formato corto: la PÍLDORA (D2 · WS36)

> **Decisión de Tomás, 09/09/2026.** El vol. 1 (30,7 s, formato largo de 5 escenas) midió
> 3,64 s de tiempo medio y 1,7 % de completado. En vez de insistir con volúmenes largos,
> **plagamos TikTok de mini-videos**: un chiste, dos imágenes, el mensaje, y afuera.
> El formato largo NO se tira: queda para cuando una historia lo merezca. Se va soltando de
> a poco, con distintos enfoques. Esto es lo que se publica seguido.

## Qué es una píldora

**10-14 segundos. Dos imágenes. Un solo chiste.** El mismo lugar visto por los dos:

| # | Imagen | Qué pasa | Dur. |
|---|---|---|---|
| 1 | **Teo, el humano moderno** | Hace la cosa de todos los días, exagerada, **y la hace EN MOVIMIENTO** (poses que alternan, la cámara que empuja). Un globo de Pipo, ≤8 palabras. | 4-5 s |
| 2 | **Pipo, en el mismo lugar** | Lo mismo, pero como lo hace un perro: bien, sin esfuerzo, feliz. Un globo, ≤8 palabras. | 4-5 s |
| 3 | **El cierre** (el de siempre) | Pipo a cámara → iris → contratapa: Dwellia y la Pausa. | 3,7 s |

Reglas duras (salen de los números del vol. 1, `REGLAS.md` §3):
- **La imagen 1 abre el video, con su globo ya puesto.** El título va de rótulo arriba.
- **Ningún cuadro quieto** (la ley del movimiento). En la píldora se nota el doble: con dos
  imágenes, si una está congelada, medio video está congelado.
- **Nada de escena de la magia, nada de resultado.** El mensaje vive en el contraste, en la
  contratapa y en la descripción. La emoción es el remate, no una escena aparte.
- **El cartel se sube como PORTADA**, no se emite.
- La imagen 2 y la 1 son **el mismo lugar**: el bucle empalma solo.

## El banco de píldoras

El pilar da el tema; cada pilar puede dar varias píldoras. `✅` = **no hay que dibujar nada**,
solo escribir el YAML.

| # | Píldora | Teo | Pipo | Lugar | Piezas |
|---|---|---|---|---|---|
| 1 | **Mil selfies** (amor propio) | se saca cuarenta fotos buscando el ángulo | se mira una vez, se ve horrible y se encanta | `espejo_bano` | brazo con teléfono · cara de pico · Pipo aplastado |
| 2 | **Meditar** (sentido) | no aguanta quieto: se rasca, mira el reloj, espía el teléfono | `buda`, inmóvil, después la V de la victoria | `habitacion` | ✅ ninguna |
| 3 | **El paseo** (perspectiva) | camina rápido mirando el teléfono, tira de la correa | `plantado`, cuatro minutos en la misma flor | `banco_plaza` | ✅ ninguna |
| 4 | **La caída** (resiliencia) | un mal día y se derrumba | se cae del sofá, se levanta y sigue. Tres veces | `sofa` | ✅ ninguna |
| 5 | **Escribir** (gratitud) | mil notas, listas, recordatorios, nada le alcanza | una croqueta y le cambia el día | `mesa_familiar` | plato de croquetas (prop simple, ya existe) |
| 6 | **El café** (gratitud) | café perfecto, sol, y él mirando vacaciones ajenas | el mismo plato de siempre, como una fiesta | `mesa_familiar` | ✅ ninguna |

El número del rótulo es el **orden de publicación**, no el de esta tabla.

## Cómo se hace una píldora

1. Elegir del banco. Si no pide piezas, se salta el paso 2.
2. Dibujar lo que falte (≤3 piezas, `motor/partes.py`).
3. Escribir `guiones/pNN_nombre.yaml` (2 cuadros + cierre) y renderizar.
4. Mirar el mp4 a resolución completa. Descripción, comentario fijado y hashtags al pie del YAML.

```bash
python3 Flipbook/motor/libro.py Flipbook/guiones/p01_selfies.yaml
```
