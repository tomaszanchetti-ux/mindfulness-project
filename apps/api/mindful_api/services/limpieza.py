"""WS30 · C3 · Limpieza de fotos huérfanas (deuda T7, WS16).

Una foto queda huérfana cuando alguien la sube desde Reflexionar y después NO
guarda la Pausa: la entrega sigue `completada = false` y la foto ocupa lugar en
Storage sin que nadie pueda verla (el Baúl solo lista Pausas vividas).

Regla: foto de una entrega NO completada, subida hace más de `dias` días
(default 7: de sobra para "la guardo mañana"). Se borra primero el archivo y
después la fila, como en `borrar_entrega`. La entrega en sí NO se toca (es la
carta de ese día; el motor la necesita).

Corre dentro del barrido de avisos (cada 15', idempotente y barato: una query)
y a mano con `python -m mindful_api.services.limpieza [--borrar] [--dias N]`.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Entrega, Foto
from . import storage

DIAS_HUERFANA = 7


def fotos_huerfanas(s: Session, dias: int = DIAS_HUERFANA, ahora: datetime | None = None) -> list[Foto]:
    """Las fotos candidatas, sin tocar nada (para el ensayo y para el test)."""
    limite = (ahora or datetime.now(timezone.utc)) - timedelta(days=dias)
    return list(
        s.scalars(
            select(Foto)
            .join(Entrega, Entrega.id == Foto.entrega_id)
            .where(Entrega.completada.is_(False), Foto.created_at < limite)
            .order_by(Foto.created_at)
        ).all()
    )


def limpiar_fotos_huerfanas(
    s: Session, dias: int = DIAS_HUERFANA, borrar: bool = True, ahora: datetime | None = None
) -> dict:
    """Devuelve conteos. Con `borrar=False` es un ensayo: cuenta y no toca."""
    fotos = fotos_huerfanas(s, dias, ahora)
    if not borrar or not fotos:
        return {"huerfanas": len(fotos), "borradas": 0}

    # Archivos primero (si Storage falla, la fila queda y se reintenta en el
    # próximo barrido); filas después, todas juntas.
    storage.borrar([f.storage_path for f in fotos])
    for f in fotos:
        s.delete(f)
    s.commit()
    return {"huerfanas": len(fotos), "borradas": len(fotos)}


if __name__ == "__main__":  # pragma: no cover — uso manual
    import argparse

    from ..db.base import SessionLocal

    ap = argparse.ArgumentParser(description="Fotos huérfanas: ensayo por defecto, --borrar para aplicar.")
    ap.add_argument("--borrar", action="store_true")
    ap.add_argument("--dias", type=int, default=DIAS_HUERFANA)
    args = ap.parse_args()
    with SessionLocal() as sesion:
        print(limpiar_fotos_huerfanas(sesion, dias=args.dias, borrar=args.borrar))
