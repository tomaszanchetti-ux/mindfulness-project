"""Q/A ADVERSARIAL de la card A1.1 · compuertas por plan (commit 973a59c).

No prueba que funcione: intenta ROMPERLO. Nació afirmando el comportamiento
OBSERVADO (los `test_BUG_*` pasaban documentando lo roto); con la corrección de la
card, esos tests quedaron INVERTIDOS y ahora afirman el comportamiento correcto —
son la red que impide que los cuatro bugs vuelvan:

1. el regalo público servía `storage_path` (id interno + no renderizable),
2. dos subidas simultáneas superaban el cupo de fotos (TOCTOU),
3. la reflexión/nota no se strippeaban (el padding gastaba cupo),
4. el comentario se validaba antes del strip, y el 422 del borde le hablaba a un
   free del tope de OTRO plan.
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
    antes_modo, antes_dir = settings.storage_mode, settings.storage_dir
    settings.storage_mode = "local"
    settings.storage_dir = str(tmp_path)
    yield
    settings.storage_mode, settings.storage_dir = antes_modo, antes_dir


def _onboard(sub: str) -> dict:
    h = _headers(sub)
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def _onboard_premium(sub: str, dias: int = 365) -> dict:
    h = _onboard(sub)
    hacer_premium(sub, dias=dias)
    return h


def _entrega_de_hoy(h: dict) -> str:
    return client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]


def _cerrar(h: dict, eid: str, **body):
    return client.put(f"/api/entregas/{eid}/cierre", headers=h, json=body)


def _subir(h: dict, eid: str, contenido: bytes = b"png-fake", mime: str = "image/png"):
    return client.post(
        f"/api/entregas/{eid}/fotos", headers=h,
        files={"foto": ("pausa.png", contenido, mime)},
    )


def _compartir(h: dict, eid: str, modo=None, nota=None):
    """WS25 · `modo` se sigue mandando en algunos casos a propósito: el servicio lo
    IGNORA y deriva el modo de la Pausa. Los tests afirman lo derivado."""
    body = {"entrega_id": eid}
    if modo is not None:
        body["modo"] = modo
    if nota is not None:
        body["nota"] = nota
    return client.post("/api/compartir", headers=h, json=body)


def _detalle(r) -> str:
    return str(r.json().get("detail"))


# ═══ 1 · BORDES EXACTOS: ¿caracteres o bytes? ════════════════════════════════


def test_borde_free_mide_CARACTERES_no_bytes_emojis_y_acentos():
    """OK · 150 emojis (600 bytes UTF-8) entran en free; 151 no."""
    h = _onboard("qa|borde-emoji")
    eid = _entrega_de_hoy(h)

    emojis = "🌿" * 150
    assert len(emojis) == 150 and len(emojis.encode()) == 600
    r = _cerrar(h, eid, reflexion=emojis)
    assert r.status_code == 200
    assert r.json()["entrega"]["reflexion"] == emojis          # round-trip intacto

    acentos = "á" * 150
    assert len(acentos.encode()) == 300
    assert _cerrar(h, eid, reflexion=acentos).status_code == 200

    r = _cerrar(h, eid, reflexion="🌿" * 151)
    assert r.status_code == 422 and "150" in _detalle(r)


def test_borde_premium_500_emojis_entra_y_501_no():
    h = _onboard_premium("qa|borde-emoji-prem")
    eid = _entrega_de_hoy(h)
    assert _cerrar(h, eid, reflexion="🌿" * 500).status_code == 200
    assert _cerrar(h, eid, reflexion="🌿" * 501).status_code == 422


def test_borde_emoji_ZWJ_una_familia_cuenta_como_5_caracteres():
    """OK (documental) · el emoji ZWJ 👨‍👩‍👧 son 5 code points: 30 familias = 150 → 31 no.

    Nadie escribe 31 familias en una reflexión, pero deja constancia de que el
    tope es code points, no grafemas percibidos.
    """
    h = _onboard("qa|borde-zwj")
    eid = _entrega_de_hoy(h)
    familia = "👨‍👩‍👧"
    assert len(familia) == 5
    assert _cerrar(h, eid, reflexion=familia * 30).status_code == 200   # 150
    assert _cerrar(h, eid, reflexion=familia * 31).status_code == 422   # 155


def test_borde_nota_de_compartir_mismo_criterio_de_caracteres():
    h = _onboard("qa|borde-nota")
    eid = _entrega_de_hoy(h)
    assert _compartir(h, eid, nota="🌿" * 150).status_code == 201
    r = _compartir(h, eid, nota="🌿" * 151)
    assert r.status_code == 422 and "150" in _detalle(r)


# ═══ 2 · PREMIUM VENCIDO: ¿se comporta como free en TODO? ════════════════════


def test_premium_vencido_es_free_en_reflexion_fotos_y_nota_pero_comparte_igual():
    h = _onboard_premium("qa|vencido", dias=-1)   # venció ayer
    eid = _entrega_de_hoy(h)

    # perfil: la etiqueta dice free y esconde plan_hasta
    p = client.get("/api/perfil", headers=h).json()
    assert p["plan"] == "free" and p["plan_hasta"] is None
    assert p["limites"]["reflexion_max"] == 150 and p["limites"]["fotos_max"] == 1

    # reflexión: 150 sí, 151 no
    assert _cerrar(h, eid, reflexion="a" * 150).status_code == 200
    r = _cerrar(h, eid, reflexion="a" * 151)
    assert r.status_code == 422 and "plan free" in _detalle(r)

    # fotos: 1 sola
    assert _subir(h, eid).status_code == 201
    assert _subir(h, eid).status_code == 409

    # nota: 150
    assert _compartir(h, eid, nota="n" * 151).status_code == 422

    # WS25 · compartir la ficha entera NO es compuerta: el vencido manda su Pausa
    # (que ya tiene reflexión y foto) igual que un premium.
    r = _compartir(h, eid)
    assert r.status_code == 201 and r.json()["modo"] == "ejercicio"


def test_plan_premium_con_plan_hasta_NULL_falla_cerrado():
    """OK · etiqueta 'premium' sin fecha ⇒ free (la verdad es la fecha)."""
    from sqlalchemy import select

    from mindful_api.db.base import SessionLocal
    from mindful_api.db.models import Usuario

    h = _onboard("qa|premium-sin-fecha")
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == "qa|premium-sin-fecha"))
        u.plan = "premium"
        u.plan_hasta = None
        s.commit()
    eid = _entrega_de_hoy(h)
    assert _cerrar(h, eid, reflexion="a" * 151).status_code == 422
    assert client.get("/api/perfil", headers=h).json()["plan"] == "free"


# ═══ 3 · DEGRADACIÓN: lo que ya creó como premium no se le muere ═════════════


def test_degradacion_conserva_sus_3_fotos_y_su_link_ejercicio():
    h = _onboard_premium("qa|degrada")
    eid = _entrega_de_hoy(h)
    urls = [_subir(h, eid).json()["url"] for _ in range(3)]
    _cerrar(h, eid, reflexion="r" * 400, completada=True)
    tok = _compartir(h, eid, nota="n" * 400).json()["token"]

    hacer_premium("qa|degrada", dias=-1)  # se le vence

    # lee sus 3 fotos
    for u in urls:
        assert client.get(u, headers=h).status_code == 200
    # el baúl sigue mostrando las 3 y la reflexión de 400
    item = [i for i in client.get("/api/baul", headers=h).json() if i["id"] == eid][0]
    assert len(item["fotos"]) == 3 and len(item["reflexion"]) == 400
    # el regalo ya entregado sigue vivo (sin login) con la nota de 400
    pub = client.get(f"/api/c/{tok}")
    assert pub.status_code == 200
    assert pub.json()["modo"] == "ejercicio" and len(pub.json()["nota"]) == 400
    # y puede borrar sus fotos
    assert client.delete(urls[0].replace("/api/fotos/", "/api/fotos/"), headers=h).status_code == 204


def test_degradacion_borrar_una_foto_NO_le_devuelve_cupo():
    """OK (fail-closed) · 3 fotos de premium, vence, borra 2 ⇒ sigue sin poder subir."""
    h = _onboard_premium("qa|degrada-cupo")
    eid = _entrega_de_hoy(h)
    urls = [_subir(h, eid).json()["url"] for _ in range(3)]
    hacer_premium("qa|degrada-cupo", dias=-1)

    client.delete(urls[0], headers=h)
    assert _subir(h, eid).status_code == 409   # quedan 2 ≥ 1
    client.delete(urls[1], headers=h)
    assert _subir(h, eid).status_code == 409   # queda 1 ≥ 1
    client.delete(urls[2], headers=h)
    assert _subir(h, eid).status_code == 201   # 0 < 1 → recupera su única foto free


# ═══ 4 · FUGA DEL COMENTARIO PRIVADO ═════════════════════════════════════════


def test_comentario_carta_no_se_filtra_al_publico_ni_al_baul():
    h = _onboard_premium("qa|fuga-comentario")
    eid = _entrega_de_hoy(h)
    _cerrar(h, eid, reflexion="mi reflexion", comentario_carta="ESTO-ES-PRIVADO",
            completada=True)
    tok = _compartir(h, eid).json()["token"]

    # dueño: sí lo ve (cierre y carta del día)
    assert client.get("/api/carta-del-dia", headers=h).json()["entrega"]["comentario_carta"] \
        == "ESTO-ES-PRIVADO"

    # público: no aparece por ningún lado
    pub = client.get(f"/api/c/{tok}").text
    assert "ESTO-ES-PRIVADO" not in pub

    # baúl: tampoco (el item ni siquiera trae la clave)
    item = [i for i in client.get("/api/baul", headers=h).json() if i["id"] == eid][0]
    assert "comentario_carta" not in item
    assert "ESTO-ES-PRIVADO" not in client.get("/api/baul", headers=h).text


def test_el_regalo_publico_sirve_las_fotos_por_el_token_y_no_filtra_rutas():
    """FIX (era BUG) · `/api/c/{token}` devuelve URLs públicas, no rutas de Storage.

    Antes hacía `select(Foto.storage_path)`: el receptor recibía
    `fotos/<usuario_id>/<entrega_id>/<foto_id>.png` — filtraba el id interno del
    remitente y NO era renderizable (las fotos sólo se servían con login), así que
    el "ejercicio" (LA función premium de A1.1) llegaba sin fotos.

    Ahora cada foto sale como `/api/c/{token}/fotos/{foto_id}`: SÓLO por el token, y
    sólo mientras el regalo esté vivo (WS25 · además con sesión, ver el router).
    """
    from sqlalchemy import select

    from mindful_api.db.base import SessionLocal
    from mindful_api.db.models import Compartido, Usuario

    h = _onboard_premium("qa|fuga-fotos")
    eid = _entrega_de_hoy(h)
    _subir(h, eid, contenido=b"png-uno")
    _subir(h, eid, contenido=b"png-dos")
    tok = _compartir(h, eid).json()["token"]

    with SessionLocal() as s:
        uid = s.scalar(select(Usuario.id).where(Usuario.firebase_uid == "qa|fuga-fotos"))

    pub = client.get(f"/api/c/{tok}")
    fotos = pub.json()["fotos"]
    assert len(fotos) == 2
    assert all(u == f"/api/c/{tok}/fotos/{u.rsplit('/', 1)[-1]}" for u in fotos)
    # el cuerpo del regalo no lleva NADA del mundo interno
    assert "storage_path" not in pub.text
    assert uid not in pub.text and eid not in pub.text

    # (a) el receptor las ve con SU sesión (el permiso es el token, no ser el dueño)
    anon = TestClient(app)      # modo dev: resuelve al usuario por defecto
    for u in fotos:
        r = anon.get(u)
        assert r.status_code == 200
        assert r.headers["content-type"].startswith("image/")
    assert {anon.get(u).content for u in fotos} == {b"png-uno", b"png-dos"}

    # (b) la puerta privada sigue siendo privada: un tercero no la abre
    foto_id = fotos[0].rsplit("/", 1)[-1]
    otro = _onboard("qa|fuga-fotos-tercero")
    assert client.get(f"/api/fotos/{foto_id}", headers=otro).status_code == 404
    assert client.get(f"/api/fotos/{foto_id}", headers=h).status_code == 200

    # (c) el token no sirve para fotos de OTRA entrega
    hb = _onboard_premium("qa|fuga-fotos-ajena")
    foto_ajena = _subir(hb, _entrega_de_hoy(hb)).json()["id"]
    assert client.get(f"/api/c/{tok}/fotos/{foto_ajena}").status_code == 404

    # (d) un token de `carta_sola` no abre ninguna foto (WS25: el modo lo deriva la
    # Pausa, así que la carta sola sale de una Pausa en blanco — la de `hb` ya tiene
    # foto, uso una tercera cuenta sin nada escrito)
    hsola = _onboard("qa|fuga-fotos-sola")
    tok_sola = _compartir(hsola, _entrega_de_hoy(hsola)).json()["token"]
    assert tok_sola != tok
    assert client.get(f"/api/c/{tok_sola}/fotos/{foto_id}").status_code == 404

    # (e) al revocar el link, las fotos se apagan con él
    with SessionLocal() as s:
        cid = s.scalar(select(Compartido.id).where(Compartido.token == tok))
    assert client.delete(f"/api/compartir/{cid}", headers=h).status_code == 204
    assert client.get(f"/api/c/{tok}").status_code == 404
    for u in fotos:
        assert anon.get(u).status_code == 404


def test_borrar_la_entrada_apaga_las_fotos_del_regalo():
    """El regalo `ejercicio` muere con la entrada: sus fotos también (404)."""
    h = _onboard_premium("qa|regalo-borrado")
    eid = _entrega_de_hoy(h)
    _subir(h, eid)
    _cerrar(h, eid, completada=True)
    tok = _compartir(h, eid).json()["token"]
    foto_url = client.get(f"/api/c/{tok}").json()["fotos"][0]
    assert client.get(foto_url).status_code == 200

    assert client.delete(f"/api/baul/{eid}", headers=h).status_code == 204
    assert client.get(foto_url).status_code == 404
    assert "fotos" not in client.get(f"/api/c/{tok}").json()


# ═══ 5 · AISLAMIENTO POR ENCIMA DEL PLAN ════════════════════════════════════


def test_aislamiento_free_y_vencido_sobre_entrega_ajena_siempre_404():
    ha = _onboard("qa|iso-duenio")
    hfree = _onboard("qa|iso-free")
    hvenc = _onboard_premium("qa|iso-vencido", dias=-1)
    hprem = _onboard_premium("qa|iso-premium")
    eid = _entrega_de_hoy(ha)

    for h in (hfree, hvenc, hprem):
        assert _cerrar(h, eid, reflexion="x").status_code == 404
        assert _subir(h, eid).status_code == 404
        assert _compartir(h, eid).status_code == 404
        # y también el PUT de visibilidad de la card A3: una Pausa ajena no existe.
        assert client.put(f"/api/baul/{eid}/visibilidad", headers=h,
                          json={"visibilidad": "compartida"}).status_code == 404

    # y el 404 gana también contra una compuerta que dispararía 422
    assert _cerrar(hfree, eid, reflexion="x" * 400).status_code == 404
    assert _compartir(hfree, eid, nota="n" * 400).status_code == 404


def test_aislamiento_de_fotos_ajenas_404():
    ha = _onboard_premium("qa|iso-foto-duenio")
    hb = _onboard_premium("qa|iso-foto-intruso")
    eid = _entrega_de_hoy(ha)
    url = _subir(ha, eid).json()["url"]
    assert client.get(url, headers=hb).status_code == 404
    assert client.delete(url, headers=hb).status_code == 404
    assert client.get(url, headers=ha).status_code == 200


# ═══ 6 · ORDEN DE VALIDACIÓN: borde (Pydantic) vs servicio (plan) ═══════════


def test_free_501_recibe_el_mensaje_de_SU_plan_no_el_del_otro():
    """FIX (era REPARO) · el borde ya no corta en 500: la compuerta del plan es la
    que habla, y siempre con el mismo mensaje.

    Antes, un free que pegaba 600 caracteres recibía un 422 de Pydantic que le
    hablaba de 500 — el número de OTRO plan — sin decirle que su tope es 150.
    Ahora el `max_length` del borde es sólo el tope duro anti-abuso (5000).
    """
    h = _onboard("qa|orden")
    eid = _entrega_de_hoy(h)

    for largo in (151, 501, 4999):
        r = _cerrar(h, eid, reflexion="a" * largo)
        assert r.status_code == 422
        assert "150" in _detalle(r) and "free" in _detalle(r)
        assert f"mandaste {largo}" in _detalle(r)

    # El tope duro sigue existiendo (nadie manda megabytes de JSON), y ahí sí
    # contesta el borde: es un error de campo de Pydantic, no de la compuerta.
    r = _cerrar(h, eid, reflexion="a" * 5001)
    assert r.status_code == 422
    assert "reflexion" in str(r.json()["detail"])

    # Mismo criterio en la nota de compartir.
    r = _compartir(h, eid, nota="n" * 501)
    assert r.status_code == 422 and "150" in _detalle(r) and "free" in _detalle(r)
    assert _compartir(h, eid, nota="n" * 5001).status_code == 422


def test_un_422_de_compuerta_no_deja_escritura_parcial():
    """OK · `estrellas` se asigna ANTES de validar la reflexión, pero sin commit."""
    h = _onboard("qa|parcial")
    eid = _entrega_de_hoy(h)
    assert _cerrar(h, eid, estrellas=5, reflexion="a" * 151).status_code == 422
    e = client.get("/api/carta-del-dia", headers=h).json()["entrega"]
    assert e["estrellas"] is None and e["reflexion"] is None
    assert e["completada"] is False


# ═══ 7 · WHITESPACE: la reflexión NO se strippea, el comentario SÍ ══════════


def test_reflexion_de_puros_espacios_no_se_guarda_y_el_padding_no_gasta_cupo():
    """FIX (era BUG) · la reflexión se strippea como el comentario, y el largo se
    mide sobre los caracteres ÚTILES.

    Antes: 100 espacios quedaban guardados como reflexión "vivida", y 145 letras
    con 10 espacios delante rebotaban con 422 por el plan.
    Línea: schemas.py `_texto_limpio` (mode="before") + services/entrega.py
    `reflexion = reflexion.strip()` antes de medir.
    """
    h = _onboard("qa|blanks")
    eid = _entrega_de_hoy(h)

    # (a) puros espacios → None (no es una pausa escrita)
    r = _cerrar(h, eid, reflexion=" " * 100, completada=True)
    assert r.status_code == 200
    assert r.json()["entrega"]["reflexion"] is None

    # ...y el Baúl tampoco muestra una reflexión en blanco
    item = [i for i in client.get("/api/baul", headers=h).json() if i["id"] == eid][0]
    assert item["reflexion"] is None

    # (b) 145 caracteres reales + padding entran en free (145 ≤ 150)
    r = _cerrar(h, eid, reflexion=" " * 10 + "a" * 145)   # 155 crudo / 145 útil
    assert r.status_code == 200
    assert r.json()["entrega"]["reflexion"] == "a" * 145   # guardada sin el padding

    # (c) y el padding no sirve para colar 151 útiles
    r = _cerrar(h, eid, reflexion="  " + "a" * 151 + "  ")
    assert r.status_code == 422 and "mandaste 151" in _detalle(r)

    # (d) el comentario se comporta igual (siempre lo hizo)
    assert _cerrar(h, eid, comentario_carta="   ").json()["entrega"]["comentario_carta"] is None


def test_el_comentario_con_padding_llega_al_servicio_y_entra():
    """FIX (era BUG) · el borde valida los 150 DESPUÉS del strip (`mode="before"`):
    145 letras con 10 espacios delante ya no mueren en Pydantic.
    """
    h = _onboard("qa|blanks-comentario")
    eid = _entrega_de_hoy(h)
    r = _cerrar(h, eid, comentario_carta=" " * 10 + "c" * 145)   # 155 crudo / 145 útil
    assert r.status_code == 200
    assert r.json()["entrega"]["comentario_carta"] == "c" * 145

    assert _cerrar(h, eid, comentario_carta="c" * 145).status_code == 200
    # 151 útiles siguen sin entrar (el tope es igual para free y premium)
    assert _cerrar(h, eid, comentario_carta=" " + "c" * 151).status_code == 422


def test_la_nota_de_compartir_strippea_igual_que_la_reflexion():
    """FIX (era BUG) · el padding no gasta cupo y una nota en blanco se publica
    como `null`, no como una nota vacía."""
    h = _onboard("qa|blanks-nota")
    eid = _entrega_de_hoy(h)

    r = _compartir(h, eid, nota=" " * 10 + "n" * 145)
    assert r.status_code == 201
    assert client.get(f"/api/c/{r.json()['token']}").json()["nota"] == "n" * 145

    tok = _compartir(h, eid, nota="   ").json()["token"]
    assert client.get(f"/api/c/{tok}").json()["nota"] is None

    # y 151 útiles siguen rebotando contra el plan
    r = _compartir(h, eid, nota="  " + "n" * 151 + "  ")
    assert r.status_code == 422 and "mandaste 151" in _detalle(r)


def test_la_compuerta_aplica_igual_con_completada_false():
    h = _onboard("qa|no-completada")
    eid = _entrega_de_hoy(h)
    r = _cerrar(h, eid, reflexion="a" * 151, completada=False)
    assert r.status_code == 422 and "150" in _detalle(r)
    # y no marcó nada
    assert client.get("/api/carta-del-dia", headers=h).json()["entrega"]["completada"] is False
    assert _cerrar(h, eid, reflexion="a" * 150, completada=False).status_code == 200


def test_borrar_y_reescribir_no_esquiva_la_compuerta():
    """Un free no acumula 150+150: cada PUT se mide entero."""
    h = _onboard("qa|acumular")
    eid = _entrega_de_hoy(h)
    assert _cerrar(h, eid, reflexion="a" * 150).status_code == 200
    assert _cerrar(h, eid, reflexion="a" * 150 + "b" * 150).status_code == 422


def test_premium_escribe_500_y_al_vencer_el_texto_sobrevive_un_cierre_sin_reflexion():
    """OK (esperado) · la compuerta valida lo que MANDÁS, no lo que ya está guardado."""
    h = _onboard_premium("qa|texto-sobrevive")
    eid = _entrega_de_hoy(h)
    assert _cerrar(h, eid, reflexion="a" * 500).status_code == 200
    hacer_premium("qa|texto-sobrevive", dias=-1)
    r = _cerrar(h, eid, estrellas=4)          # sin tocar la reflexión
    assert r.status_code == 200 and len(r.json()["entrega"]["reflexion"]) == 500


# ═══ 8 · CUPO DE FOTOS: contar-y-después-insertar (TOCTOU) ═══════════════════


def test_dos_subidas_concurrentes_NO_superan_el_cupo_del_plan(monkeypatch):
    """FIX (era BUG real) · `subir_foto` contaba y después insertaba sin lock: dos
    requests que pasaban el chequeo antes de que la otra commiteara entraban las dos
    (un FREE terminaba con 2 fotos).

    Ahora la fila de la entrega se bloquea ANTES de contar
    (`s.get(Entrega, ..., with_for_update=True)`): la segunda espera al commit de la
    primera, cuenta 1 y recibe su 409.

    La barrera va en `storage.extension_para` — que corre DESPUÉS del 404 de
    aislamiento y ANTES del lock+conteo — para que los dos hilos queden dentro de la
    ventana de la carrera: sin el lock, los dos cuentan 0 y este test ve 2 fotos.
    """
    import threading

    from fastapi import HTTPException
    from sqlalchemy import func, select

    from mindful_api.db.base import SessionLocal
    from mindful_api.db.models import Foto, Usuario
    from mindful_api.services import fotos as fotos_svc
    from mindful_api.services import storage as storage_svc

    h = _onboard("qa|race-fotos")          # FREE: cupo 1
    eid = _entrega_de_hoy(h)

    barrera = threading.Barrier(2, timeout=10)
    real_extension = storage_svc.extension_para

    def extension_sincronizada(*a, **kw):
        ext = real_extension(*a, **kw)
        barrera.wait()                     # los dos, adentro y antes de contar
        return ext
    monkeypatch.setattr(fotos_svc.storage, "extension_para", extension_sincronizada)

    subidas, errores = [], []

    def subir(payload: bytes):
        try:
            with SessionLocal() as s:
                u = s.scalar(select(Usuario).where(Usuario.firebase_uid == "qa|race-fotos"))
                subidas.append(fotos_svc.subir_foto(s, u, eid, payload, "image/png"))
        except Exception as exc:           # noqa: BLE001
            errores.append(exc)

    hilos = [threading.Thread(target=subir, args=(p,)) for p in (b"aaa", b"bbb")]
    for t_ in hilos:
        t_.start()
    for t_ in hilos:
        t_.join(timeout=20)
    assert not any(t_.is_alive() for t_ in hilos), "las subidas se trabaron"

    # Una entró, la otra se llevó el 409 del cupo (nunca un 500 ni un deadlock).
    assert len(subidas) == 1, f"entraron {len(subidas)} subidas: {subidas}"
    assert len(errores) == 1, errores
    assert isinstance(errores[0], HTTPException) and errores[0].status_code == 409

    with SessionLocal() as s:
        n = s.scalar(select(func.count()).select_from(Foto).where(Foto.entrega_id == eid))
    assert n == 1, f"un FREE quedó con {n} fotos"
