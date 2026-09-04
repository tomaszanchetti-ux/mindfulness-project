"""M4 · Baúl de Crecimiento Personal. Casi sólo lectura; escribe dos cosas: la
visibilidad de una ficha y el borrado.

Lee `entregas ⨝ cartas (global) ⨝ fotos`, filtrado por user_id. Dos modos de orden
(toggle): Reciente (default) y Más valoradas. Borrado REAL (sin papelera): limpia la
fila + sus fotos (cascade) + apaga el link de M5 si lo había (la carta-sola sobrevive).
"""

from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Carta, Compartido, Entrega, Foto
from . import storage
from .entrega import _carta_enriquecida
from .fotos import urls_de


def _item(s: Session, entrega: Entrega) -> dict:
    carta = s.get(Carta, entrega.carta_id)
    return {
        "id": entrega.id,
        "fecha": entrega.fecha,
        "estrellas": entrega.estrellas,
        "completada": entrega.completada,
        "reflexion": entrega.reflexion,
        # WS25 · quién ve esta ficha: `privada` o `compartida` (con su comunidad).
        # Las estrellas NO viajan nunca: son del dueño diga lo que diga esto.
        "visibilidad": entrega.visibilidad,
        # URLs de la API (las imágenes son privadas; se sirven con login).
        "fotos": urls_de(s, entrega.id),
        "carta": _carta_enriquecida(s, carta),
    }


def listar_baul(s: Session, usuario_id: str, orden: str = "reciente") -> list[dict]:
    # El Baúl es la colección de pausas VIVIDAS: solo entregas completadas.
    # (La carta del día entregada pero aún no vivida no aparece — coherente con
    # el vacío "cuando completes tu primera consigna, va a aparecer aquí".)
    q = select(Entrega).where(
        Entrega.usuario_id == usuario_id,
        Entrega.completada.is_(True),
    )
    if orden == "valoradas":
        # Más valoradas primero; sin estrella al fondo; desempate por fecha reciente.
        q = q.order_by(Entrega.estrellas.desc().nullslast(), Entrega.fecha.desc())
    else:  # reciente (default)
        q = q.order_by(Entrega.fecha.desc())
    return [_item(s, e) for e in s.scalars(q).all()]


def cambiar_visibilidad(
    s: Session, usuario_id: str, entrega_id: str, visibilidad: str
) -> dict:
    """WS25 · publica o repliega la ficha de una Pausa guardada. Devuelve el ítem.

    El orden importa: primero el aislamiento (una entrega ajena o inexistente es
    404, jamás un 409 que delate que existe) y recién después la regla de negocio.
    Solo se publica lo VIVIDO: una Pausa sin cerrar no tiene ficha que mostrar.
    """
    entrega = s.get(Entrega, entrega_id)
    if entrega is None or entrega.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")
    if not entrega.completada:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Guarda la Pausa en tu Baúl antes de compartirla con tu comunidad",
        )

    entrega.visibilidad = visibilidad
    s.add(entrega)
    s.commit()
    s.refresh(entrega)
    return _item(s, entrega)


def borrar_entrega(s: Session, usuario_id: str, entrega_id: str) -> None:
    entrega = s.get(Entrega, entrega_id)
    if entrega is None or entrega.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")

    # M5: el link "ejercicio" muere con la entrada; la "carta sola" no la referencia y sobrevive.
    for comp in s.scalars(
        select(Compartido).where(Compartido.entrega_id == entrega_id)
    ).all():
        comp.activo = False

    # Borrado real: primero los ARCHIVOS de las fotos (Storage), después la fila
    # (las filas de fotos caen por cascade del FK). Sin papelera.
    rutas = list(s.scalars(
        select(Foto.storage_path).where(Foto.entrega_id == entrega_id)
    ).all())
    storage.borrar(rutas)
    s.delete(entrega)
    s.commit()
