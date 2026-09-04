"""WS24 · A1.1 · las compuertas free/premium: el BACKEND las aplica.

Regla del Roadmap v2 §1: los límites viven en `services/plan.py` y el backend los
hace valer. Un free que manda 500 caracteres recibe 422 aunque la pantalla diga
otra cosa. Acá se prueba justamente eso: pegándole a la API por el borde, sin
mirar lo que el front ofrece.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from mindful_api.config import settings
from mindful_api.main import app
from tests.test_plan import _headers, hacer_premium

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
    """Crea (auto-provisión dev) al usuario y le acepta los términos."""
    h = _headers(sub)
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def _onboard_premium(sub: str) -> dict:
    h = _onboard(sub)
    hacer_premium(sub)
    return h


def _entrega_de_hoy(h: dict) -> str:
    return client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]


def _cerrar(h: dict, eid: str, **body):
    return client.put(f"/api/entregas/{eid}/cierre", headers=h, json=body)


def _subir(h: dict, eid: str, contenido: bytes = b"png-fake", mime: str = "image/png"):
    return client.post(
        f"/api/entregas/{eid}/fotos",
        headers=h,
        files={"foto": ("pausa.png", contenido, mime)},
    )


def _detalle(r) -> str:
    return str(r.json().get("detail"))


# ── Reflexión: 150 free / 500 premium ────────────────────────────────────────


def test_reflexion_free_corta_en_150():
    h = _onboard("gate|reflexion-free")
    eid = _entrega_de_hoy(h)

    assert _cerrar(h, eid, reflexion="a" * 150).status_code == 200

    r = _cerrar(h, eid, reflexion="a" * 151)
    assert r.status_code == 422
    # Es la compuerta del plan (no el tope duro del borde, que es 500).
    assert "150" in _detalle(r)


def test_reflexion_premium_llega_a_500():
    h = _onboard_premium("gate|reflexion-premium")
    eid = _entrega_de_hoy(h)

    r = _cerrar(h, eid, reflexion="a" * 151)
    assert r.status_code == 200
    assert r.json()["entrega"]["reflexion"] == "a" * 151

    assert _cerrar(h, eid, reflexion="a" * 500).status_code == 200
    # 501 ya no entra ni siendo premium: contesta la compuerta del plan (el borde
    # sólo tiene el tope duro anti-abuso de 5000), y el mensaje nombra SU plan.
    r = _cerrar(h, eid, reflexion="a" * 501)
    assert r.status_code == 422
    assert "500" in _detalle(r) and "premium" in _detalle(r)


def test_los_textos_se_miden_strippeados_y_el_blanco_se_guarda_como_None():
    """El tope por plan cuenta caracteres ÚTILES: el padding no gasta cupo, y una
    reflexión/nota/comentario en blanco se guarda como None (no como texto)."""
    h = _onboard("gate|strip")
    eid = _entrega_de_hoy(h)

    # Blanco puro → None: no queda guardado como si fuese una pausa escrita.
    r = _cerrar(h, eid, reflexion="   ", comentario_carta="  ")
    assert r.status_code == 200
    assert r.json()["entrega"]["reflexion"] is None
    assert r.json()["entrega"]["comentario_carta"] is None

    # 145 útiles + 10 espacios entran en free (antes rebotaban con 422).
    r = _cerrar(h, eid, reflexion=" " * 10 + "a" * 145)
    assert r.status_code == 200
    assert r.json()["entrega"]["reflexion"] == "a" * 145

    # Y el blanco no PISA lo ya escrito (blanco ⇒ None ⇒ "no toques este campo",
    # el mismo contrato que usa el front al omitir un comentario vacío).
    assert _cerrar(h, eid, reflexion="   ").json()["entrega"]["reflexion"] == "a" * 145

    # La nota de compartir, igual: strippeada para medir y para publicar.
    ok = client.post("/api/compartir", headers=h,
                     json={"entrega_id": eid, "nota": " " * 10 + "n" * 150})
    assert ok.status_code == 201
    assert client.get(f"/api/c/{ok.json()['token']}").json()["nota"] == "n" * 150


def test_el_regalo_ejercicio_sirve_sus_fotos_por_el_token():
    """El receptor VE las fotos (URLs atadas al token, servidas con su sesión), y
    nunca un `storage_path` con el id interno del remitente."""
    h = _onboard_premium("gate|regalo-fotos")
    eid = _entrega_de_hoy(h)
    _subir(h, eid)
    tok = client.post("/api/compartir", headers=h,
                      json={"entrega_id": eid}).json()["token"]

    pub = client.get(f"/api/c/{tok}")
    assert "storage_path" not in pub.text
    fotos = pub.json()["fotos"]
    assert len(fotos) == 1 and fotos[0].startswith(f"/api/c/{tok}/fotos/")

    # Otra persona logueada, con el link en la mano: el permiso es el token.
    otro = _onboard("gate|regalo-receptor")
    r = client.get(fotos[0], headers=otro)
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/")


# ── Comentario sobre la carta (feedback privado, ≤150 para todos) ─────────────


def test_comentario_carta_se_guarda_y_vuelve_en_la_salida():
    h = _onboard("gate|comentario")
    eid = _entrega_de_hoy(h)

    r = _cerrar(h, eid, estrellas=2, comentario_carta="Me hubiese gustado algo más corto.")
    assert r.status_code == 200
    assert r.json()["entrega"]["comentario_carta"] == "Me hubiese gustado algo más corto."

    # Vuelve también al releer la carta del día (misma salida `_salida`).
    hoy = client.get("/api/carta-del-dia", headers=h).json()
    assert hoy["entrega"]["comentario_carta"] == "Me hubiese gustado algo más corto."

    # Vacío / espacios → None en el borde, y None significa "no toques este campo":
    # un comentario en blanco NO pisa el anterior (mismo contrato que el front, que
    # ni lo manda). Sobre una entrega sin comentario, queda en None.
    assert _cerrar(h, eid, comentario_carta="   ").json()["entrega"]["comentario_carta"] \
        == "Me hubiese gustado algo más corto."
    h2 = _onboard("gate|comentario-blanco")
    eid2 = _entrega_de_hoy(h2)
    assert _cerrar(h2, eid2, comentario_carta="   ").json()["entrega"]["comentario_carta"] is None

    assert _cerrar(h, eid, comentario_carta="c" * 150).status_code == 200
    assert _cerrar(h, eid, comentario_carta="c" * 151).status_code == 422


# ── Fotos: 1 free / 3 premium ────────────────────────────────────────────────


def test_fotos_free_una_sola_por_pausa():
    h = _onboard("gate|fotos-free")
    eid = _entrega_de_hoy(h)

    assert _subir(h, eid).status_code == 201
    r = _subir(h, eid)
    assert r.status_code == 409
    assert "plan" in _detalle(r)


def test_fotos_premium_tres_y_la_cuarta_no():
    h = _onboard_premium("gate|fotos-premium")
    eid = _entrega_de_hoy(h)

    for _ in range(3):
        assert _subir(h, eid).status_code == 201
    r = _subir(h, eid)
    assert r.status_code == 409
    assert "3 fotos" in _detalle(r)


# ── Compartir ya NO es compuerta (WS25); la nota sí mide como la reflexión ───


def test_compartir_la_ficha_entera_ya_no_es_premium():
    """WS25 · murió `compartir_ejercicio`: un free que escribió su reflexión manda
    la ficha ENTERA, igual que un premium. Ya no existe el 403 por plan."""
    h = _onboard("gate|share-free")
    eid = _entrega_de_hoy(h)
    _cerrar(h, eid, reflexion="Hoy respiré antes de contestar.")

    r = client.post("/api/compartir", headers=h, json={"entrega_id": eid})
    assert r.status_code == 201
    assert r.json()["modo"] == "ejercicio"   # lo derivó la Pausa, no el plan


def test_el_modo_lo_derive_la_pausa_y_el_del_cliente_se_ignora():
    """WS25 · el usuario no elige qué parte viaja: viaja la ficha tal como está.

    Mandar `modo` (clientes viejos) no cambia nada: una Pausa en blanco viaja como
    carta sola aunque el cliente pida `ejercicio`, y una Pausa escrita viaja entera
    aunque el cliente pida `carta_sola`.
    """
    h = _onboard_premium("gate|share-premium")
    eid = _entrega_de_hoy(h)

    # En blanco: pide ejercicio, recibe carta_sola.
    r = client.post("/api/compartir", headers=h, json={"entrega_id": eid, "modo": "ejercicio"})
    assert r.status_code == 201 and r.json()["modo"] == "carta_sola"

    # Con una foto (sin reflexión) ya hay algo del usuario que viaja.
    _subir(h, eid)
    r = client.post("/api/compartir", headers=h, json={"entrega_id": eid, "modo": "carta_sola"})
    assert r.status_code == 201 and r.json()["modo"] == "ejercicio"


def test_nota_de_compartir_mide_contra_el_plan():
    h = _onboard("gate|share-nota")
    eid = _entrega_de_hoy(h)

    ok = client.post("/api/compartir", headers=h,
                     json={"entrega_id": eid, "nota": "n" * 150})
    assert ok.status_code == 201

    r = client.post("/api/compartir", headers=h,
                    json={"entrega_id": eid, "nota": "n" * 151})
    assert r.status_code == 422
    assert "150" in _detalle(r)

    # Premium: la misma nota entra.
    hp = _onboard_premium("gate|share-nota-premium")
    eidp = _entrega_de_hoy(hp)
    assert client.post("/api/compartir", headers=hp,
                       json={"entrega_id": eidp, "nota": "n" * 151}).status_code == 201


# ── El aislamiento manda: 404 antes que cualquier compuerta de plan ──────────


def test_aislamiento_intacto_con_las_compuertas():
    ha = _onboard("gate|duenio")
    hb = _onboard("gate|intruso")
    hp = _onboard_premium("gate|intruso-premium")
    eid = _entrega_de_hoy(ha)

    # Cierre, foto, compartir y visibilidad sobre una entrega ajena: 404, nunca 422.
    assert _cerrar(hb, eid, reflexion="hola").status_code == 404
    assert _subir(hb, eid).status_code == 404
    assert client.post("/api/compartir", headers=hb,
                       json={"entrega_id": eid}).status_code == 404
    assert client.put(f"/api/baul/{eid}/visibilidad", headers=hb,
                      json={"visibilidad": "compartida"}).status_code == 404
    # Ni siquiera un premium se entera de que existe.
    assert client.post("/api/compartir", headers=hp,
                       json={"entrega_id": eid}).status_code == 404
