"""WS27 · B1.1 · Cartas de la comunidad: proponer, ver las mías, reenviar, retirar.

Esqueleto registrado por el orquestador (B0); la card B1.1 lo llena.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/cartas-comunidad", tags=["cartas-comunidad"])
