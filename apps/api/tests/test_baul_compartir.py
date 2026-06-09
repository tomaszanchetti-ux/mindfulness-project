"""M4 Baúl + M5 Compartir: lectura, borrado real, link público, muerte del link."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mindful_api.main import app

client = TestClient(app)


def _onboard(sub: str, cats: list[str]) -> dict:
    h = {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}
    client.put("/api/perfil/categorias", headers=h, json={"categorias": cats})
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def _entrega_de_hoy(h: dict) -> str:
    return client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]


def test_baul_lista_y_ordenes():
    h = _onboard("baul|lectura", ["gratitud", "calma", "vinculos"])
    eid = _entrega_de_hoy(h)
    client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"estrellas": 4})

    r = client.get("/api/baul", headers=h)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["estrellas"] == 4
    assert "carta" in items[0] and "fotos" in items[0]

    # Los dos modos de orden responden 200.
    assert client.get("/api/baul?orden=reciente", headers=h).status_code == 200
    assert client.get("/api/baul?orden=valoradas", headers=h).status_code == 200
    # Orden inválido → 422.
    assert client.get("/api/baul?orden=loquesea", headers=h).status_code == 422


def test_borrado_real():
    h = _onboard("baul|borrado", ["gratitud", "calma"])
    eid = _entrega_de_hoy(h)
    assert len(client.get("/api/baul", headers=h).json()) == 1

    r = client.delete(f"/api/baul/{eid}", headers=h)
    assert r.status_code == 204
    assert client.get("/api/baul", headers=h).json() == []  # para siempre, sin papelera


def test_compartir_publico_sin_login():
    h = _onboard("share|ok", ["gratitud", "calma"])
    eid = _entrega_de_hoy(h)
    client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"reflexion": "Respiré hondo."})

    # Modo ejercicio → lleva reflexión.
    r = client.post("/api/compartir", headers=h, json={"entrega_id": eid, "modo": "ejercicio",
                                                       "nota": "Para vos."})
    assert r.status_code == 201
    token = r.json()["token"]

    # El receptor abre SIN login (sin headers de auth).
    pub = TestClient(app).get(f"/api/c/{token}")
    assert pub.status_code == 200
    regalo = pub.json()
    assert regalo["modo"] == "ejercicio"
    assert regalo["nota"] == "Para vos."
    assert regalo["reflexion"] == "Respiré hondo."
    assert "frase" in regalo["carta"]


def test_link_ejercicio_muere_al_borrar_pero_carta_sola_sobrevive():
    h = _onboard("share|muerte", ["gratitud", "calma"])
    eid = _entrega_de_hoy(h)

    t_ej = client.post("/api/compartir", headers=h,
                       json={"entrega_id": eid, "modo": "ejercicio"}).json()["token"]
    t_sola = client.post("/api/compartir", headers=h,
                         json={"entrega_id": eid, "modo": "carta_sola"}).json()["token"]

    # Borro la entrada del Baúl.
    client.delete(f"/api/baul/{eid}", headers=h)

    # El link "ejercicio" murió; la "carta sola" sigue viva.
    assert TestClient(app).get(f"/api/c/{t_ej}").status_code == 404
    assert TestClient(app).get(f"/api/c/{t_sola}").status_code == 200


def test_compartir_aislamiento():
    ha = _onboard("share|dueno", ["gratitud", "calma"])
    hb = _onboard("share|otro", ["gratitud", "calma"])
    eid_a = _entrega_de_hoy(ha)
    # B no puede compartir una entrega de A.
    r = client.post("/api/compartir", headers=hb, json={"entrega_id": eid_a, "modo": "carta_sola"})
    assert r.status_code == 404
