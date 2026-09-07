"""WS30 · Q/A de Tomás · el reenvío lleva un comentario opcional.

Lo que se prueba: el comentario viaja con la ficha en "Te enviaron", se recorta,
vacío es null, y largo es 422 SIN dejar rastro (ni reenvío ni aviso).
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    VINCULO_ACEPTADA, Aviso, Carta, Entrega, Reenvio, Usuario, Vinculo,
)
from mindful_api.main import app
from mindful_api.services.reenvios import COMENTARIO_REENVIO_MAX

client = TestClient(app)
PREFIJO = "c12b|"


def _h(sub: str) -> dict:
    return {"X-Debug-Sub": PREFIJO + sub, "X-Debug-Email": f"{sub}@c12b.local"}


def _usuario(s, sub: str) -> Usuario:
    u = Usuario(firebase_uid=PREFIJO + sub, email=f"{sub}@c12b.local", apodo=sub.title(),
                terminos_aceptados_at=datetime.now(timezone.utc))
    s.add(u)
    s.commit()
    s.refresh(u)
    return u


def _mundo(s):
    """Yo, un receptor en mi comunidad y una Pausa MÍA compartida y vivida."""
    yo, receptor = _usuario(s, "yo"), _usuario(s, "receptor")
    s.add(Vinculo(solicitante_id=yo.id, destinatario_id=receptor.id, estado=VINCULO_ACEPTADA))
    carta_id = s.scalar(select(Carta.id).order_by(Carta.id).limit(1))
    e = Entrega(usuario_id=yo.id, carta_id=carta_id, completada=True,
                visibilidad="compartida", reflexion="una pausa")
    s.add(e)
    s.commit()
    return e.id, receptor.id


@pytest.fixture(autouse=True)
def _limpio():
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()
    yield
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()


def test_el_comentario_viaja_con_la_ficha_recortado():
    with SessionLocal() as s:
        ficha_id, receptor_id = _mundo(s)
    r = client.post("/api/reenvios", headers=_h("yo"), json={
        "entrega_id": ficha_id, "a_usuario_id": receptor_id,
        "comentario": "  Me acordé de ti con esta.  ",
    })
    assert r.status_code == 201, r.text
    bandeja = client.get("/api/reenvios/recibidos", headers=_h("receptor")).json()
    assert bandeja["reenvios"][0]["comentario"] == "Me acordé de ti con esta."
    assert bandeja["reenvios"][0]["ficha"]["id"] == ficha_id


@pytest.mark.parametrize("comentario", [None, "", "   "])
def test_sin_comentario_es_null(comentario):
    with SessionLocal() as s:
        ficha_id, receptor_id = _mundo(s)
    body = {"entrega_id": ficha_id, "a_usuario_id": receptor_id}
    if comentario is not None:
        body["comentario"] = comentario
    assert client.post("/api/reenvios", headers=_h("yo"), json=body).status_code == 201
    bandeja = client.get("/api/reenvios/recibidos", headers=_h("receptor")).json()
    assert bandeja["reenvios"][0]["comentario"] is None


def test_comentario_largo_es_422_sin_rastro():
    with SessionLocal() as s:
        ficha_id, receptor_id = _mundo(s)
    # El borde exacto pasa; uno más, no.
    justo = "a" * COMENTARIO_REENVIO_MAX
    r = client.post("/api/reenvios", headers=_h("yo"), json={
        "entrega_id": ficha_id, "a_usuario_id": receptor_id, "comentario": justo + "a",
    })
    assert r.status_code == 422 and "200 caracteres" in r.json()["detail"]
    with SessionLocal() as s:
        assert s.scalar(select(Reenvio).where(Reenvio.entrega_id == ficha_id)) is None
        assert s.scalar(select(Aviso).where(Aviso.usuario_id == receptor_id)) is None
    r = client.post("/api/reenvios", headers=_h("yo"), json={
        "entrega_id": ficha_id, "a_usuario_id": receptor_id, "comentario": justo,
    })
    assert r.status_code == 201
