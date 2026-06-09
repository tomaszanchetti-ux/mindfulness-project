"""M1 · Perfil y onboarding. Todo opera sobre el usuario logueado (auto-aislado).

Onboarding (wizard M1): elegir 2-6 categorías · horario+TZ · aviso (1 toggle) ·
aceptar términos al cerrar. Todo editable después desde el mismo perfil.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Categoria, Usuario, UsuarioCategoria
from ..schemas import CategoriasUpdate, PerfilOut, PerfilUpdate

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


def _categorias_de(s: Session, usuario_id: str) -> list[str]:
    rows = s.scalars(
        select(UsuarioCategoria.categoria_slug).where(
            UsuarioCategoria.usuario_id == usuario_id
        )
    ).all()
    return list(rows)


def _a_salida(s: Session, usuario: Usuario) -> PerfilOut:
    cats = _categorias_de(s, usuario.id)
    terminos = usuario.terminos_aceptados_at is not None
    return PerfilOut(
        email=usuario.email,
        tz=usuario.tz,
        hora_aviso=usuario.hora_aviso,
        aviso_activo=usuario.aviso_activo,
        terminos_aceptados=terminos,
        categorias=cats,
        # Onboarding completo = términos aceptados + al menos 2 categorías (regla M1).
        onboarding_completo=terminos and len(cats) >= 2,
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


@router.put("/categorias", response_model=PerfilOut)
def fijar_categorias(
    body: CategoriasUpdate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> PerfilOut:
    # Validar que cada slug exista en el contenido global (Mundo 1).
    validas = set(s.scalars(select(Categoria.slug)).all())
    invalidas = [c for c in body.categorias if c not in validas]
    if invalidas:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"categorías inexistentes: {', '.join(invalidas)}",
        )

    # Reemplazo total: borro las actuales y dejo exactamente las nuevas.
    s.query(UsuarioCategoria).filter(UsuarioCategoria.usuario_id == usuario.id).delete()
    for slug in body.categorias:
        s.add(UsuarioCategoria(usuario_id=usuario.id, categoria_slug=slug))
    s.commit()
    s.refresh(usuario)
    return _a_salida(s, usuario)
