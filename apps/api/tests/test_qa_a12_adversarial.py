"""Q/A ADVERSARIAL · card A1.2 (Stripe). NO es parte de la suite: se corre a mano.

Objetivo: ROMPER el webhook y el checkout. Nada de red (todo monkeypatch).
Subs con prefijo `qa12|` para no chocar con otros agentes de Q/A.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
import stripe
from fastapi.testclient import TestClient
from sqlalchemy import delete, select, text

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Usuario
from mindful_api.main import app
from mindful_api.services import stripe as srv

client = TestClient(app)
# Como corre uvicorn en produccion: la excepcion NO se re-lanza, se ve el 500.
client_prod = TestClient(app, raise_server_exceptions=False)

AHORA = int(datetime.now(timezone.utc).timestamp())


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


def _usuario(sub: str) -> str:
    assert client.get("/api/perfil", headers=_headers(sub)).status_code == 200
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
        assert u is not None
        return u.id


def _leer(uid: str) -> Usuario:
    with SessionLocal() as s:
        u = s.get(Usuario, uid)
        assert u is not None
        return u


def _set_plan(uid: str, plan: str, hasta):
    with SessionLocal() as s:
        u = s.get(Usuario, uid)
        u.plan = plan
        u.plan_hasta = hasta
        s.commit()


def _alta(uid, customer, **extra) -> dict:
    obj = {
        "id": "cs_qa12",
        "client_reference_id": uid,
        "customer": customer,
        "subscription": "sub_qa12",
        # Las sesiones reales de Stripe traen su propio `created`: es el respaldo
        # del ancla de fecha cuando el `created` del evento viene roto (BUG-4).
        "created": AHORA,
    }
    obj.update(extra)
    return {"id": "evt_qa_alta", "type": "checkout.session.completed",
            "created": AHORA, "data": {"object": obj}}


def _renov(customer, fin, **extra) -> dict:
    obj = {
        "id": "in_qa12",
        "customer": customer,
        "lines": {"data": [{"subscription": "sub_qa12",
                            "period": {"start": AHORA, "end": fin}}]},
    }
    obj.update(extra)
    return {"id": "evt_qa_renov", "type": "invoice.paid",
            "created": AHORA, "data": {"object": obj}}


def _baja(customer, sub_id="sub_qa12") -> dict:
    return {"id": "evt_qa_baja", "type": "customer.subscription.deleted",
            "created": AHORA, "data": {"object": {"id": sub_id, "customer": customer}}}


@pytest.fixture
def wh(monkeypatch):
    """Webhook encendido; la firma se da por buena y el body vuelve tal cual."""
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_qa")
    monkeypatch.setattr(
        stripe.Webhook, "construct_event",
        lambda payload, sig, secret, **kw: json.loads(payload),
    )

    def _enviar(evento):
        return client.post("/api/pagos/webhook", json=evento,
                           headers={"stripe-signature": "t=1,v1=falsa"})

    return _enviar


@pytest.fixture
def wh_prod(monkeypatch):
    """Igual que `wh` pero con el cliente que devuelve el 500 en vez de re-lanzarlo."""
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_qa")
    monkeypatch.setattr(
        stripe.Webhook, "construct_event",
        lambda payload, sig, secret, **kw: json.loads(payload),
    )

    def _enviar(evento):
        return client_prod.post("/api/pagos/webhook", json=evento,
                                headers={"stripe-signature": "t=1,v1=falsa"})

    return _enviar


# ═══ 1 · PAYLOADS MALFORMADOS — ninguno debe dar 500 ═════════════════════════
@pytest.mark.parametrize(
    "evento",
    [
        pytest.param({"id": "e", "type": "checkout.session.completed", "created": AHORA},
                     id="data-ausente"),
        pytest.param({"id": "e", "type": "checkout.session.completed", "created": AHORA,
                      "data": None}, id="data-null"),
        pytest.param({"id": "e", "type": "checkout.session.completed", "created": AHORA,
                      "data": {"object": None}}, id="object-null"),
        pytest.param({"id": "e", "type": "invoice.paid", "created": AHORA,
                      "data": {"object": {}}}, id="invoice-vacia"),
        pytest.param({"id": "e", "type": "invoice.paid", "created": AHORA,
                      "data": {"object": {"customer": "cus_qa12_nadie", "lines": None}}},
                     id="invoice-lines-null"),
        pytest.param({"id": "e", "type": "customer.subscription.deleted", "created": AHORA,
                      "data": {"object": {}}}, id="baja-vacia"),
        pytest.param({"id": "e", "created": AHORA, "data": {"object": {}}}, id="sin-type"),
        pytest.param({"id": "e", "type": None, "created": AHORA, "data": {"object": {}}},
                     id="type-null"),
        pytest.param({}, id="evento-vacio"),
    ],
)
def test_payload_malformado_no_rompe(wh, evento):
    r = wh(evento)
    assert r.status_code == 200, r.text
    assert r.json()["resultado"] == "ignorado"


def test_customer_como_dict_expandido(wh):
    """Stripe a veces expande objetos: `customer` viene como dict, no como str.
    `_customer_id` normaliza las dos formas → el customer queda anclado igual."""
    sub = "qa12|cust-dict"
    uid = _usuario(sub)
    r = wh(_alta(uid, {"id": "cus_qa12_dict", "object": "customer"}))
    assert r.status_code == 200
    assert r.json()["resultado"] == "premium-activado"
    u = _leer(uid)
    assert u.plan == "premium"
    assert u.stripe_customer_id == "cus_qa12_dict"


def test_customer_dict_deja_portal_y_renovacion_funcionando(wh, monkeypatch):
    """El corolario del anterior: con el customer anclado, el portal abre y la
    renovación de ese customer encuentra al usuario."""
    sub = "qa12|cust-dict-2"
    uid = _usuario(sub)
    assert wh(_alta(uid, {"id": "cus_qa12_dict2"})).json()["resultado"] == "premium-activado"

    monkeypatch.setattr(settings, "stripe_secret_key", "sk_qa")
    cap = {}
    monkeypatch.setattr(stripe.billing_portal.Session, "create",
                        lambda **kw: (cap.update(kw), SimpleNamespace(url="https://portal"))[1])
    r = client.post("/api/pagos/portal", headers=_headers(sub))
    assert r.status_code == 200 and cap["customer"] == "cus_qa12_dict2"

    fin = int((datetime.now(timezone.utc) + timedelta(days=400)).timestamp())
    assert wh(_renov("cus_qa12_dict2", fin)).json()["resultado"] == "premium-renovado"


@pytest.mark.parametrize(
    "customer",
    [None, "", {}, {"id": None}, {"id": 42}, 12345, ["cus_x"], True],
    ids=["null", "vacio", "dict-vacio", "dict-id-null", "dict-id-int", "int", "lista", "bool"],
)
def test_sin_customer_anclable_no_hay_premium(wh, customer):
    """OBS-1: sin `stripe_customer_id` guardado, la renovación y la baja de esa
    suscripción no encuentran a nadie → premium vitalicio y sin portal. No se activa."""
    # Mismo usuario para todos los casos: si el candado funciona nunca lo tocamos.
    uid = _usuario("qa12|no-anclable")
    r = wh(_alta(uid, customer))
    assert r.status_code == 200, r.text
    assert r.json()["resultado"] == "ignorado"
    u = _leer(uid)
    assert u.plan == "free" and u.stripe_customer_id is None


def test_subscription_expandida_usa_current_period_end(wh):
    sub = "qa12|sub-exp"
    uid = _usuario(sub)
    fin = int((datetime.now(timezone.utc) + timedelta(days=30)).timestamp())
    r = wh(_alta(uid, "cus_qa12_subexp", subscription={"id": "sub_x", "current_period_end": fin}))
    assert r.json()["resultado"] == "premium-activado"
    hasta = _leer(uid).plan_hasta
    assert abs((hasta - datetime.fromtimestamp(fin, tz=timezone.utc)).total_seconds()) < 2


def test_subscription_expandida_api_nueva_items(wh):
    sub = "qa12|sub-items"
    uid = _usuario(sub)
    fin = int((datetime.now(timezone.utc) + timedelta(days=45)).timestamp())
    ev = _alta(uid, "cus_qa12_items",
               subscription={"id": "sub_y", "items": {"data": [{"current_period_end": fin}]}})
    assert wh(ev).json()["resultado"] == "premium-activado"
    hasta = _leer(uid).plan_hasta
    assert abs((hasta - datetime.fromtimestamp(fin, tz=timezone.utc)).total_seconds()) < 2


def test_created_como_string_usa_el_del_objeto_y_es_idempotente(wh):
    """BUG-4: `created` del evento no numérico → se cae al `created` del OBJETO,
    que sí es un epoch. Reprocesar tres veces deja exactamente la misma fecha."""
    sub = "qa12|created-str"
    uid = _usuario(sub)
    ev = _alta(uid, "cus_qa12_created")
    ev["created"] = str(AHORA)  # string, no int
    assert ev["data"]["object"]["created"] == AHORA  # el respaldo, numérico

    fechas = []
    for _ in range(3):
        assert wh(ev).json()["resultado"] == "premium-activado"
        fechas.append(_leer(uid).plan_hasta)
        time.sleep(0.4)  # el reintento de Stripe llega segundos/minutos después
    assert len(set(fechas)) == 1, f"deriva: {fechas}"
    esperado = datetime.fromtimestamp(AHORA, tz=timezone.utc) + timedelta(days=366)
    assert abs((fechas[0] - esperado).total_seconds()) < 2


def test_created_roto_en_evento_y_en_objeto_cae_en_ahora(wh):
    """Última opción documentada: sin ningún epoch usable, se ancla en `ahora()`
    (y ahí sí, reprocesar corre la fecha unos segundos — es el menor de los males)."""
    sub = "qa12|created-nada"
    uid = _usuario(sub)
    ev = _alta(uid, "cus_qa12_creadonada")
    ev["created"] = "no-numerico"
    ev["data"]["object"]["created"] = None
    assert wh(ev).json()["resultado"] == "premium-activado"
    dias = (_leer(uid).plan_hasta - datetime.now(timezone.utc)).days
    assert 364 <= dias <= 366, dias


def test_client_reference_id_de_usuario_borrado(wh):
    sub = "qa12|borrado"
    uid = _usuario(sub)
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.id == uid))
        s.commit()
    r = wh(_alta(uid, "cus_qa12_fantasma_borrado"))
    assert r.status_code == 200
    assert r.json()["resultado"] == "ignorado"


@pytest.mark.parametrize(
    "ref", [{"id": "x"}, ["a"], 12345, True, "", None], ids=
    ["dict", "lista", "int", "bool", "vacio", "null"]
)
def test_client_reference_id_de_tipo_raro(wh, ref):
    ev = _alta(ref, "cus_qa12_ref_raro")
    r = wh(ev)
    assert r.status_code == 200, r.text
    assert r.json()["resultado"] == "ignorado"


@pytest.mark.parametrize("obj", ["cs_texto", 42, ["lista"]],
                         ids=["object-string", "object-int", "object-lista"])
def test_data_object_no_dict(wh_prod, obj):
    """data.object que no es un dict: hoy revienta con 500 (AttributeError)."""
    ev = {"id": "e", "type": "checkout.session.completed", "created": AHORA,
          "data": {"object": obj}}
    r = wh_prod(ev)
    assert r.status_code == 200, f"data.object={obj!r} -> HTTP {r.status_code}"


def test_data_no_dict(wh_prod):
    ev = {"id": "e", "type": "invoice.paid", "created": AHORA, "data": "texto"}
    r = wh_prod(ev)
    assert r.status_code == 200, f"data string -> HTTP {r.status_code}"


def test_evento_json_que_no_es_objeto(wh_prod):
    """construct_event devolviendo algo que no es dict (body JSON = lista)."""
    r = client_prod.post("/api/pagos/webhook", json=[1, 2, 3],
                         headers={"stripe-signature": "t=1,v1=falsa"})
    assert r.status_code in (200, 400), f"evento lista -> HTTP {r.status_code}"


# ═══ 2 · ORDEN INVERSO ══════════════════════════════════════════════════════
def test_renovacion_antes_del_alta(wh):
    cus = "cus_qa12_orden"
    fin = int((datetime.now(timezone.utc) + timedelta(days=400)).timestamp())
    # 1) renovación de un customer que nadie tiene
    assert wh(_renov(cus, fin)).json()["resultado"] == "ignorado"
    # 2) recién ahora llega el alta
    sub = "qa12|orden"
    uid = _usuario(sub)
    assert wh(_alta(uid, cus)).json()["resultado"] == "premium-activado"
    u = _leer(uid)
    assert u.plan == "premium" and u.stripe_customer_id == cus
    # 3) reintento de la renovación (Stripe reintenta): ahora sí engancha
    assert wh(_renov(cus, fin)).json()["resultado"] == "premium-renovado"
    assert abs((_leer(uid).plan_hasta
                - datetime.fromtimestamp(fin, tz=timezone.utc)).total_seconds()) < 2


def test_baja_antes_de_todo(wh):
    assert wh(_baja("cus_qa12_baja_huerfana")).json()["resultado"] == "ignorado"
    sub = "qa12|baja-antes"
    uid = _usuario(sub)
    assert wh(_alta(uid, "cus_qa12_baja_huerfana")).json()["resultado"] == "premium-activado"
    assert _leer(uid).plan == "premium"


# ═══ 3 · LA FECHA NUNCA VA HACIA ATRÁS ══════════════════════════════════════
def test_alta_tardia_no_recorta_el_ano_ya_pagado(wh):
    sub = "qa12|no-atras"
    uid = _usuario(sub)
    lejos = datetime.now(timezone.utc) + timedelta(days=400)
    _set_plan(uid, "premium", lejos)
    assert wh(_alta(uid, "cus_qa12_noatras")).json()["resultado"] == "premium-activado"
    assert abs((_leer(uid).plan_hasta - lejos).total_seconds()) < 2


def test_renovacion_mas_corta_no_recorta(wh):
    sub = "qa12|no-atras-2"
    uid = _usuario(sub)
    lejos = datetime.now(timezone.utc) + timedelta(days=400)
    wh(_alta(uid, "cus_qa12_noatras2"))
    _set_plan(uid, "premium", lejos)
    corto = int((datetime.now(timezone.utc) + timedelta(days=10)).timestamp())
    assert wh(_renov("cus_qa12_noatras2", corto)).json()["resultado"] == "premium-renovado"
    assert abs((_leer(uid).plan_hasta - lejos).total_seconds()) < 2


def test_la_baja_si_baja_aunque_la_fecha_sea_futura(wh):
    sub = "qa12|baja-futura"
    uid = _usuario(sub)
    wh(_alta(uid, "cus_qa12_bajafutura"))
    _set_plan(uid, "premium", datetime.now(timezone.utc) + timedelta(days=400))
    assert wh(_baja("cus_qa12_bajafutura")).json()["resultado"] == "premium-vencido"
    u = _leer(uid)
    assert u.plan == "free" and u.plan_hasta is None
    assert u.stripe_customer_id == "cus_qa12_bajafutura"
    assert client.get("/api/pagos/estado", headers=_headers(sub)).json()["plan"] == "free"


def test_usuario_free_con_fecha_futura_si_se_pisa(wh):
    """Estado imposible por diseño (vencer_premium anula la fecha): la guarda
    `plan == premium` sólo protege a un premium vigente. Documentado."""
    sub = "qa12|free-futuro"
    uid = _usuario(sub)
    _set_plan(uid, "free", datetime.now(timezone.utc) + timedelta(days=400))
    wh(_alta(uid, "cus_qa12_freefuturo"))
    hasta = _leer(uid).plan_hasta
    assert (hasta - datetime.now(timezone.utc)).days < 380  # se pisó con +366


# ═══ 4 · BAJA PARCIAL (dos suscripciones del mismo customer) ════════════════
def test_baja_de_una_suscripcion_vieja_apaga_la_nueva(wh):
    sub = "qa12|baja-parcial"
    uid = _usuario(sub)
    cus = "cus_qa12_parcial"
    wh(_alta(uid, cus))
    fin = int((datetime.now(timezone.utc) + timedelta(days=400)).timestamp())
    wh(_renov(cus, fin))  # sub nueva vigente
    assert _leer(uid).plan == "premium"
    # llega la baja de la suscripción VIEJA (otro sub_id)
    r = wh(_baja(cus, sub_id="sub_qa12_VIEJA"))
    assert r.json()["resultado"] == "premium-vencido"
    assert _leer(uid).plan == "free"  # ← se apagó una suscripción que sigue viva


# ═══ 5 · CROSS-USUARIO ══════════════════════════════════════════════════════
def test_alta_de_A_con_customer_que_ya_es_de_B(wh):
    cus = "cus_qa12_compartido"
    uid_b = _usuario("qa12|cross-B")
    wh(_alta(uid_b, cus))
    assert _leer(uid_b).stripe_customer_id == cus
    hasta_b = _leer(uid_b).plan_hasta

    uid_a = _usuario("qa12|cross-A")
    r = wh(_alta(uid_a, cus))
    assert r.status_code == 200, r.text  # NO 500 por el UNIQUE
    # El customer es de B: no se puede anclar a A → no se activa (OBS-1).
    assert r.json()["resultado"] == "ignorado"
    a, b = _leer(uid_a), _leer(uid_b)
    assert a.stripe_customer_id is None       # no se pisó el customer de B
    assert b.stripe_customer_id == cus
    assert b.plan_hasta == hasta_b            # B no se movió
    assert a.plan == "free"                   # A no se lleva un año gratis
    # la baja de ese customer cae sobre B, su dueño, y A sigue igual (free)
    assert wh(_baja(cus)).json()["resultado"] == "premium-vencido"
    assert _leer(uid_b).plan == "free"
    assert _leer(uid_a).plan == "free"


# ═══ 6 · CHECKOUT ═══════════════════════════════════════════════════════════
def test_checkout_parametros(monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_qa")
    monkeypatch.setattr(settings, "stripe_price_id", "price_qa")
    cap = {}
    monkeypatch.setattr(stripe.checkout.Session, "create",
                        lambda **kw: (cap.update(kw), SimpleNamespace(url="https://x"))[1])
    sub = "qa12|checkout"
    uid = _usuario(sub)
    r = client.post("/api/pagos/checkout", headers=_headers(sub))
    assert r.status_code == 200 and r.json() == {"url": "https://x"}
    assert cap["client_reference_id"] == uid
    assert cap["client_reference_id"] != sub  # id interno, NO el firebase_uid
    assert "{CHECKOUT_SESSION_ID}" in cap["success_url"]
    assert cap["success_url"].endswith("session_id={CHECKOUT_SESSION_ID}")
    assert cap["cancel_url"] == f"{settings.app_url}/premium"
    assert cap["customer_email"] == f"{sub}@mindful.local" and "customer" not in cap
    assert cap["mode"] == "subscription"


def test_checkout_reusa_el_customer_si_ya_existe(monkeypatch, wh):
    sub = "qa12|checkout-cus"
    uid = _usuario(sub)
    wh(_alta(uid, "cus_qa12_checkout"))
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_qa")
    monkeypatch.setattr(settings, "stripe_price_id", "price_qa")
    cap = {}
    monkeypatch.setattr(stripe.checkout.Session, "create",
                        lambda **kw: (cap.update(kw), SimpleNamespace(url="https://x"))[1])
    assert client.post("/api/pagos/checkout", headers=_headers(sub)).status_code == 200
    assert cap["customer"] == "cus_qa12_checkout"
    assert "customer_email" not in cap


def test_key_sin_price_da_503(monkeypatch):
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_qa")
    monkeypatch.setattr(settings, "stripe_price_id", "")
    sub = "qa12|sin-price"
    _usuario(sub)
    r = client.post("/api/pagos/checkout", headers=_headers(sub))
    assert r.status_code == 503


def test_checkout_no_llama_a_stripe_si_falta_el_price(monkeypatch):
    """El 503 tiene que salir ANTES de tocar la red."""
    monkeypatch.setattr(settings, "stripe_secret_key", "sk_qa")
    monkeypatch.setattr(settings, "stripe_price_id", "")
    llamado = []
    monkeypatch.setattr(stripe.checkout.Session, "create",
                        lambda **kw: llamado.append(kw))
    sub = "qa12|sin-price-2"
    _usuario(sub)
    client.post("/api/pagos/checkout", headers=_headers(sub))
    assert llamado == []


# ═══ 7 · SEGURIDAD ══════════════════════════════════════════════════════════
def test_webhook_sin_header_de_firma_da_400(monkeypatch):
    """Sin monkeypatch de construct_event: la firma REAL tiene que fallar con 400."""
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_qa")
    r = client.post("/api/pagos/webhook", json={"type": "invoice.paid"})
    assert r.status_code == 400, r.text


def test_webhook_con_firma_forjada_da_400(monkeypatch):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_qa")
    r = client.post("/api/pagos/webhook", json=_alta("x", "cus_x"),
                    headers={"stripe-signature": "t=1,v1=" + "0" * 64})
    assert r.status_code == 400, r.text


def test_webhook_body_no_json_da_400(monkeypatch):
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_qa")
    monkeypatch.setattr(stripe.Webhook, "construct_event",
                        lambda payload, sig, secret, **kw: json.loads(payload))
    r = client.post("/api/pagos/webhook", content=b"{no-json",
                    headers={"stripe-signature": "t=1,v1=falsa"})
    assert r.status_code == 400, r.text


def test_endpoints_sin_auth_dan_401_en_modo_firebase(monkeypatch):
    monkeypatch.setattr(settings, "auth_mode", "firebase")
    for m, p in [("get", "/api/pagos/estado"), ("post", "/api/pagos/checkout"),
                 ("post", "/api/pagos/portal")]:
        r = getattr(client, m)(p)
        assert r.status_code == 401, f"{p} → {r.status_code}"


def test_webhook_no_pide_auth_en_modo_firebase(monkeypatch):
    """El webhook lo llama Stripe: nunca debe pedir token."""
    monkeypatch.setattr(settings, "auth_mode", "firebase")
    monkeypatch.setattr(settings, "stripe_webhook_secret", "whsec_qa")
    monkeypatch.setattr(stripe.Webhook, "construct_event",
                        lambda payload, sig, secret, **kw: json.loads(payload))
    r = client.post("/api/pagos/webhook", json={"type": "customer.created", "data": {"object": {}}},
                    headers={"stripe-signature": "t=1,v1=falsa"})
    assert r.status_code == 200


def test_premium_vencido_es_free_en_estado():
    sub = "qa12|vencido"
    uid = _usuario(sub)
    _set_plan(uid, "premium", datetime.now(timezone.utc) - timedelta(days=1))
    e = client.get("/api/pagos/estado", headers=_headers(sub)).json()
    assert e["plan"] == "free" and e["plan_hasta"] is None


def test_nadie_se_hace_premium_desde_el_front():
    """No puede existir una ruta que active premium sin webhook."""
    rutas = {r.path for r in app.routes if r.path.startswith("/api/pagos")}
    assert rutas == {"/api/pagos/estado", "/api/pagos/checkout",
                     "/api/pagos/portal", "/api/pagos/webhook"}


# ═══ 8 · NAIVE vs AWARE ═════════════════════════════════════════════════════
def test_plan_hasta_naive_por_sql_no_rompe_el_alta(wh):
    sub = "qa12|naive"
    uid = _usuario(sub)
    with SessionLocal() as s:
        s.execute(text("UPDATE usuarios SET plan='premium', "
                       "plan_hasta = (now() + interval '400 days')::timestamp "
                       "WHERE id = :i"), {"i": uid})
        s.commit()
    r = wh(_alta(uid, "cus_qa12_naive"))
    assert r.status_code == 200, r.text
    assert r.json()["resultado"] == "premium-activado"


def test_activar_con_actual_naive_no_explota():
    """Rama `actual.tzinfo is None` de `_activar`, llamada en frío (sin DB)."""
    u = Usuario(firebase_uid="qa12|naive-puro", email="x@y.z")
    u.plan = "premium"
    u.plan_hasta = datetime(2099, 1, 1)  # NAIVE
    srv._activar(u, datetime.now(timezone.utc) + timedelta(days=366))
    assert u.plan_hasta.year == 2099  # no fue hacia atrás


def test_activar_con_hasta_naive_se_normaliza():
    """OBS-3: la guarda es de DOS caras. Si `hasta` llega naive se normaliza a UTC
    antes del `max` — nada de TypeError comparando naive con aware."""
    u = Usuario(firebase_uid="qa12|naive-hasta", email="x@y.z")
    u.plan = "premium"
    u.plan_hasta = datetime.now(timezone.utc) + timedelta(days=400)  # AWARE
    srv._activar(u, datetime(2030, 1, 1))  # naive → gana porque es más lejos
    assert u.plan_hasta.year == 2030
    assert u.plan_hasta.tzinfo is not None


def test_activar_con_hasta_naive_mas_corto_no_recorta():
    """La otra cara: `hasta` naive y ANTERIOR al año ya pagado no lo recorta."""
    u = Usuario(firebase_uid="qa12|naive-hasta-2", email="x@y.z")
    u.plan = "premium"
    lejos = datetime(2099, 6, 1, tzinfo=timezone.utc)
    u.plan_hasta = lejos
    srv._activar(u, datetime(2030, 1, 1))  # naive, más corto
    assert u.plan_hasta == lejos


# ═══ 9 · IDEMPOTENCIA REAL ══════════════════════════════════════════════════
def test_mismo_evento_tres_veces(wh):
    sub = "qa12|idem"
    uid = _usuario(sub)
    ev = _alta(uid, "cus_qa12_idem")
    fechas, custs, res = [], [], []
    for _ in range(3):
        res.append(wh(ev).json()["resultado"])
        u = _leer(uid)
        fechas.append(u.plan_hasta)
        custs.append(u.stripe_customer_id)
    assert res == ["premium-activado"] * 3
    assert len(set(fechas)) == 1, fechas
    assert set(custs) == {"cus_qa12_idem"}
    with SessionLocal() as s:
        n = len(s.scalars(select(Usuario).where(
            Usuario.stripe_customer_id == "cus_qa12_idem")).all())
    assert n == 1


def test_renovacion_tres_veces(wh):
    sub = "qa12|idem-renov"
    uid = _usuario(sub)
    wh(_alta(uid, "cus_qa12_idemr"))
    fin = int((datetime.now(timezone.utc) + timedelta(days=400)).timestamp())
    ev = _renov("cus_qa12_idemr", fin)
    fechas = []
    for _ in range(3):
        assert wh(ev).json()["resultado"] == "premium-renovado"
        fechas.append(_leer(uid).plan_hasta)
    assert len(set(fechas)) == 1, fechas


def test_baja_tres_veces(wh):
    sub = "qa12|idem-baja"
    uid = _usuario(sub)
    wh(_alta(uid, "cus_qa12_idemb"))
    for _ in range(3):
        assert wh(_baja("cus_qa12_idemb")).json()["resultado"] == "premium-vencido"
    u = _leer(uid)
    assert u.plan == "free" and u.plan_hasta is None


# ═══ 10 · EL COBRO SE VERIFICA (BUG-1) ══════════════════════════════════════
def test_checkout_completado_pero_no_pagado_no_activa(wh):
    """Stripe manda `checkout.session.completed` con payment_status='unpaid'
    para métodos de pago diferidos (SEPA débito, boleto…): NO es plata cobrada.
    Se ancla el customer (para engancharlo después) pero no se activa nada."""
    sub = "qa12|unpaid"
    uid = _usuario(sub)
    ev = _alta(uid, "cus_qa12_unpaid", payment_status="unpaid", status="complete")
    r = wh(ev)
    assert r.json() == {"ok": True, "resultado": "pago-pendiente"}
    u = _leer(uid)
    assert u.plan == "free" and u.plan_hasta is None
    assert u.stripe_customer_id == "cus_qa12_unpaid"  # anclado igual


def test_pago_diferido_que_entra_despues_si_activa(wh):
    """El camino completo del SEPA: `completed` unpaid → `async_payment_succeeded`."""
    sub = "qa12|async-ok"
    uid = _usuario(sub)
    cus = "cus_qa12_async"
    assert wh(_alta(uid, cus, payment_status="unpaid")).json()["resultado"] == "pago-pendiente"
    assert _leer(uid).plan == "free"

    ev = _alta(uid, cus, payment_status="unpaid")  # Stripe puede no actualizarlo
    ev["type"] = "checkout.session.async_payment_succeeded"
    ev["id"] = "evt_qa_async"
    assert wh(ev).json()["resultado"] == "premium-activado"
    u = _leer(uid)
    assert u.plan == "premium" and u.stripe_customer_id == cus


def test_pago_diferido_que_falla_no_activa(wh):
    sub = "qa12|async-ko"
    uid = _usuario(sub)
    ev = _alta(uid, "cus_qa12_asyncko", payment_status="unpaid")
    ev["type"] = "checkout.session.async_payment_failed"
    assert wh(ev).json()["resultado"] == "ignorado"
    assert _leer(uid).plan == "free"


def test_no_payment_required_si_activa(wh):
    """Cupón del 100 % / prueba gratis: no hay cobro pero la suscripción existe."""
    sub = "qa12|gratis"
    uid = _usuario(sub)
    ev = _alta(uid, "cus_qa12_gratis", payment_status="no_payment_required")
    assert wh(ev).json()["resultado"] == "premium-activado"
    assert _leer(uid).plan == "premium"


def test_checkout_expirado_no_activa(wh):
    """`status='expired'` en el objeto session: la sesión murió sin comprar."""
    sub = "qa12|expirado"
    uid = _usuario(sub)
    ev = _alta(uid, "cus_qa12_expirado", status="expired", payment_status="unpaid")
    assert wh(ev).json()["resultado"] == "ignorado"
    u = _leer(uid)
    assert u.plan == "free" and u.stripe_customer_id is None


def test_modo_payment_no_suscripcion_no_activa(wh):
    """`mode='payment'` es un pago único: no crea suscripción, no hay renovación
    ni baja que seguir. Nuestro premium sale SOLO de `mode='subscription'`."""
    sub = "qa12|modo-payment"
    uid = _usuario(sub)
    ev = _alta(uid, "cus_qa12_modopay", mode="payment", subscription=None,
               payment_status="paid")
    assert wh(ev).json()["resultado"] == "ignorado"
    assert _leer(uid).plan == "free"


def test_payload_minimo_sin_payment_status_activa(wh):
    """Decisión documentada: `payment_status` AUSENTE se trata como "paid" (los
    payloads mínimos no lo traen). El candado real lo pone el "unpaid" explícito."""
    sub = "qa12|minimo"
    uid = _usuario(sub)
    ev = {"id": "e", "type": "checkout.session.completed", "created": AHORA,
          "data": {"object": {"client_reference_id": uid, "customer": "cus_qa12_minimo"}}}
    assert wh(ev).json()["resultado"] == "premium-activado"


# ═══ 11 · varios ════════════════════════════════════════════════════════════
def test_customer_id_larguisimo(wh_prod):
    """BUG-5: String(64) en la DB. Un customer más largo no se guarda (daría
    DataError → 500 → reintentos infinitos): se descarta y no se activa nada."""
    sub = "qa12|cus-largo"
    uid = _usuario(sub)
    r = wh_prod(_alta(uid, "cus_" + "z" * 200))
    assert r.status_code == 200, f"customer de 204 chars -> HTTP {r.status_code}"
    assert r.json()["resultado"] == "ignorado"
    u = _leer(uid)
    assert u.plan == "free" and u.stripe_customer_id is None


def test_customer_de_exactamente_64_si_entra(wh):
    """El límite es inclusivo: 64 caracteres entran en la columna."""
    sub = "qa12|cus-64"
    uid = _usuario(sub)
    cus = "cus_qa12_64_" + "z" * (64 - len("cus_qa12_64_"))
    assert len(cus) == 64
    assert wh(_alta(uid, cus)).json()["resultado"] == "premium-activado"
    assert _leer(uid).stripe_customer_id == cus


def test_error_inesperado_devuelve_200_y_no_reintentos(wh_prod, monkeypatch):
    """BUG-3 · red de última instancia del router: si `procesar_evento` explota
    por algo que no previmos, Stripe recibe 200 (deja de reintentar) y el error
    queda en el log — ESE log es la alarma; el evento se reenvía a mano."""
    def _explota(s, evento):
        raise RuntimeError("boom inesperado")

    monkeypatch.setattr(srv, "procesar_evento", _explota)
    r = wh_prod(_alta("x", "cus_qa12_boom"))
    assert r.status_code == 200, r.text
    assert r.json() == {"ok": False, "resultado": "error-interno"}


def test_invoice_con_lineas_sin_period(wh):
    sub = "qa12|inv-sin-period"
    uid = _usuario(sub)
    wh(_alta(uid, "cus_qa12_invsp"))
    ev = {"id": "e", "type": "invoice.paid", "created": AHORA,
          "data": {"object": {"customer": "cus_qa12_invsp",
                              "lines": {"data": [{"subscription": "s"}]}}}}
    r = wh(ev)
    assert r.status_code == 200 and r.json()["resultado"] == "premium-renovado"
    assert _leer(uid).plan == "premium"


def test_invoice_de_importe_cero_renueva_igual(wh):
    """`invoice.paid` con amount_paid 0 (prueba gratis / crédito) renueva el año."""
    sub = "qa12|inv-cero"
    uid = _usuario(sub)
    wh(_alta(uid, "cus_qa12_invcero"))
    fin = int((datetime.now(timezone.utc) + timedelta(days=400)).timestamp())
    ev = _renov("cus_qa12_invcero", fin, amount_paid=0, billing_reason="subscription_cycle")
    assert wh(ev).json()["resultado"] == "premium-renovado"
