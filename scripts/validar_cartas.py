#!/usr/bin/env python3
"""Motor de validación de cartas (WS17) — el gate de calidad de M0.

Valida cartas contra el canon ejecutable (`M0_Motor_de_Contenido/canon_cartas.md`)
en dos capas:

  CAPA 1 · determinística (siempre, gratis, sin dependencias):
    estructura, matriz de afinidad, diario presente, longitudes, localismos,
    muletillas de mazo, conectores de diario, similitud entre cartas, conceptos.

  CAPA 2 · LLM-judge (opcional, `--judge`): Claude evalúa cada carta contra el
    rubric completo (coherencia frase↔prompt, poética, clichés, cuidado emocional,
    concepto, safety) con salida estructurada `aprueba / requiere_revision / rechaza`.
    Necesita ANTHROPIC_API_KEY y `pip install anthropic`.

Usos:
  python3 scripts/validar_cartas.py                  # capa 1 sobre todo el mazo
  python3 scripts/validar_cartas.py --judge          # capa 1 + judge sobre el mazo
  python3 scripts/validar_cartas.py --carta x.json   # validar UNA candidata nueva
                                                     # (el flujo premium de cartas
                                                     # de usuarios entra por acá)

Salida: informe legible + exit code 1 si hay errores (sirve de gate en CI).
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import unicodedata
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[1]
DATA = RAIZ / "M0_Motor_de_Contenido" / "data"
CANON = RAIZ / "M0_Motor_de_Contenido" / "canon_cartas.md"

# ── Parámetros del gate (espejo del canon R8 y R7) ───────────────────────────
MAX_FRASE = 75
MAX_PROMPT = 300

# Matriz de afinidad (Madre §1): pares categoría×acción viables (✅ y ○).
MATRIZ_VIABLE = {
    "gratitud": {"escribir", "contemplar", "caminar", "hacer"},
    "calma": {"escribir", "contemplar", "respirar", "caminar"},
    "perspectiva": {"escribir", "contemplar", "respirar", "caminar"},
    "resiliencia": {"escribir", "respirar", "caminar", "hacer"},
    "amor-propio": {"escribir", "contemplar", "respirar", "hacer"},
    "vinculos": {"escribir", "contemplar", "hacer"},
}

# R6 · localismos / voseo / calcos (regex, case-insensitive).
LOCALISMOS = [
    # Solo formas inequívocas: "hace"/"anda" (3ª persona) son español normal.
    (r"\bvos\b|\btenés\b|\bpodés\b|\bquerés\b|\bhacé\b|\bandá\b|\bfijate\b|\bmirá\b|\bescribí\b", "voseo"),
    (r"\bapur(arse|ate|es|o)\b", "apurarse (ES: darse prisa)"),
    (r"\bpostergar\b|\bposterga(ndo|da|do)?\b", "postergar (ES: dejar para luego)"),
    (r"\ba ning[uú]n lado\b", "a ningún lado (ES: a ningún sitio)"),
    (r"\b(date|regálate|darse) un gusto\b", "darse un gusto (ES: un capricho)"),
    (r"\bdate el m[eé]rito\b", "date el mérito (ES: reconócete el mérito)"),
    (r"\bc[oó]mo se siente\b", "calco del inglés (how it feels)"),
]

# R2.2 · supuestos prohibidos (heurístico → warning, el judge confirma).
SUPUESTOS = [
    (r"\bpareja\b|\bnovi[oa]\b|\bespos[oa]\b", "supone pareja"),
    (r"\bcompra\w*\b|\bdinero\b|\bgasta\w*\b", "supone dinero"),
    (r"\blluvia\b|\bsoleado\b|\bbuen tiempo\b", "supone clima"),
    (r"\bcuando te cruces\b|\bla pr[oó]xima vez que veas\b", "supone encuentro"),
]

# R7.1 · muletillas de mazo: máximo 1 uso por categoría.
MULETILLAS = [
    (r"\btambi[eé]n\b", "también", "frase"),
    (r"\bprisa\b", "prisa", "frase"),
    (r"\bDetente\b", "Detente a…", "prompt"),
    (r"qu[eé] despert[oó] en ti", "qué despertó en ti", "prompt"),
    (r"por peque[ñn]", "por pequeño/a que…", "prompt"),
    (r"a alguien que quieres", "como a alguien que quieres", "prompt"),
    (r"qu[eé] te llevas", "qué te llevas", "prompt"),
]

# Calibrado WS17: el mazo curado llega a ~0.67 de similitud puramente estructural
# ("Escribe en tu diario sobre…"); gemelas reales superan 0.72.
UMBRAL_SIMILITUD = 0.72


def _norm(s: str) -> str:
    s = unicodedata.normalize("NFD", s.lower())
    return "".join(c for c in s if unicodedata.category(c) != "Mn")


class Informe:
    def __init__(self) -> None:
        self.errores: list[str] = []       # rompen el gate (exit 1)
        self.avisos: list[str] = []        # R mayores probables → revisar
        self.observaciones: list[str] = [] # R menores / info

    def vacio(self) -> bool:
        return not (self.errores or self.avisos or self.observaciones)


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 1 · determinística
# ─────────────────────────────────────────────────────────────────────────────
def validar_deterministica(cartas: list[dict], categorias: set[str],
                           acciones: set[str]) -> Informe:
    inf = Informe()

    # R8.1 · estructura, slugs, matriz, ids/conceptos.
    ids = [c.get("id", "") for c in cartas]
    for cid, n in Counter(ids).items():
        if n > 1:
            inf.errores.append(f"id duplicado: {cid}")
    for c in cartas:
        cid = c.get("id", "?")
        for campo in ("id", "categoria", "accion", "concepto", "frase", "prompt"):
            if not c.get(campo):
                inf.errores.append(f"{cid}: falta el campo '{campo}'")
        if c.get("categoria") not in categorias:
            inf.errores.append(f"{cid}: categoría inexistente '{c.get('categoria')}'")
        if c.get("accion") not in acciones:
            inf.errores.append(f"{cid}: acción inexistente '{c.get('accion')}'")
        viables = MATRIZ_VIABLE.get(c.get("categoria"), set())
        if c.get("accion") and viables and c["accion"] not in viables:
            inf.errores.append(
                f"{cid}: el par {c['categoria']}×{c['accion']} está marcado 'evitar' en la matriz"
            )
        if c.get("concepto") and not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", c["concepto"]):
            inf.errores.append(f"{cid}: concepto '{c['concepto']}' no es kebab-case")

        frase, prompt = c.get("frase", ""), c.get("prompt", "")
        # R8.2 / R3.1
        if prompt and "diario" not in prompt.lower():
            inf.errores.append(f"{cid}: el prompt no menciona el diario")
        # R8.3
        if len(frase) > MAX_FRASE:
            inf.avisos.append(f"{cid}: frase de {len(frase)} caracteres (máx ~{MAX_FRASE})")
        if len(prompt) > MAX_PROMPT:
            inf.avisos.append(f"{cid}: prompt de {len(prompt)} caracteres (máx ~{MAX_PROMPT})")
        # R6
        for patron, etiqueta in LOCALISMOS:
            for campo, texto in (("frase", frase), ("prompt", prompt)):
                if re.search(patron, texto, re.IGNORECASE):
                    inf.avisos.append(f"{cid}: {etiqueta} en {campo}: «{texto[:60]}…»")
        # R2.2 (heurístico)
        for patron, etiqueta in SUPUESTOS:
            if re.search(patron, prompt, re.IGNORECASE):
                inf.avisos.append(f"{cid}: posible supuesto — {etiqueta}")

    # R7.1 · muletillas por categoría (>1 uso = observación).
    for patron, etiqueta, campo in MULETILLAS:
        por_cat: dict[str, list[str]] = defaultdict(list)
        for c in cartas:
            if re.search(patron, c.get(campo, ""), re.IGNORECASE):
                por_cat[c["categoria"]].append(c["id"])
        for cat, lista in sorted(por_cat.items()):
            if len(lista) > 1:
                inf.observaciones.append(
                    f"muletilla «{etiqueta}» ×{len(lista)} en {cat}: {', '.join(lista)}"
                )

    # R7.2 · distribución del conector al diario (info).
    conectores = Counter()
    for c in cartas:
        p = c.get("prompt", "")
        if re.match(r"escribe en tu diario", p, re.IGNORECASE):
            conectores["(acción escribir — integrado)"] += 1
        elif re.search(r"Despu[eé]s escribe", p):
            conectores["Después escribe…"] += 1
        elif re.search(r"Luego escr[ií]be", p):
            conectores["Luego escribe…"] += 1
        else:
            conectores["tejido/otro"] += 1
    inf.observaciones.append(
        "conectores al diario: "
        + " · ".join(f"{k} {v}" for k, v in conectores.most_common())
    )

    # R5.1 / R5.2 · similitud entre cartas con conceptos DISTINTOS.
    for i, a in enumerate(cartas):
        for b in cartas[i + 1:]:
            if a.get("concepto") == b.get("concepto"):
                continue  # gemelas declaradas: el motor ya las desduplica
            sim = SequenceMatcher(None, _norm(a["prompt"]), _norm(b["prompt"])).ratio()
            if sim >= UMBRAL_SIMILITUD:
                inf.avisos.append(
                    f"prompts muy parecidos ({sim:.0%}) con concepto distinto: "
                    f"{a['id']} ({a['concepto']}) vs {b['id']} ({b['concepto']})"
                )

    # Conceptos compartidos (info, sanidad).
    comp = {k: v for k, v in Counter(c["concepto"] for c in cartas if c.get("concepto")).items() if v > 1}
    if comp:
        inf.observaciones.append(
            f"conceptos compartidos (variantes deliberadas): {len(comp)} → "
            + ", ".join(sorted(comp))
        )
    return inf


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 2 · LLM-judge (rubric = canon_cartas.md)
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


def juzgar(cartas_a_juzgar: list[dict], mazo: list[dict], modelo: str,
           modo_regresion: bool = False) -> list[dict]:
    """Evalúa cada carta con Claude contra el canon. Devuelve los veredictos.

    modo_regresion=True (mazo aprobado): solo violaciones inequívocas — el mazo
    ya pasó curaduría humana y no se re-litigan elecciones de estilo aceptadas.
    modo_regresion=False (carta candidata nueva): severidad máxima, el gate real.
    """
    try:
        import anthropic
    except ImportError:
        print("⚠️  capa judge: falta `pip install anthropic` — omitida.", file=sys.stderr)
        return []
    if not (os.environ.get("ANTHROPIC_API_KEY") or os.environ.get("ANTHROPIC_AUTH_TOKEN")):
        print("⚠️  capa judge: sin ANTHROPIC_API_KEY — omitida.", file=sys.stderr)
        return []

    client = anthropic.Anthropic()
    canon = CANON.read_text(encoding="utf-8")
    # Mazo completo para R5 (dedup de concepto Y guion físico): el judge necesita
    # los prompts, no solo las frases. Va cacheado, el tamaño no duele.
    resumen = "\n".join(
        f"{c['id']} · {c['categoria']} · {c['accion']} · {c['concepto']}\n"
        f"  frase: «{c['frase']}»\n"
        f"  prompt: «{c['prompt']}»"
        for c in mazo
    )
    calibracion = (
        # Modo regresión: el mazo ya pasó curaduría humana (WS17). No es una
        # re-curaduría: es un detector de regresiones e incumplimientos duros.
        "MODO REGRESIÓN: la carta que vas a evaluar YA pertenece al mazo aprobado "
        "por curaduría humana. Señala SOLO incumplimientos claros e inequívocos — "
        "los que justificarían rechazar la carta si fuera nueva. NO propongas "
        "mejoras de gusto, reformulaciones opcionales ni señales 'podría ser más "
        "concreta/única': si una elección de estilo es defendible, está aprobada. "
        "En la duda, aprueba."
        if modo_regresion else
        # Modo alta: el gate real para cartas candidatas (UGC premium incluido).
        "MODO ALTA: la carta es una candidata NUEVA que pide entrar al mazo. "
        "Aplica el canon con severidad completa, regla por regla."
    )
    sistema = [
        {
            "type": "text",
            "text": (
                "Eres el juez de calidad de cartas de Dwellia, una app de pausas de "
                "mindfulness. Evalúas cada carta contra el canon (rule base) que "
                "sigue, regla por regla. Eres exigente pero justo: señalas solo "
                "incumplimientos reales, citando la regla (R1.1…S3). 'mayor' = true para "
                "R1-R5 y S; false para R6-R8. Si el veredicto es requiere_revision, "
                "propones un fix concreto (frase y/o prompt alternativos) que respete el "
                "canon. Sugieres siempre el concepto (kebab-case): el existente si la "
                "carta es variante deliberada de otra, o uno nuevo.\n\n"
                + calibracion
                + "\n\n=== CANON ===\n"
                + canon
                + "\n\n=== MAZO VIGENTE (para R5: conceptos y duplicados) ===\n"
                + resumen
            ),
            "cache_control": {"type": "ephemeral"},
        }
    ]

    veredictos = []
    for c in cartas_a_juzgar:
        respuesta = client.messages.create(
            model=modelo,
            max_tokens=2000,
            system=sistema,
            messages=[{
                "role": "user",
                "content": "Evalúa esta carta candidata:\n" + json.dumps(c, ensure_ascii=False, indent=2),
            }],
            output_config={"format": {"type": "json_schema", "schema": ESQUEMA_VEREDICTO}},
        )
        texto = next(b.text for b in respuesta.content if b.type == "text")
        v = json.loads(texto)
        v["id"] = c.get("id", "(candidata)")
        veredictos.append(v)
        marca = {"aprueba": "✅", "requiere_revision": "🟡", "rechaza": "🔴"}[v["veredicto"]]
        print(f"  {marca} {v['id']}: {v['veredicto']}"
              + (f" — {len(v['hallazgos'])} hallazgo(s)" if v["hallazgos"] else ""))
    return veredictos


# ─────────────────────────────────────────────────────────────────────────────
def main() -> int:
    ap = argparse.ArgumentParser(description="Validador de cartas Dwellia (canon WS17)")
    ap.add_argument("--carta", help="JSON con UNA carta candidata (modo alta de carta nueva)")
    ap.add_argument("--judge", action="store_true", help="correr también la capa LLM-judge")
    ap.add_argument("--model", default="claude-opus-4-8", help="modelo del judge")
    ap.add_argument("--json", action="store_true", help="salida JSON (para integrar)")
    args = ap.parse_args()

    mazo = json.loads((DATA / "cartas.json").read_text(encoding="utf-8"))
    categorias = {c["slug"] for c in json.loads((DATA / "categorias.json").read_text(encoding="utf-8"))}
    acciones = {a["slug"] for a in json.loads((DATA / "acciones.json").read_text(encoding="utf-8"))}

    if args.carta:
        candidata = json.loads(Path(args.carta).read_text(encoding="utf-8"))
        candidata.setdefault("id", "(candidata)")
        a_validar = [candidata]
        universo = mazo + [candidata]  # similitud/conceptos contra el mazo real
    else:
        a_validar = mazo
        universo = mazo

    inf = validar_deterministica(universo, categorias, acciones)

    veredictos = []
    if args.judge:
        # Sin --carta = mazo aprobado → modo regresión. Con --carta = alta nueva.
        modo_regresion = not args.carta
        etiqueta = "regresión sobre el mazo" if modo_regresion else "alta de candidata"
        print(f"— capa judge ({args.model}) · modo {etiqueta} · {len(a_validar)} carta(s) —")
        veredictos = juzgar(a_validar, mazo, args.model, modo_regresion=modo_regresion)

    if args.json:
        print(json.dumps({
            "errores": inf.errores, "avisos": inf.avisos,
            "observaciones": inf.observaciones, "judge": veredictos,
        }, ensure_ascii=False, indent=2))
    else:
        print(f"\n=== VALIDADOR DE CARTAS · {len(a_validar)} carta(s) ===")
        for titulo, lista, marca in (("ERRORES (gate)", inf.errores, "🔴"),
                                     ("AVISOS (revisar)", inf.avisos, "🟡"),
                                     ("OBSERVACIONES", inf.observaciones, "·")):
            print(f"\n{titulo}: {len(lista)}")
            for item in lista:
                print(f"  {marca} {item}")
        if args.judge and veredictos:
            problematicas = [v for v in veredictos if v["veredicto"] != "aprueba"]
            print(f"\nJUDGE: {len(veredictos) - len(problematicas)} aprueban · "
                  f"{len(problematicas)} con reparos")
            for v in problematicas:
                print(f"\n  {v['id']} → {v['veredicto']}")
                for h in v["hallazgos"]:
                    print(f"    [{h['regla']}{' · mayor' if h['mayor'] else ''}] {h['detalle']}")
                if v.get("fix_sugerido"):
                    print(f"    fix → frase: «{v['fix_sugerido']['frase']}»")
                    print(f"          prompt: «{v['fix_sugerido']['prompt']}»")

    rechazadas = [v for v in veredictos if v["veredicto"] == "rechaza"]
    return 1 if (inf.errores or rechazadas) else 0


if __name__ == "__main__":
    sys.exit(main())
