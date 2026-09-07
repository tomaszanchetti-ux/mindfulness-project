"""WS30 · C3 · Fotos huérfanas: solo las de entregas NO completadas y viejas."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Carta, Entrega, Foto, Usuario
from mindful_api.main import app
from mindful_api.services import limpieza, storage
from mindful_api.services.limpieza import fotos_huerfanas, limpiar_fotos_huerfanas

client = TestClient(app)
PREFIJO = "c3|"


@pytest.fixture(autouse=True)
def _limpio():
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()
    yield
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()


def _mundo(s, ahora):
    u = Usuario(firebase_uid=PREFIJO + "u", email="u@c3.local", apodo="U",
                terminos_aceptados_at=ahora)
    s.add(u)
    s.commit()
    carta_id = s.scalar(select(Carta.id).order_by(Carta.id).limit(1))

    def entrega(completada):
        e = Entrega(usuario_id=u.id, carta_id=carta_id, completada=completada)
        s.add(e)
        s.commit()
        return e

    def foto(e, hace_dias, nombre):
        f = Foto(entrega_id=e.id, storage_path=f"{PREFIJO}{nombre}.png",
                 created_at=ahora - timedelta(days=hace_dias))
        s.add(f)
        s.commit()
        return f.id

    vivida, abandonada, reciente = entrega(True), entrega(False), entrega(False)
    return {
        "vivida_vieja": foto(vivida, 30, "vivida"),        # se queda: la Pausa está vivida
        "abandonada_vieja": foto(abandonada, 8, "abandonada"),  # se va
        "abandonada_reciente": foto(reciente, 6, "reciente"),   # se queda: puede guardarla aún
    }


def test_solo_se_van_las_viejas_de_entregas_no_completadas(monkeypatch):
    borrados = []
    monkeypatch.setattr(storage, "borrar", lambda paths: borrados.extend(paths))
    ahora = datetime.now(timezone.utc)
    with SessionLocal() as s:
        ids = _mundo(s, ahora)
        assert [f.id for f in fotos_huerfanas(s, ahora=ahora)] == [ids["abandonada_vieja"]]

        # Ensayo: cuenta y no toca.
        assert limpiar_fotos_huerfanas(s, borrar=False, ahora=ahora) == {"huerfanas": 1, "borradas": 0}
        assert borrados == [] and s.get(Foto, ids["abandonada_vieja"]) is not None

        assert limpiar_fotos_huerfanas(s, ahora=ahora) == {"huerfanas": 1, "borradas": 1}
        assert borrados == [f"{PREFIJO}abandonada.png"]
        assert s.get(Foto, ids["abandonada_vieja"]) is None
        assert s.get(Foto, ids["vivida_vieja"]) is not None
        assert s.get(Foto, ids["abandonada_reciente"]) is not None
        # La entrega abandonada sigue existiendo: solo se fue su foto.
        assert s.scalar(select(Entrega).where(Entrega.id == s.get(Foto, ids["abandonada_reciente"]).entrega_id)) is not None

        # Segunda pasada: nada que hacer.
        assert limpiar_fotos_huerfanas(s, ahora=ahora) == {"huerfanas": 0, "borradas": 0}


def test_el_barrido_limpia_y_no_se_cae_si_storage_falla(monkeypatch):
    monkeypatch.setattr(storage, "borrar", lambda paths: (_ for _ in ()).throw(RuntimeError("bucket caído")))
    monkeypatch.setattr(settings, "aviso_secret", "s3creto")
    with SessionLocal() as s:
        ids = _mundo(s, datetime.now(timezone.utc))
    r = client.post("/api/internal/aviso-diario", headers={"X-Aviso-Secret": "s3creto"})
    assert r.status_code == 200, r.text
    assert "enviados" in r.json()
    assert r.json()["fotos_huerfanas"] == {"error": "bucket caído"}
    with SessionLocal() as s:
        assert s.get(Foto, ids["abandonada_vieja"]) is not None   # Storage falló: la fila se queda para reintentar

    monkeypatch.setattr(storage, "borrar", lambda paths: None)
    r = client.post("/api/internal/aviso-diario", headers={"X-Aviso-Secret": "s3creto"})
    assert r.json()["fotos_huerfanas"] == {"huerfanas": 1, "borradas": 1}
