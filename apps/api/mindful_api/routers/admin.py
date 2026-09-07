"""WS27 · B1.3 · Administración (Tomás): revisar y aprobar cartas, leer comentarios.

Esqueleto registrado por el orquestador (B0); la card B1.3 lo llena.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/admin", tags=["admin"])
