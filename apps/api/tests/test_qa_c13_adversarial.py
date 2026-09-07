"""Q/A adversarial · C1.3 · Recomendaciones (WS29).

Prefijo `qa13c|`. No repite lo que ya cubre `test_c13_recomendaciones.py`
(candado del plan básico, límites de largo con ASCII, tope de 30 secuencial,
aislamiento básico, mezcla Baúl/vitrina por fecha, `de` sin email). Acá:
concurrencia real, admin, bordes de multibyte y de la URL, ids raros, body
vacío/extra, vitrina con vínculo y Baúl sin Pausas.

Las dos mutaciones del vector 6 (guarda premium del POST, filtro de la
vitrina) se hicieron a mano contra este archivo + `test_c13_recomendaciones.py`
y se restauraron con `git checkout` — no viven acá como test permanente.

`test_ok_...` = candado (pasa, el comportamiento es el esperado).
`test_bug_...` = falla y documenta un defecto real (sin xfail).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    RECOMENDACIONES_MAX,
    Carta,
    Entrega,
    Recomendacion,
    Usuario,
    Vinculo,
    VINCULO_ACEPTADA,
)
from mindful_api.main import app

client = TestClient(app)
PREFIJO = "qa13c|"


# ── Herramientas (copiadas de test_c13_recomendaciones.py) ──────────────────

def _h(sub: str) -> dict:
    return {"X-Debug-Sub": PREFIJO + sub, "X-Debug-Email": f"{sub}@qa13c.local"}


def _usuario(s, sub: str, premium: bool = True, vencido: bool = False, **campos) -> Usuario:
    u = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + sub))
    if u is None:
        u = Usuario(firebase_uid=PREFIJO + sub, email=f"{sub}@qa13c.local", apodo=sub.title())
        s.add(u)
    u.terminos_aceptados_at = datetime.now(timezone.utc)
    if vencido:
        u.plan = "premium"
        u.plan_hasta = datetime.now(timezone.utc) - timedelta(days=1)
    elif premium:
        u.plan = "premium"
        u.plan_hasta = datetime.now(timezone.utc) + timedelta(days=30)
    else:
        u.plan = "free"
        u.plan_hasta = None
    for k, v in campos.items():
        setattr(u, k, v)
    s.commit()
    s.refresh(u)
    return u


def _pausa(s, duenio, visibilidad="compartida", fecha=None, estrellas=None) -> Entrega:
    carta_id = s.scalar(select(Carta.id).order_by(Carta.id).limit(1))
    e = Entrega(
        usuario_id=duenio.id, carta_id=carta_id, completada=True,
        visibilidad=visibilidad, reflexion="qa13c", estrellas=estrellas,
    )
    if fecha is not None:
        e.fecha = fecha
    s.add(e)
    s.commit()
    s.refresh(e)
    return e


def _crear(sub: str, **campos) -> "tuple[int, dict]":
    cuerpo = {"titulo": "Un libro", "tipo": "libro", "texto": "Me hizo bien."}
    cuerpo.update(campos)
    r = client.post("/api/recomendaciones", headers=_h(sub), json=cuerpo)
    return r.status_code, (r.json() if r.content else {})


def _vinculo_aceptado(s, a: Usuario, b: Usuario) -> None:
    s.add(Vinculo(solicitante_id=a.id, destinatario_id=b.id, estado=VINCULO_ACEPTADA))
    s.commit()


@pytest.fixture(autouse=True)
def _limpio():
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()
    yield


# ═════════════════════════════════════════════════════════════════════════════
# 1 · Premium: admin y vencido
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_admin_es_premium_sin_stripe_y_puede_crear(monkeypatch):
    with SessionLocal() as s:
        _usuario(s, "admin", premium=False)  # free, sin Stripe

    monkeypatch.setattr(settings, "admin_uids", PREFIJO + "admin")
    codigo, item = _crear("admin", titulo="Regla del admin")
    assert codigo == 201, item
    assert item["visibilidad"] == "privada"


def test_ok_vencido_403_tambien_en_put_y_visibilidad():
    with SessionLocal() as s:
        _usuario(s, "venc2")
    _, item = _crear("venc2", titulo="Cuando era premium")

    with SessionLocal() as s:
        _usuario(s, "venc2", vencido=True)

    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("venc2"),
                   json={"texto": "otra cosa"})
    assert r.status_code == 403
    r = client.put(f"/api/recomendaciones/{item['id']}/visibilidad", headers=_h("venc2"),
                   json={"visibilidad": "compartida"})
    assert r.status_code == 403
    # Pero el Baúl le sigue mostrando la suya.
    baul = client.get("/api/baul", headers=_h("venc2")).json()
    assert [i["id"] for i in baul] == [item["id"]]


# ═════════════════════════════════════════════════════════════════════════════
# 2 · Validación: multibyte, URL, mayúsculas, extra keys, PUT vacío/null
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_texto_multibyte_se_cuenta_en_caracteres_no_bytes():
    with SessionLocal() as s:
        _usuario(s, "multi")

    # 😀 y ñ: un carácter Python cada uno, varios bytes en UTF-8.
    base = "😀ñ" * 250  # 500 caracteres exactos
    assert len(base) == 500
    codigo, item = _crear("multi", texto=base)
    assert codigo == 201, item
    assert item["texto"] == base

    codigo, cuerpo = _crear("multi", texto=base + "x")  # 501
    assert codigo == 422
    assert cuerpo["detail"] == "El texto no puede tener más de 500 caracteres."


def test_ok_url_https_en_mayusculas_se_acepta():
    """Contrato: `url` opcional, "solo https" (WS29 §4.3). Un esquema HTTPS en
    mayúsculas (`HTTPS://…`) es una URL https válida (RFC 3986: el esquema no
    distingue mayúsculas/minúsculas) pero el servicio la rechaza con 422 porque
    compara con `str.startswith("https://")`, sensible a mayúsculas.

    mindful_api/services/recomendaciones.py:169 (`limpiar_url`,
    `if not url.startswith(URL_PREFIJO)`).
    """
    with SessionLocal() as s:
        _usuario(s, "mayus")

    codigo, cuerpo = _crear("mayus", url="HTTPS://ejemplo.org/valido")
    assert codigo == 201, (
        f"se esperaba 201 (URL https válida) pero dio {codigo}: {cuerpo}"
    )


def test_ok_url_https_a_secas_pasa_la_validacion_de_prefijo():
    """Documenta el alcance real: `limpiar_url` solo exige el prefijo `https://`,
    sin validar que exista un host después. `"https://"` a secas es aceptada."""
    with SessionLocal() as s:
        _usuario(s, "pelado")

    codigo, item = _crear("pelado", url="https://")
    assert codigo == 201, item
    assert item["url"] == "https://"


def test_ok_url_javascript_es_rechazada():
    with SessionLocal() as s:
        _usuario(s, "xss")
    codigo, cuerpo = _crear("xss", url="javascript:alert(1)")
    assert codigo == 422
    assert cuerpo["detail"] == "El enlace debe empezar con https://"


def test_ok_url_en_el_borde_de_501_falla_500_pasa():
    with SessionLocal() as s:
        _usuario(s, "urlborde")

    url_500 = "https://" + "a" * (500 - len("https://"))
    assert len(url_500) == 500
    codigo, item = _crear("urlborde", url=url_500)
    assert codigo == 201, item
    assert item["url"] == url_500

    url_501 = url_500 + "a"
    codigo, cuerpo = _crear("urlborde", url=url_501)
    assert codigo == 422
    assert cuerpo["detail"] == "El enlace no puede tener más de 500 caracteres."


def test_ok_tipo_en_mayusculas_es_rechazado():
    with SessionLocal() as s:
        _usuario(s, "tipoup")
    codigo, cuerpo = _crear("tipoup", tipo="LIBRO")
    assert codigo == 422
    assert "libro" in cuerpo["detail"]


def test_ok_claves_extra_en_el_body_se_ignoran():
    with SessionLocal() as s:
        _usuario(s, "extra")

    r = client.post(
        "/api/recomendaciones", headers=_h("extra"),
        json={
            "titulo": "Con extras", "tipo": "libro", "texto": "Ok",
            "usuario_id": "otro-cualquiera", "es_admin": True, "precio": 999,
        },
    )
    assert r.status_code == 201, r.json()
    item = r.json()
    assert "usuario_id" not in item and "es_admin" not in item and "precio" not in item
    assert item["titulo"] == "Con extras"


def test_ok_put_body_vacio_no_cambia_nada():
    with SessionLocal() as s:
        _usuario(s, "vacio")
    _, item = _crear("vacio", titulo="Sin tocar", texto="Nada cambia",
                     url="https://algo.example", visibilidad="compartida")

    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("vacio"), json={})
    assert r.status_code == 200
    puesto = r.json()
    assert puesto["titulo"] == "Sin tocar"
    assert puesto["texto"] == "Nada cambia"
    assert puesto["url"] == "https://algo.example"
    assert puesto["visibilidad"] == "compartida"


def test_ok_put_url_null_no_toca_pero_vacio_borra():
    with SessionLocal() as s:
        _usuario(s, "urlnull")
    _, item = _crear("urlnull", url="https://conservame.example")

    # url: null (ausente en el JSON del modelo == None) no toca el campo.
    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("urlnull"),
                   json={"url": None, "titulo": "Otro titulo"})
    assert r.status_code == 200
    assert r.json()["url"] == "https://conservame.example"

    # url: "" sí lo borra.
    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("urlnull"),
                   json={"url": ""})
    assert r.status_code == 200
    assert r.json()["url"] is None


# ═════════════════════════════════════════════════════════════════════════════
# 3 · Tope 30 bajo carrera
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_dos_post_simultaneos_con_29_nunca_dan_31_ni_500():
    with SessionLocal() as s:
        _usuario(s, "carrera")
    for n in range(RECOMENDACIONES_MAX - 1):  # 29
        codigo, item = _crear("carrera", titulo=f"Previa {n}")
        assert codigo == 201, item

    def _post():
        return client.post("/api/recomendaciones", headers=_h("carrera"),
                           json={"titulo": "La treinta", "tipo": "libro", "texto": "x"})

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(_post)
        f2 = ex.submit(_post)
        r1, r2 = f1.result(), f2.result()

    codigos = sorted([r1.status_code, r2.status_code])
    assert 500 not in codigos, (r1.status_code, r1.text, r2.status_code, r2.text)
    assert codigos == [201, 409], (r1.status_code, r1.text, r2.status_code, r2.text)

    r = client.get("/api/recomendaciones", headers=_h("carrera"))
    assert len(r.json()) == RECOMENDACIONES_MAX


# ═════════════════════════════════════════════════════════════════════════════
# 4 · Aislamiento: ids raros
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_ids_raros_dan_404_o_422_nunca_500():
    with SessionLocal() as s:
        _usuario(s, "raro")

    for id_raro in ("..%2F..%2Fetc", "x" * 300):
        r = client.put(f"/api/recomendaciones/{id_raro}", headers=_h("raro"),
                       json={"texto": "y"})
        assert r.status_code in (404, 422), (id_raro, r.status_code, r.text)
        r = client.delete(f"/api/recomendaciones/{id_raro}", headers=_h("raro"))
        assert r.status_code in (404, 422), (id_raro, r.status_code, r.text)
        r = client.put(f"/api/recomendaciones/{id_raro}/visibilidad", headers=_h("raro"),
                       json={"visibilidad": "compartida"})
        assert r.status_code in (404, 422), (id_raro, r.status_code, r.text)

    # Segmento vacío: la ruta ni matchea con el recurso — no debe ser 500.
    r = client.put("/api/recomendaciones//visibilidad", headers=_h("raro"),
                   json={"visibilidad": "compartida"})
    assert r.status_code != 500, r.text


# ═════════════════════════════════════════════════════════════════════════════
# 5 · Vitrina y Baúl
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_privada_no_aparece_ni_con_vinculo_aceptado():
    with SessionLocal() as s:
        duenio = _usuario(s, "privB", perfil_publico=False)
        yo = _usuario(s, "amigoA", premium=False)
        _vinculo_aceptado(s, yo, duenio)
        duenio_id = duenio.id

    _, privada = _crear("privB", titulo="Solo para mi", visibilidad="privada")
    _, compartida = _crear("privB", titulo="Para todos", visibilidad="compartida")

    r = client.get(f"/api/fichas/de/{duenio_id}", headers=_h("amigoA"))
    assert r.status_code == 200
    fichas = r.json()["fichas"]
    assert fichas is not None  # con vínculo, el perfil SÍ se ve
    ids = [f["id"] for f in fichas]
    assert compartida["id"] in ids
    assert privada["id"] not in ids
    assert "Solo para mi" not in r.text


def test_ok_baul_con_cero_pausas_y_una_recomendacion_no_devuelve_vacio():
    with SessionLocal() as s:
        _usuario(s, "solareco")
    _, item = _crear("solareco", titulo="La unica ficha")

    baul = client.get("/api/baul", headers=_h("solareco")).json()
    assert baul != []
    assert len(baul) == 1
    assert baul[0]["tipo"] == "recomendacion"
    assert baul[0]["id"] == item["id"]
