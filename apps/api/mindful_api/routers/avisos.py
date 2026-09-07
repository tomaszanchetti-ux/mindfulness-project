"""WS27 · B2.1 · Avisos: la campana de la app.

Router fino: resuelve sesión y usuario, y delega TODO en `services/avisos.py`
(que es donde vive el aislamiento y el orden). Escribe B1.1/B1.3, lee esto.

Dos verbos de escritura: `PUT /leidos` marca todos (vaciar la campana de un
toque) y `PUT /{aviso_id}/leido` marca uno. Los caminos no se pisan (uno tiene un
segmento y el otro dos), pero la ruta fija se declara igual ANTES que la que
lleva parámetro: FastAPI matchea en orden de declaración y esa costumbre es lo
que evita que mañana, al sumar `PUT /{aviso_id}`, "leidos" pase a leerse como un id.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..services.avisos import (
    LIMITE_DEFAULT,
    bandeja,
    marcar_leido,
    marcar_todos_leidos,
)

router = APIRouter(prefix="/api/avisos", tags=["avisos"])


@router.get("")
def listar(
    limite: int = Query(default=LIMITE_DEFAULT, ge=1, le=200),
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Mis avisos, el más nuevo primero, con el contador de no leídos.

    El contador cuenta TODOS los no leídos, aunque la lista venga recortada por
    `limite`: la campana no puede decir 50 cuando hay 60.
    """
    return bandeja(s, usuario, limite)


@router.put("/leidos")
def marcar_todos(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Vacía la campana de un toque. Devuelve cuántos marcó y el contador nuevo (0)."""
    marcados = marcar_todos_leidos(s, usuario)
    return {"marcados": marcados, "no_leidos": 0}


@router.put("/{aviso_id}/leido")
def marcar_uno(
    aviso_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Marca un aviso como leído y lo devuelve. Un aviso ajeno es 404, no 403."""
    return marcar_leido(s, usuario, aviso_id)
