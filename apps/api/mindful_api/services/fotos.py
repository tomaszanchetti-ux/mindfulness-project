"""M3 captura / M4 muestra · las fotos de una pausa.

Reglas: en la versión free es **1 foto por pausa** (decisión Tomás WS16; subir a
3 queda para premium — ajusta el "hasta 3" del canon M3). Solo imágenes, ≤8 MB.
Siempre del usuario logueado — las fotos jamás se sirven sin login (el modo
ejercicio público de M5 queda para v2/premium).
"""

from __future__ import annotations

from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.models import Entrega, Foto
from . import storage

MAX_FOTOS = 1  # free; premium (v2) sube a 3
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
    s: Session, usuario_id: str, entrega_id: str,
    contenido: bytes, content_type: str | None,
) -> dict:
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

    cuantas = s.scalar(
        select(func.count()).select_from(Foto).where(Foto.entrega_id == entrega_id)
    )
    if cuantas >= MAX_FOTOS:
        detalle = (
            "Esta pausa ya tiene su foto"
            if MAX_FOTOS == 1
            else f"Esta pausa ya tiene {MAX_FOTOS} fotos"
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
