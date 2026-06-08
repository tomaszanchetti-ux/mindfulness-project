# Prompt maestro — Dibujos de categoría (Claude Design)

Reusable para las 6 categorías. Se trabaja **de a una**: se pega el bloque
maestro + la línea de la categoría, se itera en Claude Design hasta que sale bien,
se exporta el SVG a `../assets/cartas/cat_<nombre>.svg`, y recién ahí se pasa a la
siguiente. **Gratitud es la primera** (valida el estilo para todo el set).

> Referencia de estilo cerrada: `../00_Estetica_Carta.md`.

---

## Bloque maestro (igual para las 6)

```
Necesito una ilustración para una app de mindfulness. Voy a pedirte varias, una
por vez, y TODAS tienen que compartir el mismo sistema visual para que sean un set
coherente. Seguí estas reglas al pie:

SISTEMA VISUAL (idéntico en todas)
- Estilo: ilustración precisa con textura de acuarela suave; elegante, serena,
  contemplativa; sensibilidad minimalista japonesa. Trazo fino y seguro.
- Color: TODO el dibujo en negro neutro (#2b2925). UN solo elemento se pinta en el
  color de acento que te indico abajo; nada más lleva color. El acento es un wash
  de acuarela suave, de valor claro y contenido (no saturado).
- Composición centrada, con mucho aire alrededor. Mismo peso de línea y misma
  textura de pincel en todas las ilustraciones del set.
- Sin texto, sin marco y sin fondo: fondo 100% transparente, sólo el dibujo.

FORMATO DE SALIDA
- Entregá un SVG listo para descargar, con viewBox "0 0 120 120", centrado y con
  padding parejo.
- Para poder recolorear el acento sin tocar el resto: poné el/los elementos con
  acento dentro de un grupo <g class="accent" fill="VAR(--accent)"> y el resto del
  dibujo en #2b2925.
- Si la textura de acuarela no se logra bien en vector, entregá igual el SVG (con
  filtros) y, como alternativa, un PNG de fondo transparente en alta resolución.

ILUSTRACIÓN A GENERAR:
{AQUÍ VA LA LÍNEA DE LA CATEGORÍA}
```

## Líneas por categoría (la variable)

| Categoría | Línea a pegar |
|-----------|----------------|
| **Gratitud** *(primera)* | Categoría "Gratitud". Motivo: un amanecer — el sol naciendo sobre un horizonte, con un par de colinas suaves y unos pocos rayos sobrios. Elemento con acento: el SOL, en amarillo opaco (#E0A92E). Sensación: calidez y agradecer lo pequeño que sostiene. |
| **Calma** | Categoría "Calma". Motivo: la luna llena sobre el agua, con olas suaves; el agua apenas sombreada para que el reflejo lea en negativo. Elemento con acento: el REFLEJO de la luna sobre el agua, en blanco (#FFFFFF). Sensación: quietud, bajar el ritmo. |
| **Perspectiva** | Categoría "Perspectiva". Motivo: una cadena de montañas vista desde lejos, paisaje amplio con horizonte. Elemento con acento: UNA montaña (o su cima), en marrón (#8A5A3B). Sensación: mirar lo de hoy desde más lejos, con aire. |
| **Resiliencia** | Categoría "Resiliencia". Motivo: una pequeña planta que brota entre dos piedras. Elemento con acento: la PLANTA, en verde (#5E8C4E). Sensación: sostenerse y reponerse en lo difícil. |
| **Amor propio** | Categoría "Amor propio". Motivo: una flor abriéndose. Elemento con acento: el CENTRO / un detalle de la flor, en rosa (#D98AA6). Sensación: trato amable y honesto con uno mismo. |
| **Vínculos** | Categoría "Vínculos". Motivo: dos pájaros cerca uno del otro. Elemento con acento: el ALA (o un detalle) de UNO de los pájaros, en rojo (#C8453E). Sensación: cercanía con las personas que importan. |

## Al recibir el SVG

1. Guardar como `../assets/cartas/cat_<nombre>.svg`.
2. Chequear: fondo transparente · sin texto · viewBox `0 0 120 120` · acento en `<g class="accent">`.
3. Si Gratitud sale bien → mismo bloque maestro para la siguiente. Si no, se ajusta el bloque maestro (vale para todas).
