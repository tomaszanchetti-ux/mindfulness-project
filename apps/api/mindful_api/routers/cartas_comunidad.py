"""WS27 · B1.1 · Cartas de la comunidad: proponer, ver las mías, reenviar, retirar.

Router fino: resuelve la sesión y el usuario, y delega TODO en
`services/cartas_comunidad.py` (permisos, límites, estados y el juez).
"""

from __future__ import annotations

from fastapi import APIRouter, BackgroundTasks, Depends, Response, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..schemas import CartaComunidadCreate, CartaComunidadOut, CartaComunidadUpdate
from ..services.cartas_comunidad import (
    crear_propuesta,
    listar_mias,
    reenviar_propuesta,
    retirar_propuesta,
)

router = APIRouter(prefix="/api/cartas-comunidad", tags=["cartas-comunidad"])


@router.post("", status_code=status.HTTP_201_CREATED, response_model=CartaComunidadOut)
def proponer(
    body: CartaComunidadCreate,
    tareas: BackgroundTasks,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Escribe una carta para la comunidad (premium; una en curso a la vez).

    Responde apenas se guarda: el juez la mira después, en background.
    """
    return crear_propuesta(s, usuario, body, tareas)


@router.get("/mias", response_model=list[CartaComunidadOut])
def mias(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> list:
    """Las cartas que escribí, con su estado y la sugerencia del juez si la hay."""
    return listar_mias(s, usuario)


@router.put("/{carta_comunidad_id}", response_model=CartaComunidadOut)
def reenviar(
    carta_comunidad_id: str,
    body: CartaComunidadUpdate,
    tareas: BackgroundTasks,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Corrige una carta que necesita un retoque y la manda de nuevo al juez."""
    return reenviar_propuesta(s, usuario, carta_comunidad_id, body, tareas)


@router.delete("/{carta_comunidad_id}", status_code=status.HTTP_204_NO_CONTENT)
def retirar(
    carta_comunidad_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """Baja la carta del recorrido. Después el autor puede escribir otra."""
    retirar_propuesta(s, usuario, carta_comunidad_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
