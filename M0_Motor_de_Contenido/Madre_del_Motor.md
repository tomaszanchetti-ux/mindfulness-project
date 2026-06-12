# Madre del Motor (M0)

La **lógica completa del Motor de Contenido**: cómo se modelan, se ven y se
producen las cartas. Es la referencia única del módulo.

> Contexto general: [`../00_Documento_Madre.md`](../00_Documento_Madre.md) ·
> Teoría de los pilares: [`fundamentos_pilares.md`](fundamentos_pilares.md) ·
> Reglas de toda carta: [`canon_cartas.md`](canon_cartas.md).

---

## 1. Modelo de contenido (WS22)

La unidad es la **carta**: `pilar + acción inicial + concepto + frase + micro-prompt + color + dibujo`.
(En la DB los campos se llaman `categoria` y `accion` — los slugs no cambian.)

**Toda carta es una pausa de dos tiempos** ([canon §0](canon_cartas.md)):
`acción inicial → calma → escribir`. La acción inicial conduce a la calma; en
calma se escribe lo sentido; lo escrito trabaja el pilar del día.

**Dos ejes (no un árbol):**
- **Pilar** = el *qué* (el curriculum del crecimiento, 6 en tres anillos —
  [`fundamentos_pilares.md`](fundamentos_pilares.md) §4). **No se eligen:** M2 los
  recorre todos, cada semana (rotación 6+1).
- **Acción inicial** = el *cómo* (contemplar · respirar · pasear · hacer). Su única
  misión es **conducir a la calma** (canon R2.5). **Tampoco se elige (WS22):** el
  motor sirve las 4; el eje quietud (contemplar·respirar) / movimiento
  (pasear·hacer) habilita el cambio de carta v2.
- **Escribir** = la **acción final universal**, no un eje: toda carta cierra en el
  diario físico (canon R3.1). Ya no existe "carta de acción escribir": las de
  escritura pura llevan una acción inicial mínima explícita (triage WS22).
- **Concepto** = la huella de deduplicación: cartas que producen la misma
  experiencia comparten etiqueta y M2 no repite concepto en la semana (canon R5).

**La matriz de afinidad pilar × acción inicial vive en el canon (R8.1)** — una
sola fuente, no se duplica acá. Cada pilar cubre ambos lados del eje.

**Profundidad (mazo WS22): 77 cartas** — gratitud 13 · sentido 12 · perspectiva 14
· resiliencia 12 · amor propio 14 · vínculos 12, todas con ambos lados del eje
cubiertos. El motor del día (M2) no repite **ni carta ni concepto** en una ventana
de 7 días y balancea la acción (que no caigan varios días seguidos de la misma).

---

## 2. Reglas del Motor → viven en el canon (una sola fuente)

**Las reglas de toda carta viven en [`canon_cartas.md`](canon_cartas.md)** — el SoT
único que consume el validador (`scripts/validar_cartas.py`: capa determinística +
LLM-judge) y que rige también las cartas de usuarios (premium). La **teoría** que
fundamenta las reglas vive en [`fundamentos_pilares.md`](fundamentos_pilares.md).
Acá no se duplican (WS18, *Simpleza*: dos copias = dos idiomas).

El espíritu, en cuatro líneas (los cuatro gates del recorrido del usuario):
- **La frase enciende el deseo** — es la puerta de la pausa; atrae por imán, jamás
  por arenga (canon R1.5).
- **La acción inicial conduce a la calma** — el vehículo de todo el método (R2.5).
- **La consigna abre a lo sentido** — el diario recoge emociones, no hechos (R3.4).
- **Lo escrito trabaja la función del pilar** — su pregunta-norte, no solo su tema
  (R4.2). Cero relleno.

---

## 3. Estética de la carta

Estilo **tarjeta japonesa**: papel crema, mínimo, elegante, mucho aire. Dos caras;
se **gira con un tap** (recibes la carta cerrada y la giras para ver la consigna).

```
        FRENTE                          DORSO (al girar)
┌───────────────────┐          ┌───────────────────┐
│███ franja color ██│          │███ franja color ██│ ← misma franja, da la vuelta
│   g r a t i t u d │ ←pilar   │  "A veces lo que  │ ← FRASE (protagonista, aire)
│        ☀          │ ←dibujo  │   más sostiene…"  │
│       pilar       │          │        ◡          │ ← glifo de la acción inicial
│  c o n t e m p l a r │ ←acción │  Mira a tu…   ✒  │ ← micro-prompt + pluma (cierre)
└───────────────────┘          └───────────────────┘
```

> **Re-layout WS22 (pendiente, paso UX):** el dorso acompaña los dos tiempos —
> frase (la puerta) → acción inicial con su glifo → cierre en el diario con la
> **pluma como sello universal**. Bien simple, elegante.

**Dos capas de estilo (regla clave):**
- **Dibujo del pilar:** preciso, acuarela, **todo en negro neutro** (`#2b2925`); el **color del pilar pinta UN solo elemento**. Mismo valor y textura en los 6.
- **Glifo de acción:** minimalista, geométrico, un color (se pinta del color del pilar), chico. No le roba protagonismo a la frase.

**Vocabulario cerrado (WS22)**

| Pilar | Motivo | Acento (color) | | Acción | Glifo |
|-----------|--------|----------------|---|--------|-------|
| Gratitud | amanecer | el sol — amarillo `#E0A92E` | | Contemplar | un ojo |
| Sentido | luna sobre agua *(heredado de Calma, WS22)* | la luna — azul-gris `#becdd7` | | Respirar | círculos concéntricos |
| Perspectiva | montañas a lo lejos | una montaña — marrón `#8A5A3B` | | Pasear | pasos (chevrons) |
| Resiliencia | planta entre piedras | la planta — verde `#5E8C4E` | | Hacer | un destello |
| Amor propio | flor abriéndose | el centro — rosa `#D98AA6` | | *(cierre)* Escribir | una pluma — **sello universal** |
| Vínculos | dos pájaros | un ala — rojo `#C8453E` | | | |

> **La luna resignificada (WS22):** ya no es *quietud* — es **la luz que orienta en
> la noche, que solo el agua quieta refleja**: la calma (el agua) es el vehículo
> que deja ver el sentido (la luna). La imagen dice la tesis del método. El guiño
> de frase (canon R1.4) para Sentido es *luz que orienta*, no *bajar el ritmo*.
> **Calma ya no tiene motivo de pilar** (es el vehículo, está en todas las cartas).

Papel `#EFE6D3` · tinta `#2b2925`. La **franja superior** y el **glifo** usan el
color del pilar. Los **colores de acento reales** de los 6 dibujos (ya hechos)
están en `molde_carta.html`. Tipografía: serif elegante para la frase
(protagonista); sans fina con tracking amplio para los nombres (`g r a t i t u d`).

---

## 4. Producción de los dibujos

**Los 6 dibujos de pilar ya están hechos** (PNG acuarela en
`assets/categorias/`); **Sentido hereda el de Calma sin regenerar nada**
(`cat_calma.png`, mismo arte, lectura nueva). Esta sección queda como referencia
para futuros pilares o packs (v2).

> **Workflow real (desde WS01):** **ChatGPT rinde mejor que Claude Design** para
> estas ilustraciones. Salen como **PNG** (acuarela raster), a veces con un damero
> de fondo "horneado"; Claude lo **limpia a PNG transparente** y lo recorta →
> `assets/categorias/cat_<nombre>.png`. **Pilares = PNG** (acuarela). Los
> **glifos de acción = SVG** (geométricos, un color vía `currentColor`).

**Qué debe entregar:** dibujo a línea fina en negro (`#2b2925`) sobre fondo
transparente, con UN solo elemento en el color de acento, sin texto ni marco,
centrado y cuadrado.

### Bloque maestro para ChatGPT (igual para todos los pilares)

Pegar este bloque + la línea del pilar (tabla §3). Trae los aprendizajes de
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
{LÍNEA DEL PILAR}
```

> **Aprendizajes:** (1) Gratitud salió de una; (2) la luna la primera vez salió
> plana/pálida → de ahí la CLAVE 1. El fondo suele venir con un damero "horneado":
> no importa, Claude lo limpia a PNG transparente y recorta. El acento va
> **siempre del color del pilar**.

### Líneas por pilar (la variable — los 6 ya generados)

- **Gratitud:** Motivo: un amanecer — el sol naciendo sobre un horizonte, con un par de colinas suaves y unos pocos rayos sobrios. Acento: el SOL, en amarillo opaco (#E0A92E). Sensación: calidez y agradecer lo pequeño que sostiene.
- **Sentido** *(arte heredado de Calma, WS22 — NO regenerar)*: Motivo: la luna llena sobre el agua, con olas suaves en línea negra. Acento: la LUNA, disco de acuarela azul-gris con textura/cráteres (#becdd7); el reflejo insinuado con líneas y grises suaves. Sensación nueva: **la luz que orienta en la noche, reflejada en el agua quieta**.
- **Perspectiva:** Motivo: una cadena de montañas vista desde lejos, paisaje amplio con horizonte. Acento: UNA montaña (o su cima), en marrón (#8A5A3B). Sensación: mirar lo de hoy desde más lejos.
- **Resiliencia:** Motivo: una pequeña planta que brota entre dos piedras. Acento: la PLANTA, en verde (#5E8C4E). Sensación: sostenerse y reponerse en lo difícil.
- **Amor propio:** Motivo: una flor abriéndose. Acento: el CENTRO / un detalle de la flor, en rosa (#D98AA6). Sensación: trato amable con uno mismo.
- **Vínculos:** Motivo: dos pájaros cerca. Acento: el ALA de UNO de los pájaros, en rojo (#C8453E). Sensación: cercanía con las personas que importan.

**Molde de carta:** [`molde_carta.html`](molde_carta.html) arma las **cartas
reales** (frente + dorso) por pilar a partir de los `cat_*.png`. Sirve de
plantilla: por cada pilar nuevo se agrega una entrada al array y se ve al toque.
La **franja** de cada carta usa el color de acento de su pilar.

---

## 5. Plan del Motor (general → particular)

| Paso | Qué | Estado |
|------|-----|--------|
| 1 | Estética y anatomía de la carta | ✅ (re-layout dos tiempos pendiente, paso UX WS22) |
| 2 | Dibujos de pilar (6 PNG) + glifos de acción (SVG) | ✅ (Sentido hereda el de Calma) |
| 3 | Biblioteca de cartas | ✅ triage WS22 hecho: **77 cartas** (gate determinístico 0/0 · judge LLM 77/77 ✅) |
| 4 | Seed para la DB + motor | ⏳ re-seed + migración + motor (paso 3, canon §Transición) |
