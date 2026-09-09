# El formato corto: la PÍLDORA (D2 · WS36)

> **Decisión de Tomás, 09/09/2026.** El vol. 1 (30,7 s, formato largo de 5 escenas) midió
> 3,64 s de tiempo medio y 1,7 % de completado. En vez de insistir con volúmenes largos,
> **plagamos TikTok de mini-videos**: un chiste, dos imágenes, el mensaje, y afuera.
> El formato largo NO se tira: queda para cuando una historia lo merezca. Se va soltando de
> a poco, con distintos enfoques. Esto es lo que se publica seguido.

## El mensaje general de la cuenta (el norte de TODO)

> **Tomás, 09/09/2026.** Todas las píldoras tienden a lo mismo, y ninguna se publica si no
> tira para este lado:
>
> ### **Vivir el momento presente. Y cómo una Pausa y escribir en un diario te acercan a él.**
>
> Ese mensaje **no se explica en un video: se construye con muchos**. Cada píldora aporta una
> astilla — una forma concreta en la que la vida moderna nos saca del presente y una forma
> concreta en la que Pipo ya está ahí. La cuenta entera es el mensaje; el video es la astilla.

Cómo aterriza en cada pieza, en orden de importancia:

1. **El último globo de Pipo** es el que nombra el presente. Es el remate y es la tesis:
   *"yo no medito. yo ya estoy aquí."* No es una moraleja pegada: es el chiste bien puesto.
2. **La contratapa** (lo único que dice Dwellia): **"una Pausa al día / para volver al
   presente"** · la D · Dwellia · *"una línea escrita, fuera del teléfono"* · link en la bio.
   Nombra las dos herramientas del producto: **la Pausa** y **escribirla**.
3. **La descripción y el comentario fijado**, donde vive el texto lindo que no cabe en el video.

**Las dos clases de píldora**, y hay que ir alternando:

| Clase | Qué hace | Imágenes | Cuándo |
|---|---|---|---|
| **A · El contraste** | Teo se pierde el presente / Pipo ya está en él. El mensaje queda implícito, el video es puro chiste. | 2 | La mayoría. Es lo que se comparte. |
| **B · La Pausa** | Igual, pero Teo **se detiene y escribe una línea** en el cuadernito, y el mundo se le abre. Nombra la herramienta. | 3 | Una de cada tres. Es lo que explica de qué va la cuenta. |

Si solo hubiera píldoras A, la cuenta sería graciosa y nadie sabría para qué existe. Si solo
hubiera B, sería un anuncio. La proporción es el producto.

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
- **En las píldoras A no hay escena de la magia ni resultado.** El mensaje vive en el último
  globo, la contratapa y la descripción. En las **B**, la tercera imagen ES la Pausa: Teo
  deja el teléfono, escribe una línea en el cuadernito, y ahí sí aparece el aura.
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
| 5 | **Escribir** (gratitud) · **clase B** | mil notas, listas, recordatorios, nada le alcanza | una croqueta y le cambia el día | `mesa_familiar` | plato de croquetas (prop simple, ya existe) |
| 7 | **La Pausa** (clase B, la píldora madre) | scrollea sin fin, la cara vacía | espera al lado, tranquilo | `sofa` | ✅ ninguna (cuadernito ya existe) |
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
