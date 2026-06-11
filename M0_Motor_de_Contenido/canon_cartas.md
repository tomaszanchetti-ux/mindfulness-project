# Canon ejecutable de cartas — rule base del validador

Versión formal y evaluable de las reglas de la [`Madre_del_Motor.md`](Madre_del_Motor.md) (§2).
Este documento es la **rule base que consume el LLM-judge** de `scripts/validar_cartas.py`:
cada regla tiene id, criterio observable y peso en el veredicto. Si una regla cambia acá,
cambia para todas las cartas — propias y (a futuro, premium) creadas por usuarios.

## §0 · Storytelling de Dwellia (la tesis que toda carta sirve — WS18)

Dwellia es un **espacio de crecimiento personal** construido sobre una pausa diaria
que conecta a la persona **consigo misma, con su alrededor y con la naturaleza**, y
la invita a **reconocer las emociones y sentimientos** que esa conexión genera.

- **La pausa = actividad de desconexión + escribir lo sentido.** Escribir en el
  diario físico no es una opción del menú ni una coletilla final: **escribir ES la
  pausa**. Las **actividades de desconexión** (contemplar, respirar, caminar, hacer)
  son disparadores que la preparan; las cartas de acción "escribir" son la pausa de
  escritura pura (conexión directa, el día sin tiempo).
- **Los 6 pilares** (gratitud, calma, perspectiva, resiliencia, amor propio,
  vínculos) son el curriculum del crecimiento: interconectados, con la persona en
  el centro. El motor los recorre todos, todas las semanas (rotación 6+1).
- **Consecuencia para toda carta:** la actividad prepara, el diario recoge. La
  pregunta de diario apunta a **lo que la pausa hizo sentir**, no solo a lo que
  hizo ver (R3.4).

*Terminología de producto:* "pilares" (no "categorías") · "actividades de
desconexión" (no "modalidades") · "complementar tu pausa" (las actividades
complementan la escritura, nunca al revés). Los slugs internos de la DB no cambian.

## Entrada y salida del validador

**Entrada:** una carta candidata `{categoria (= pilar), accion (= actividad), frase, prompt, concepto?}` + el mazo
vigente (para similitud y conceptos existentes).

**Salida:** veredicto `aprueba | requiere_revision | rechaza` + lista de reglas incumplidas
(con explicación de una línea) + `concepto` sugerido si no vino + sugerencia de fix
(frase/prompt alternativos) cuando el veredicto es `requiere_revision`.

**Reglas de veredicto:**
- Cualquier **S-x** incumplida → `rechaza` (sin sugerencia de fix).
- Una o más **R-x mayores** (R1–R5) incumplidas → `requiere_revision` con fix sugerido.
- Solo **R-x menores** (R6–R8) → `aprueba` con observaciones.
- Nada incumplido → `aprueba`.

---

## R1 — La frase

| id | Criterio |
|----|----------|
| R1.1 | Corta (una línea, ~70 caracteres máx.), poética, abstracta, **memorable**. |
| R1.2 | **No instruye ni explica la acción** — resuena con ella; es imagen o idea, no consigna. |
| R1.3 | Sin clichés, refranes literales ni calcos del self-help inglés. |
| R1.4 | Bonus (no bloquea): guiña al motivo del pilar (amanecer, luna, montaña, planta, flor, pájaros) sin nombrarlo. |

## R2 — El prompt

| id | Criterio |
|----|----------|
| R2.1 | **Una sola idea.** Concreto, hacible en ~10 minutos. |
| R2.2 | Realizable **cualquier día por cualquier persona**: sin supuestos de pareja, dinero, clima, movilidad, estado de ánimo, evento puntual de hoy ni cruzarse con alguien. Condicionales tipo "si surge la ocasión" solo si el diario sigue funcionando cuando no surge. **Matiz Vínculos:** contactar a alguien (en persona o a distancia) es el territorio del pilar y no cuenta como supuesto prohibido, siempre que el prompt ofrezca la vía a distancia. |
| R2.3 | Invitación, nunca obligación. La actividad de desconexión se mantiene **pura** (caminar es caminar) y **prepara la escritura** (§0): dispara, no sustituye. |
| R2.4 | Cuidado emocional: invita a mirar la fortaleza, no a abrir la herida. |

## R3 — El cierre en el diario

| id | Criterio |
|----|----------|
| R3.1 | Todo prompt termina (o teje) la vuelta al **diario físico**, con redacción única conectada al contenido de la carta — nunca coletilla idéntica pegada. En acción "escribir", el diario va dentro de la consigna. |
| R3.2 | La pregunta es **respondible y concreta**: no binaria, no pide cuantificar la metáfora ("qué cambió de tamaño" a secas), no presupone que el ejercicio funcionó — si no pasó nada, debe seguir habiendo qué escribir. |
| R3.3 | Pide **contenido, no confirmación del efecto** (o deja salida explícita: "…o qué se resiste a salir"). |
| R3.4 | **Abre a lo sentido (§0):** la pregunta invita a reconocer emociones/sentimientos que la pausa generó. Puede anclar en lo observado ("qué viste…") siempre que tienda el puente a la emoción ("…y qué te hizo sentir"). No se queda en registro puramente observacional — pero tampoco exige que las 69 terminen en "¿qué sentiste?": variedad de ángulos, mismo norte. |

## R4 — Coherencia frase ↔ prompt

| id | Criterio |
|----|----------|
| R4.1 | La frase **dispara** lo que el prompt pide: misma idea emocional vista desde lo poético y desde lo concreto. Si la frase apunta a A y el prompt a B, no entra. |

## R5 — Concepto y variedad (regla WS17)

| id | Criterio |
|----|----------|
| R5.1 | **Un concepto = una experiencia.** La carta lleva etiqueta `concepto`; si su experiencia ya existe en el mazo con otra etiqueta, o duplica un concepto sin aportar nada distinto, no entra. Variantes deliberadas comparten etiqueta. |
| R5.2 | El **guion físico varía dentro de la actividad**: el cuerpo del ejercicio no puede ser idéntico al de otra carta de la misma actividad (cambiar el *cómo*, no solo la pregunta de diario). **Excepción:** no aplica entre cartas que comparten `concepto` — son gemelas declaradas (alternativas que el motor jamás sirve en la misma semana), no compañeras de mazo. |

## R6 — Tono e idioma (menor)

| id | Criterio |
|----|----------|
| R6.1 | Español de España, neutro, tuteo ("escribe", "te gustaría"). Sin voseo. |
| R6.2 | Sin localismos americanos: apurarse, acomodarse, postergar, "afuera" estático, "a ningún lado", "darse un gusto", "date el mérito". |
| R6.3 | Sin calcos del inglés ("cómo se siente + infinitivo"). |

## R7 — Muletillas de mazo (menor)

| id | Criterio |
|----|----------|
| R7.1 | Palabras/estructuras ya cargadas en el mazo ("también", "prisa", "Detente a…", "qué despertó en ti", "por pequeño que sea", "como a alguien que quieres"): máximo un uso por pilar, idealmente ninguno nuevo. |
| R7.2 | El conector al diario varía ("Después/Luego escribe…" no puede ser la única forma; alternar con tejidos: "Al volver…", "Al cerrar el día…", "cierra anotando…"). |

## R8 — Estructura (menor, verificable por la capa determinística)

| id | Criterio |
|----|----------|
| R8.1 | Campos completos; `categoria` y `accion` existen en los seeds; el par pilar×actividad respeta la matriz de afinidad (abajo). |
| R8.2 | La palabra "diario" aparece en el prompt. |
| R8.3 | Longitudes: frase ≤ ~70 caracteres; prompt ≤ ~280 caracteres. |

**Matriz de afinidad pilar × actividad** (pares viables; el resto no entra):

| Pilar | escribir | contemplar | respirar | caminar | hacer |
|---|:--:|:--:|:--:|:--:|:--:|
| gratitud | ✅ | ✅ | — | ✅ | ✅ |
| calma | ✅ | ✅ | ✅ | ✅ | — |
| perspectiva | ✅ | ✅ | ✅ | ✅ | — |
| resiliencia | ✅ | — | ✅ | ✅ | ✅ |
| amor-propio | ✅ | ✅ | ✅ | — | ✅ |
| vinculos | ✅ | ✅ | — | — | ✅ |


## S — Safety (bloqueante, pensado para cartas de usuarios)

| id | Criterio |
|----|----------|
| S1 | Sin contenido clínico o de riesgo: autolesión, trastornos, daño a terceros, consejo médico/psicológico. |
| S2 | Sin datos personales, marcas, promoción, proselitismo (religioso, político) ni contenido sexual. |
| S3 | Sin lenguaje que culpabilice o presione ("si no haces esto, fallas"). |
