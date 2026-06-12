"""M1 · Perfil y onboarding. Todo opera sobre el usuario logueado (auto-aislado).

Onboarding (wizard M1, WS22): nombre/apodo · horario+TZ · aviso (1 toggle) ·
aceptar términos al cerrar. Todo editable después desde el mismo perfil.
Ni los pilares (WS17) ni las acciones (WS22) se eligen: M2 rota los 6 pilares
cada semana y sirve las 4 acciones iniciales.
"""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Accion, Categoria, Usuario, UsuarioAccion, UsuarioCategoria
from ..schemas import AccionesUpdate, CategoriasUpdate, PerfilOut, PerfilUpdate

router = APIRouter(prefix="/api/perfil", tags=["perfil"])


def _categorias_de(s: Session, usuario_id: str) -> list[str]:
    rows = s.scalars(
        select(UsuarioCategoria.categoria_slug).where(
            UsuarioCategoria.usuario_id == usuario_id
        )
    ).all()
    return list(rows)


def _acciones_de(s: Session, usuario_id: str) -> list[str]:
    rows = s.scalars(
        select(UsuarioAccion.accion_slug).where(
            UsuarioAccion.usuario_id == usuario_id
        )
    ).all()
    return list(rows)


def _a_salida(s: Session, usuario: Usuario) -> PerfilOut:
    cats = _categorias_de(s, usuario.id)
    accs = _acciones_de(s, usuario.id)
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
        categorias=cats,
        acciones=accs,
        # WS17: las categorías ya no se eligen (rotación completa de los 6 campos).
        # Onboarding completo = términos aceptados.
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


@router.put("/categorias", response_model=PerfilOut)
def fijar_categorias(
    body: CategoriasUpdate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> PerfilOut:
    """DEPRECATED (WS17): M2 rota las 6 categorías y ya no filtra por elección.

    El endpoint queda por compatibilidad (clientes viejos cacheados); lo que
    guarde no afecta la entrega. Se elimina en una limpieza futura.
    """
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


@router.put("/acciones", response_model=PerfilOut)
def fijar_acciones(
    body: AccionesUpdate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> PerfilOut:
    """DEPRECATED (WS22): las acciones ya no se eligen — M2 sirve las 4.

    El endpoint queda por compatibilidad (el front desplegado pre-WS22 todavía lo
    llama desde el onboarding); lo que guarde no afecta la entrega (nada lee
    `usuario_acciones`). Se elimina junto a la tabla en la limpieza del paso 4.
    """
    # Validar que cada slug exista en el contenido global (Mundo 1).
    validas = set(s.scalars(select(Accion.slug)).all())
    invalidas = [a for a in body.acciones if a not in validas]
    if invalidas:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"acciones inexistentes: {', '.join(invalidas)}",
        )

    # Reemplazo total (sin piso "escribir": ya no es una acción del enum — WS22).
    s.query(UsuarioAccion).filter(UsuarioAccion.usuario_id == usuario.id).delete()
    for slug in dict.fromkeys(body.acciones):
        s.add(UsuarioAccion(usuario_id=usuario.id, accion_slug=slug))
    s.commit()
    s.refresh(usuario)
    return _a_salida(s, usuario)
