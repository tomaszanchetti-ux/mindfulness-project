"""WS21 · suscripciones de push del usuario logueado (aislamiento de siempre).

El navegador genera la suscripción (endpoint + llaves) y acá se registra.
Un usuario puede tener varias (teléfono + computadora). El endpoint es único
globalmente: si reaparece con otro dueño (cambio de cuenta en el mismo
dispositivo), se reasigna — el dispositivo es de quien está logueado.
"""

from __future__ import annotations

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import PushSuscripcion, Usuario

router = APIRouter(prefix="/api/push", tags=["push"])


class SuscripcionIn(BaseModel):
    endpoint: str = Field(min_length=10, max_length=2000)
    p256dh: str = Field(min_length=10, max_length=255)
    auth: str = Field(min_length=5, max_length=255)


class BajaIn(BaseModel):
    endpoint: str = Field(min_length=10, max_length=2000)


@router.post("/suscripcion")
def alta(
    body: SuscripcionIn,
    usuario: Usuario = Depends(get_current_user),
    s: Session = Depends(get_session),
) -> dict:
    existente = s.scalars(
        select(PushSuscripcion).where(PushSuscripcion.endpoint == body.endpoint)
    ).first()
    if existente:
        existente.usuario_id = usuario.id
        existente.p256dh = body.p256dh
        existente.auth = body.auth
    else:
        s.add(
            PushSuscripcion(
                usuario_id=usuario.id,
                endpoint=body.endpoint,
                p256dh=body.p256dh,
                auth=body.auth,
            )
        )
    s.commit()
    return {"ok": True}


@router.post("/baja")
def baja(
    body: BajaIn,
    usuario: Usuario = Depends(get_current_user),
    s: Session = Depends(get_session),
) -> dict:
    s.execute(
        delete(PushSuscripcion).where(
            PushSuscripcion.endpoint == body.endpoint,
            PushSuscripcion.usuario_id == usuario.id,
        )
    )
    s.commit()
    return {"ok": True}
