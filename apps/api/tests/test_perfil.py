"""M1 · perfil + onboarding + aislamiento. Corre en modo dev (header X-Debug-Sub).

WS23: los endpoints de elección (PUT /api/perfil/categorias|acciones) ya no
existen — ni pilares ni acciones se eligen; el onboarding es solo perfil + términos.
"""

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
    # Hora mal formada → 422.
    r = client.put("/api/perfil", headers=h, json={"hora_aviso": "25:99"})
    assert r.status_code == 422


def test_endpoints_de_eleccion_ya_no_existen():
    """WS23 · las tablas y endpoints de elección se retiraron (canon WS22)."""
    h = _headers("test|sin-eleccion")
    assert client.put(
        "/api/perfil/categorias", headers=h, json={"categorias": ["gratitud", "sentido"]}
    ).status_code in (404, 405)
    assert client.put(
        "/api/perfil/acciones", headers=h, json={"acciones": ["caminar"]}
    ).status_code in (404, 405)


def test_aislamiento_entre_usuarios():
    ha = _headers("test|aisla-a", "a@mindful.local")
    hb = _headers("test|aisla-b", "b@mindful.local")

    client.put("/api/perfil", headers=ha, json={"apodo": "Ana", "hora_aviso": "08:00"})
    client.put("/api/perfil", headers=hb, json={"apodo": "Beto", "hora_aviso": "21:00"})

    a = client.get("/api/perfil", headers=ha).json()
    b = client.get("/api/perfil", headers=hb).json()

    # El perfil de uno jamás toca el del otro.
    assert a["apodo"] == "Ana" and a["hora_aviso"] == "08:00"
    assert b["apodo"] == "Beto" and b["hora_aviso"] == "21:00"
    assert a["email"] == "a@mindful.local"
    assert b["email"] == "b@mindful.local"
