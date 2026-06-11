# Madre del Motor (M0)

La **lógica completa del Motor de Contenido**: cómo se modelan, se ven y se
producen las cartas. Es la referencia única del módulo.

> Contexto general: [`../00_Documento_Madre.md`](../00_Documento_Madre.md).

---

## 1. Modelo de contenido

La unidad es la **carta**: `pilar + actividad + concepto + frase + micro-prompt + color + dibujo`.
(En la DB los campos se llaman `categoria` y `accion` — los slugs no cambian.)

**Dos ejes (no un árbol), según el storytelling ([canon §0](canon_cartas.md)):**
- **Pilar** = el *qué* (el curriculum del crecimiento personal). Los 6 están
  interconectados, con la persona en el centro. **No se eligen:** M2 los recorre
  todos, cada semana (rotación 6+1).
- **Actividad de desconexión** = el *cómo* (el disparador que prepara la escritura).
  Es propiedad de la carta y el usuario **elige cuáles quiere recibir** como
  complemento de su pausa. La capa blanda que aprende de las ⭐ vive **dentro** de
  ese menú (lógica en M2).
- **La escritura es la pausa misma:** las cartas de acción "escribir" son la pausa
  de escritura pura (conexión directa, el día sin tiempo) y **siempre están en el
  pool** — no son una opción del menú, son el núcleo.
- **Concepto** = la huella de deduplicación: cartas que producen la misma experiencia
  comparten etiqueta y M2 no repite concepto en la semana (canon R5).

**6 pilares × 5 actividades.**

> **La pausa = actividad de desconexión + escribir lo sentido (canon §0).** La
> actividad dispara; el diario recoge. Toda carta termina (o teje) la vuelta al
> diario físico.

**Matriz de afinidad** (✅ fuerte · ○ posible · · evitar) → **23 moldes viables**:

| Pilar | Escribir | Contemplar | Respirar | Caminar | Hacer |
|-----------|:--:|:--:|:--:|:--:|:--:|
| Gratitud | ✅ | ✅ | · | ○ | ✅ |
| Calma | ○ | ✅ | ✅ | ✅ | · |
| Perspectiva | ✅ | ✅ | ○ | ○ | · |
| Resiliencia | ✅ | · | ○ | ✅ | ○ |
| Amor propio | ✅ | ○ | ○ | · | ✅ |
| Vínculos | ✅ | ○ | · | · | ✅ |

**Profundidad:** arrancar con **3 a 5 cartas por molde**, sin agotar. El motor del
día (M2) no repite **ni carta ni concepto** en una ventana de 7 días y balancea la
actividad (que no caigan varios días seguidos de la misma).

---

## 2. Reglas del Motor → viven en el canon (una sola fuente)

**Las reglas de toda carta viven en [`canon_cartas.md`](canon_cartas.md)** — el SoT
único que consume el validador (`scripts/validar_cartas.py`: capa determinística +
LLM-judge) y que rige también las cartas de usuarios (premium). Acá no se duplican
(WS18, *Simpleza*: dos copias = dos idiomas).

El espíritu, en tres líneas:
- **Calidad sobre cantidad** — cada carta justifica su existencia; una sola idea.
- **Invitación, nunca obligación** — sin supuestos, sin presión; mirar la fortaleza,
  no abrir la herida. La frase sola ya vale.
- **La actividad dispara, el diario recoge** — toda carta vuelve al diario físico con
  redacción única, y la pregunta abre a lo sentido (canon §0 y R3).

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
- **Dibujo del pilar:** preciso, acuarela, **todo en negro neutro** (`#2b2925`); el **color de la categoría pinta UN solo elemento**. Mismo valor y textura en las 6.
- **Glifo de acción:** minimalista, geométrico, un color (se pinta del color de la categoría), chico. No le roba protagonismo a la frase.

**Vocabulario cerrado**

| Pilar | Motivo | Acento (color) | | Actividad | Glifo |
|-----------|--------|----------------|---|--------|-------|
| Gratitud | amanecer | el sol — amarillo `#E0A92E` | | Escribir | una pluma |
| Calma | luna sobre agua | la luna — azul-gris `#becdd7` | | Contemplar | un ojo |
| Perspectiva | montañas a lo lejos | una montaña — marrón `#8A5A3B` | | Respirar | círculos concéntricos |
| Resiliencia | planta entre piedras | la planta — verde `#5E8C4E` | | Caminar | pasos (chevrons) |
| Amor propio | flor abriéndose | el centro — rosa `#D98AA6` | | Hacer | un destello |
| Vínculos | dos pájaros | un ala — rojo `#C8453E` | | | |

Papel `#EFE6D3` · tinta `#2b2925`. La **franja superior** y el **glifo** usan el
color de la categoría. Los **colores de acento reales** de las 6 categorías (ya
dibujadas) están en `molde_carta.html`. Tipografía: serif elegante para la frase (protagonista);
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

### Bloque maestro para ChatGPT (igual para las 6 categorías)

Pegar este bloque + la línea de la categoría (tabla §3). Trae los aprendizajes de
Gratitud y Calma para acertar al primer intento.

```
Ilustración minimalista estilo acuarela, elegante y serena, con sensibilidad
japonesa. Dibujo a línea fina en NEGRO sobre fondo TRANSPARENTE (PNG con canal
alfa, sin ningún fondo). UN solo elemento pintado en color (el que indico abajo);
TODO el resto en línea negra. Composición centrada, con mucho aire, sin texto, sin
marco. Formato cuadrado.

CLAVE 1 — el elemento de color tiene que tener CUERPO Y TEXTURA desde el arranque:
acuarela rica, con variaciones de tono, nunca plano ni pálido. Mismo "peso" visual
que un sol o una luna bien logrados.

CLAVE 2 — consistencia de set: tiene que combinar con las cartas ya hechas del
mismo set: un amanecer con el sol como disco de acuarela amarillo, y una luna como
disco de acuarela azul-gris con textura. Mismo peso de línea, misma textura de
acuarela, mismo nivel de detalle y de aire.

ILUSTRACIÓN A GENERAR:
{LÍNEA DE LA CATEGORÍA}
```

> **Aprendizajes (de nuestras interacciones):** (1) Gratitud salió de una; (2)
> Calma la primera vez salió plana/pálida → de ahí la CLAVE 1. El fondo suele venir
> con un damero "horneado": no importa, Claude lo limpia a PNG transparente y
> recorta. El acento va **siempre del color de la categoría**.

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
