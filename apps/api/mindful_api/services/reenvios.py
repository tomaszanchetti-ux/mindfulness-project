"""WS29 · C1.2 · Reenviar una Pausa a alguien de mi comunidad.

Un reenvío es un permiso de lectura prestado: le abre a UNA persona UNA ficha,
mientras el dueño la siga teniendo compartida. Si el dueño la repliega, el
reenvío deja de mostrar nada (no se borra la fila: la regla la apaga sola).

Solo se reenvía a personas de mi comunidad (vínculo aceptado). Todo lo que no
puedo ver o a quien no puedo mandarle es 404: nunca un 403 que confirme que la
ficha o la persona existen.
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import AVISO_REENVIO, Entrega, Reenvio, Usuario
from .avisos import crear_aviso
from .comunidad import (
    como_se_llama,
    entrega_visible,
    persona_min,
    puede_ver,
    son_comunidad,
)
from .fichas import ficha_ajena

NO_ESTA = "No encontramos esta Pausa."
NO_ES_COMUNIDAD = "Esa persona no está en tu comunidad."


def _url_ficha(entrega_id: str) -> str:
    """El link IN-APP de una ficha ajena (WS29 §0.3: el `/c/{token}` sigue siendo
    solo para las propias, porque un token de un tercero sobreviviría al dueño)."""
    return f"/comunidad/ficha/{entrega_id}"


def reenviar(s: Session, yo: Usuario, entrega_id: str, a_usuario_id: str) -> dict:
    entrega = entrega_visible(s, yo, entrega_id)
    if entrega is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ESTA)

    # A mí mismo no: el 422 va ANTES de la pata de comunidad, porque conmigo
    # mismo no hay vínculo y el 404 diría una mentira.
    if a_usuario_id == yo.id:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, "No puedes enviarte una Pausa a ti mismo."
        )

    a = s.get(Usuario, a_usuario_id)
    if a is None or not son_comunidad(s, yo.id, a.id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ES_COMUNIDAD)

    ya = s.scalar(
        select(Reenvio.id).where(
            Reenvio.de_usuario_id == yo.id,
            Reenvio.a_usuario_id == a.id,
            Reenvio.entrega_id == entrega.id,
        ).limit(1)
    )
    if ya is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya le enviaste esta Pausa.")

    reenvio = Reenvio(de_usuario_id=yo.id, a_usuario_id=a.id, entrega_id=entrega.id)
    s.add(reenvio)
    crear_aviso(
        s, a, AVISO_REENVIO, f"{como_se_llama(yo)} te envió una Pausa.",
        referencia_id=entrega.id, url=_url_ficha(entrega.id),
    )
    s.commit()
    s.refresh(reenvio)
    return {"id": reenvio.id}


def recibidos(s: Session, yo: Usuario) -> dict:
    """Los reenvíos que me llegaron, del más nuevo al más viejo. Solo los que
    TODAVÍA puedo ver: si el dueño replegó la ficha, el reenvío desaparece de la
    lista (y su no-leído deja de contar)."""
    filas = s.scalars(
        select(Reenvio)
        .where(Reenvio.a_usuario_id == yo.id)
        .order_by(Reenvio.created_at.desc())
    ).all()

    salida = []
    for r in filas:
        entrega = s.get(Entrega, r.entrega_id)
        if entrega is None or not puede_ver(s, yo, entrega):
            continue
        de = s.get(Usuario, r.de_usuario_id)
        salida.append({
            "id": r.id,
            "de": persona_min(de) if de is not None else None,
            "ficha": ficha_ajena(s, yo, entrega),
            "leido": r.leido,
            "created_at": r.created_at,
        })

    return {
        "no_leidos": sum(1 for x in salida if not x["leido"]),
        "reenvios": salida,
    }


def marcar_leido(s: Session, yo: Usuario, reenvio_id: str) -> dict:
    reenvio = s.get(Reenvio, reenvio_id)
    if reenvio is None or reenvio.a_usuario_id != yo.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos este envío.")
    reenvio.leido = True
    s.add(reenvio)
    s.commit()
    return {"leido": True}
