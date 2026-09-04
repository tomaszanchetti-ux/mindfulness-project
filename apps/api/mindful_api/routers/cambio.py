"""WS24 · A1.3 · Cambiar la carta del día (premium, hasta 3 veces).

Esqueleto registrado por el orquestador (A0); la card A1.3 lo llena.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..services.cambio import cambiar_carta_del_dia

router = APIRouter(prefix="/api/entregas", tags=["cambio"])


@router.post("/{entrega_id}/cambiar")
def cambiar(
    entrega_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Reemplaza la carta de HOY por otra del mismo pilar que cruza el eje.

    Premium: hasta 3 veces por día. La entrega es la misma fila (no se duplica).
    """
    return cambiar_carta_del_dia(s, usuario, entrega_id)
