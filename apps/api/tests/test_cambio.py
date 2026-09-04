"""WS24 · A1.3 · cambiar la carta del día: premium, 3 veces, misma entrega.

Regla de producto: sigue llegando UNA carta por día. El cambio la REEMPLAZA en
la misma fila `entregas` (nunca crea otra) y la vieja queda descartada por hoy.
"""

from __future__ import annotations

from fastapi.testclient import TestClient

from mindful_api.main import app
from mindful_api.services.seleccion import EJE_MOVIMIENTO, EJE_QUIETUD
from tests.test_plan import _headers, hacer_premium

client = TestClient(app)


def _onboard(sub: str) -> dict:
    h = _headers(sub)
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def _onboard_premium(sub: str) -> dict:
    h = _onboard(sub)
    hacer_premium(sub)
    return h


def _eje(accion: str) -> str:
    assert accion in EJE_QUIETUD | EJE_MOVIMIENTO
    return "quietud" if accion in EJE_QUIETUD else "movimiento"


def test_free_no_puede_cambiar():
    h = _onboard("cam|free")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]

    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 403
    assert "premium" in r.json()["detail"].lower()


def test_premium_cambia_tres_veces_y_la_cuarta_rebota():
    h = _onboard_premium("cam|tres")
    primera = client.get("/api/carta-del-dia", headers=h).json()
    entrega_id = primera["entrega"]["id"]
    pilar = primera["carta"]["categoria"]["slug"]
    vistas = {primera["carta"]["id"]}
    accion_previa = primera["carta"]["accion"]["slug"]

    for i in (1, 2, 3):
        r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
        assert r.status_code == 200, r.text
        data = r.json()

        # Misma entrega (1 carta por día), mismo pilar, otra carta.
        assert data["entrega"]["id"] == entrega_id
        assert data["entrega"]["ya_existia"] is True
        assert data["carta"]["categoria"]["slug"] == pilar
        assert data["carta"]["id"] not in vistas  # las descartadas no vuelven

        # Cruza el eje quietud ↔ movimiento (con el mazo real siempre hay).
        assert _eje(data["carta"]["accion"]["slug"]) != _eje(accion_previa)

        assert data["cambios"] == i
        assert data["cambios_restantes"] == 3 - i

        vistas.add(data["carta"]["id"])
        accion_previa = data["carta"]["accion"]["slug"]

    # La 4.ª vez ya no hay cambios disponibles.
    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 409
    assert "3 veces" in r.json()["detail"]


def test_la_carta_del_dia_devuelve_la_nueva_en_la_misma_entrega():
    h = _onboard_premium("cam|persiste")
    antes = client.get("/api/carta-del-dia", headers=h).json()
    entrega_id = antes["entrega"]["id"]

    nueva = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).json()
    assert nueva["carta"]["id"] != antes["carta"]["id"]

    despues = client.get("/api/carta-del-dia", headers=h).json()
    assert despues["carta"]["id"] == nueva["carta"]["id"]
    assert despues["entrega"]["id"] == entrega_id
    assert despues["entrega"]["ya_existia"] is True


def test_entrega_ajena_da_404():
    ha = _onboard_premium("cam|dueno")
    hb = _onboard_premium("cam|intruso")
    entrega_a = client.get("/api/carta-del-dia", headers=ha).json()["entrega"]["id"]

    # Aislamiento: ni siendo premium ve la entrega del otro (404, no filtra existencia).
    r = client.post(f"/api/entregas/{entrega_a}/cambiar", headers=hb)
    assert r.status_code == 404


def test_pausa_ya_cerrada_no_se_cambia():
    h = _onboard_premium("cam|cerrada")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    client.put(
        f"/api/entregas/{entrega_id}/cierre",
        headers=h,
        json={"estrellas": 5, "reflexion": "Ya la viví.", "completada": True},
    )

    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 409
    assert "cerrada" in r.json()["detail"]
