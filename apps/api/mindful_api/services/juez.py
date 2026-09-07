"""WS27 · B1.2 · El juez de cartas de la comunidad.

Dos capas, como el CLI (`scripts/validar_cartas.py`, que ahora importa de acá):

  CAPA 1 · `services/canon.py` — determinística, gratis, siempre. Decide lo que se
    puede decidir por código: pilar y acción existen y combinan, el prompt cierra
    en el diario, localismos, supuestos, muletillas y parecidos contra el mazo.

  CAPA 2 · este módulo — UNA llamada a Claude con el canon cacheado y salida
    estructurada. Alcance ESTRICTO (decisión de Tomás, WS27): la capa 1 ya miró lo
    que está en la base, así que al modelo se le piden solo tres cosas —
    seguridad (S1-S3), alineación con Dwellia (R1.5, R2.5, R3.4, R4.2) y el
    concepto. En la duda sobre estilo, aprueba: Tomás decide después.

Contrato (lo consume B1.1):
  evaluar(propuesta, mazo, categorias, acciones) -> Veredicto
    propuesta = {"categoria", "accion", "frase", "prompt"}  (slugs ya validados)
    mazo      = [{"id","categoria","accion","concepto","frase","prompt"}, ...]
    categorias / acciones = sets de slugs válidos
  Veredicto.resultado ∈ {"aprueba", "requiere_revision", "rechaza", "off"}
    off = sin `MINDFUL_ANTHROPIC_API_KEY` (o error de red): el llamador manda la
    propuesta a `revision_dwellia` y sigue. El juez NUNCA levanta.

Sin key, la capa 1 protege igual: si encuentra un error duro o un parecido por
encima del umbral, el veredicto es `requiere_revision` (vuelve al autor con el
motivo). Si en cambio el juez SE CAE (red, JSON, modelo), el veredicto es `off` y
la propuesta va a `revision_dwellia`: una carta no vuelve al autor por una caída
nuestra, pero los hallazgos de la capa 1 viajan igual en el expediente.
"""

from __future__ import annotations

import json
import os
import sys
from dataclasses import dataclass, field
from typing import Optional

from ..config import settings
from .canon import (
    MAX_FRASE_COMUNIDAD,
    MAX_PROMPT_COMUNIDAD,
    MIN_PROMPT_COMUNIDAD,
    InformeCandidata,
    leer_canon,
    validar_candidata,
)

# Sonnet 5 piensa antes de responder (thinking adaptativo por defecto) y esos
# tokens cuentan dentro de `max_tokens`: con 2000 la primera llamada real se
# quedó sin espacio para el JSON (WS27). 8000 deja aire de sobra; el veredicto
# en sí pesa ~500.
MAX_TOKENS = 8000
TIMEOUT_SEGUNDOS = 120


@dataclass
class Veredicto:
    resultado: str                       # aprueba | requiere_revision | rechaza | off
    hallazgos: list = field(default_factory=list)   # [{"regla","mayor","detalle"}]
    concepto: Optional[str] = None       # kebab-case sugerido
    fix: Optional[dict] = None           # {"frase","prompt"} si requiere_revision
    motivo: Optional[str] = None         # una línea legible para el autor
    detalle: dict = field(default_factory=dict)     # lo crudo (capa 1 + respuesta del modelo)


# ─────────────────────────────────────────────────────────────────────────────
# Salida estructurada (structured output). La comparten el runtime y el CLI.
# ─────────────────────────────────────────────────────────────────────────────
ESQUEMA_VEREDICTO = {
    "type": "object",
    "properties": {
        "veredicto": {"type": "string", "enum": ["aprueba", "requiere_revision", "rechaza"]},
        "hallazgos": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "regla": {"type": "string"},
                    "mayor": {"type": "boolean"},
                    "detalle": {"type": "string"},
                },
                "required": ["regla", "mayor", "detalle"],
                "additionalProperties": False,
            },
        },
        "concepto_sugerido": {"type": "string"},
        "fix_sugerido": {
            "anyOf": [
                {"type": "null"},
                {
                    "type": "object",
                    "properties": {"frase": {"type": "string"}, "prompt": {"type": "string"}},
                    "required": ["frase", "prompt"],
                    "additionalProperties": False,
                },
            ]
        },
    },
    "required": ["veredicto", "hallazgos", "concepto_sugerido", "fix_sugerido"],
    "additionalProperties": False,
}


# ─────────────────────────────────────────────────────────────────────────────
# El prompt
# ─────────────────────────────────────────────────────────────────────────────
ROL = (
    "Eres el juez de calidad de cartas de Dwellia, una app de pausas de "
    "mindfulness. Evalúas cada carta contra el canon (rule base) que sigue, regla "
    "por regla. Eres exigente pero justo: señalas solo incumplimientos reales, "
    "citando la regla (R1.1…S3). 'mayor' = true para R1-R5 y S; false para R6-R8. "
    "Si el veredicto es requiere_revision, propones un fix concreto (frase y/o "
    "prompt alternativos) que respete el canon. Sugieres siempre el concepto "
    "(kebab-case): el existente si la carta es variante deliberada de otra, o uno "
    "nuevo."
)

# Modo alta = el gate real de una candidata nueva (las cartas de la comunidad).
CALIBRACION_ALTA = (
    "MODO ALTA: la carta es una candidata NUEVA que pide entrar al mazo. "
    "Aplica el canon con severidad completa, regla por regla."
)

# Modo regresión = el mazo ya curado por humanos (solo lo usa el CLI).
CALIBRACION_REGRESION = (
    "MODO REGRESIÓN: la carta que vas a evaluar YA pertenece al mazo aprobado "
    "por curaduría humana. Señala SOLO incumplimientos claros e inequívocos — "
    "los que justificarían rechazar la carta si fuera nueva. NO propongas "
    "mejoras de gusto, reformulaciones opcionales ni señales 'podría ser más "
    "concreta/única': si una elección de estilo es defendible, está aprobada. "
    "En la duda, aprueba."
)

# El alcance estricto del runtime (decisión de Tomás, WS27): lo que está en la base
# ya lo controló la capa 1; al modelo se le piden tres cosas y ninguna más.
ALCANCE_RUNTIME = (
    "ALCANCE ESTRICTO — la carta la escribió una persona de la comunidad y este "
    "es su gate en runtime. Mira SOLO lo que sigue.\n\n"
    "Una capa determinística ya verificó por código, y NO tienes que volver a "
    "mirarlo: que el pilar y la acción inicial existen y forman un par viable "
    "(R8.1), los largos de la frase y del prompt (R8.3), que el prompt nombra el "
    "diario (R3.1) y el parecido literal contra el mazo vigente (R5.1/R5.2). Sus "
    "hallazgos te llegan en el mensaje como «hallazgos previos»: no los repitas ni "
    "los contradigas.\n\n"
    "Tu trabajo son tres cosas:\n\n"
    "(a) SEGURIDAD (S1-S3) → veredicto «rechaza», con fix_sugerido en null. "
    "Rechaza si hay insultos o faltas de respeto; contenido clínico o de riesgo "
    "(autolesión, trastornos, daño a terceros, consejo médico o psicológico); "
    "datos personales, marcas o promoción; proselitismo religioso o político; "
    "contenido sexual; o lenguaje que culpabilice o presione a quien la recibe.\n\n"
    "(b) ALINEACIÓN CON DWELLIA → veredicto «requiere_revision» con fix_sugerido "
    "concreto. Cuatro preguntas, ninguna más:\n"
    "  · R1.5 — ¿la frase ABRE la pausa? Leída sola, ¿da ganas de vivirla hoy? "
    "Una frase correcta pero inerte no entra.\n"
    "  · R2.5 — ¿la acción inicial, tal como está planteada, CONDUCE A LA CALMA? "
    "(no compite, no apura, no exige rendimiento, no enciende pantallas).\n"
    "  · R3.4 — ¿el cierre en el diario ABRE A LO SENTIDO, o se queda en el "
    "registro de hechos?\n"
    "  · R4.2 — ¿lo que pide escribir trabaja la FUNCIÓN del pilar (su "
    "pregunta-norte en los fundamentos), y no solo su tema?\n\n"
    "(c) CONCEPTO → devuelve siempre concepto_sugerido en kebab-case: el concepto "
    "EXISTENTE de una carta del mazo si esta es una variante de esa misma "
    "experiencia, o uno nuevo si la experiencia es nueva.\n\n"
    "El fix_sugerido respeta los límites de las cartas de la comunidad: frase de "
    "hasta {max_frase} caracteres · prompt de entre {min_prompt} y {max_prompt} "
    "caracteres · el prompt nombra el diario · español de España, tuteo, sin "
    "voseo. Es la carta de su autor: cambia lo mínimo para que entre, conserva su "
    "imagen y su voz.\n\n"
    "EN LA DUDA SOBRE ESTILO, APRUEBA. La poética, los clichés, las muletillas, el "
    "ritmo y el gusto no son tuyos: Dwellia los decide después, con una persona. "
    "Tu «requiere_revision» es para las cuatro preguntas de (b), nunca para "
    "mejorar una carta que ya entra."
).format(
    max_frase=MAX_FRASE_COMUNIDAD,
    min_prompt=MIN_PROMPT_COMUNIDAD,
    max_prompt=MAX_PROMPT_COMUNIDAD,
)


def _resumen_mazo(mazo: list) -> str:
    """El mazo entero (R5 necesita los prompts, no solo las frases). Va cacheado."""
    return "\n".join(
        "{id} · {categoria} · {accion} · {concepto}\n"
        "  frase: «{frase}»\n"
        "  prompt: «{prompt}»".format(
            id=c.get("id", "?"), categoria=c.get("categoria", "?"),
            accion=c.get("accion", "?"), concepto=c.get("concepto", "?"),
            frase=c.get("frase", ""), prompt=c.get("prompt", ""),
        )
        for c in mazo
    )


def _sistema(mazo: list, calibracion: str, alcance: str = "") -> list:
    """El system del juez: rol + calibración + alcance, y el bloque grande cacheado.

    El bloque 2 (canon + mazo, ~13k tokens) lleva `cache_control` ephemeral: la
    primera llamada tras cada deploy paga la escritura, el resto lee (≈1 céntimo).
    """
    cabecera = ROL + "\n\n" + calibracion
    if alcance:
        cabecera += "\n\n" + alcance
    return [
        {"type": "text", "text": cabecera},
        {
            "type": "text",
            "text": (
                "=== CANON (rule base) ===\n"
                + leer_canon()
                + "\n\n=== MAZO VIGENTE (para R5: conceptos y duplicados) ===\n"
                + _resumen_mazo(mazo)
            ),
            "cache_control": {"type": "ephemeral"},
        },
    ]


def _texto_de(respuesta) -> str:
    """El bloque de texto de la respuesta. Si no hay (se cortó por `max_tokens`,
    el modelo rehusó, etc.) levanta con el `stop_reason`, que es lo que hay que
    leer en `detalle["error"]`; un StopIteration pelado no decía nada."""
    for b in respuesta.content:
        if getattr(b, "type", None) == "text":
            return b.text
    raise ValueError(
        "la respuesta no trae texto (stop_reason={})".format(
            getattr(respuesta, "stop_reason", None))
    )


def _cliente():
    """El cliente Anthropic. Aislado acá para poder simularlo en los tests."""
    import anthropic

    return anthropic.Anthropic(api_key=settings.anthropic_api_key)


# ─────────────────────────────────────────────────────────────────────────────
# Capa 1 → hallazgos del contrato
# ─────────────────────────────────────────────────────────────────────────────
def _mayor(regla: str) -> bool:
    """Canon: R1-R5 y S son mayores; R6-R8 son menores."""
    return regla.startswith(("R1", "R2", "R3", "R4", "R5", "S"))


def _hallazgos_capa1(capa1: InformeCandidata) -> list:
    """Los hallazgos de la capa 1 en el formato del contrato."""
    salida = [
        {"regla": h["regla"], "mayor": _mayor(h["regla"]), "detalle": h["detalle"]}
        for h in list(capa1.errores) + list(capa1.avisos)
    ]
    for s in capa1.similares:
        salida.append({
            "regla": "R5.1",
            "mayor": True,
            "detalle": "se parece a la carta {id} ({campo}, {pct:.0%} de coincidencia)".format(
                id=s["id"], campo=s["campo"], pct=s["similitud"]
            ),
        })
    return salida


def _motivo_capa1(capa1: InformeCandidata) -> str:
    """La línea legible para el autor cuando frena la capa 1."""
    if capa1.errores:
        return capa1.errores[0]["motivo"]
    if capa1.similares:
        return "Se parece mucho a una carta que ya existe"
    return "Necesita un retoque"


def _sin_key(capa1: InformeCandidata, detalle: dict) -> Veredicto:
    """Sin key el juez está apagado, pero la capa 1 sigue protegiendo.

    Si encontró un error duro o un parecido por encima del umbral, la carta vuelve
    al autor con el motivo; si no, `off` y el llamador la manda a `revision_dwellia`.
    """
    hallazgos = _hallazgos_capa1(capa1)
    if not capa1.limpia():
        return Veredicto(
            resultado="requiere_revision",
            hallazgos=hallazgos,
            motivo=_motivo_capa1(capa1),
            detalle=detalle,
        )
    return Veredicto(
        resultado="off", hallazgos=hallazgos, motivo="juez apagado", detalle=detalle
    )


def _caido(capa1: InformeCandidata, detalle: dict) -> Veredicto:
    """El juez se cayó (red, JSON, modelo): SIEMPRE `off`, nunca una excepción.

    A diferencia del caso sin key, acá no se decide nada por cuenta propia: la
    propuesta va a `revision_dwellia` y Tomás ve los hallazgos de la capa 1 en el
    expediente. Una carta no vuelve al autor por una caída nuestra.
    """
    return Veredicto(
        resultado="off",
        hallazgos=_hallazgos_capa1(capa1),
        motivo="juez apagado",
        detalle=detalle,
    )


def _usage_dict(respuesta) -> Optional[dict]:
    usage = getattr(respuesta, "usage", None)
    if usage is None:
        return None
    for attr in ("model_dump", "dict", "to_dict"):
        metodo = getattr(usage, attr, None)
        if callable(metodo):
            try:
                return json.loads(json.dumps(metodo(), default=str))
            except Exception:
                continue
    try:
        return json.loads(json.dumps(vars(usage), default=str))
    except Exception:
        return None


def _motivo_modelo(resultado: str, hallazgos: list) -> str:
    """Una línea legible: el detalle del primer hallazgo mayor, o el primero."""
    if resultado == "aprueba":
        return "Lista para publicar"
    for h in hallazgos:
        if h.get("mayor") and h.get("detalle"):
            return str(h["detalle"])
    for h in hallazgos:
        if h.get("detalle"):
            return str(h["detalle"])
    return "No se pudo publicar" if resultado == "rechaza" else "Necesita un retoque"


# ─────────────────────────────────────────────────────────────────────────────
# EL CONTRATO
# ─────────────────────────────────────────────────────────────────────────────
def evaluar(propuesta: dict, mazo: list, categorias: set, acciones: set) -> Veredicto:
    """Juzga UNA propuesta de la comunidad. Nunca levanta: en el peor caso, `off`."""
    try:
        capa1 = validar_candidata(propuesta, mazo, categorias, acciones)
    except Exception as e:  # ni la capa 1 puede tumbar la propuesta de nadie.
        return Veredicto(
            resultado="off",
            motivo="juez apagado",
            detalle={"error": "{}: {}".format(type(e).__name__, e)},
        )
    detalle = {"capa1": capa1.como_dict()}

    if not settings.anthropic_api_key:
        return _sin_key(capa1, detalle)

    hallazgos_previos = _hallazgos_capa1(capa1)
    try:
        respuesta = _cliente().messages.create(
            model=settings.juez_modelo,
            max_tokens=MAX_TOKENS,
            system=_sistema(mazo, CALIBRACION_ALTA, ALCANCE_RUNTIME),
            messages=[{
                "role": "user",
                "content": (
                    "Evalúa esta carta candidata:\n"
                    + json.dumps(propuesta, ensure_ascii=False, indent=2)
                    + "\n\nHallazgos previos de la capa determinística "
                    "(ya verificados por código; no los repitas):\n"
                    + json.dumps(hallazgos_previos, ensure_ascii=False, indent=2)
                ),
            }],
            output_config={"format": {"type": "json_schema", "schema": ESQUEMA_VEREDICTO}},
            timeout=TIMEOUT_SEGUNDOS,
        )
        texto = _texto_de(respuesta)
        crudo = json.loads(texto)
        resultado = crudo["veredicto"]
    except Exception as e:  # red, JSON, esquema, modelo… el juez NUNCA levanta.
        detalle["error"] = "{}: {}".format(type(e).__name__, e)
        return _caido(capa1, detalle)

    detalle["modelo"] = {"crudo": crudo}
    usage = _usage_dict(respuesta)
    if usage is not None:
        detalle["modelo"]["usage"] = usage

    hallazgos = hallazgos_previos + list(crudo.get("hallazgos") or [])
    # La capa 1 manda sobre lo que ya verificó: si encontró un error duro o un
    # parecido, el modelo no puede publicar la carta por encima de ella.
    if resultado == "aprueba" and not capa1.limpia():
        resultado = "requiere_revision"
        detalle["degradado_por_capa1"] = True

    fix = crudo.get("fix_sugerido") or None
    if resultado == "rechaza":
        fix = None  # una S no se arregla con un retoque

    motivo = (
        _motivo_capa1(capa1)
        if detalle.get("degradado_por_capa1")
        # Primero lo que dijo el modelo (es lo que decidió el veredicto); la capa 1
        # solo habla si el modelo no dejó ningún hallazgo.
        else _motivo_modelo(resultado, list(crudo.get("hallazgos") or []) + hallazgos_previos)
    )
    return Veredicto(
        resultado=resultado,
        hallazgos=hallazgos,
        concepto=(crudo.get("concepto_sugerido") or None),
        fix=fix,
        motivo=motivo,
        detalle=detalle,
    )


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 2 en lote — la usa `scripts/validar_cartas.py --judge` (no el runtime)
# ─────────────────────────────────────────────────────────────────────────────
def juzgar_lote(cartas_a_juzgar: list, mazo: list, modelo: str,
                modo_regresion: bool = False) -> list:
    """Evalúa cada carta con Claude contra el canon COMPLETO. Devuelve los veredictos.

    modo_regresion=True (mazo aprobado): solo violaciones inequívocas — el mazo
    ya pasó curaduría humana y no se re-litigan elecciones de estilo aceptadas.
    modo_regresion=False (carta candidata nueva): severidad máxima, el gate real.

    A diferencia de `evaluar`, acá NO hay alcance recortado: es la pasada de
    curaduría del mazo propio, con el rubric entero.
    """
    try:
        import anthropic
    except ImportError:
        print("⚠️  capa judge: falta `pip install anthropic` — omitida.", file=sys.stderr)
        return []
    if not (settings.anthropic_api_key
            or os.environ.get("ANTHROPIC_API_KEY")
            or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        print("⚠️  capa judge: sin ANTHROPIC_API_KEY — omitida.", file=sys.stderr)
        return []

    client = anthropic.Anthropic(api_key=settings.anthropic_api_key or None)
    sistema = _sistema(
        mazo, CALIBRACION_REGRESION if modo_regresion else CALIBRACION_ALTA
    )

    veredictos = []
    for c in cartas_a_juzgar:
        respuesta = client.messages.create(
            model=modelo,
            max_tokens=MAX_TOKENS,
            system=sistema,
            messages=[{
                "role": "user",
                "content": "Evalúa esta carta candidata:\n"
                           + json.dumps(c, ensure_ascii=False, indent=2),
            }],
            output_config={"format": {"type": "json_schema", "schema": ESQUEMA_VEREDICTO}},
        )
        texto = _texto_de(respuesta)
        v = json.loads(texto)
        v["id"] = c.get("id", "(candidata)")
        veredictos.append(v)
        marca = {"aprueba": "✅", "requiere_revision": "🟡", "rechaza": "🔴"}[v["veredicto"]]
        print("  {} {}: {}".format(marca, v["id"], v["veredicto"])
              + (" — {} hallazgo(s)".format(len(v["hallazgos"])) if v["hallazgos"] else ""))
    return veredictos
