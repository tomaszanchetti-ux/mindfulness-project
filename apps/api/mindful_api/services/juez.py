"""WS27 · B1.2 · El juez de cartas de la comunidad.

ESQUELETO del orquestador (B0): define el CONTRATO que B1.1 consume. La card
B1.2 lo llena portando `scripts/validar_cartas.py` (capa 1 → `services/canon.py`,
capa 2 → acá, con Claude, canon cacheado y structured output).

Contrato:
  evaluar(propuesta, mazo, categorias, acciones) -> Veredicto
    propuesta = {"categoria", "accion", "frase", "prompt"}  (slugs ya validados)
    mazo      = [{"id","categoria","accion","concepto","frase","prompt"}, ...]
    categorias / acciones = sets de slugs válidos
  Veredicto.resultado ∈ {"aprueba", "requiere_revision", "rechaza", "off"}
    off = sin `MINDFUL_ANTHROPIC_API_KEY` (o error de red): el llamador manda la
    propuesta a `revision_dwellia` y sigue. El juez NUNCA levanta.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Veredicto:
    resultado: str                       # aprueba | requiere_revision | rechaza | off
    hallazgos: list = field(default_factory=list)   # [{"regla","mayor","detalle"}]
    concepto: Optional[str] = None       # kebab-case sugerido
    fix: Optional[dict] = None           # {"frase","prompt"} si requiere_revision
    motivo: Optional[str] = None         # una línea legible para el autor
    detalle: dict = field(default_factory=dict)     # lo crudo (capa 1 + respuesta del modelo)


def evaluar(propuesta: dict, mazo: list, categorias: set, acciones: set) -> Veredicto:
    """ESQUELETO: hasta que B1.2 lo llene, el juez está apagado."""
    return Veredicto(resultado="off", motivo="juez no configurado")
