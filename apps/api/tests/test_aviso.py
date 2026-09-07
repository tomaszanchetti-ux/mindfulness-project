"""WS20/WS21 · aviso diario por push: barrido, dedup por día, suscripciones."""

from __future__ import annotations

from datetime import datetime, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import PushSuscripcion, Usuario
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


def _suscribir(h: dict, sufijo: str) -> None:
    r = client.post(
        "/api/push/suscripcion",
        headers=h,
        json={
            "endpoint": f"https://push.test/device-{sufijo}",
            "p256dh": "k" * 20,
            "auth": "a" * 10,
        },
    )
    assert r.status_code == 200


def _capturar_envios(monkeypatch) -> list[str]:
    """Reemplaza el sender real: anota el endpoint y responde ok."""
    enviados: list[str] = []

    def _fake(sus, titulo, cuerpo, url):  # noqa: ANN001 — firma del real
        enviados.append(sus.endpoint)
        return "ok"

    monkeypatch.setattr(aviso_srv, "enviar_push", _fake)
    return enviados


# 12:00 UTC = 14:00 en Madrid (verano) = 09:00 en Buenos Aires.
AHORA = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)


def test_barrido_manda_solo_a_quien_le_toca(monkeypatch):
    _suscribir(_usuario("avi|pasado", "08:00"), "pasado")  # 14:00 > 08:00 → le toca
    _suscribir(_usuario("avi|futuro", "22:00"), "futuro")  # 14:00 < 22:00 → todavía no
    _suscribir(_usuario("avi|apagado", "08:00", aviso=False), "apagado")  # toggle off
    _suscribir(  # 09:00 local < 10:00 → todavía no
        _usuario("avi|otra-tz", "10:00", tz="America/Argentina/Buenos_Aires"), "otra-tz"
    )
    _usuario("avi|sin-device", "08:00")  # le toca pero NO tiene dispositivo

    enviados = _capturar_envios(monkeypatch)
    with SessionLocal() as s:
        enviar_avisos(s, AHORA)

    # Solo miramos NUESTROS dispositivos (otros tests de la suite también crean usuarios).
    assert "https://push.test/device-pasado" in enviados
    assert "https://push.test/device-futuro" not in enviados
    assert "https://push.test/device-apagado" not in enviados
    assert "https://push.test/device-otra-tz" not in enviados

    # Sin dispositivo: no se estampa (si se suscribe hoy más tarde, le llega hoy).
    with SessionLocal() as s:
        u = s.scalars(select(Usuario).where(Usuario.firebase_uid == "avi|sin-device")).one()
        assert u.ultimo_aviso_fecha is None

    # Segundo tick del mismo día: a nadie de nuevo (dedup por fecha local).
    enviados.clear()
    with SessionLocal() as s:
        enviar_avisos(s, AHORA)
    assert "https://push.test/device-pasado" not in enviados


def test_suscripcion_tardia_recibe_el_mismo_dia(monkeypatch):
    h = _usuario("avi|tardio", "08:00")
    enviados = _capturar_envios(monkeypatch)

    with SessionLocal() as s:  # tick sin dispositivo: nada, sin estampa
        enviar_avisos(s, AHORA)
    assert not [e for e in enviados if "tardio" in e]

    _suscribir(h, "tardio")  # activa las notificaciones a la tarde
    with SessionLocal() as s:
        enviar_avisos(s, AHORA)
    assert "https://push.test/device-tardio" in enviados


def test_suscripcion_muerta_se_borra(monkeypatch):
    h = _usuario("avi|muerto", "08:00")
    _suscribir(h, "muerto")

    monkeypatch.setattr(aviso_srv, "enviar_push", lambda *a: "gone")
    with SessionLocal() as s:
        enviar_avisos(s, AHORA)

    with SessionLocal() as s:
        quedan = s.scalars(
            select(PushSuscripcion).where(
                PushSuscripcion.endpoint == "https://push.test/device-muerto"
            )
        ).all()
        assert quedan == []


def test_no_avisa_si_ya_guardo_la_pausa(monkeypatch):
    h = _usuario("avi|cumplidor", "08:00")
    _suscribir(h, "cumplidor")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    client.put(f"/api/entregas/{entrega_id}/cierre", headers=h, json={"completada": True})

    enviados = _capturar_envios(monkeypatch)
    with SessionLocal() as s:
        enviar_avisos(s, datetime.now(timezone.utc))
    assert "https://push.test/device-cumplidor" not in enviados


def test_suscripcion_cambia_de_dueno_y_baja():
    ha = _usuario("avi|duenio-a", "08:00")
    hb = _usuario("avi|duenio-b", "08:00")
    _suscribir(ha, "compartido")
    _suscribir(hb, "compartido")  # mismo endpoint, otro usuario → se reasigna

    with SessionLocal() as s:
        sus = s.scalars(
            select(PushSuscripcion).where(
                PushSuscripcion.endpoint == "https://push.test/device-compartido"
            )
        ).one()
        ub = s.scalars(select(Usuario).where(Usuario.firebase_uid == "avi|duenio-b")).one()
        assert sus.usuario_id == ub.id

    # La baja de otro usuario NO borra (aislamiento); la del dueño sí.
    client.post("/api/push/baja", headers=ha, json={"endpoint": "https://push.test/device-compartido"})
    with SessionLocal() as s:
        assert s.scalars(select(PushSuscripcion).where(
            PushSuscripcion.endpoint == "https://push.test/device-compartido")).first()
    client.post("/api/push/baja", headers=hb, json={"endpoint": "https://push.test/device-compartido"})
    with SessionLocal() as s:
        assert not s.scalars(select(PushSuscripcion).where(
            PushSuscripcion.endpoint == "https://push.test/device-compartido")).first()


def test_endpoint_interno_protegido(monkeypatch):
    # Sin secreto configurado: el endpoint no existe.
    monkeypatch.setattr(settings, "aviso_secret", "")
    assert client.post("/api/internal/aviso-diario").status_code == 404

    # Con secreto: exige el header correcto.
    monkeypatch.setattr(settings, "aviso_secret", "s3creto")
    assert client.post("/api/internal/aviso-diario").status_code == 401
    r = client.post("/api/internal/aviso-diario", headers={"X-Aviso-Secret": "s3creto"})
    assert r.status_code == 200
    # WS30 · C3: el mismo barrido informa la limpieza de fotos huérfanas.
    assert set(r.json()) == {"candidatos", "enviados", "saltados", "fotos_huerfanas"}
