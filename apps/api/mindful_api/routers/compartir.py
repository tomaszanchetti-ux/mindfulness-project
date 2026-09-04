"""M5 · Compartir. Crear/revocar links + leer el regalo. WS25: TODO exige login.

Decisión de Tomás (WS25 §1.3): el receptor del link también entra con su cuenta.
El permiso para ver el regalo sigue siendo el TOKEN — el login es la puerta de la
comunidad, no un filtro de destinatario: cualquiera con el link y una sesión lo abre.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..schemas import CompartirCreate
from ..services.compartir import (
    crear_compartido,
    leer_foto_publica,
    leer_publico,
    revocar,
)

# Con login: crear / revocar.
router = APIRouter(prefix="/api/compartir", tags=["compartir"])


@router.post("", status_code=status.HTTP_201_CREATED)
def crear(
    body: CompartirCreate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    # `body.modo` llega pero NO se usa: el servicio lo deriva de la Pausa (WS25).
    return crear_compartido(s, usuario, body.entrega_id, nota=body.nota)


@router.delete("/{compartido_id}", status_code=status.HTTP_204_NO_CONTENT)
def revocar_link(
    compartido_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    revocar(s, usuario.id, compartido_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


# La página del regalo. WS25: con login (sin identidad, 401), pero el permiso de
# CONTENIDO lo sigue dando el token, no quién sea el que abre.
public_router = APIRouter(prefix="/api/c", tags=["compartir-regalo"])


@public_router.get("/{token}")
def ver_regalo(
    token: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Lo que ve el receptor. Necesita sesión (Google o enlace por email)."""
    return leer_publico(s, token)


@public_router.get("/{token}/fotos/{foto_id}")
def ver_foto_del_regalo(
    token: str,
    foto_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """La imagen de un regalo `ejercicio`: hace falta sesión, y el permiso es el token.

    Sólo por esta puerta: el token manda, y si se revoca o se borra la entrada,
    la foto deja de servirse (404). Nunca sale un `storage_path`.
    """
    contenido, mime = leer_foto_publica(s, token, foto_id)
    return Response(
        content=contenido,
        media_type=mime,
        # WS25 · ahora se sirve con sesión: caché PRIVADA (nunca en un proxy
        # compartido) y corta, para que al revocar el link no quede pegada.
        headers={"Cache-Control": "private, max-age=300"},
    )
