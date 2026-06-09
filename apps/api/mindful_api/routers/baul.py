"""M4 · Baúl. Historial del usuario (ordenable) + borrado real."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..services.baul import borrar_entrega, listar_baul

router = APIRouter(prefix="/api/baul", tags=["baul"])


@router.get("")
def ver_baul(
    orden: str = Query("reciente", pattern="^(reciente|valoradas)$"),
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> list[dict]:
    """El historial vivido: carta + reflexión + fotos. Orden Reciente o Más valoradas."""
    return listar_baul(s, usuario.id, orden=orden)


@router.delete("/{entrega_id}", status_code=status.HTTP_204_NO_CONTENT)
def borrar(
    entrega_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """Borrado real para siempre: fila + fotos + apaga el link (la carta sola sobrevive)."""
    borrar_entrega(s, usuario.id, entrega_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
