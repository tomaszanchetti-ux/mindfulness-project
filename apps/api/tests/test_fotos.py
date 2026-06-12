"""Fotos de la pausa: subir, servir con login, límite 3, aislamiento y borrado."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from mindful_api.config import settings
from mindful_api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def _storage_temporal(tmp_path):
    """Modo local apuntando a un tmp por test: no ensucia el repo ni corridas previas."""
    antes_modo, antes_dir = settings.storage_mode, settings.storage_dir
    settings.storage_mode = "local"
    settings.storage_dir = str(tmp_path)
    yield
    settings.storage_mode, settings.storage_dir = antes_modo, antes_dir


def _onboard(sub: str) -> dict:
    h = {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def _entrega_de_hoy(h: dict) -> str:
    return client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]


def _subir(h: dict, eid: str, contenido: bytes = b"png-fake", mime: str = "image/png"):
    return client.post(
        f"/api/entregas/{eid}/fotos",
        headers=h,
        files={"foto": ("pausa.png", contenido, mime)},
    )


def test_subir_servir_y_listar_en_baul():
    h = _onboard("fotos|flujo")
    eid = _entrega_de_hoy(h)

    r = _subir(h, eid, b"abc123")
    assert r.status_code == 201
    url = r.json()["url"]
    assert url.startswith("/api/fotos/")

    # Se sirve con login, con el mime de la extensión.
    r2 = client.get(url, headers=h)
    assert r2.status_code == 200
    assert r2.content == b"abc123"
    assert r2.headers["content-type"].startswith("image/png")

    # El Baúl la lista como URL de la API (tras completar la pausa).
    client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"completada": True})
    item = client.get("/api/baul", headers=h).json()[0]
    assert item["fotos"] == [url]


def test_limite_free_y_formatos():
    h = _onboard("fotos|limites")
    eid = _entrega_de_hoy(h)

    # Free: 1 foto por pausa (WS16). Quitar la que está libera el cupo.
    primera = _subir(h, eid)
    assert primera.status_code == 201
    assert _subir(h, eid).status_code == 409  # la 2ª no entra
    client.delete(primera.json()["url"], headers=h)
    assert _subir(h, eid).status_code == 201  # con el cupo libre, entra

    assert _subir(h, eid, mime="text/plain").status_code == 415
    r = client.post(f"/api/entregas/{eid}/fotos", headers=h,
                    files={"foto": ("v.png", b"", "image/png")})
    assert r.status_code == 400  # vacía


def test_aislamiento_entre_usuarios():
    ha = _onboard("fotos|duenio")
    hb = _onboard("fotos|intruso")
    eid = _entrega_de_hoy(ha)
    url = _subir(ha, eid).json()["url"]

    # El intruso no puede ver la foto ni subir a la entrega ajena (404, no 403).
    assert client.get(url, headers=hb).status_code == 404
    assert _subir(hb, eid).status_code == 404
    assert client.delete(url, headers=hb).status_code == 404
    # Sin headers, en dev, la request cae al usuario default `dev|user` → también
    # es OTRO usuario → 404 por aislamiento. (En prod firebase sin token es 401.)
    assert client.get(url).status_code == 404


def test_quitar_foto_borra_archivo_y_fila():
    h = _onboard("fotos|quitar")
    eid = _entrega_de_hoy(h)
    url = _subir(h, eid).json()["url"]

    archivos = list(Path(settings.storage_dir).rglob("*.png"))
    assert len(archivos) == 1

    assert client.delete(url, headers=h).status_code == 204
    assert client.get(url, headers=h).status_code == 404
    assert not archivos[0].exists()


def test_borrar_entrega_limpia_storage():
    h = _onboard("fotos|borrado")
    eid = _entrega_de_hoy(h)
    _subir(h, eid)
    client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"completada": True})

    assert len(list(Path(settings.storage_dir).rglob("*.png"))) == 1
    assert client.delete(f"/api/baul/{eid}", headers=h).status_code == 204
    assert list(Path(settings.storage_dir).rglob("*.png")) == []
