"""WS27 · B1.3 · Administración (Tomás): revisar y aprobar cartas, leer comentarios.

TODO endpoint de acá cuelga de `Depends(get_admin)`: sin uid en
`MINDFUL_ADMIN_UIDS` la respuesta es 403 antes de tocar la base. El default es
la lista vacía, o sea que el panel nace CERRADO: en un despliegue nuevo nadie es
admin hasta que se declara explícitamente quién.

Los modelos de entrada viven acá (y no en `schemas.py`) porque no los usa nadie
más: son el formulario del panel, no el contrato público de la app.
"""

from __future__ import annotations

import re
import unicodedata
from typing import Optional

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel, Field, field_validator
from sqlalchemy.orm import Session

from ..auth import get_admin
from ..db.base import get_session
from ..db.models import Usuario
from ..services.admin import (
    COMENTARIOS_LIMIT_DEFAULT,
    ESTADO_DEFAULT,
    aprobar as aprobar_carta,
    listar_cartas,
    listar_comentarios,
    marcar_a_revisar,
    rechazar as rechazar_carta,
    resumen as resumen_admin,
)
from ..services.cartas_comunidad import FRASE_MAX, PROMPT_MAX, PROMPT_MIN

router = APIRouter(prefix="/api/admin", tags=["admin"])


def _limpio(v):
    """strip() y blanco puro → None: el largo se mide sobre los caracteres útiles."""
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


# El concepto es un SLUG, no un título: `scripts/validar_cartas.py` (capa 1, R8)
# exige `[a-z0-9-]+` y M2 lo usa como huella de dedupe semanal. Tomás escribe en
# un input libre ("Gratitud POR el Día!!"), así que se normaliza acá.
CONCEPTO_MAX = 80


def _kebab(v):
    """"  Gratitud POR el Día!!  " → "gratitud-por-el-dia". Vacío → None.

    Sin acentos (NFKD y se descartan los diacríticos), en minúscula, y todo lo
    que no sea `[a-z0-9]` pasa a ser un guion — colapsado y sin guiones en los
    bordes. NO se recorta a `CONCEPTO_MAX`: un concepto más largo que la columna
    es un 422 del borde Pydantic, no un texto cortado a la mitad a escondidas.
    """
    v = _limpio(v)
    if not isinstance(v, str):
        return v
    v = unicodedata.normalize("NFKD", v)
    v = "".join(ch for ch in v if not unicodedata.combining(ch))
    v = re.sub(r"[^a-z0-9]+", "-", v.lower()).strip("-")
    return v or None


class AprobarBody(BaseModel):
    """El concepto es la huella de dedupe (M2 no repite concepto en la ventana
    semanal). Si Tomás no escribe uno, se usa el que propuso el juez y, si no hay,
    uno derivado del id — nunca se publica una carta sin concepto."""

    concepto: Optional[str] = Field(default=None, max_length=CONCEPTO_MAX)

    @field_validator("concepto", mode="before")
    @classmethod
    def _slug(cls, v):
        return _kebab(v)


class RechazarBody(BaseModel):
    """El motivo NO es opcional: una carta no aprobada siempre se explica."""

    motivo: str = Field(min_length=1, max_length=300)

    @field_validator("motivo", mode="before")
    @classmethod
    def _strip(cls, v):
        return _limpio(v)


class FixSugerido(BaseModel):
    """La frase/prompt que Tomás propone. Ambos opcionales: se puede sugerir solo uno.

    Q/A B1.3 (BUG-B13-6): los límites son los MISMOS del contrato (`FRASE_MAX`,
    `PROMPT_MIN`/`PROMPT_MAX` de B1.1), no unos propios más anchos. Una sugerencia
    tiene que ser APLICABLE: si Tomás sugiere una frase de 61, el autor la copia,
    la reenvía y el PUT se la rechaza con 422 — una trampa. Se mide sobre el texto
    ya strippeado, igual que en B1.1.
    """

    frase: Optional[str] = None
    prompt: Optional[str] = None

    @field_validator("frase", mode="before")
    @classmethod
    def _v_frase(cls, v):
        v = _limpio(v)
        if isinstance(v, str) and len(v) > FRASE_MAX:
            raise ValueError(f"La frase no puede pasar de {FRASE_MAX} caracteres.")
        return v

    @field_validator("prompt", mode="before")
    @classmethod
    def _v_prompt(cls, v):
        v = _limpio(v)
        if isinstance(v, str) and not (PROMPT_MIN <= len(v) <= PROMPT_MAX):
            raise ValueError(
                f"El prompt tiene que medir entre {PROMPT_MIN} y {PROMPT_MAX} caracteres."
            )
        return v


class ARevisarBody(BaseModel):
    """`sugerencia` es lo que el autor lee; `fix` es opcional (el retoque concreto)."""

    sugerencia: str = Field(min_length=1, max_length=500)
    fix: Optional[FixSugerido] = None

    @field_validator("sugerencia", mode="before")
    @classmethod
    def _strip(cls, v):
        return _limpio(v)


@router.get("/resumen")
def resumen(
    s: Session = Depends(get_session),
    admin: Usuario = Depends(get_admin),
) -> dict:
    """WS27 · B2.1 · El tablero del adminland, en una sola lectura.

    Cuatro bloques: el mazo (total, propias, de la comunidad, y los 6 pilares en
    el orden del reloj) · las propuestas por estado (+ `pendientes`) · la gente
    (cuánta hay, cuánta terminó el onboarding, cuánta paga, cuánta escribe) · los
    comentarios (todos y los de la última semana).

    Decisión de Tomás (WS27 §6): NADA por usuario individual. El tablero es del
    sistema; sirve para ver si un pilar quedó desparejo y escribir cartas de
    Dwellia para emparejarlo.
    """
    return resumen_admin(s)


@router.get("/cartas")
def cartas(
    estado: str = Query(default=ESTADO_DEFAULT),
    s: Session = Depends(get_session),
    admin: Usuario = Depends(get_admin),
) -> list:
    """La bandeja de propuestas, más nueva primero.

    Por defecto solo lo que espera decisión (`revision_dwellia`);
    `estado=pendientes` suma lo que todavía tiene el juez (`en_revision`), y
    `estado=todas` muestra el recorrido completo. Cada ítem trae la carta ya
    armada con la misma forma que sirve la app, para dibujarla con el componente
    de siempre, y el funnel entero: `historial` (v1) · `veredicto` +
    `veredicto_resumen` (v2) · `estado`/`motivo`/`carta_id` (vFinal).
    """
    return listar_cartas(s, estado)


@router.post("/cartas/{carta_comunidad_id}/aprobar")
def aprobar(
    carta_comunidad_id: str,
    body: Optional[AprobarBody] = None,
    s: Session = Depends(get_session),
    admin: Usuario = Depends(get_admin),
) -> dict:
    """Aprobar = CARGAR al mazo: publica la carta en `cartas` y avisa al autor."""
    return aprobar_carta(s, carta_comunidad_id, concepto=None if body is None else body.concepto)


@router.post("/cartas/{carta_comunidad_id}/rechazar")
def rechazar(
    carta_comunidad_id: str,
    body: RechazarBody,
    s: Session = Depends(get_session),
    admin: Usuario = Depends(get_admin),
) -> dict:
    """No entra al mazo. El motivo viaja al autor (aviso + pantalla Crear)."""
    return rechazar_carta(s, carta_comunidad_id, body.motivo)


@router.post("/cartas/{carta_comunidad_id}/a-revisar")
def a_revisar(
    carta_comunidad_id: str,
    body: ARevisarBody,
    s: Session = Depends(get_session),
    admin: Usuario = Depends(get_admin),
) -> dict:
    """Vuelve al autor con una sugerencia; puede llevar un retoque concreto."""
    fix = None if body.fix is None else body.fix.model_dump()
    return marcar_a_revisar(s, carta_comunidad_id, body.sugerencia, fix)


@router.get("/comentarios")
def comentarios(
    limit: int = Query(default=COMENTARIOS_LIMIT_DEFAULT, ge=1, le=500),
    s: Session = Depends(get_session),
    admin: Usuario = Depends(get_admin),
) -> list:
    """El feedback privado de las cartas, más nuevo primero. Sin emails: es anónimo."""
    return listar_comentarios(s, limit)
