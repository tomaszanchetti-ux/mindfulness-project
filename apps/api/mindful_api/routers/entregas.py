"""M2/M3 · La carta del día + el cierre del ritual. Todo sobre el usuario logueado."""

from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..schemas import CierreRitual
from ..services.entrega import cerrar_ritual, obtener_carta_del_dia

router = APIRouter(prefix="/api", tags=["entregas"])


@router.get("/carta-del-dia")
def carta_del_dia(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """La carta de hoy (la crea si aún no existe; la devuelve si ya se entregó hoy)."""
    return obtener_carta_del_dia(s, usuario)


@router.put("/entregas/{entrega_id}/cierre")
def cerrar(
    entrega_id: str,
    body: CierreRitual,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """M3 · cerrar el ritual: estrellas + reflexión + completada (opcionales)."""
    return cerrar_ritual(
        s, usuario, entrega_id,
        estrellas=body.estrellas, reflexion=body.reflexion, completada=body.completada,
    )
