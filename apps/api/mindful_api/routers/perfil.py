"""M1 · Perfil y onboarding. Todo opera sobre el usuario logueado (auto-aislado).

Onboarding (wizard M1, WS22): nombre/apodo · horario+TZ · aviso (1 toggle) ·
aceptar términos al cerrar. Todo editable después desde el mismo perfil.
Ni los pilares (WS17) ni las acciones (WS22) se eligen: M2 rota los 6 pilares
cada semana y sirve las 4 acciones iniciales.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..schemas import PerfilOut, PerfilUpdate

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


def _a_salida(s: Session, usuario: Usuario) -> PerfilOut:
    terminos = usuario.terminos_aceptados_at is not None
    return PerfilOut(
        email=usuario.email,
        nombre=usuario.nombre,
        apellido=usuario.apellido,
        apodo=usuario.apodo,
        tz=usuario.tz,
        hora_aviso=usuario.hora_aviso,
        aviso_activo=usuario.aviso_activo,
        terminos_aceptados=terminos,
        # WS17/WS22: ni pilares ni acciones se eligen. Onboarding completo = términos.
        onboarding_completo=terminos,
    )


@router.get("", response_model=PerfilOut)
def obtener_perfil(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> PerfilOut:
    return _a_salida(s, usuario)


@router.put("", response_model=PerfilOut)
def actualizar_perfil(
    body: PerfilUpdate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> PerfilOut:
    if body.nombre is not None:
        usuario.nombre = body.nombre.strip() or None
    if body.apellido is not None:
        usuario.apellido = body.apellido.strip() or None
    if body.apodo is not None:
        usuario.apodo = body.apodo.strip() or None
    if body.tz is not None:
        usuario.tz = body.tz
    if body.hora_aviso is not None:
        usuario.hora_aviso = body.hora_aviso
    if body.aviso_activo is not None:
        usuario.aviso_activo = body.aviso_activo
    if body.aceptar_terminos:
        usuario.terminos_aceptados_at = datetime.now(timezone.utc)

    s.add(usuario)
    s.commit()
    s.refresh(usuario)
    return _a_salida(s, usuario)
