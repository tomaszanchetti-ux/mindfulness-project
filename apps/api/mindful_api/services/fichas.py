"""WS29 · C1.2 · La ficha AJENA: cómo se ve la Pausa de otra persona.

Una `FichaAjena` es la misma Pausa que el dueño ve en su Baúl, menos lo que es
suyo y de nadie más: **sin estrellas, sin visibilidad y sin comentario de la
carta**. Lleva `de` (quién la vivió) y `guardada` (si yo la tengo en mi Baúl).

Las fotos NO viajan por `/api/fotos/{id}` (ese endpoint es solo del dueño):
cada foto se pide por `/api/fichas/{entrega_id}/fotos/{foto_id}`, que vuelve a
pasar por la regla de lectura antes de abrir el archivo.

La regla de quién ve qué vive en `services/comunidad` y acá solo se usa.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db.models import (
    VINCULO_ACEPTADA,
    VISIBILIDAD_COMPARTIDA,
    Carta,
    Entrega,
    Foto,
    Guardada,
    Usuario,
    Vinculo,
)
from . import storage
from .comunidad import persona_de, persona_min, puede_ver_perfil
from .entrega import _carta_enriquecida

# Cuántas fichas devuelve "Descubrir" como mucho (una pantalla, no un feed infinito).
DESCUBRIR_MAX = 30


def url_foto(entrega_id: str, foto_id: str) -> str:
    """La URL con la que se pide una foto AJENA (pasa por la regla de lectura)."""
    return f"/api/fichas/{entrega_id}/fotos/{foto_id}"


def _fotos_de(s: Session, entrega_id: str) -> list:
    ids = s.scalars(
        select(Foto.id).where(Foto.entrega_id == entrega_id).order_by(Foto.created_at)
    ).all()
    return [url_foto(entrega_id, fid) for fid in ids]


def _la_guarde(s: Session, quien_id: str, entrega_id: str) -> bool:
    return s.scalar(
        select(Guardada.id)
        .where(Guardada.usuario_id == quien_id, Guardada.entrega_id == entrega_id)
        .limit(1)
    ) is not None


def ficha_ajena(s: Session, quien: Usuario, entrega: Entrega) -> dict:
    """LA forma de una ficha ajena. Quien la llama ya pasó por `puede_ver`."""
    duenio = s.get(Usuario, entrega.usuario_id)
    return {
        "tipo": "pausa",
        "id": entrega.id,
        "fecha": entrega.fecha,
        "reflexion": entrega.reflexion,
        "fotos": _fotos_de(s, entrega.id),
        "carta": _carta_enriquecida(s, s.get(Carta, entrega.carta_id)),
        "de": persona_min(duenio),
        "guardada": _la_guarde(s, quien.id, entrega.id),
    }


def ids_de_mi_comunidad(s: Session, yo_id: str) -> list:
    """Los ids de las personas con las que tengo un vínculo ACEPTADO."""
    filas = s.execute(
        select(Vinculo.solicitante_id, Vinculo.destinatario_id).where(
            Vinculo.estado == VINCULO_ACEPTADA,
            or_(Vinculo.solicitante_id == yo_id, Vinculo.destinatario_id == yo_id),
        )
    ).all()
    return [b if a == yo_id else a for (a, b) in filas]


def _publicables():
    """Lo que puede aparecer en una vitrina ajena: Pausas vividas y compartidas
    que NO son extra (una Pausa que hice de la ficha de otro no se re-publica:
    la reflexión es mía, pero la vitrina se llenaría de ecos)."""
    return (
        Entrega.completada.is_(True),
        Entrega.visibilidad == VISIBILIDAD_COMPARTIDA,
        Entrega.extra.is_(False),
    )


def descubrir(s: Session, yo: Usuario) -> list:
    """Las fichas que puedo ver sin buscar a nadie: las de los perfiles públicos
    y las de mi comunidad. Con foto primero (entra por los ojos), luego recientes."""
    tiene_fotos = select(Foto.id).where(Foto.entrega_id == Entrega.id).exists()
    q = (
        select(Entrega)
        .join(Usuario, Usuario.id == Entrega.usuario_id)
        .where(
            *_publicables(),
            Entrega.usuario_id != yo.id,
            or_(
                Usuario.perfil_publico.is_(True),
                Entrega.usuario_id.in_(ids_de_mi_comunidad(s, yo.id)),
            ),
        )
        .order_by(tiene_fotos.desc(), Entrega.fecha.desc())
        .limit(DESCUBRIR_MAX)
    )
    return [ficha_ajena(s, yo, e) for e in s.scalars(q).all()]


def vitrina_de(s: Session, yo: Usuario, usuario_id: str) -> dict:
    """El perfil de alguien: la persona SIEMPRE (para poder pedirle vínculo) y
    sus fichas solo si puedo verlas (`fichas: null` = privado sin vínculo).

    404 solo si la persona no existe: que un perfil sea privado no se esconde,
    se muestra cerrado. Lo que se esconde es el contenido.
    """
    otro = s.get(Usuario, usuario_id)
    if otro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "No encontramos a esta persona.")

    persona = persona_de(s, yo, otro)
    if not puede_ver_perfil(s, yo, otro):
        return {"persona": persona, "fichas": None}

    q = (
        select(Entrega)
        .where(*_publicables(), Entrega.usuario_id == otro.id)
        .order_by(Entrega.fecha.desc())
    )
    return {"persona": persona, "fichas": [ficha_ajena(s, yo, e) for e in s.scalars(q).all()]}


def foto_de_ficha(
    s: Session, entrega: Entrega, foto_id: str
) -> Optional[tuple]:
    """El contenido+mime de una foto de `entrega`, o None (foto de otra ficha,
    inexistente o archivo perdido). El llamador ya validó `puede_ver`."""
    foto = s.get(Foto, foto_id)
    if foto is None or foto.entrega_id != entrega.id:
        return None
    contenido = storage.leer(foto.storage_path)
    if contenido is None:
        return None
    return contenido, storage.mime_de(foto.storage_path)
