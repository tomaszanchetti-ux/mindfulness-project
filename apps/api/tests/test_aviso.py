"""WS20 · aviso diario por email: barrido, dedup por día, endpoint interno."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Usuario
from mindful_api.main import app
from mindful_api.services import aviso as aviso_srv
from mindful_api.services.aviso import enviar_avisos

client = TestClient(app)


def _usuario(sub: str, hora: str, tz: str = "Europe/Madrid", aviso: bool = True) -> dict:
    h = {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}
    client.put(
        "/api/perfil",
        headers=h,
        json={"aceptar_terminos": True, "hora_aviso": hora, "tz": tz, "aviso_activo": aviso},
    )
    return h


def _capturar_envios(monkeypatch) -> list[str]:
    enviados: list[str] = []

    def _fake(destino, asunto, texto, html):  # noqa: ANN001 — firma del real
        enviados.append(destino)
        return True

    monkeypatch.setattr(aviso_srv, "enviar_email", _fake)
    return enviados


# 12:00 UTC = 14:00 en Madrid (verano) = 09:00 en Buenos Aires.
AHORA = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)


def test_barrido_manda_solo_a_quien_le_toca(monkeypatch):
    _usuario("avi|pasado", "08:00")  # 14:00 local > 08:00 → le toca
    _usuario("avi|futuro", "22:00")  # 14:00 local < 22:00 → todavía no
    _usuario("avi|apagado", "08:00", aviso=False)  # toggle off → jamás
    _usuario("avi|otra-tz", "10:00", tz="America/Argentina/Buenos_Aires")  # 09:00 < 10:00

    enviados = _capturar_envios(monkeypatch)
    with SessionLocal() as s:
        enviar_avisos(s, AHORA)

    # Solo miramos NUESTROS usuarios (otros tests de la suite también crean).
    assert "avi|pasado@mindful.local" in enviados
    assert "avi|futuro@mindful.local" not in enviados
    assert "avi|apagado@mindful.local" not in enviados
    assert "avi|otra-tz@mindful.local" not in enviados

    # Segundo tick del mismo día: a nadie de nuevo (dedup por fecha local).
    enviados.clear()
    with SessionLocal() as s:
        enviar_avisos(s, AHORA)
    assert all(not e.startswith("avi|") for e in enviados)


def test_no_avisa_si_ya_guardo_la_pausa(monkeypatch):
    h = _usuario("avi|cumplidor", "08:00")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    client.put(f"/api/entregas/{entrega_id}/cierre", headers=h, json={"completada": True})

    enviados = _capturar_envios(monkeypatch)
    with SessionLocal() as s:
        enviar_avisos(s, datetime.now(timezone.utc))
    assert "avi|cumplidor@mindful.local" not in enviados

    # Quedó estampado para no re-evaluarlo el resto del día.
    with SessionLocal() as s:
        u = s.scalars(select(Usuario).where(Usuario.firebase_uid == "avi|cumplidor")).one()
        assert u.ultimo_aviso_fecha is not None


def test_endpoint_interno_protegido(monkeypatch):
    # Sin secreto configurado: el endpoint no existe.
    monkeypatch.setattr(settings, "aviso_secret", "")
    assert client.post("/api/internal/aviso-diario").status_code == 404

    # Con secreto: exige el header correcto.
    monkeypatch.setattr(settings, "aviso_secret", "s3creto")
    assert client.post("/api/internal/aviso-diario").status_code == 401
    r = client.post("/api/internal/aviso-diario", headers={"X-Aviso-Secret": "s3creto"})
    assert r.status_code == 200
    assert set(r.json()) == {"candidatos", "enviados", "saltados"}
