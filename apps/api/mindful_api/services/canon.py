"""WS27 · B1.2 · CAPA 1 del juez de cartas: determinística, gratis, sin modelo.

Es el motor que hasta la WS27 vivía dentro de `scripts/validar_cartas.py`. Ahora
vive acá y el CLI lo importa: **una regla, un solo lugar**.

Dos entradas, la misma rule base (`M0_Motor_de_Contenido/canon_cartas.md`):

  `validar_deterministica(cartas, categorias, acciones)` → el MAZO entero (el CLI,
  gate de CI): estructura, matriz de afinidad, diario, largos, localismos,
  supuestos, muletillas de mazo, conectores y similitud entre cartas.

  `validar_candidata(propuesta, mazo, categorias, acciones)` → UNA propuesta de un
  usuario (el runtime de `services/juez.py`): errores duros, avisos y parecidos
  contra el mazo vigente.

Todo lo que esta capa ya verificó, el juez LLM NO lo vuelve a mirar (ver el
alcance estricto en `services/juez.py`).
"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Optional


# ─────────────────────────────────────────────────────────────────────────────
# Rutas al canon · UN SOLO LUGAR
# En el repo: <raíz>/M0_Motor_de_Contenido/…  ·  en la imagen Docker el Dockerfile
# copia esos dos .md a /app/M0_Motor_de_Contenido/ y el código vive en
# /app/apps/api/mindful_api/… , así que la misma subida de directorios sirve en
# los dos sitios. Igual se busca hacia arriba, para no romperse si el layout cambia.
# ─────────────────────────────────────────────────────────────────────────────
def _dir_contenido() -> Path:
    aqui = Path(__file__).resolve()
    for padre in aqui.parents:
        candidato = padre / "M0_Motor_de_Contenido"
        if (candidato / "canon_cartas.md").is_file():
            return candidato
    return aqui.parents[4] / "M0_Motor_de_Contenido"


M0_DIR = _dir_contenido()
CANON_PATH = M0_DIR / "canon_cartas.md"
FUNDAMENTOS_PATH = M0_DIR / "fundamentos_pilares.md"

_canon_cacheado: Optional[str] = None


def leer_canon() -> str:
    """El rubric completo: canon ejecutable + fundamentos (R4.2 los cita).

    Se lee una sola vez por proceso: es lo que va cacheado en el prompt del juez.
    """
    global _canon_cacheado
    if _canon_cacheado is None:
        _canon_cacheado = (
            CANON_PATH.read_text(encoding="utf-8")
            + "\n\n=== FUNDAMENTOS DE LOS PILARES "
            "(la teoría; R4.2 mira la FUNCIÓN del pilar, no su tema) ===\n\n"
            + FUNDAMENTOS_PATH.read_text(encoding="utf-8")
        )
    return _canon_cacheado


# ── Parámetros del gate (espejo del canon R8 y R7) ───────────────────────────
MAX_FRASE = 75      # R8.3 · el mazo propio
MAX_PROMPT = 300    # R8.3 · el mazo propio

# Límites de las cartas de la COMUNIDAD (Roadmap v2 §0, más estrictos que R8.3).
# Los aplica `routers/cartas_comunidad.py` con 422; acá viven para que el fix que
# propone el juez los respete.
MAX_FRASE_COMUNIDAD = 60
MIN_PROMPT_COMUNIDAD = 100
MAX_PROMPT_COMUNIDAD = 220

# R8.1 · el concepto es kebab-case y cabe en la columna (`cartas_comunidad.concepto`
# es String(80)). El juez sugiere conceptos con un modelo: la forma se impone acá.
MAX_CONCEPTO = 80

# Matriz de afinidad (canon R8.1, WS22): pares pilar×acción inicial viables.
# "escribir" ya no es acción inicial (cierre universal); slug `caminar` se muestra "pasear".
MATRIZ_VIABLE = {
    "gratitud": {"contemplar", "caminar", "hacer"},
    "sentido": {"contemplar", "respirar", "caminar", "hacer"},
    "perspectiva": {"contemplar", "respirar", "caminar"},
    "resiliencia": {"respirar", "caminar", "hacer"},
    "amor-propio": {"contemplar", "respirar", "hacer"},
    "vinculos": {"contemplar", "caminar", "hacer"},
}

# R6 · localismos / voseo / calcos (regex, case-insensitive) con la sub-regla.
LOCALISMOS = [
    # Solo formas inequívocas: "hace"/"anda" (3ª persona) son español normal.
    (r"\bvos\b|\btenés\b|\bpodés\b|\bquerés\b|\bhacé\b|\bandá\b|\bfijate\b|\bmirá\b|\bescribí\b",
     "voseo", "R6.1"),
    (r"\bapur(arse|ate|es|o)\b", "apurarse (ES: darse prisa)", "R6.2"),
    # WS27: "acá" no está en el mazo propio (0 usos) pero sí llega en las cartas
    # de la comunidad — R6.2 lo pide igual que "afuera" estático.
    (r"\bac[aá]\b", "acá (ES: aquí)", "R6.2"),
    (r"\bpostergar\b|\bposterga(ndo|da|do)?\b", "postergar (ES: dejar para luego)", "R6.2"),
    (r"\ba ning[uú]n lado\b", "a ningún lado (ES: a ningún sitio)", "R6.2"),
    (r"\b(date|regálate|darse) un gusto\b", "darse un gusto (ES: un capricho)", "R6.2"),
    (r"\bdate el m[eé]rito\b", "date el mérito (ES: reconócete el mérito)", "R6.2"),
    (r"\bc[oó]mo se siente\b", "calco del inglés (how it feels)", "R6.3"),
]

# R2.2 · supuestos prohibidos (heurístico → aviso, el juez confirma).
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


def _similitud(a: str, b: str) -> float:
    return SequenceMatcher(None, _norm(a), _norm(b)).ratio()


def a_kebab(valor, maximo: int = MAX_CONCEPTO) -> Optional[str]:
    """Un texto cualquiera → concepto kebab-case, o None si no queda nada.

    Minúsculas, sin acentos, todo lo que no sea `[a-z0-9]` pasa a guion, sin
    guiones en los bordes y recortado a `maximo` caracteres (la columna). Lo usa
    el juez con lo que sugiere el modelo: «No Es Kebab Case» → `no-es-kebab-case`.
    """
    if not isinstance(valor, str):
        return None
    kebab = re.sub(r"[^a-z0-9]+", "-", _norm(valor)).strip("-")
    if maximo:
        kebab = kebab[:maximo].strip("-")
    return kebab or None


class Informe:
    """Informe del MAZO entero (lo que imprime el CLI). Listas de texto plano."""

    def __init__(self) -> None:
        self.errores: list = []        # rompen el gate (exit 1)
        self.avisos: list = []         # R mayores probables → revisar
        self.observaciones: list = []  # R menores / info

    def vacio(self) -> bool:
        return not (self.errores or self.avisos or self.observaciones)


@dataclass
class InformeCandidata:
    """Informe de UNA propuesta de la comunidad (lo que consume `juez.evaluar`).

    `errores` y `avisos` son dicts `{"regla", "detalle", "motivo"}`:
      · `detalle` = la explicación técnica (va al expediente y al prompt del juez).
      · `motivo`  = la línea legible que puede leer el autor.
    `similares` = `[{"id", "campo", "similitud"}]` con similitud ≥ UMBRAL_SIMILITUD.
    """

    errores: list = field(default_factory=list)
    avisos: list = field(default_factory=list)
    similares: list = field(default_factory=list)

    def limpia(self) -> bool:
        """Sin nada que frene: ni errores duros ni parecidos por encima del umbral."""
        return not (self.errores or self.similares)

    def como_dict(self) -> dict:
        return {"errores": self.errores, "avisos": self.avisos, "similares": self.similares}


def _hallazgo(regla: str, detalle: str, motivo: str) -> dict:
    return {"regla": regla, "detalle": detalle, "motivo": motivo}


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 1 · el MAZO entero (gate del CLI / CI)
# ─────────────────────────────────────────────────────────────────────────────
def validar_deterministica(cartas: list, categorias: set, acciones: set) -> Informe:
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
        # La matriz solo se consulta si los DOS slugs existen: si la acción no
        # existe, el error es ese y ninguno más (no se inventa un par inviable).
        viables = MATRIZ_VIABLE.get(c.get("categoria"), set())
        if (c.get("categoria") in categorias and c.get("accion") in acciones
                and viables and c["accion"] not in viables):
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
        for patron, etiqueta, _regla in LOCALISMOS:
            for campo, texto in (("frase", frase), ("prompt", prompt)):
                if re.search(patron, texto, re.IGNORECASE):
                    inf.avisos.append(f"{cid}: {etiqueta} en {campo}: «{texto[:60]}…»")
        # R2.2 (heurístico)
        for patron, etiqueta in SUPUESTOS:
            if re.search(patron, prompt, re.IGNORECASE):
                inf.avisos.append(f"{cid}: posible supuesto — {etiqueta}")

    # R7.1 · muletillas por categoría (>1 uso = observación).
    for patron, etiqueta, campo in MULETILLAS:
        por_cat: dict = defaultdict(list)
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
            conectores["(arranca en el diario — revisar: falta acción inicial)"] += 1
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
            sim = _similitud(a["prompt"], b["prompt"])
            if sim >= UMBRAL_SIMILITUD:
                inf.avisos.append(
                    f"prompts muy parecidos ({sim:.0%}) con concepto distinto: "
                    f"{a['id']} ({a['concepto']}) vs {b['id']} ({b['concepto']})"
                )

    # Conceptos compartidos (info, sanidad).
    comp = {
        k: v
        for k, v in Counter(c["concepto"] for c in cartas if c.get("concepto")).items()
        if v > 1
    }
    if comp:
        inf.observaciones.append(
            f"conceptos compartidos (variantes deliberadas): {len(comp)} → "
            + ", ".join(sorted(comp))
        )
    return inf


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 1 · UNA candidata de la comunidad (runtime)
# ─────────────────────────────────────────────────────────────────────────────
def validar_candidata(propuesta: dict, mazo: list, categorias: set,
                      acciones: set) -> InformeCandidata:
    """Lo que se puede decidir SIN modelo sobre una propuesta de un usuario.

    propuesta = {"categoria", "accion", "frase", "prompt"} (los slugs ya vienen
    del wizard, pero acá no se confía en nadie).

    Errores duros: estructura y matriz (R8.1), los largos de la comunidad
    (R8.3 · frase ≤60 · prompt 100-220) y el cierre en el diario (R3.1). El
    `concepto` NO se pide: lo sugiere el juez, no lo escribe el autor.
    """
    inf = InformeCandidata()
    categoria = (propuesta.get("categoria") or "").strip()
    accion = (propuesta.get("accion") or "").strip()
    frase = propuesta.get("frase") or ""
    prompt = propuesta.get("prompt") or ""

    # ── Errores duros (R8.1 · estructura y matriz) ───────────────────────────
    for campo, valor in (("categoria", categoria), ("accion", accion),
                         ("frase", frase.strip()), ("prompt", prompt.strip())):
        if not valor:
            inf.errores.append(_hallazgo(
                "R8.1", f"falta el campo '{campo}'",
                "La carta está incompleta",
            ))

    if categoria and categoria not in categorias:
        inf.errores.append(_hallazgo(
            "R8.1", f"pilar inexistente '{categoria}'",
            "Ese pilar no existe en Dwellia",
        ))
    if accion and accion not in acciones:
        inf.errores.append(_hallazgo(
            "R8.1", f"acción inicial inexistente '{accion}'",
            "Esa acción inicial no existe en Dwellia",
        ))
    # La matriz solo se consulta si los DOS slugs EXISTEN. Si la acción no existe,
    # el error es ese y ninguno más: preguntarle a la matriz por un slug que no
    # está en ella inventaba un segundo error ("el par X×Y está marcado evitar")
    # que no dice la verdad y confunde al autor.
    viables = MATRIZ_VIABLE.get(categoria, set())
    if (categoria in categorias and accion in acciones
            and viables and accion not in viables):
        inf.errores.append(_hallazgo(
            "R8.1",
            f"el par {categoria}×{accion} está marcado 'evitar' en la matriz de afinidad",
            "Ese pilar y esa acción inicial no combinan",
        ))

    # ── Errores duros (R8.3 · los largos de la COMUNIDAD) ────────────────────
    # Los mide esta capa, no solo el router de B1.1: el juez le AFIRMA al modelo
    # que los largos ya están verificados (ver `ALCANCE_RUNTIME`), así que
    # cualquier llamador —el CLI, un reproceso, un test— tiene que quedar cubierto
    # por el mismo código. Se miden sobre el texto sin espacios de los bordes; si
    # el campo está vacío ya lo dijo R8.1 más arriba y acá no se repite.
    frase_medida, prompt_medido = frase.strip(), prompt.strip()
    if frase_medida and len(frase_medida) > MAX_FRASE_COMUNIDAD:
        inf.errores.append(_hallazgo(
            "R8.3",
            f"frase de {len(frase_medida)} caracteres (máx {MAX_FRASE_COMUNIDAD})",
            f"La frase no puede pasar de {MAX_FRASE_COMUNIDAD} caracteres",
        ))
    if prompt_medido and len(prompt_medido) < MIN_PROMPT_COMUNIDAD:
        inf.errores.append(_hallazgo(
            "R8.3",
            f"prompt de {len(prompt_medido)} caracteres (mín {MIN_PROMPT_COMUNIDAD})",
            f"El prompt tiene que medir al menos {MIN_PROMPT_COMUNIDAD} caracteres",
        ))
    if prompt_medido and len(prompt_medido) > MAX_PROMPT_COMUNIDAD:
        inf.errores.append(_hallazgo(
            "R8.3",
            f"prompt de {len(prompt_medido)} caracteres (máx {MAX_PROMPT_COMUNIDAD})",
            f"El prompt no puede pasar de {MAX_PROMPT_COMUNIDAD} caracteres",
        ))

    # ── Error duro (R3.1 · el cierre en el diario es universal) ──────────────
    if prompt and "diario" not in prompt.lower():
        inf.errores.append(_hallazgo(
            "R3.1", "el prompt no menciona el diario",
            "El prompt no cierra en el diario",
        ))

    # ── Avisos (R6 · localismos y calcos) ────────────────────────────────────
    for patron, etiqueta, regla in LOCALISMOS:
        for campo, texto in (("frase", frase), ("prompt", prompt)):
            if re.search(patron, texto, re.IGNORECASE):
                inf.avisos.append(_hallazgo(
                    regla, f"{etiqueta} en {campo}: «{texto[:60]}…»",
                    "Hay una expresión que no es del español de España",
                ))

    # ── Avisos (R2.2 · supuestos, heurístico) ────────────────────────────────
    for patron, etiqueta in SUPUESTOS:
        if re.search(patron, prompt, re.IGNORECASE):
            inf.avisos.append(_hallazgo(
                "R2.2", f"posible supuesto — {etiqueta}",
                "La carta puede no servir para cualquier persona cualquier día",
            ))

    # ── Avisos (R7.1 · muletillas ya cargadas en ese pilar) ──────────────────
    for patron, etiqueta, campo in MULETILLAS:
        texto = frase if campo == "frase" else prompt
        if not re.search(patron, texto, re.IGNORECASE):
            continue
        ya_usada = [
            c["id"] for c in mazo
            if c.get("categoria") == categoria
            and re.search(patron, c.get(campo, ""), re.IGNORECASE)
        ]
        if ya_usada:
            inf.avisos.append(_hallazgo(
                "R7.1",
                f"muletilla «{etiqueta}» en {campo}; ya está en {categoria}: "
                + ", ".join(ya_usada[:3]),
                "Esa forma de decirlo ya se repite en el mazo",
            ))

    # ── Parecidos (R5.1 · una experiencia, una carta) ────────────────────────
    for c in mazo:
        for campo, texto in (("frase", c.get("frase", "")), ("prompt", c.get("prompt", ""))):
            propio = frase if campo == "frase" else prompt
            if not (propio and texto):
                continue
            sim = _similitud(propio, texto)
            if sim >= UMBRAL_SIMILITUD:
                inf.similares.append({
                    "id": c.get("id"),
                    "campo": campo,
                    "similitud": round(sim, 4),
                })
    inf.similares.sort(key=lambda s: s["similitud"], reverse=True)

    return inf
