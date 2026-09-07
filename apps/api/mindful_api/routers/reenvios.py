"""WS29 · C1.2 · Lo que se HACE con la ficha de otro: reenviarla, guardarla o
vivirla. Tres prefijos que comparten territorio y por eso viven en un archivo:

- `/api/reenvios`  · mandarle una Pausa a alguien de mi comunidad y ver las que
                     me mandaron.
- `/api/guardadas` · guardar/quitar una ficha ajena de mi Baúl.
- `/api/pausas`    · hacer la Pausa de otra persona (premium): ahora o en la
                     próxima carta del día.

Los bodies viven acá (Pydantic) y no en `schemas.py`: son de esta card.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..services.guardadas import guardar, quitar
from ..services.pausas import hacer
from ..services.reenvios import marcar_leido, recibidos, reenviar

router = APIRouter(prefix="/api/reenvios", tags=["reenvios"])
guardadas_router = APIRouter(prefix="/api/guardadas", tags=["guardadas"])
pausas_router = APIRouter(prefix="/api/pausas", tags=["pausas"])


class ReenvioIn(BaseModel):
    entrega_id: str
    a_usuario_id: str


class HacerPausaIn(BaseModel):
    entrega_id: str
    # El vocabulario cerrado lo valida el servicio (`MODOS_PAUSA`), con un
    # mensaje en español en vez del error crudo de Pydantic.
    modo: str


# ── Reenvíos ─────────────────────────────────────────────────────────────────

@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    body: ReenvioIn,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Le envío una Pausa (mía o de un tercero que puedo ver) a alguien de mi comunidad."""
    return reenviar(s, usuario, body.entrega_id, body.a_usuario_id)


@router.get("/recibidos")
def ver_recibidos(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Las Pausas que me enviaron, con la ficha adentro. Solo las que siguen visibles."""
    return recibidos(s, usuario)


@router.put("/{reenvio_id}/leido")
def leer(
    reenvio_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    return marcar_leido(s, usuario, reenvio_id)


# ── Guardadas ────────────────────────────────────────────────────────────────

@guardadas_router.post("/{entrega_id}", status_code=status.HTTP_201_CREATED)
def guardar_ficha(
    entrega_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    return guardar(s, usuario, entrega_id)


@guardadas_router.delete("/{entrega_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar_ficha(
    entrega_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    quitar(s, usuario, entrega_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# ── Hacer la Pausa ───────────────────────────────────────────────────────────

@pausas_router.post("/hacer", status_code=status.HTTP_201_CREATED)
def hacer_pausa(
    body: HacerPausaIn,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """`ahora` → la entrega extra lista para vivir · `siguiente` → queda en cola."""
    return hacer(s, usuario, body.entrega_id, body.modo)
