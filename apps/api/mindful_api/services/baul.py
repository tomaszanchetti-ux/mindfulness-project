"""M4 · Baúl de Crecimiento Personal. Casi sólo lectura; su única escritura es el borrado.

Lee `entregas ⨝ cartas (global) ⨝ fotos`, filtrado por user_id. Dos modos de orden
(toggle): Reciente (default) y Más valoradas. Borrado REAL (sin papelera): limpia la
fila + sus fotos (cascade) + apaga el link de M5 si lo había (la carta-sola sobrevive).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Carta, Compartido, Entrega, Foto
from .entrega import _carta_enriquecida


def _fotos_de(s: Session, entrega_id: str) -> list[str]:
    return list(s.scalars(
        select(Foto.storage_path).where(Foto.entrega_id == entrega_id)
    ).all())


def _item(s: Session, entrega: Entrega) -> dict:
    carta = s.get(Carta, entrega.carta_id)
    return {
        "id": entrega.id,
        "fecha": entrega.fecha,
        "estrellas": entrega.estrellas,
        "completada": entrega.completada,
        "reflexion": entrega.reflexion,
        "fotos": _fotos_de(s, entrega.id),
        "carta": _carta_enriquecida(s, carta),
    }


def listar_baul(s: Session, usuario_id: str, orden: str = "reciente") -> list[dict]:
    q = select(Entrega).where(Entrega.usuario_id == usuario_id)
    if orden == "valoradas":
        # Más valoradas primero; sin estrella al fondo; desempate por fecha reciente.
        q = q.order_by(Entrega.estrellas.desc().nullslast(), Entrega.fecha.desc())
    else:  # reciente (default)
        q = q.order_by(Entrega.fecha.desc())
    return [_item(s, e) for e in s.scalars(q).all()]


def borrar_entrega(s: Session, usuario_id: str, entrega_id: str) -> None:
    entrega = s.get(Entrega, entrega_id)
    if entrega is None or entrega.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")

    # M5: el link "ejercicio" muere con la entrada; la "carta sola" no la referencia y sobrevive.
    for comp in s.scalars(
        select(Compartido).where(Compartido.entrega_id == entrega_id)
    ).all():
        comp.activo = False

    # Borrado real: la fila + sus fotos (cascade por FK). Sin papelera.
    s.delete(entrega)
    s.commit()
