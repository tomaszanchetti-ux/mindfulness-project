"""WS29 · C1.2 · "Hacer la Pausa" de otra persona (premium).

Desde la ficha de alguien puedo vivir SU carta. Dos modos:

- `ahora`     → nace una entrega EXTRA en mi Baúl con esa carta. No es la carta
                del día: el motor la ignora para decidir si hoy ya hay carta y
                para la rotación (así "hacer una extra" no me deja sin carta
                mañana ni me quema el pilar).
- `siguiente` → se encola: la PRÓXIMA carta del día que me toque va a ser esa.
                Hay una sola en cola (decisión de Tomás): programar de nuevo
                reemplaza la anterior.

En los dos casos queda `de_usuario_id` = el dueño de la ficha, para que la Pausa
recuerde de quién vino.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    MODOS_PAUSA,
    PAUSA_AHORA,
    Carta,
    Entrega,
    PausaProgramada,
    Usuario,
)
from .comunidad import entrega_visible
from .entrega import _carta_enriquecida, _salida
from .plan import limites

SOLO_PREMIUM = "Hacer la Pausa de otra persona es de quienes son parte."


def hacer(s: Session, yo: Usuario, entrega_id: str, modo: str) -> dict:
    if modo not in MODOS_PAUSA:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            "Elige cómo quieres hacerla: ahora o en tu próxima carta.",
        )
    if not limites(yo).pausas_extra:
        raise HTTPException(status.HTTP_403_FORBIDDEN, SOLO_PREMIUM)

    origen = entrega_visible(s, yo, entrega_id)
    if origen is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos esta Pausa.")

    if modo == PAUSA_AHORA:
        nueva = Entrega(
            usuario_id=yo.id, carta_id=origen.carta_id,
            extra=True, de_usuario_id=origen.usuario_id,
        )
        s.add(nueva)
        s.commit()
        s.refresh(nueva)
        return _salida(s, nueva, ya_existia=False)

    # `siguiente`: la cola es de UNA. Lo que hubiera sin servir se reemplaza.
    for vieja in s.scalars(
        select(PausaProgramada).where(
            PausaProgramada.usuario_id == yo.id,
            PausaProgramada.servida_at.is_(None),
        )
    ).all():
        s.delete(vieja)

    s.add(PausaProgramada(
        usuario_id=yo.id, carta_id=origen.carta_id,
        de_usuario_id=origen.usuario_id, entrega_origen_id=origen.id,
    ))
    s.commit()
    return {
        "programada": True,
        "carta": _carta_enriquecida(s, s.get(Carta, origen.carta_id)),
    }
