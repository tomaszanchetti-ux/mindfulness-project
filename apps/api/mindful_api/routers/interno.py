"""Endpoints internos (no son de usuarios): los golpea Cloud Scheduler.

Protección: header `X-Aviso-Secret` con el secreto compartido (env). Si el env
no está configurado, el endpoint queda apagado (404 — no existe para nadie).
"""

from __future__ import annotations

import secrets as _secrets

from fastapi import APIRouter, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from ..config import settings
from ..db.base import get_session
from ..services.aviso import enviar_avisos
from ..services.limpieza import limpiar_fotos_huerfanas

router = APIRouter(prefix="/api/internal", tags=["interno"])


@router.post("/aviso-diario")
def aviso_diario(
    s: Session = Depends(get_session),
    x_aviso_secret: str = Header(default=""),
) -> dict:
    if not settings.aviso_secret:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    if not _secrets.compare_digest(x_aviso_secret, settings.aviso_secret):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    resultado = enviar_avisos(s)
    # WS30 · C3 · el mismo barrido limpia las fotos huérfanas (deuda T7). Nunca
    # tumba el aviso: si Storage falla, se reintenta en el próximo golpe.
    try:
        resultado["fotos_huerfanas"] = limpiar_fotos_huerfanas(s)
    except Exception as exc:  # noqa: BLE001
        resultado["fotos_huerfanas"] = {"error": str(exc)[:200]}
    return resultado
