"""M1 · Perfil y onboarding. Todo opera sobre el usuario logueado (auto-aislado).

Onboarding (wizard M1, WS22): nombre/apodo · horario+TZ · aviso (1 toggle) ·
aceptar términos al cerrar. Todo editable después desde el mismo perfil.
Ni los pilares (WS17) ni las acciones (WS22) se eligen: M2 rota los 6 pilares
cada semana y sirve las 4 acciones iniciales.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..db.base import get_session
from ..db.models import Usuario
from ..schemas import LimitesOut, PerfilOut, PerfilUpdate
from ..services.comunidad import leer_foto_perfil, quitar_foto_perfil, subir_foto_perfil
from ..services.plan import limites

router = APIRouter(prefix="/api/perfil", tags=["perfil"])
# WS29 · C1.1 · la foto de perfil la mira CUALQUIER logueado (es lo que la
# comunidad ve de mí), así que vive fuera de /api/perfil, que es siempre mío.
usuarios_router = APIRouter(prefix="/api/usuarios", tags=["usuarios"])


def _a_salida(s: Session, usuario: Usuario) -> PerfilOut:
    terminos = usuario.terminos_aceptados_at is not None
    lim = limites(usuario)
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
        # WS24: el plan y sus límites salen de un solo lugar (services/plan.py).
        plan=lim.plan,
        plan_hasta=usuario.plan_hasta if lim.plan == "premium" else None,
        limites=LimitesOut(**lim.dict()),
        es_admin=usuario.firebase_uid in settings.admin_uids_list,
        perfil_publico=usuario.perfil_publico,
        usuario_id=usuario.id,
        foto_url=f"/api/usuarios/{usuario.id}/foto" if usuario.foto_path else None,
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
    if body.perfil_publico is not None:
        usuario.perfil_publico = body.perfil_publico
    if body.aceptar_terminos:
        usuario.terminos_aceptados_at = datetime.now(timezone.utc)

    s.add(usuario)
    s.commit()
    s.refresh(usuario)
    return _a_salida(s, usuario)


# ── WS29 · C1.1 · foto de perfil ─────────────────────────────────────────────

@router.post("/foto")
async def subir_mi_foto(
    foto: UploadFile = File(...),
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Pone (o reemplaza) mi foto de perfil: JPG/PNG/WebP, ≤8 MB."""
    contenido = await foto.read()
    return subir_foto_perfil(s, usuario, contenido, foto.content_type)


@router.delete("/foto", status_code=status.HTTP_204_NO_CONTENT)
def quitar_mi_foto(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """Me quedo sin foto. Idempotente: sin foto también contesta 204."""
    quitar_foto_perfil(s, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@usuarios_router.get("/{usuario_id}/foto")
def ver_foto_de(
    usuario_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """La foto de alguien. Cualquier logueado la ve (es una cara, no una ficha);
    404 si esa persona no existe o no tiene foto. El `storage_path` jamás viaja."""
    contenido, mime = leer_foto_perfil(s, usuario_id)
    return Response(
        content=contenido,
        media_type=mime,
        headers={"Cache-Control": "private, max-age=86400"},
    )
