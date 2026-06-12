"""M1 · perfil + onboarding + aislamiento. Corre en modo dev (header X-Debug-Sub)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mindful_api.main import app

client = TestClient(app)


def _headers(sub: str, email: str = "t@mindful.local") -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": email}


def test_onboarding_completo_flujo():
    h = _headers("test|perfil")

    # Usuario fresco: sin términos aceptados, onboarding incompleto.
    r = client.get("/api/perfil", headers=h)
    assert r.status_code == 200
    p = r.json()
    assert p["onboarding_completo"] is False

    # WS22: ni pilares ni acciones se eligen; el endpoint deprecado sigue vivo
    # por compatibilidad con el front pre-WS22 y no afecta nada.
    r = client.put("/api/perfil/acciones", headers=h, json={"acciones": ["caminar"]})
    assert r.status_code == 200
    # Falta aceptar términos → todavía incompleto.
    assert r.json()["onboarding_completo"] is False

    # Horario + aviso + aceptar términos → completo (único requisito: términos).
    r = client.put(
        "/api/perfil",
        headers=h,
        json={"hora_aviso": "07:30", "tz": "Europe/Madrid", "aceptar_terminos": True},
    )
    assert r.status_code == 200
    p = r.json()
    assert p["hora_aviso"] == "07:30"
    assert p["terminos_aceptados"] is True
    assert p["onboarding_completo"] is True


def test_validaciones():
    h = _headers("test|valida")
    # Menos de 2 categorías → 422.
    r = client.put("/api/perfil/categorias", headers=h, json={"categorias": ["sentido"]})
    assert r.status_code == 422
    # Categoría inexistente → 422 ("calma" ya no es pilar — WS22).
    r = client.put(
        "/api/perfil/categorias", headers=h, json={"categorias": ["sentido", "calma"]}
    )
    assert r.status_code == 422
    # Hora mal formada → 422.
    r = client.put("/api/perfil", headers=h, json={"hora_aviso": "25:99"})
    assert r.status_code == 422


def test_acciones_endpoint_deprecado_ws22():
    """WS22 · las acciones no se eligen. El endpoint queda por compatibilidad:
    guarda lo que venga (sin piso "escribir") y nada lo lee."""
    h = _headers("test|acciones")

    # Usuario fresco: sin filas.
    assert client.get("/api/perfil", headers=h).json()["acciones"] == []

    # Guarda exactamente lo enviado — ya NO se fuerza "escribir" (no existe).
    r = client.put("/api/perfil/acciones", headers=h, json={"acciones": ["caminar"]})
    assert r.status_code == 200
    assert r.json()["acciones"] == ["caminar"]

    # Vaciar deja vacío.
    r = client.put("/api/perfil/acciones", headers=h, json={"acciones": []})
    assert r.json()["acciones"] == []

    # Acción inexistente → 422 ("escribir" tampoco existe ya como acción).
    r = client.put("/api/perfil/acciones", headers=h, json={"acciones": ["escribir"]})
    assert r.status_code == 422


def test_aislamiento_entre_usuarios():
    ha = _headers("test|aisla-a", "a@mindful.local")
    hb = _headers("test|aisla-b", "b@mindful.local")

    client.put("/api/perfil/categorias", headers=ha, json={"categorias": ["gratitud", "sentido"]})
    client.put(
        "/api/perfil/categorias", headers=hb, json={"categorias": ["resiliencia", "perspectiva"]}
    )

    a = client.get("/api/perfil", headers=ha).json()
    b = client.get("/api/perfil", headers=hb).json()

    assert set(a["categorias"]) == {"gratitud", "sentido"}
    assert set(b["categorias"]) == {"resiliencia", "perspectiva"}
    # El de uno jamás toca el del otro.
    assert set(a["categorias"]).isdisjoint(b["categorias"])
    assert a["email"] == "a@mindful.local"
    assert b["email"] == "b@mindful.local"
