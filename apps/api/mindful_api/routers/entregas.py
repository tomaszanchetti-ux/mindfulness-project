"""M2/M3 · La carta del día + el cierre del ritual. Todo sobre el usuario logueado."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Entrega, Usuario
from ..schemas import CierreRitual
from ..services.entrega import _salida, cerrar_ritual, obtener_carta_del_dia

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
    """M3 · cerrar el ritual: estrellas + reflexión + comentario + completada (opcionales)."""
    return cerrar_ritual(
        s, usuario, entrega_id,
        estrellas=body.estrellas, reflexion=body.reflexion, completada=body.completada,
        comentario_carta=body.comentario_carta,
    )


@router.get("/entregas/{entrega_id}")
def ver_entrega(
    entrega_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """WS29 · C1.2: una entrega MÍA con la forma de la carta del día (la pantalla
    `/pausa/:id` la usa para vivir una Pausa extra que no es la de hoy).

    Ajena o inexistente: el mismo 404 (nada delata que exista). No colisiona con
    `PUT /entregas/{id}/cierre`: distinto método y distinto path.
    """
    entrega = s.get(Entrega, entrega_id)
    if entrega is None or entrega.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")
    return _salida(s, entrega, ya_existia=True)
