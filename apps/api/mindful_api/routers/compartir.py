"""M5 · Compartir. Crear/revocar links (con login) + leer el regalo (SIN login)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..schemas import CompartirCreate
from ..services.compartir import crear_compartido, leer_publico, revocar

# Con login: crear / revocar.
router = APIRouter(prefix="/api/compartir", tags=["compartir"])


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    body: CompartirCreate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    return crear_compartido(s, usuario.id, body.entrega_id, body.modo, nota=body.nota)


@router.delete("/{compartido_id}", status_code=status.HTTP_204_NO_CONTENT)
def revocar_link(
    compartido_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    revocar(s, usuario.id, compartido_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# SIN login: la página pública del regalo (el receptor abre y ve).
public_router = APIRouter(prefix="/api/c", tags=["compartir-publico"])


@public_router.get("/{token}")
def ver_regalo(token: str, s: Session = Depends(get_session)) -> dict:
    return leer_publico(s, token)
