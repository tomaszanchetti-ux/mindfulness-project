"""WS24 · A1.3 · las cartas descartadas al cambiar cuentan como vistas (ventanas de 7 días)."""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from sqlalchemy import select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Carta, Entrega
from mindful_api.services.entrega import historial_motor


def test_las_descartadas_entran_al_historial_antes_de_la_servida():
    tz = ZoneInfo("Europe/Madrid")
    with SessionLocal() as s:
        cartas = s.scalars(select(Carta).order_by(Carta.id).limit(3)).all()
        servida, d1, d2 = cartas
        e = Entrega(usuario_id="x", carta_id=servida.id,
                    fecha=datetime(2026, 9, 4, 10, 0, tzinfo=timezone.utc),
                    descartadas=[d1.id, d2.id], cambios=2, estrellas=4)
        rows = [(e, servida.categoria_slug, servida.accion_slug, servida.concepto)]
        h = historial_motor(s, rows, tz)

    assert [x.carta_id for x in h] == [d1.id, d2.id, servida.id]
    assert {x.dia for x in h} == {datetime(2026, 9, 4).toordinal()}
    # La servida conserva sus estrellas; las descartadas no inclinan nada.
    assert h[-1].estrellas == 4 and h[0].estrellas is None and h[1].estrellas is None
    assert h[0].concepto == d1.concepto and h[0].categoria == d1.categoria_slug


def test_sin_descartadas_es_el_historial_de_siempre():
    tz = ZoneInfo("Europe/Madrid")
    with SessionLocal() as s:
        c = s.scalars(select(Carta).limit(1)).first()
        e = Entrega(usuario_id="x", carta_id=c.id,
                    fecha=datetime(2026, 9, 4, 10, 0, tzinfo=timezone.utc))
        h = historial_motor(s, [(e, c.categoria_slug, c.accion_slug, c.concepto)], tz)
    assert [x.carta_id for x in h] == [c.id]
