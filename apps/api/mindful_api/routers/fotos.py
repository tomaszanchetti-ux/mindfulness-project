"""M3/M4 · Fotos de la pausa: subir (al guardar extras), servir (Baúl) y quitar.

Las fotos son privadas SIEMPRE: se sirven a través de la API con el usuario
logueado (nunca URLs públicas de Storage). El front las pide con fetch+auth.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..services.fotos import borrar_foto, leer_foto, subir_foto

router = APIRouter(prefix="/api", tags=["fotos"])


@router.post("/entregas/{entrega_id}/fotos", status_code=status.HTTP_201_CREATED)
async def subir(
    entrega_id: str,
    foto: UploadFile = File(...),
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Sube una foto a la entrega (hasta 3, solo imágenes, ≤8 MB)."""
    contenido = await foto.read()
    return subir_foto(s, usuario.id, entrega_id, contenido, foto.content_type)


@router.get("/fotos/{foto_id}")
def ver(
    foto_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """La imagen en sí, solo para su dueño."""
    contenido, mime = leer_foto(s, usuario.id, foto_id)
    return Response(
        content=contenido,
        media_type=mime,
        headers={"Cache-Control": "private, max-age=86400"},
    )


@router.delete("/fotos/{foto_id}", status_code=status.HTTP_204_NO_CONTENT)
def quitar(
    foto_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """Quita una foto (archivo + fila)."""
    borrar_foto(s, usuario.id, foto_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
