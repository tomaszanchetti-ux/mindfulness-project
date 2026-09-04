"""M3 captura / M4 muestra · las fotos de una pausa.

Reglas: el cupo por pausa sale del plan (`limites(usuario).fotos_max`: 1 free, 3
premium) — acá no se hardcodea ningún número. Solo imágenes, ≤8 MB. Siempre del
usuario logueado: acá las fotos jamás se sirven sin login (la única otra puerta
es el regalo `ejercicio`, donde el permiso es el token — ver services/compartir).
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Entrega, Foto, Usuario
from . import storage
from .plan import limites

MAX_BYTES = 8 * 1024 * 1024  # 8 MB


def _entrega_propia(s: Session, usuario_id: str, entrega_id: str) -> Entrega:
    entrega = s.get(Entrega, entrega_id)
    # Aislamiento: 404 si no existe O es de otro usuario (no delata existencia ajena).
    if entrega is None or entrega.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")
    return entrega


def _foto_propia(s: Session, usuario_id: str, foto_id: str) -> Foto:
    foto = s.get(Foto, foto_id)
    if foto is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foto no encontrada")
    _entrega_propia(s, usuario_id, foto.entrega_id)
    return foto


def url_de(foto_id: str) -> str:
    return f"/api/fotos/{foto_id}"


def urls_de(s: Session, entrega_id: str) -> list[str]:
    ids = s.scalars(
        select(Foto.id).where(Foto.entrega_id == entrega_id).order_by(Foto.created_at)
    ).all()
    return [url_de(fid) for fid in ids]


def subir_foto(
    s: Session, usuario: Usuario, entrega_id: str,
    contenido: bytes, content_type: str | None,
) -> dict:
    """WS24 · recibe el Usuario (no el id) porque el cupo depende de su plan."""
    usuario_id = usuario.id
    _entrega_propia(s, usuario_id, entrega_id)

    ext = storage.extension_para(content_type)
    if ext is None:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Formato no soportado: usa una imagen (JPG, PNG o WebP)",
        )
    if len(contenido) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La foto llegó vacía")
    if len(contenido) > MAX_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "La foto supera los 8 MB"
        )

    max_fotos = limites(usuario).fotos_max
    # TOCTOU: contar-y-después-insertar deja pasar dos subidas simultáneas (las dos
    # cuentan 0 antes de que la otra commitee). Bloqueamos la fila de la entrega
    # (SELECT ... FOR UPDATE) ANTES de contar: la segunda espera al commit de la
    # primera, cuenta 1 y se lleva su 409. El lock se suelta al commit/close.
    s.get(Entrega, entrega_id, with_for_update=True)
    cuantas = s.scalar(
        select(func.count()).select_from(Foto).where(Foto.entrega_id == entrega_id)
    )
    if cuantas >= max_fotos:
        detalle = (
            "Esta pausa ya tiene su foto: tu plan permite 1 foto por pausa"
            if max_fotos == 1
            else f"Esta pausa ya tiene {max_fotos} fotos, el máximo de tu plan"
        )
        raise HTTPException(status.HTTP_409_CONFLICT, detalle)

    foto_id = str(uuid4())
    ruta = storage.ruta_canonica(usuario_id, entrega_id, foto_id, ext)
    # Primero el archivo, después la fila: si la DB falla, limpiamos el archivo.
    storage.guardar(ruta, contenido, content_type or "application/octet-stream")
    try:
        foto = Foto(id=foto_id, entrega_id=entrega_id, storage_path=ruta)
        s.add(foto)
        s.commit()
    except Exception:
        s.rollback()
        storage.borrar([ruta])
        raise
    return {"id": foto_id, "url": url_de(foto_id)}


def leer_foto(s: Session, usuario_id: str, foto_id: str) -> tuple[bytes, str]:
    foto = _foto_propia(s, usuario_id, foto_id)
    contenido = storage.leer(foto.storage_path)
    if contenido is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Foto no encontrada")
    return contenido, storage.mime_de(foto.storage_path)


def borrar_foto(s: Session, usuario_id: str, foto_id: str) -> None:
    foto = _foto_propia(s, usuario_id, foto_id)
    storage.borrar([foto.storage_path])
    s.delete(foto)
    s.commit()
