"""WS28 · ajustes de Tomás tras el Q/A visual: frase 20-40, prompt 80-150, admin premium."""

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Usuario
from mindful_api.main import app
from mindful_api.services.cartas_comunidad import FRASE_MAX, FRASE_MIN, PROMPT_MAX, PROMPT_MIN
from mindful_api.services.plan import activar_premium, es_premium, limites

client = TestClient(app)
SUB = "ws28|autor"
PROMPT_OK = ("Mira por la ventana hasta encontrar algo que no habías visto. "
             "Escribe en tu diario qué era y por qué se te escapaba.")


def _usuario(premium: bool = True) -> str:
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid == SUB))
        u = Usuario(firebase_uid=SUB, email="ws28@mindful.local", apodo="Ana",
                    terminos_aceptados_at=datetime.now(timezone.utc))
        if premium:
            activar_premium(u, datetime(2099, 1, 1, tzinfo=timezone.utc))
        s.add(u); s.commit()
        return u.id


def _proponer(frase: str, prompt: str):
    return client.post("/api/cartas-comunidad", headers={"X-Debug-Sub": SUB}, json={
        "categoria": "gratitud", "accion": "contemplar",
        "frase": frase, "prompt": prompt, "firma": "anonima", "cesion_aceptada": True,
    })


def test_los_limites_son_los_de_tomas():
    assert (FRASE_MIN, FRASE_MAX, PROMPT_MIN, PROMPT_MAX) == (20, 40, 80, 150)
    assert PROMPT_MIN <= len(PROMPT_OK) <= PROMPT_MAX


def test_frase_corta_rebota_y_el_borde_entra():
    _usuario()
    r = _proponer("x" * (FRASE_MIN - 1), PROMPT_OK)
    assert r.status_code == 422
    assert f"al menos {FRASE_MIN}" in r.json()["detail"]
    r = _proponer("Una frase con veinte." + "x" * (FRASE_MIN - 21), PROMPT_OK)  # justo 20
    assert r.status_code == 201, r.json()


def test_prompt_corto_rebota_y_el_borde_entra():
    _usuario()
    base = "Escribe en tu diario"
    r = _proponer("Una frase que mide bien.", ("x" * (PROMPT_MIN - 1 - len(base))) + base)
    assert r.status_code == 422
    assert f"entre {PROMPT_MIN} y {PROMPT_MAX}" in r.json()["detail"]
    r = _proponer("Una frase que mide bien.", ("x" * (PROMPT_MIN - len(base))) + base)
    assert r.status_code == 201, r.json()


def test_el_admin_es_premium_sin_pagar(monkeypatch):
    _usuario(premium=False)
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == SUB))
        assert not es_premium(u) and limites(u).plan == "free"
        monkeypatch.setattr(settings, "admin_uids", SUB)
        assert es_premium(u) and limites(u).plan == "premium"
        assert limites(u).propone_cartas is True
    # Y la API lo ve igual: sin Stripe, puede proponer.
    monkeypatch.setattr(settings, "admin_uids", SUB)
    assert _proponer("Una frase que mide bien.", PROMPT_OK).status_code == 201
