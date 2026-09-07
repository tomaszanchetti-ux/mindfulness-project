"""WS29 · C1.2 · Las fichas AJENAS: descubrir, la vitrina de alguien, una ficha,
sus fotos. Todo con login y todo pasando por la regla de lectura del Bloque C.

El orden de las rutas importa: `/descubrir` y `/de/{id}` se declaran ANTES que
`/{entrega_id}`, si no FastAPI le daría "descubrir" como id a la última.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..services.comunidad import entrega_visible
from ..services.fichas import descubrir, ficha_ajena, foto_de_ficha, vitrina_de

router = APIRouter(prefix="/api/fichas", tags=["fichas"])

NO_ESTA = "No encontramos esta Pausa."


@router.get("/descubrir")
def ver_descubrir(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> list:
    """Hasta 30 fichas que puedo ver: perfiles públicos + mi comunidad."""
    return descubrir(s, usuario)


@router.get("/de/{usuario_id}")
def ver_de(
    usuario_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """La vitrina de una persona. `fichas: null` = su perfil está cerrado para mí."""
    return vitrina_de(s, usuario, usuario_id)


@router.get("/{entrega_id}")
def ver_ficha(
    entrega_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    entrega = entrega_visible(s, usuario, entrega_id)
    if entrega is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ESTA)
    return ficha_ajena(s, usuario, entrega)


@router.get("/{entrega_id}/fotos/{foto_id}")
def ver_foto(
    entrega_id: str,
    foto_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """La imagen de una ficha ajena. La regla se aplica sobre la ENTREGA, y la
    foto tiene que ser de esa entrega: un foto_id de otra ficha es 404 aunque la
    entrega del path sí sea visible."""
    entrega = entrega_visible(s, usuario, entrega_id)
    if entrega is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ESTA)
    leida = foto_de_ficha(s, entrega, foto_id)
    if leida is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foto no encontrada")
    contenido, mime = leida
    return Response(
        content=contenido,
        media_type=mime,
        headers={"Cache-Control": "private, max-age=86400"},
    )
