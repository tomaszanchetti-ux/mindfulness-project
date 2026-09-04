"""WS24 · A1.2 · Pagos (Stripe). Checkout anual premium · webhook · portal.

Esqueleto registrado por el orquestador (A0); la card A1.2 lo llena.
"""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(prefix="/api/pagos", tags=["pagos"])
