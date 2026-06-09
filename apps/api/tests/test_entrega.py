"""M2/M3 · carta del día + cierre del ritual + reglas (1/día, aislamiento)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mindful_api.main import app

client = TestClient(app)


def _onboard(sub: str, cats: list[str]) -> dict:
    h = {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}
    client.put("/api/perfil/categorias", headers=h, json={"categorias": cats})
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def test_carta_del_dia_requiere_onboarding():
    h = {"X-Debug-Sub": "ent|sin-onboarding"}
    r = client.get("/api/carta-del-dia", headers=h)
    assert r.status_code == 409  # faltan categorías


def test_carta_del_dia_y_una_por_dia():
    h = _onboard("ent|diaria", ["gratitud", "calma", "vinculos"])

    r = client.get("/api/carta-del-dia", headers=h)
    assert r.status_code == 200
    data = r.json()
    # La carta viene enriquecida con lo visual (categoría + acción).
    assert data["carta"]["categoria"]["slug"] in {"gratitud", "calma", "vinculos"}
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
    h = _onboard("ent|cierre", ["gratitud", "resiliencia"])
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
    ha = _onboard("ent|dueno", ["calma", "gratitud"])
    hb = _onboard("ent|intruso", ["calma", "gratitud"])
    entrega_a = client.get("/api/carta-del-dia", headers=ha).json()["entrega"]["id"]

    # El intruso no puede cerrar la entrega ajena → 404 (no filtra existencia).
    r = client.put(f"/api/entregas/{entrega_a}/cierre", headers=hb, json={"estrellas": 1})
    assert r.status_code == 404


def test_reflexion_max_250():
    h = _onboard("ent|larga", ["calma", "gratitud"])
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    r = client.put(
        f"/api/entregas/{entrega_id}/cierre", headers=h, json={"reflexion": "x" * 251}
    )
    assert r.status_code == 422
