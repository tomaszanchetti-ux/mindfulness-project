"""WS24 · A1.2 · Pagos con Stripe: apagado por defecto, y el webhook manda.

Nada de red: se monkeypatchea la verificación de firma y la creación de la
sesión de Checkout. Lo que se prueba es NUESTRA lógica — quién se vuelve
premium, con qué fecha, y qué pasa cuando Stripe repite un evento.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import stripe
from fastapi.testclient import TestClient
from sqlalchemy import select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Usuario
from mindful_api.main import app

client = TestClient(app)

AHORA = int(datetime.now(timezone.utc).timestamp())


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


def _usuario(sub: str) -> str:
    """Auto-provisiona al usuario (modo dev) y devuelve su id."""
    assert client.get("/api/perfil", headers=_headers(sub)).status_code == 200
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
        assert u is not None
        return u.id


def _leer(usuario_id: str) -> Usuario:
    with SessionLocal() as s:
        u = s.get(Usuario, usuario_id)
        assert u is not None
        return u


# ── Eventos de Stripe (la forma real, recortada a lo que miramos) ────────────
def _evento_alta(usuario_id: str, customer: str, evento_id: str = "evt_alta") -> dict:
    return {
        "id": evento_id,
        "type": "checkout.session.completed",
        "created": AHORA,
        "data": {
            "object": {
                "id": "cs_test_1",
                "client_reference_id": usuario_id,
                "customer": customer,
                "subscription": "sub_test_1",  # sin expandir: fuerza el respaldo +366 d
            }
        },
    }


def _evento_renovacion(customer: str, fin: int) -> dict:
    return {
        "id": "evt_renov",
        "type": "invoice.paid",
        "created": AHORA,
        "data": {
            "object": {
                "id": "in_test_1",
                "customer": customer,
                "lines": {
                    "data": [
                        {
                            "subscription": "sub_test_1",
                            "period": {"start": AHORA, "end": fin},
                        }
                    ]
                },
            }
        },
    }


def _evento_baja(customer: str) -> dict:
    return {
        "id": "evt_baja",
        "type": "customer.subscription.deleted",
        "created": AHORA,
        "data": {"object": {"id": "sub_test_1", "customer": customer}},
    }


@pytest.fixture
def enviar_webhook(monkeypatch):
    """Webhook encendido y firma dada por buena: el body vuelve tal cual."""
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")
    monkeypatch.setattr(
        stripe.Webhook, "construct_event", lambda payload, sig, secret, **kw: json.loads(payload)
    )

    def _enviar(evento: dict):
        return client.post(
            "/api/pagos/webhook", json=evento, headers={"stripe-signature": "t=1,v1=falsa"}
        )

    return _enviar


# ── Apagado por defecto ──────────────────────────────────────────────────────
def test_sin_clave_los_pagos_estan_apagados():
    h = _headers("test|pago-apagado")
    assert settings.stripe_secret_key == ""
    assert client.post("/api/pagos/checkout", headers=h).status_code == 503
    assert client.post("/api/pagos/portal", headers=h).status_code == 503
    estado = client.get("/api/pagos/estado", headers=h).json()
    assert estado == {"plan": "free", "plan_hasta": None, "configurado": False}


def test_webhook_sin_secreto_da_400():
    assert settings.stripe_webhook_secret == ""
    r = client.post("/api/pagos/webhook", json={"type": "checkout.session.completed"})
    assert r.status_code == 400


def test_webhook_con_firma_invalida_da_400(monkeypatch):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_test")

    def _explota(payload, sig, secret, **kw):
        raise stripe.SignatureVerificationError("firma inválida", sig)

    monkeypatch.setattr(stripe.Webhook, "construct_event", _explota)
    r = client.post(
        "/api/pagos/webhook", json={"type": "invoice.paid"}, headers={"stripe-signature": "mala"}
    )
    assert r.status_code == 400


# ── El webhook activa, renueva y da de baja ─────────────────────────────────
def test_checkout_completado_activa_premium_y_guarda_el_customer(enviar_webhook):
    sub = "test|pago-alta"
    uid = _usuario(sub)

    r = enviar_webhook(_evento_alta(uid, "cus_alta"))
    assert r.status_code == 200
    assert r.json() == {"ok": True, "resultado": "premium-activado"}

    p = client.get("/api/perfil", headers=_headers(sub)).json()
    assert p["plan"] == "premium"
    assert p["limites"]["reflexion_max"] == 500
    assert p["limites"]["fotos_max"] == 3
    assert _leer(uid).stripe_customer_id == "cus_alta"

    estado = client.get("/api/pagos/estado", headers=_headers(sub)).json()
    assert estado["plan"] == "premium" and estado["plan_hasta"] is not None


def test_repetir_el_mismo_evento_no_cambia_nada(enviar_webhook):
    """Stripe reintenta: el segundo intento tiene que dejar el mismo estado."""
    sub = "test|pago-repetido"
    uid = _usuario(sub)
    evento = _evento_alta(uid, "cus_repetido")

    assert enviar_webhook(evento).json()["resultado"] == "premium-activado"
    primera = _leer(uid).plan_hasta

    assert enviar_webhook(evento).json()["resultado"] == "premium-activado"
    segunda = _leer(uid).plan_hasta

    assert primera == segunda
    with SessionLocal() as s:
        iguales = s.scalars(
            select(Usuario).where(Usuario.stripe_customer_id == "cus_repetido")
        ).all()
    assert len(iguales) == 1 and iguales[0].id == uid


def test_invoice_paid_renueva_la_fecha(enviar_webhook):
    sub = "test|pago-renovacion"
    uid = _usuario(sub)
    enviar_webhook(_evento_alta(uid, "cus_renovacion"))
    antes = _leer(uid).plan_hasta

    fin = int((datetime.now(timezone.utc) + timedelta(days=400)).timestamp())
    r = enviar_webhook(_evento_renovacion("cus_renovacion", fin))
    assert r.json() == {"ok": True, "resultado": "premium-renovado"}

    despues = _leer(uid).plan_hasta
    assert despues > antes
    assert abs((despues - datetime.fromtimestamp(fin, tz=timezone.utc)).total_seconds()) < 2
    assert client.get("/api/perfil", headers=_headers(sub)).json()["plan"] == "premium"


def test_subscription_deleted_vuelve_a_free(enviar_webhook):
    sub = "test|pago-baja"
    uid = _usuario(sub)
    enviar_webhook(_evento_alta(uid, "cus_baja"))

    r = enviar_webhook(_evento_baja("cus_baja"))
    assert r.json() == {"ok": True, "resultado": "premium-vencido"}

    p = client.get("/api/perfil", headers=_headers(sub)).json()
    assert p["plan"] == "free" and p["plan_hasta"] is None
    assert p["limites"]["reflexion_max"] == 150
    u = _leer(uid)
    assert u.plan == "free" and u.plan_hasta is None
    # El cliente de Stripe NO se borra: si vuelve, reusamos el mismo.
    assert u.stripe_customer_id == "cus_baja"


def test_usuario_inexistente_se_ignora_sin_romper(enviar_webhook):
    """Devolver 5xx haría que Stripe reintente para siempre por un fantasma."""
    r = enviar_webhook(_evento_alta("no-existe-jamas", "cus_fantasma"))
    assert r.status_code == 200
    assert r.json() == {"ok": True, "resultado": "ignorado"}

    r = enviar_webhook(_evento_renovacion("cus_fantasma", AHORA + 100))
    assert r.status_code == 200 and r.json()["resultado"] == "ignorado"


def test_evento_que_no_nos_interesa_se_ignora(enviar_webhook):
    r = enviar_webhook({"id": "evt_x", "type": "customer.created", "data": {"object": {}}})
    assert r.json() == {"ok": True, "resultado": "ignorado"}


# ── Checkout con la clave puesta (sin tocar la red) ─────────────────────────
def test_checkout_arma_la_suscripcion_anual_con_la_referencia_del_usuario(monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_falsa")
    monkeypatch.setattr(settings, "stripe_price_id", "price_anual_899")
    capturado = {}

    def _fake_create(**kw):
        capturado.update(kw)
        return SimpleNamespace(url="https://checkout.stripe.com/c/pay/cs_test_1")

    monkeypatch.setattr(stripe.checkout.Session, "create", _fake_create)

    sub = "test|pago-checkout"
    uid = _usuario(sub)
    r = client.post("/api/pagos/checkout", headers=_headers(sub))
    assert r.status_code == 200
    assert r.json() == {"url": "https://checkout.stripe.com/c/pay/cs_test_1"}

    assert capturado["mode"] == "subscription"
    assert capturado["line_items"] == [{"price": "price_anual_899", "quantity": 1}]
    assert capturado["client_reference_id"] == uid
    assert capturado["success_url"] == (
        f"{settings.app_url}/premium/gracias?session_id={{CHECKOUT_SESSION_ID}}"
    )
    assert capturado["cancel_url"] == f"{settings.app_url}/premium"
    assert capturado["allow_promotion_codes"] is True
    # Todavía no es cliente de Stripe: va el email, no un customer inventado.
    assert capturado["customer_email"] == f"{sub}@mindful.local"
    assert "customer" not in capturado

    estado = client.get("/api/pagos/estado", headers=_headers(sub)).json()
    assert estado["configurado"] is True


def test_sin_price_no_se_puede_vender_pero_el_portal_vive(monkeypatch):
    """El Price es del Checkout; gestionar una suscripción vieja no lo necesita."""
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_falsa")
    assert settings.stripe_price_id == ""
    sub = "test|pago-sin-price"
    _usuario(sub)
    assert client.post("/api/pagos/checkout", headers=_headers(sub)).status_code == 503
    # 409 (no 503): los pagos están encendidos, lo que falta es su suscripción.
    assert client.post("/api/pagos/portal", headers=_headers(sub)).status_code == 409


def test_portal_sin_suscripcion_da_409(monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_falsa")
    monkeypatch.setattr(settings, "stripe_price_id", "price_anual_899")
    sub = "test|pago-portal"
    _usuario(sub)
    assert client.post("/api/pagos/portal", headers=_headers(sub)).status_code == 409


def test_portal_con_suscripcion_devuelve_la_url(monkeypatch, enviar_webhook):
    sub = "test|pago-portal-ok"
    uid = _usuario(sub)
    enviar_webhook(_evento_alta(uid, "cus_portal"))

    monkeypatch.setattr(settings, "stripe_secret_key", "sk_test_falsa")
    monkeypatch.setattr(settings, "stripe_price_id", "price_anual_899")
    capturado = {}

    def _fake_create(**kw):
        capturado.update(kw)
        return SimpleNamespace(url="https://billing.stripe.com/p/session/test_1")

    monkeypatch.setattr(stripe.billing_portal.Session, "create", _fake_create)

    r = client.post("/api/pagos/portal", headers=_headers(sub))
    assert r.status_code == 200
    assert r.json() == {"url": "https://billing.stripe.com/p/session/test_1"}
    assert capturado["customer"] == "cus_portal"
    assert capturado["return_url"] == f"{settings.app_url}/premium"
