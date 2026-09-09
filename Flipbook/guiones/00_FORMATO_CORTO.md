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

## La gramática de la serie (el patrón que se repite SIEMPRE)

> **Tomás, 09/09/2026.** Habrá escenas de conexión y escenas de desconexión, en mil
> situaciones distintas — pero lo que se repite, píldora tras píldora, es esto:

| | Pipo | Teo |
|---|---|---|
| **CONEXIÓN** — algo que lo trae al presente (meditar, escribir, mirar a alguien, oler una flor) | **contento** | **aura verde** y la boca sonriendo |
| **DESCONEXIÓN** — algo que se lo lleva (el teléfono, la comparación, la queja, el piloto automático) | **enojado** | **triste, sin aura** |

Eso es lo que enseña a leer la cuenta sin explicar nada: a la tercera píldora, cualquiera
sabe qué significa el verde. **No es decoración: es el idioma.**

Está metido en el motor, no en la buena voluntad del guionista: se escribe `estado:
conexion` o `estado: desconexion` en el cuadro y el motor pone el aura, la boca de Teo y la
cara de Pipo. El guion sigue eligiendo la MIRADA (`cerrada`, `abajo`, `costado`…) y puede
pisar cualquier cosa a mano (`boca_libre: true`, o una `cara` explícita en Pipo).

**El teléfono que desconecta se enciende BLANCO, nunca verde** (`props/telefono_4`): el
salvia es el color del presente y de Dwellia; lo que te saca del presente no puede usar el
color del presente. Es la misma regla vista desde el otro lado.

## Qué es una píldora

**10-14 segundos. Dos imágenes. Un solo chiste.** El mismo lugar visto por los dos:

| # | Imagen | Qué pasa | Dur. |
|---|---|---|---|
| 1 | **UNA situación, con un beat adentro** | No dos láminas: una sola escena que **cambia de estado** delante de la cámara. Teo empieza conectado (aura) y algo se lo lleva, o al revés. El cambio se cuenta en 3-4 cuadros del mismo lugar: el estado, el disparador, el movimiento, el resultado. | 7-9 s |
| 2 | **Pipo entra y sale** | Aparece para comentar y **se va** (`desde`/`hasta` en su globo), y vuelve con la otra cara cuando la cosa cambió. Dos globos, ≤8 palabras cada uno. | (sobre la misma escena) |
| 3 | **El cierre** | Pipo a cámara **con su globo**: ahí va el mensaje de la cuenta, y el iris se cierra sobre eso. Después, el cierre de siempre: "Teo y Pipo volverán próximamente" y el bloque de Dwellia — **eso no se toca**. | 5,3 s |

Reglas duras (salen de los números del vol. 1, `REGLAS.md` §3):
- **La imagen 1 abre el video, con su globo ya puesto.** El título va de rótulo arriba.
- **Ningún cuadro quieto** (la ley del movimiento). En la píldora se nota el doble: con dos
  imágenes, si una está congelada, medio video está congelado.
- **Nada de escena de la magia.** El mensaje vive en el globo del cierre y en la descripción.
  En las píldoras **B**, la conexión ES la acción: Teo deja el teléfono, escribe una línea en
  el cuadernito, y ahí aparece el aura verde. Es la gramática, no una escena aparte.
- **Menos escenas, mejores escenas.** Antes que agregar una lámina, hacer que la que hay
  cambie: es lo que separa un video de una ilustración con texto.
- **El cartel se sube como PORTADA**, no se emite.
- La imagen 2 y la 1 son **el mismo lugar**: el bucle empalma solo.

## El banco de píldoras

El pilar da el tema; cada pilar puede dar varias píldoras. `✅` = **no hay que dibujar nada**,
solo escribir el YAML.

| # | Píldora | Teo | Pipo | Lugar | Piezas |
|---|---|---|---|---|---|
| 1 | **Mil selfies** (amor propio) ✅ **HECHA** (`p01_selfies`, 13,6 s) | se saca cuarenta fotos buscando el ángulo | pega la cara al vidrio, se ve horrible y le encanta | `espejo_bano` | `selfie` + `selfie_flex` + boca `pico` (dibujadas) |
| 2 | **Meditar** (sentido) ✅ **HECHA** (`p02_meditar`, 12,8 s) | medita en paz hasta que el teléfono se enciende y le gana | asoma, anuncia "toma uno" y vuelve enojado | `habitacion` | `medita_toma` (dibujada) |
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
