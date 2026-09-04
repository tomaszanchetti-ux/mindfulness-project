"""WS24 · A1.3 · Cambiar la carta del día (premium, hasta 3 veces).

Esqueleto registrado por el orquestador (A0); la card A1.3 lo llena.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/entregas", tags=["cambio"])
