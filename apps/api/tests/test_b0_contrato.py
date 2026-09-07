"""WS27 · B0 · el contrato del Bloque B en pie.

Lo que más importa acá es el hallazgo de la Fase 0: el seed corre en cada deploy y
borraba toda carta que no estuviera en los JSON. Una carta de la comunidad
publicada en `cartas` tiene que SOBREVIVIR al seed; una carta huérfana de Dwellia
(que ya no está en los JSON) tiene que seguir yéndose.
"""

from __future__ import annotations

from fastapi.testclient import TestClient
from sqlalchemy import select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    ORIGEN_COMUNIDAD,
    ORIGEN_DWELLIA,
    Aviso,
    Carta,
    CartaComunidad,
    Usuario,
)
from mindful_api.main import app
from mindful_api.seed import seed

client = TestClient(app)

COM_ID = "test-b0-com-01"
HUERFANA_ID = "test-b0-dw-huerfana"


def _limpiar():
    with SessionLocal() as s:
        for cid in (COM_ID, HUERFANA_ID):
            c = s.get(Carta, cid)
            if c is not None:
                s.delete(c)
        s.commit()


def test_seed_respeta_las_cartas_de_la_comunidad_y_borra_las_huerfanas_de_dwellia():
    _limpiar()
    with SessionLocal() as s:
        s.add(Carta(id=COM_ID, categoria_slug="gratitud", accion_slug="contemplar",
                    concepto="test-b0", frase="Una frase de la comunidad",
                    prompt="Un prompt de prueba que escribe en tu diario.",
                    origen=ORIGEN_COMUNIDAD, firma_publica="Tomito"))
        s.add(Carta(id=HUERFANA_ID, categoria_slug="gratitud", accion_slug="contemplar",
                    concepto="test-b0-h", frase="Huérfana", prompt="No está en el JSON. Diario.",
                    origen=ORIGEN_DWELLIA))
        s.commit()

    conteos = seed()

    with SessionLocal() as s:
        com = s.get(Carta, COM_ID)
        assert com is not None, "el seed borró una carta de la comunidad"
        assert com.origen == ORIGEN_COMUNIDAD and com.firma_publica == "Tomito"
        assert s.get(Carta, HUERFANA_ID) is None, "una carta de Dwellia fuera del JSON debe irse"
        # El mazo de Dwellia queda exactamente como los JSON; el resumen público
        # cuenta TODO el mazo servible (77 + la de la comunidad).
        n_dw = len(s.scalars(select(Carta).where(Carta.origen == ORIGEN_DWELLIA)).all())
        assert n_dw == conteos["cartas"] == 77
    assert client.get("/api/contenido/resumen").json()["cartas"] == 78
    _limpiar()


def test_seed_es_idempotente_con_cartas_de_la_comunidad():
    _limpiar()
    with SessionLocal() as s:
        s.add(Carta(id=COM_ID, categoria_slug="sentido", accion_slug="caminar",
                    frase="Otra", prompt="Prompt con diario.", origen=ORIGEN_COMUNIDAD))
        s.commit()
    seed()
    seed()
    with SessionLocal() as s:
        assert s.get(Carta, COM_ID) is not None
        assert len(s.scalars(select(Carta)).all()) == 78
    _limpiar()


def test_carta_del_dia_declara_origen_y_firma():
    h = {"X-Debug-Sub": "b0|origen", "X-Debug-Email": "b0@mindful.local"}
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    carta = client.get("/api/carta-del-dia", headers=h).json()["carta"]
    assert carta["origen"] == ORIGEN_DWELLIA
    assert carta["firma_publica"] is None


def test_defaults_del_contrato():
    with SessionLocal() as s:
        u = Usuario(firebase_uid="b0|defaults", email="d@mindful.local")
        s.add(u)
        s.commit()
        s.refresh(u)
        assert u.recibe_comunidad is False

        cc = CartaComunidad(usuario_id=u.id, categoria_slug="vinculos", accion_slug="hacer",
                            frase="Frase", prompt="Prompt con diario.")
        av = Aviso(usuario_id=u.id, tipo="carta_estado", texto="Tu carta cambió de estado")
        s.add_all([cc, av])
        s.commit()
        s.refresh(cc)
        s.refresh(av)
        assert cc.estado == "en_revision" and cc.firma == "anonima" and cc.carta_id is None
        assert av.leido is False

        # Borrar al usuario arrastra su propuesta y sus avisos (CASCADE).
        cc_id, av_id = cc.id, av.id
        s.delete(u)
        s.commit()
        s.expire_all()  # el CASCADE lo hizo Postgres: que la sesión vuelva a mirar
        assert s.get(CartaComunidad, cc_id) is None
        assert s.get(Aviso, av_id) is None
