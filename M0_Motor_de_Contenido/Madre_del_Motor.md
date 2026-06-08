# Madre del Motor (M0)

La **lógica completa del Motor de Contenido**: cómo se modelan, se ven y se
producen las cartas. Es la referencia única del módulo.

> Contexto general: [`../00_Documento_Madre.md`](../00_Documento_Madre.md).

---

## 1. Modelo de contenido

La unidad es la **carta**: `categoría + modalidad + frase + micro-prompt + tono + color + dibujo`.

**Dos ejes (no un árbol):**
- **Categoría** = el *qué* (tema). La elige el usuario en el onboarding: **de 2 a 6**.
- **Modalidad** = el *cómo* (ejercicio). Es **propiedad de la carta**; el usuario NO la elige, la recibe.

**6 categorías × 5 modalidades.** El tono es interno (curaduría/filtrado), no se muestra.

**Matriz de afinidad** (✅ fuerte · ○ posible · · evitar) → **23 moldes viables**:

| Categoría | Escribir | Contemplar | Respirar | Caminar | Hacer |
|-----------|:--:|:--:|:--:|:--:|:--:|
| Gratitud | ✅ | ✅ | · | ○ | ✅ |
| Calma | ○ | ✅ | ✅ | ✅ | · |
| Perspectiva | ✅ | ✅ | ○ | ○ | · |
| Resiliencia | ✅ | · | ○ | ✅ | ○ |
| Amor propio | ✅ | ○ | ○ | · | ✅ |
| Vínculos | ✅ | ○ | · | · | ✅ |

**Profundidad:** arrancar con **3 a 5 cartas por molde**, sin agotar. El algoritmo
del día no repite carta (ventana ~60 días) **y** balancea la modalidad (que no
caigan varios días seguidos de la misma).

---

## 2. Reglas del Motor

Toda carta se mide contra esto. Si no las cumple, no entra.

**Calidad sobre cantidad.** Menos cartas pero coherentes y que de verdad ayuden.
- Cada carta justifica su existencia (si no aporta algo distinto, no entra).
- Una sola idea por carta. Micro-prompt concreto, hacible en ~10 min. Sin clichés.

**Invitación, nunca obligación.** Nadie se siente forzado.
- La actividad sugerida se mantiene **pura** (caminar es caminar; sin actividad supletoria).
- Única opcionalidad: **guardar sin hacer nada y sin probar** que se hizo.
- Sin supuestos (pareja, plata, clima, movilidad, estar bien). Cuidado emocional: invitar a mirar la fortaleza, no a abrir la herida. La frase sola ya vale.

---

## 3. Estética de la carta

Estilo **tarjeta japonesa**: papel crema, mínimo, elegante, mucho aire. Dos caras;
se **gira con un tap** (recibís la carta cerrada y la girás para ver la consigna).

```
        FRENTE                          DORSO (al girar)
┌───────────────────┐          ┌───────────────────┐
│███ franja color ██│          │███ franja color ██│ ← misma franja, da la vuelta
│   g r a t i t u d │ ←cat.    │  "A veces lo que  │ ← FRASE (protagonista, aire)
│        ☀          │ ←dibujo  │   más sostiene…"  │
│      categoría    │          │        ◡          │ ← glifo de acción (acento chico)
│  c o n t e m p l a r │ ←acción │  Mirá a tu…       │ ← micro-prompt
└───────────────────┘          └───────────────────┘
```

**Dos capas de estilo (regla clave):**
- **Dibujo de categoría:** preciso, acuarela, **todo en negro neutro** (`#2b2925`); el **color de la categoría pinta UN solo elemento**. Mismo valor y textura en las 6.
- **Glifo de acción:** minimalista, geométrico, un color (se pinta del color de la categoría), chico. No le roba protagonismo a la frase.

**Vocabulario cerrado**

| Categoría | Motivo | Acento (color) | | Acción | Glifo |
|-----------|--------|----------------|---|--------|-------|
| Gratitud | amanecer | el sol — amarillo `#E0A92E` | | Escribir | una pluma |
| Calma | luna sobre agua | la luna — azul-gris `#becdd7` | | Contemplar | un ojo |
| Perspectiva | montañas a lo lejos | una montaña — marrón `#8A5A3B` | | Respirar | círculos concéntricos |
| Resiliencia | planta entre piedras | la planta — verde `#5E8C4E` | | Caminar | pasos (chevrons) |
| Amor propio | flor abriéndose | el centro — rosa `#D98AA6` | | Hacer | un destello |
| Vínculos | dos pájaros | un ala — rojo `#C8453E` | | | |

Papel `#EFE6D3` · tinta `#2b2925`. La **franja superior** y el **glifo** usan el
color de la categoría. Tipografía: serif elegante para la frase (protagonista);
sans fina con tracking amplio para los nombres (`g r a t i t u d`).

---

## 4. Producción de los dibujos

Se trabaja **de a uno**. **Gratitud fue la primera** y validó el estilo del set.

> **Workflow real (desde WS01):** **ChatGPT rinde mejor que Claude Design** para
> estas ilustraciones. Salen como **PNG** (acuarela raster), a veces con un damero
> de fondo "horneado"; Claude lo **limpia a PNG transparente** y lo recorta →
> `assets/categorias/cat_<nombre>.png`. **Categorías = PNG** (acuarela). Los
> **glifos de acción = SVG** (geométricos, vienen después).

El bloque maestro de abajo sirve igual (para ChatGPT o Claude Design); lo que
importa es el sistema visual. **Qué debe entregar:** dibujo a línea fina en negro
(`#2b2925`) sobre fondo transparente, con UN solo elemento en el color de acento,
sin texto ni marco, centrado y cuadrado.

**Qué debe entregar:** SVG, fondo transparente, sin texto ni chrome de carta,
viewBox consistente (categorías `0 0 120 120` · acciones `0 0 90 90`), dibujo en
`#2b2925` y el **acento recoloreable** en `<g class="accent">`.

### Bloque maestro (igual para las 6 categorías)

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
{LÍNEA DE LA CATEGORÍA}
```

### Líneas por categoría (la variable)

- **Gratitud:** Categoría "Gratitud". Motivo: un amanecer — el sol naciendo sobre un horizonte, con un par de colinas suaves y unos pocos rayos sobrios. Acento: el SOL, en amarillo opaco (#E0A92E). Sensación: calidez y agradecer lo pequeño que sostiene.
- **Calma:** Categoría "Calma". Motivo: la luna llena sobre el agua, con olas suaves en línea negra. Acento: la LUNA, disco de acuarela azul-gris con textura/cráteres (#becdd7); el reflejo insinuado con líneas y grises suaves. Sensación: quietud, bajar el ritmo. *(El acento era "reflejo blanco"; se cambió a luna azul-gris porque el blanco no se ve sobre transparente/crema.)*
- **Perspectiva:** Categoría "Perspectiva". Motivo: una cadena de montañas vista desde lejos, paisaje amplio con horizonte. Acento: UNA montaña (o su cima), en marrón (#8A5A3B). Sensación: mirar lo de hoy desde más lejos.
- **Resiliencia:** Categoría "Resiliencia". Motivo: una pequeña planta que brota entre dos piedras. Acento: la PLANTA, en verde (#5E8C4E). Sensación: sostenerse y reponerse en lo difícil.
- **Amor propio:** Categoría "Amor propio". Motivo: una flor abriéndose. Acento: el CENTRO / un detalle de la flor, en rosa (#D98AA6). Sensación: trato amable con uno mismo.
- **Vínculos:** Categoría "Vínculos". Motivo: dos pájaros cerca. Acento: el ALA de UNO de los pájaros, en rojo (#C8453E). Sensación: cercanía con las personas que importan.

Para los **glifos de acción** se hace lo mismo con un bloque maestro propio
(minimalista, viewBox `0 0 90 90`, un solo color vía `currentColor`) cuando se
cierren las categorías.

**Molde de carta:** [`molde_carta.html`](molde_carta.html) arma las **cartas
reales** (frente + dorso) por categoría a partir de los `cat_*.png`. Sirve de
plantilla: por cada categoría nueva se agrega una entrada al array y se ve al toque.
La **franja** de cada carta usa el color de acento de su categoría.

---

## 5. Plan del Motor (general → particular)

| Paso | Qué | Estado |
|------|-----|--------|
| 1 | Estética y anatomía de la carta | ✅ |
| 2 | Dibujos de categoría (6 SVG) + glifos de acción (5 SVG) | ⏳ Gratitud primero |
| 3 | Biblioteca de cartas (3-5 por molde) | ⏳ |
| 4 | Consolidación → seed para la DB + script mixer | ⏳ |
