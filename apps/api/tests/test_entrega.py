"""M2/M3 · carta del día + cierre del ritual + reglas (1/día, aislamiento)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mindful_api.main import app

client = TestClient(app)


TODAS = {"gratitud", "sentido", "perspectiva", "resiliencia", "amor-propio", "vinculos"}


def _onboard(sub: str) -> dict:
    """WS17: el onboarding ya no elige categorías — solo acepta términos."""
    h = {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def test_carta_del_dia_requiere_onboarding():
    h = {"X-Debug-Sub": "ent|sin-onboarding"}
    r = client.get("/api/carta-del-dia", headers=h)
    assert r.status_code == 409  # faltan los términos


def test_carta_del_dia_y_una_por_dia():
    h = _onboard("ent|diaria")

    r = client.get("/api/carta-del-dia", headers=h)
    assert r.status_code == 200
    data = r.json()
    # La carta viene enriquecida con lo visual (categoría + acción).
    assert data["carta"]["categoria"]["slug"] in TODAS
    assert "frase" in data["carta"] and "prompt" in data["carta"]
    assert data["entrega"]["ya_existia"] is False
    carta_id = data["carta"]["id"]
    entrega_id = data["entrega"]["id"]

    # Segundo pedido el mismo día → MISMA carta (regla 1/día).
    r2 = client.get("/api/carta-del-dia", headers=h)
    assert r2.json()["carta"]["id"] == carta_id
    assert r2.json()["entrega"]["ya_existia"] is True
    assert r2.json()["entrega"]["id"] == entrega_id


def test_cierre_ritual():
    h = _onboard("ent|cierre")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]

    r = client.put(
        f"/api/entregas/{entrega_id}/cierre",
        headers=h,
        json={"estrellas": 5, "reflexion": "Hoy frené un momento.", "completada": True},
    )
    assert r.status_code == 200
    e = r.json()["entrega"]
    assert e["estrellas"] == 5
    assert e["completada"] is True
    assert e["reflexion"] == "Hoy frené un momento."


def test_cierre_valida_aislamiento():
    ha = _onboard("ent|dueno")
    hb = _onboard("ent|intruso")
    entrega_a = client.get("/api/carta-del-dia", headers=ha).json()["entrega"]["id"]

    # El intruso no puede cerrar la entrega ajena → 404 (no filtra existencia).
    r = client.put(f"/api/entregas/{entrega_a}/cierre", headers=hb, json={"estrellas": 1})
    assert r.status_code == 404


def test_reflexion_max_150():
    h = _onboard("ent|larga")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    r = client.put(
        f"/api/entregas/{entrega_id}/cierre", headers=h, json={"reflexion": "x" * 151}
    )
    assert r.status_code == 422


def test_enviar_sin_guardar_persiste_la_reflexion_y_no_llega_al_baul():
    """WS25 §1.2 · los dos caminos del cierre, en el orden real de Tomás.

    "Enviar" cierra con `completada:false`: lo escrito se GUARDA (para que viaje en
    el link) pero la Pausa no entra al Baúl. Después, "¿Quieres guardar la Pausa?"
    cierra otra vez con `completada:true` y SIN reflexión — y esa segunda llamada
    no puede pisar lo escrito: reflexión ausente (None) significa "no toques este
    campo", no "bórralo".
    """
    h = _onboard("ent|enviar-sin-guardar")
    eid = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]

    # (1) Enviar: persiste la reflexión, pero la Pausa NO está en el Baúl.
    r = client.put(f"/api/entregas/{eid}/cierre", headers=h,
                   json={"reflexion": "La escribí antes de enviarla.", "estrellas": 4,
                         "completada": False})
    assert r.status_code == 200
    assert r.json()["entrega"]["reflexion"] == "La escribí antes de enviarla."
    assert r.json()["entrega"]["completada"] is False
    assert client.get("/api/baul", headers=h).json() == []

    # (2) Guardar después, sin mandar reflexión: entra al Baúl con su texto intacto.
    r = client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"completada": True})
    assert r.status_code == 200
    assert r.json()["entrega"]["reflexion"] == "La escribí antes de enviarla."

    items = client.get("/api/baul", headers=h).json()
    assert len(items) == 1
    assert items[0]["id"] == eid
    assert items[0]["reflexion"] == "La escribí antes de enviarla."
    assert items[0]["estrellas"] == 4
    assert items[0]["visibilidad"] == "privada"
