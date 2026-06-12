# Canon ejecutable de cartas — rule base del validador

Versión formal y evaluable de las reglas de la [`Madre_del_Motor.md`](Madre_del_Motor.md) (§2),
fundadas en la teoría de [`fundamentos_pilares.md`](fundamentos_pilares.md) (SoT teórico, WS22).
Este documento es la **rule base que consume el LLM-judge** de `scripts/validar_cartas.py`:
cada regla tiene id, criterio observable y peso en el veredicto. Si una regla cambia acá,
cambia para todas las cartas — propias y (a futuro, premium) creadas por usuarios.

## §0 · Storytelling de Dwellia (la tesis que toda carta sirve — WS18 · refundado WS22)

Dwellia es un **espacio de crecimiento personal** construido sobre una pausa diaria
que conecta a la persona **consigo misma, con su alrededor y con la naturaleza**, y
la invita a **reconocer las emociones y sentimientos** que esa conexión genera.

- **La pausa tiene dos tiempos y una bisagra:**
  `ACCIÓN INICIAL (contemplar · respirar · pasear · hacer) → CALMA → ACCIÓN FINAL (escribir)`
  - La **acción inicial** rota; su única misión es **conducir a la calma** (lente de
    admisión de toda acción: si no puede inducir calma, no entra — R2.5).
  - La **calma** NO es un pilar: es el **vehículo** de toda la pausa (samatha →
    vipassana: primero se aquieta el agua, después se ve el fondo). Está en todas
    las cartas, todos los días.
  - **Escribir es siempre la acción final** y el acto central: en calma, la persona
    escribe lo sentido en su diario físico, y eso que escribe **trabaja el pilar del
    día** (su función, no solo su tema — R4.2).
- **Los 6 pilares** (amor propio, sentido, gratitud, perspectiva, resiliencia,
  vínculos) son el curriculum del crecimiento, en **tres anillos** con la persona al
  centro y la calma como suelo: *hacia adentro* (amor propio · sentido), *hacia la
  experiencia* (gratitud · perspectiva), *hacia afuera y adelante* (vínculos ·
  resiliencia). El motor los recorre todos, todas las semanas (rotación 6+1).
- **El usuario no elige** ni pilar ni acción: el motor cura. Única agencia = cambio
  de carta (v2 premium, 1×/día) **cruzando el eje movimiento↔quietud** (quietud =
  contemplar · respirar / movimiento = pasear · hacer; mismo pilar, `concepto`
  distinto, ventanas de 7 días intactas).
- **La carta visual acompaña los dos tiempos:** frase (protagonista y **puerta de
  la pausa**: su misión es encender las ganas de vivirla — R1.5) → acción inicial
  con su glifo → cierre escribir con la pluma como sello universal.
  (Bajada visual fina: paso UX.)

*Terminología de producto:* "pilares" (no "categorías") · "acción inicial" y "acción
final" (no "modalidades" ni "actividades a elegir") · **"pasear"** (no "caminar": un
paseo puede ser a pie, asistido o sobre ruedas — la palabra resuelve la
accesibilidad sin configuración) · "calma" = el vehículo, jamás un tema más. Los
slugs internos de la DB no cambian (`caminar` se muestra "pasear").

## Entrada y salida del validador

**Entrada:** una carta candidata `{categoria (= pilar), accion (= acción inicial), frase, prompt, concepto?}` + el mazo
vigente (para similitud y conceptos existentes). `escribir` ya **no** es un valor
válido de acción inicial (el cierre en el diario es universal); `calma` ya **no** es
un pilar (cartas heredadas con esos valores → triage, ver §Transición).

**Salida:** veredicto `aprueba | requiere_revision | rechaza` + lista de reglas incumplidas
(con explicación de una línea) + `concepto` sugerido si no vino + sugerencia de fix
(frase/prompt alternativos) cuando el veredicto es `requiere_revision`.

**Reglas de veredicto:**
- Cualquier **S-x** incumplida → `rechaza` (sin sugerencia de fix).
- Una o más **R-x mayores** (R1–R5) incumplidas → `requiere_revision` con fix sugerido.
- Solo **R-x menores** (R6–R8) → `aprueba` con observaciones.
- Nada incumplido → `aprueba`.

**El triple gate** (síntesis de fundamentos §6, atraviesa las R): ① ¿la acción
inicial conduce a la calma? (R2.5) · ② ¿la consigna abre a lo sentido? (R3.4) ·
③ ¿lo escrito trabaja la **función** del pilar, no solo su tema? (R4.2).

---

## R1 — La frase

| id | Criterio |
|----|----------|
| R1.1 | Corta (una línea, ~70 caracteres máx.), poética, abstracta, **memorable**. |
| R1.2 | **No instruye ni explica la acción** — resuena con ella; es imagen o idea, no consigna. |
| R1.3 | Sin clichés, refranes literales ni calcos del self-help inglés. |
| R1.4 | Bonus (no bloquea): guiña al motivo del pilar sin nombrarlo — amanecer (gratitud), luna sobre el agua como *luz que orienta en la noche* (sentido), montaña (perspectiva), planta (resiliencia), flor (amor propio), pájaros (vínculos). |
| R1.5 | **Gate de deseo (WS22):** la frase es lo primero que la persona ve y es la **puerta de la pausa** — leída sola, debe encender las ganas de vivir la pausa hoy: promete sentido, intriga o belleza que atraen hacia adentro. **Atrae por imán, jamás por empuje:** la exhortación motivacional ("tú puedes", "hoy será un gran día") ya queda fuera por R1.3. Una frase correcta pero inerte, que no da ganas de nada → `requiere_revision`. |

## R2 — El prompt

| id | Criterio |
|----|----------|
| R2.1 | **Una sola idea.** Concreto, hacible en ~10 minutos. |
| R2.2 | Realizable **cualquier día por cualquier persona**: sin supuestos de pareja, dinero, clima, movilidad, estado de ánimo, evento puntual de hoy ni cruzarse con alguien. Condicionales tipo "si surge la ocasión" solo si el diario sigue funcionando cuando no surge. **Matiz Vínculos:** contactar a alguien (en persona o a distancia) es el territorio del pilar y no cuenta como supuesto prohibido, siempre que el prompt ofrezca la vía a distancia. **Matiz pasear:** el paseo no presupone caminar — vale asistido o sobre ruedas; el prompt no exige marcha a pie. |
| R2.3 | Invitación, nunca obligación. La acción inicial se mantiene **pura** (pasear es pasear) y **conduce a la calma que prepara la escritura** (§0): dispara, no sustituye. |
| R2.4 | Cuidado emocional: invita a mirar la fortaleza, no a abrir la herida. |
| R2.5 | **Gate de calma (WS22):** la acción inicial, tal como está planteada, **conduce a la calma** — baja la activación, no compite, no apura, no enciende pantallas, no exige rendimiento. Si la acción no puede inducir calma, la carta no entra. |

## R3 — El cierre en el diario (la acción final)

| id | Criterio |
|----|----------|
| R3.1 | **Toda carta cierra en el diario físico** — escribir es la acción final universal, con redacción única conectada al contenido de la carta, nunca coletilla idéntica pegada. (La antigua acción "escribir" ya no existe como inicial: las ex cartas de escritura pura llevan una acción inicial mínima explícita — ver §Transición.) |
| R3.2 | La pregunta es **respondible y concreta**: no binaria, no pide cuantificar la metáfora ("qué cambió de tamaño" a secas), no presupone que el ejercicio funcionó — si no pasó nada, debe seguir habiendo qué escribir. |
| R3.3 | Pide **contenido, no confirmación del efecto** (o deja salida explícita: "…o qué se resiste a salir"). |
| R3.4 | **Abre a lo sentido (§0):** la pregunta invita a reconocer emociones/sentimientos que la pausa generó. Puede anclar en lo observado ("qué viste…") siempre que tienda el puente a la emoción ("…y qué te hizo sentir"). No se queda en registro puramente observacional — pero tampoco exige que todas terminen en "¿qué sentiste?": variedad de ángulos, mismo norte. |

## R4 — Coherencia y función

| id | Criterio |
|----|----------|
| R4.1 | La frase **dispara** lo que el prompt pide: misma idea emocional vista desde lo poético y desde lo concreto. Si la frase apunta a A y el prompt a B, no entra. |
| R4.2 | **Gate de función (WS22):** lo que la carta pide escribir trabaja la **función del pilar** según su **pregunta-norte** ([`fundamentos_pilares.md`](fundamentos_pilares.md) §4/§6), no solo su tema. Una carta que matchea el tema pero no provoca el movimiento interior del pilar → `requiere_revision`. **Matiz Sentido:** micro-sentido vivido, jamás interrogatorio existencial ("¿cuál es tu propósito?" no es una carta). |

## R5 — Concepto y variedad (regla WS17)

| id | Criterio |
|----|----------|
| R5.1 | **Un concepto = una experiencia.** La carta lleva etiqueta `concepto`; si su experiencia ya existe en el mazo con otra etiqueta, o duplica un concepto sin aportar nada distinto, no entra. Variantes deliberadas comparten etiqueta. |
| R5.2 | El **guion físico varía dentro de la acción inicial**: el cuerpo del ejercicio no puede ser idéntico al de otra carta de la misma acción (cambiar el *cómo*, no solo la pregunta de diario). **Excepción:** no aplica entre cartas que comparten `concepto` — son gemelas declaradas (alternativas que el motor jamás sirve en la misma semana), no compañeras de mazo. |

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
| R8.1 | Campos completos; `categoria` y `accion` existen en los seeds; el par pilar×acción inicial respeta la matriz de afinidad (abajo). |
| R8.2 | La palabra "diario" aparece en el prompt. |
| R8.3 | Longitudes: frase ≤ ~70 caracteres; prompt ≤ ~280 caracteres. |

**Matriz de afinidad pilar × acción inicial** (pares viables; el resto no entra).
La columna "escribir" desapareció: el diario es el cierre universal de todas.
Cada pilar cubre **ambos lados del eje** quietud (contemplar·respirar) / movimiento
(pasear·hacer) — requisito del cambio de carta v2:

| Pilar | contemplar | respirar | pasear | hacer |
|---|:--:|:--:|:--:|:--:|
| gratitud | ✅ | — | ✅ | ✅ |
| sentido | ✅ | ✅ | ✅ | ✅ |
| perspectiva | ✅ | ✅ | ✅ | — |
| resiliencia | — | ✅ | ✅ | ✅ |
| amor-propio | ✅ | ✅ | — | ✅ |
| vinculos | ✅ | — | ✅ * | ✅ |

\* `vinculos × pasear` ampliada en WS22 (paseo pensando en alguien, o con alguien)
para dar profundidad al lado movimiento del pilar más flaco del mazo.

## S — Safety (bloqueante, pensado para cartas de usuarios)

| id | Criterio |
|----|----------|
| S1 | Sin contenido clínico o de riesgo: autolesión, trastornos, daño a terceros, consejo médico/psicológico. |
| S2 | Sin datos personales, marcas, promoción, proselitismo (religioso, político) ni contenido sexual. |
| S3 | Sin lenguaje que culpabilice o presione ("si no haces esto, fallas"). |

---

## §Transición (WS22 → pasos 2-3 del plan; el canon manda, el código sigue)

1. ✅ **Triage del mazo (paso 2 — HECHO, WS22):** el mazo canónico son **79
   cartas** en los seeds JSON (gratitud 13 · sentido 12 · perspectiva 16 ·
   resiliencia 12 · amor propio 14 · vínculos 12; ambos lados del eje en los 6).
   Las 12 de `calma`: 8 remapeadas por función (4→perspectiva · 2→amor propio ·
   1→gratitud · 1→sentido) y 4 retiradas; las 18 ex `escribir` recibieron acción
   inicial mínima explícita; `caminar`→"pasea/paseo" en todos los prompts (slug
   intacto); 12 de sentido nuevas + vínculos 9→12. Capa determinística: 0 errores ·
   0 avisos. ⏳ Pendiente: pasada del **LLM-judge** (necesita ANTHROPIC_API_KEY).
2. ✅ **DB + código (paso 3 — HECHO, WS22, EN PRODUCCIÓN):** migración
   `g7b8c9d0e1f2` (vacía entregas/fotos/compartidos + tablas de elección;
   conserva usuarios y push) + seed con **sync** (borra lo retirado) + motor sin
   filtro de acciones (pool = pilar completo; constantes `EJE_QUIETUD`/
   `EJE_MOVIMIENTO` listas para el swap v2; rotación 6+1 intacta) + endpoints
   `PUT /api/perfil/acciones|categorias` deprecados-vivos (compat front
   pre-WS22). 35 tests ✓ · prod rev `dwellia-api-00012`, resumen = 77 cartas.
3. ⏳ **UX (paso 4, con Tomás):** onboarding de anillos (cae el paso de
   actividades del front), teoría in-app, re-layout de carta (frase → acción
   inicial → cierre con pluma). Al cerrar: **drop** de `usuario_acciones` y
   `usuario_categorias` + retiro de sus endpoints. ⏳ También pendiente: pasada
   del **LLM-judge** sobre las 77 (necesita ANTHROPIC_API_KEY).
