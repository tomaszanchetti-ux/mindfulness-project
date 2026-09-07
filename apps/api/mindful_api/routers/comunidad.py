"""WS29 · C1.1 · La pestaña Comunidad: encontrar personas y armar los vínculos.

Todo con login. La forma de salida es siempre `Persona` (`services/comunidad.persona_de`):
apodo, foto, si es público, nombre/apellido y cómo está el vínculo DESDE quien mira.
El email nunca sale: sirve para buscar a alguien que ya te lo dio, no para mostrarse.

Un vínculo es UNO solo entre dos personas: aceptarlo abre las dos puertas y
borrarlo las cierra las dos. Rechazar, cancelar y quitar son el mismo borrado
visto desde distintos momentos, por eso comparten forma (204, sin aviso).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..services import comunidad as svc

router = APIRouter(prefix="/api/comunidad", tags=["comunidad"])


@router.get("/buscar")
def buscar(
    q: Optional[str] = Query(default=None),
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> list:
    """Personas por email exacto o por un pedazo de apodo/nombre/apellido.
    Con menos de 2 caracteres devuelve vacío (no es un listado del padrón)."""
    return svc.buscar_personas(s, usuario, q)


@router.get("")
def mi_comunidad(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """`{gente, recibidas, enviadas}` — las tres listas de la pestaña."""
    return svc.mi_comunidad(s, usuario)


# Las rutas de /solicitudes van ANTES de /{usuario_id}: si no, "solicitudes"
# entraría como un usuario_id.
@router.post("/solicitudes/{usuario_id}", status_code=status.HTTP_201_CREATED)
def pedir(
    usuario_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    return svc.crear_solicitud(s, usuario, usuario_id)


@router.post("/solicitudes/{usuario_id}/aceptar")
def aceptar(
    usuario_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Solo el destinatario acepta; para cualquier otro es un 404."""
    return svc.aceptar_solicitud(s, usuario, usuario_id)


@router.delete("/solicitudes/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def rechazar_o_cancelar(
    usuario_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    svc.borrar_solicitud(s, usuario, usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar(
    usuario_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """Quitar a alguien de mi comunidad (borra el vínculo aceptado)."""
    svc.quitar_de_comunidad(s, usuario, usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
