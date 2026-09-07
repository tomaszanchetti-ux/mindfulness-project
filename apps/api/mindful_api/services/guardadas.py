"""WS29 · C1.2 · Guardar la Pausa de otra persona en mi Baúl.

No es una copia: es un puntero. La ficha se lee EN VIVO con la regla de lectura,
así que si el dueño la vuelve privada, la borra o me saca de su comunidad, la
guardada desaparece de mi Baúl sola. Si la vuelve a compartir, reaparece.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Guardada, Usuario
from .comunidad import entrega_visible

NO_ESTA = "No encontramos esta Pausa."


def guardar(s: Session, yo: Usuario, entrega_id: str) -> dict:
    entrega = entrega_visible(s, yo, entrega_id)
    if entrega is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ESTA)
    if entrega.usuario_id == yo.id:
        # Mi propia Pausa ya vive en mi Baúl: guardarla sería duplicarla.
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "Esta Pausa ya es tuya.")

    ya = s.scalar(
        select(Guardada.id)
        .where(Guardada.usuario_id == yo.id, Guardada.entrega_id == entrega.id)
        .limit(1)
    )
    if ya is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya guardaste esta Pausa.")

    s.add(Guardada(usuario_id=yo.id, entrega_id=entrega.id))
    s.commit()
    return {"guardada": True}


def quitar(s: Session, yo: Usuario, entrega_id: str) -> None:
    guardada = s.scalar(
        select(Guardada).where(
            Guardada.usuario_id == yo.id, Guardada.entrega_id == entrega_id
        )
    )
    if guardada is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No tienes guardada esta Pausa.")
    s.delete(guardada)
    s.commit()
