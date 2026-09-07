"""WS27 · B1.3 · Administración: el panel donde Tomás decide sobre las cartas.

Qué se prueba acá, y por qué:

1. **La puerta.** `/api/admin` nace CERRADO (lista de admins vacía = nadie entra),
   y con la lista puesta entra SOLO ese uid. Es el único lugar de la app donde un
   usuario puede tocar el Mundo 1.
2. **Aprobar es cargar.** No alcanza con que la propuesta quede en `aprobada`: la
   carta tiene que EXISTIR en `cartas`, con origen comunidad, autor y la firma que
   eligió el autor, y tiene que estar en el pool que el motor sortea. Se verifica
   con el conteo público (`/api/contenido/resumen`: 77 → 78) y leyendo la fila.
3. **Las transiciones.** Cada decisión sale de un conjunto acotado de estados; lo
   demás es 409. Una carta ya decidida no se re-decide.
4. **El autor se entera.** Toda decisión que le cambia la vida deja un `Aviso`.
5. **Los comentarios son anónimos.** El feedback de las cartas es para Dwellia:
   viaja el apodo, JAMÁS el email.

Las propuestas se siembran directo con `SessionLocal()` (no dependen de B1.1) y
todo lo que estos tests publican en `cartas` se borra al empezar y al terminar
cada test: el mazo tiene que volver siempre a 77, porque otros tests lo cuentan.
"""

from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    AVISO_CARTA_ESTADO,
    ESTADO_A_REVISAR,
    ESTADO_APROBADA,
    ESTADO_EN_REVISION,
    ESTADO_RECHAZADA,
    ESTADO_RETIRADA,
    ESTADO_REVISION_DWELLIA,
    FIRMA_ANONIMA,
    FIRMA_APODO,
    ORIGEN_COMUNIDAD,
    ORIGEN_DWELLIA,
    Aviso,
    Carta,
    CartaComunidad,
    Entrega,
    Usuario,
)
from mindful_api.main import app
from mindful_api.services.admin import PREFIJO_CARTA_COMUNIDAD
from mindful_api.services.entrega import _carta_enriquecida

client = TestClient(app)

ADMIN_SUB = "b13|admin"
PROMPT_OK = (
    "Escribe en tu diario tres cosas que hoy sostuvieron tu día sin que las "
    "nombraras, y qué cambiaría si les dieras las gracias en voz alta."
)


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


# ── Limpieza: cada test arranca y termina con el mazo en 77 ──────────────────
def _limpiar() -> None:
    """Borra SOLO lo de esta card, nunca "todo lo que no es de Dwellia".

    Los usuarios `b13|` se llevan en cascada sus entregas, fotos, avisos y
    propuestas; las cartas publicadas se reconocen por el prefijo `com-`, que solo
    escribe el aprobar de B1.3. Así, cuando la suite entera corra sobre una sola
    base, este módulo no le pisa las filas a las otras cards.
    """
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like("b13|%")))
        s.execute(delete(Carta).where(Carta.id.like(PREFIJO_CARTA_COMUNIDAD + "%")))
        s.commit()


@pytest.fixture(autouse=True)
def limpio():
    _limpiar()
    yield
    _limpiar()


@pytest.fixture
def admin(monkeypatch) -> dict:
    """Declara a `b13|admin` como administración (en tiempo de request) y lo devuelve."""
    monkeypatch.setattr(settings, "admin_uids", ADMIN_SUB)
    return _headers(ADMIN_SUB)


# ── Siembra ──────────────────────────────────────────────────────────────────
def _crear_usuario(sub: str, apodo=None, nombre=None, terminos: bool = False) -> str:
    with SessionLocal() as s:
        u = Usuario(
            firebase_uid=sub, email=f"{sub}@mindful.local", apodo=apodo, nombre=nombre
        )
        if terminos:
            u.terminos_aceptados_at = datetime.now(timezone.utc)
        s.add(u)
        s.commit()
        return u.id


def _sembrar(
    usuario_id: str,
    estado: str = ESTADO_REVISION_DWELLIA,
    firma: str = FIRMA_ANONIMA,
    frase: str = "Hoy alcanza con lo que ya está.",
    prompt: str = PROMPT_OK,
    categoria: str = "gratitud",
    accion: str = "contemplar",
    concepto=None,
    veredicto=None,
    created_at=None,
) -> str:
    """Una propuesta en la tabla, sin pasar por B1.1 (esta card no depende de ella)."""
    with SessionLocal() as s:
        p = CartaComunidad(
            usuario_id=usuario_id, categoria_slug=categoria, accion_slug=accion,
            frase=frase, prompt=prompt, firma=firma, estado=estado,
            concepto=concepto, veredicto=veredicto,
        )
        if created_at is not None:
            p.created_at = created_at
            p.updated_at = created_at
        s.add(p)
        s.commit()
        return p.id


def _estado_en_db(propuesta_id: str) -> CartaComunidad:
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        assert p is not None
        s.expunge(p)
        return p


def _avisos(usuario_id: str) -> list:
    with SessionLocal() as s:
        return list(s.scalars(
            select(Aviso).where(Aviso.usuario_id == usuario_id)
        ).all())


def _total_cartas() -> int:
    return client.get("/api/contenido/resumen").json()["cartas"]


# ═══════════════════════════════════════════════════════════════════════════
# 1. La puerta
# ═══════════════════════════════════════════════════════════════════════════
def test_sin_admin_uids_nadie_es_admin(monkeypatch):
    """El default seguro: lista vacía ⇒ /api/admin devuelve 403 a TODO el mundo."""
    monkeypatch.setattr(settings, "admin_uids", "")
    for headers in (_headers(ADMIN_SUB), _headers("b13|cualquiera")):
        r = client.get("/api/admin/cartas", headers=headers)
        assert r.status_code == 403
        assert r.json()["detail"] == "Solo administración"
    assert client.get("/api/admin/comentarios", headers=_headers(ADMIN_SUB)).status_code == 403


def test_otro_uid_no_entra(admin):
    """Con la lista puesta, un usuario cualquiera sigue siendo un usuario cualquiera."""
    autor = _crear_usuario("b13|autor-403")
    propuesta = _sembrar(autor)
    h = _headers("b13|intruso")

    assert client.get("/api/admin/cartas", headers=h).status_code == 403
    assert client.get("/api/admin/comentarios", headers=h).status_code == 403
    assert client.post(f"/api/admin/cartas/{propuesta}/aprobar", headers=h).status_code == 403
    assert client.post(
        f"/api/admin/cartas/{propuesta}/rechazar", json={"motivo": "no"}, headers=h
    ).status_code == 403
    assert client.post(
        f"/api/admin/cartas/{propuesta}/a-revisar", json={"sugerencia": "meh"}, headers=h
    ).status_code == 403
    # Y no tocó nada.
    assert _estado_en_db(propuesta).estado == ESTADO_REVISION_DWELLIA


def test_el_admin_entra(admin):
    r = client.get("/api/admin/cartas", headers=admin)
    assert r.status_code == 200
    assert r.json() == []


def test_la_lista_se_lee_en_cada_request(monkeypatch, admin):
    """`get_admin` NO congela la lista al importar: sacar el uid cierra la puerta ya."""
    assert client.get("/api/admin/cartas", headers=admin).status_code == 200
    monkeypatch.setattr(settings, "admin_uids", "b13|otro-admin")
    assert client.get("/api/admin/cartas", headers=admin).status_code == 403


# ═══════════════════════════════════════════════════════════════════════════
# 2. La bandeja
# ═══════════════════════════════════════════════════════════════════════════
def test_listar_filtra_por_estado_y_ordena_por_mas_nueva(admin):
    autor = _crear_usuario("b13|autor-lista", apodo="Lu")
    base = datetime.now(timezone.utc)
    vieja = _sembrar(autor, created_at=base - timedelta(hours=3), frase="La vieja.")
    nueva = _sembrar(autor, created_at=base - timedelta(hours=1), frase="La nueva.")
    rechazada = _sembrar(autor, estado=ESTADO_RECHAZADA, created_at=base - timedelta(hours=2))
    retirada = _sembrar(autor, estado=ESTADO_RETIRADA, created_at=base - timedelta(hours=4))

    # Default = lo que espera decisión, más nueva primero.
    datos = client.get("/api/admin/cartas", headers=admin).json()
    assert [d["id"] for d in datos] == [nueva, vieja]

    # Un estado puntual.
    datos = client.get("/api/admin/cartas?estado=rechazada", headers=admin).json()
    assert [d["id"] for d in datos] == [rechazada]

    # Todas = el recorrido completo, mismo orden.
    datos = client.get("/api/admin/cartas?estado=todas", headers=admin).json()
    assert [d["id"] for d in datos] == [nueva, rechazada, vieja, retirada]


def test_estado_invalido_es_422(admin):
    r = client.get("/api/admin/cartas?estado=inventado", headers=admin)
    assert r.status_code == 422
    assert "inventado" in r.json()["detail"]


def test_forma_del_item_carta_y_autor(admin):
    """La carta de la propuesta se dibuja con el MISMO componente que la del día:
    por eso tiene exactamente las mismas claves que `_carta_enriquecida`."""
    autor = _crear_usuario("b13|autor-forma", apodo="Lu", nombre="Lucía")
    veredicto = {"veredicto": "requiere_revision", "hallazgos": ["R3.1"]}
    propuesta = _sembrar(
        autor, firma=FIRMA_APODO, concepto="lo-que-sostiene", veredicto=veredicto,
        categoria="vinculos", accion="caminar",
    )

    item = client.get("/api/admin/cartas", headers=admin).json()[0]
    assert item["id"] == propuesta
    assert item["estado"] == ESTADO_REVISION_DWELLIA
    assert item["firma"] == FIRMA_APODO
    assert item["concepto"] == "lo-que-sostiene"
    assert item["motivo"] is None
    assert item["carta_id"] is None
    # El veredicto viaja CRUDO: Tomás lee literalmente lo que dijo el juez.
    assert item["veredicto"] == veredicto
    assert item["created_at"] and item["updated_at"]
    # El autor sí se identifica (es el panel interno, no el feed).
    assert item["autor"] == {"apodo": "Lu", "email": "b13|autor-forma@mindful.local",
                             "nombre": "Lucía"}

    with SessionLocal() as s:
        dwellia = s.scalars(select(Carta).where(Carta.origen == ORIGEN_DWELLIA)).first()
        referencia = _carta_enriquecida(s, dwellia)
    assert set(item["carta"]) == set(referencia)

    carta = item["carta"]
    assert carta["id"] == propuesta          # todavía no hay carta publicada
    assert carta["frase"] == "Hoy alcanza con lo que ya está."
    assert carta["prompt"] == PROMPT_OK
    assert carta["origen"] == ORIGEN_COMUNIDAD
    assert carta["firma_publica"] == "Lu"    # eligió firmar con su apodo
    assert carta["categoria"]["slug"] == "vinculos"
    assert set(carta["categoria"]) == {"slug", "nombre", "color_accent", "color_text", "img"}
    assert carta["accion"]["slug"] == "caminar"
    assert set(carta["accion"]) == {"slug", "nombre", "glifo"}


def test_firma_anonima_no_expone_el_apodo_en_la_previa(admin):
    autor = _crear_usuario("b13|autor-anon", apodo="Lu")
    _sembrar(autor, firma=FIRMA_ANONIMA)
    item = client.get("/api/admin/cartas", headers=admin).json()[0]
    assert item["autor"]["apodo"] == "Lu"          # Tomás sí sabe quién es
    assert item["carta"]["firma_publica"] is None  # la comunidad, no


# ═══════════════════════════════════════════════════════════════════════════
# 3. Aprobar = cargar al mazo
# ═══════════════════════════════════════════════════════════════════════════
def test_aprobar_publica_la_carta_con_apodo_y_avisa(admin):
    autor_id = _crear_usuario("b13|autor-aprueba", apodo="Lu", nombre="Lucía")
    propuesta = _sembrar(autor_id, firma=FIRMA_APODO, concepto="lo-que-sostiene",
                         categoria="sentido", accion="respirar")
    assert _total_cartas() == 77

    r = client.post(f"/api/admin/cartas/{propuesta}/aprobar", headers=admin)
    assert r.status_code == 200
    item = r.json()
    assert item["estado"] == ESTADO_APROBADA
    carta_id = item["carta_id"]
    assert carta_id and carta_id.startswith("com-")

    # La propuesta quedó decidida y con el rastro de qué carta salió de ella.
    p = _estado_en_db(propuesta)
    assert p.estado == ESTADO_APROBADA and p.carta_id == carta_id

    # APROBAR ES CARGAR: la carta existe de verdad en el Mundo 1.
    with SessionLocal() as s:
        c = s.get(Carta, carta_id)
        assert c is not None
        assert c.origen == ORIGEN_COMUNIDAD
        assert c.autor_usuario_id == autor_id
        assert c.firma_publica == "Lu"
        assert c.categoria_slug == "sentido" and c.accion_slug == "respirar"
        assert c.frase == "Hoy alcanza con lo que ya está." and c.prompt == PROMPT_OK
        assert c.concepto == "lo-que-sostiene"
        # …y está en el pool que el motor sortea (hoy `select(Carta)` completo;
        # B2.1 lo filtrará por opt-in, pero la carta tiene que ESTAR).
        assert carta_id in [x.id for x in s.scalars(select(Carta)).all()]

    # El conteo público lo confirma sin mirar la base.
    assert _total_cartas() == 78

    # El autor se enteró.
    avisos = _avisos(autor_id)
    assert len(avisos) == 1
    assert avisos[0].tipo == AVISO_CARTA_ESTADO
    assert avisos[0].referencia_id == propuesta
    assert avisos[0].leido is False
    assert "comunidad" in avisos[0].texto

    # Aprobar dos veces no publica dos cartas.
    r2 = client.post(f"/api/admin/cartas/{propuesta}/aprobar", headers=admin)
    assert r2.status_code == 409
    assert _total_cartas() == 78


def test_aprobar_firma_anonima_no_guarda_firma_publica(admin):
    autor_id = _crear_usuario("b13|autor-aprueba-anon", apodo="Lu")
    propuesta = _sembrar(autor_id, firma=FIRMA_ANONIMA)

    carta_id = client.post(f"/api/admin/cartas/{propuesta}/aprobar", headers=admin).json()["carta_id"]
    with SessionLocal() as s:
        c = s.get(Carta, carta_id)
        assert c.firma_publica is None          # "de alguien de la comunidad"
        assert c.autor_usuario_id == autor_id   # pero el impacto sigue siendo suyo
    assert _total_cartas() == 78


def test_aprobar_con_firma_apodo_sin_apodo_queda_anonima(admin):
    """Eligió firmar, pero nunca cargó apodo: no se inventa una firma."""
    autor_id = _crear_usuario("b13|autor-sin-apodo")
    propuesta = _sembrar(autor_id, firma=FIRMA_APODO)
    carta_id = client.post(f"/api/admin/cartas/{propuesta}/aprobar", headers=admin).json()["carta_id"]
    with SessionLocal() as s:
        assert s.get(Carta, carta_id).firma_publica is None


def test_aprobar_acepta_concepto_del_body_y_tiene_respaldo(admin):
    autor_id = _crear_usuario("b13|autor-concepto")

    # 1) Tomás escribe el concepto: manda el suyo.
    p1 = _sembrar(autor_id, concepto="el-del-juez")
    c1 = client.post(f"/api/admin/cartas/{p1}/aprobar", json={"concepto": "el-de-tomas"},
                     headers=admin).json()
    assert c1["concepto"] == "el-de-tomas"
    # 2) Sin body: queda el del juez.
    p2 = _sembrar(autor_id, concepto="el-del-juez")
    c2 = client.post(f"/api/admin/cartas/{p2}/aprobar", headers=admin).json()
    assert c2["concepto"] == "el-del-juez"
    # 3) Sin concepto por ningún lado: NUNCA se publica sin concepto (M2 lo usa
    #    para no repetir "lo mismo" dentro de la ventana semanal).
    p3 = _sembrar(autor_id, concepto=None)
    c3 = client.post(f"/api/admin/cartas/{p3}/aprobar", headers=admin).json()
    assert c3["concepto"] == "com-" + p3[:8]

    with SessionLocal() as s:
        for item, esperado in ((c1, "el-de-tomas"), (c2, "el-del-juez"), (c3, c3["concepto"])):
            assert s.get(Carta, item["carta_id"]).concepto == esperado
    assert _total_cartas() == 80


def test_aprobar_desde_en_revision_tambien_vale(admin):
    """Si el juez está apagado o colgado, Tomás puede decidir igual."""
    autor_id = _crear_usuario("b13|autor-en-revision")
    propuesta = _sembrar(autor_id, estado=ESTADO_EN_REVISION)
    assert client.post(f"/api/admin/cartas/{propuesta}/aprobar", headers=admin).status_code == 200


@pytest.mark.parametrize("estado", [ESTADO_A_REVISAR, ESTADO_RECHAZADA, ESTADO_RETIRADA])
def test_aprobar_desde_estado_invalido_es_409(admin, estado):
    autor_id = _crear_usuario(f"b13|autor-inv-{estado}")
    propuesta = _sembrar(autor_id, estado=estado)
    r = client.post(f"/api/admin/cartas/{propuesta}/aprobar", headers=admin)
    assert r.status_code == 409
    assert estado in r.json()["detail"]
    assert _total_cartas() == 77
    assert _avisos(autor_id) == []


def test_decidir_sobre_una_carta_inexistente_es_404(admin):
    for url, body in (
        ("/api/admin/cartas/no-existe/aprobar", None),
        ("/api/admin/cartas/no-existe/rechazar", {"motivo": "no"}),
        ("/api/admin/cartas/no-existe/a-revisar", {"sugerencia": "probá otra vez"}),
    ):
        r = client.post(url, json=body, headers=admin)
        assert r.status_code == 404, url


# ═══════════════════════════════════════════════════════════════════════════
# 4. Rechazar y a-revisar
# ═══════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize(
    "desde", [ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA, ESTADO_A_REVISAR]
)
def test_rechazar_desde_los_estados_validos(admin, desde):
    autor_id = _crear_usuario(f"b13|autor-rech-{desde}")
    propuesta = _sembrar(autor_id, estado=desde)

    item = client.post(
        f"/api/admin/cartas/{propuesta}/rechazar",
        json={"motivo": "  Se parece mucho a una carta que ya está en el mazo.  "},
        headers=admin,
    ).json()
    assert item["estado"] == ESTADO_RECHAZADA
    assert item["motivo"] == "Se parece mucho a una carta que ya está en el mazo."
    assert item["carta_id"] is None

    p = _estado_en_db(propuesta)
    assert p.estado == ESTADO_RECHAZADA and p.motivo.startswith("Se parece")
    assert _total_cartas() == 77  # rechazar NO toca el Mundo 1

    avisos = _avisos(autor_id)
    assert len(avisos) == 1 and avisos[0].referencia_id == propuesta


@pytest.mark.parametrize("estado", [ESTADO_APROBADA, ESTADO_RECHAZADA, ESTADO_RETIRADA])
def test_rechazar_desde_estado_invalido_es_409(admin, estado):
    autor_id = _crear_usuario(f"b13|autor-rech-inv-{estado}")
    propuesta = _sembrar(autor_id, estado=estado)
    assert client.post(
        f"/api/admin/cartas/{propuesta}/rechazar", json={"motivo": "no"}, headers=admin
    ).status_code == 409
    assert _avisos(autor_id) == []


def test_rechazar_exige_motivo(admin):
    autor_id = _crear_usuario("b13|autor-rech-vacio")
    propuesta = _sembrar(autor_id)
    for body in ({}, {"motivo": ""}, {"motivo": "   "}, {"motivo": "x" * 301}):
        r = client.post(f"/api/admin/cartas/{propuesta}/rechazar", json=body, headers=admin)
        assert r.status_code == 422, body
    assert _estado_en_db(propuesta).estado == ESTADO_REVISION_DWELLIA


def test_a_revisar_guarda_la_sugerencia_y_el_fix(admin):
    autor_id = _crear_usuario("b13|autor-retoque")
    propuesta = _sembrar(
        autor_id, veredicto={"veredicto": "requiere_revision", "hallazgos": ["R4.2"]}
    )

    item = client.post(
        f"/api/admin/cartas/{propuesta}/a-revisar",
        json={
            "sugerencia": "La frase promete un resultado; probá describir el gesto.",
            "fix": {"frase": "Mirá lo que ya estaba ahí.", "prompt": PROMPT_OK},
        },
        headers=admin,
    ).json()

    assert item["estado"] == ESTADO_A_REVISAR
    assert item["motivo"].startswith("La frase promete")
    # El veredicto del juez se conserva; se le SUMA el retoque de Dwellia.
    assert item["veredicto"]["hallazgos"] == ["R4.2"]
    assert item["veredicto"]["fuente"] == "dwellia"
    assert item["veredicto"]["fix_sugerido"] == {
        "frase": "Mirá lo que ya estaba ahí.", "prompt": PROMPT_OK,
    }

    p = _estado_en_db(propuesta)
    assert p.estado == ESTADO_A_REVISAR
    assert p.veredicto["fix_sugerido"]["frase"] == "Mirá lo que ya estaba ahí."
    assert _total_cartas() == 77

    avisos = _avisos(autor_id)
    assert len(avisos) == 1 and "retoque" in avisos[0].texto


def test_a_revisar_sin_fix_y_sin_veredicto_previo(admin):
    autor_id = _crear_usuario("b13|autor-retoque-pelado")
    propuesta = _sembrar(autor_id, estado=ESTADO_EN_REVISION, veredicto=None)
    item = client.post(
        f"/api/admin/cartas/{propuesta}/a-revisar",
        json={"sugerencia": "El prompt no invita a escribir en el diario."},
        headers=admin,
    ).json()
    assert item["veredicto"] == {"fix_sugerido": None, "fuente": "dwellia"}


@pytest.mark.parametrize(
    "estado", [ESTADO_A_REVISAR, ESTADO_APROBADA, ESTADO_RECHAZADA, ESTADO_RETIRADA]
)
def test_a_revisar_desde_estado_invalido_es_409(admin, estado):
    autor_id = _crear_usuario(f"b13|autor-rev-inv-{estado}")
    propuesta = _sembrar(autor_id, estado=estado)
    assert client.post(
        f"/api/admin/cartas/{propuesta}/a-revisar", json={"sugerencia": "dale otra vuelta"},
        headers=admin,
    ).status_code == 409
    assert _avisos(autor_id) == []


def test_a_revisar_exige_sugerencia(admin):
    autor_id = _crear_usuario("b13|autor-rev-vacio")
    propuesta = _sembrar(autor_id)
    for body in ({}, {"sugerencia": "  "}, {"sugerencia": "x" * 501}):
        assert client.post(
            f"/api/admin/cartas/{propuesta}/a-revisar", json=body, headers=admin
        ).status_code == 422, body


def test_el_recorrido_completo_retoque_y_despues_aprobada(admin):
    """a_revisar → (el autor reenvía, B1.1) en_revision → aprobada."""
    autor_id = _crear_usuario("b13|autor-recorrido", apodo="Lu")
    propuesta = _sembrar(autor_id, firma=FIRMA_APODO)

    client.post(f"/api/admin/cartas/{propuesta}/a-revisar",
                json={"sugerencia": "Acortá la frase."}, headers=admin)
    with SessionLocal() as s:  # el reenvío del autor (territorio de B1.1)
        p = s.get(CartaComunidad, propuesta)
        p.estado = ESTADO_EN_REVISION
        s.commit()

    item = client.post(f"/api/admin/cartas/{propuesta}/aprobar", headers=admin).json()
    assert item["estado"] == ESTADO_APROBADA and item["carta_id"]
    assert len(_avisos(autor_id)) == 2  # retoque + cargada
    assert _total_cartas() == 78


# ═══════════════════════════════════════════════════════════════════════════
# 5. Comentarios (feedback privado de las cartas)
# ═══════════════════════════════════════════════════════════════════════════
def _pausa_con_comentario(sub: str, comentario=None, estrellas=None) -> str:
    """Una entrega real por la API (carta del día + cierre). Devuelve el id."""
    h = _headers(sub)
    entrega = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    body = {"completada": True}
    if estrellas is not None:
        body["estrellas"] = estrellas
    if comentario is not None:
        body["comentario_carta"] = comentario
    r = client.put(f"/api/entregas/{entrega}/cierre", json=body, headers=h)
    assert r.status_code == 200, r.text
    return entrega


def _fechar(entrega_id: str, cuando: datetime) -> None:
    with SessionLocal() as s:
        e = s.get(Entrega, entrega_id)
        e.fecha = cuando
        s.commit()


def test_comentarios_orden_limite_y_sin_email(admin):
    ahora = datetime.now(timezone.utc)
    _crear_usuario("b13|coment-1", apodo="Lu", terminos=True)
    _crear_usuario("b13|coment-2", apodo="Nico", terminos=True)
    _crear_usuario("b13|coment-3", apodo="Sin", terminos=True)

    vieja = _pausa_con_comentario("b13|coment-1", "Me hubiese gustado algo más corto.", 2)
    nueva = _pausa_con_comentario("b13|coment-2", "Justo lo que necesitaba hoy.", 5)
    muda = _pausa_con_comentario("b13|coment-3", comentario=None, estrellas=4)
    _fechar(vieja, ahora - timedelta(hours=3))
    _fechar(nueva, ahora - timedelta(hours=1))
    _fechar(muda, ahora)  # la más nueva, pero sin comentario: no aparece

    datos = client.get("/api/admin/comentarios", headers=admin).json()
    assert [d["entrega_id"] for d in datos] == [nueva, vieja]

    primero = datos[0]
    assert set(primero) == {
        "entrega_id", "fecha", "estrellas", "comentario", "carta_id", "frase",
        "categoria", "apodo",
    }
    assert primero["comentario"] == "Justo lo que necesitaba hoy."
    assert primero["estrellas"] == 5
    assert primero["apodo"] == "Nico"
    assert primero["carta_id"] and primero["frase"] and primero["categoria"]

    # Es feedback ANÓNIMO para Dwellia: el email no viaja por ningún lado.
    crudo = json.dumps(datos)
    assert "@mindful.local" not in crudo
    assert "email" not in crudo

    # El límite recorta desde la más nueva.
    uno = client.get("/api/admin/comentarios?limit=1", headers=admin).json()
    assert [d["entrega_id"] for d in uno] == [nueva]

    # Y está acotado por contrato.
    assert client.get("/api/admin/comentarios?limit=0", headers=admin).status_code == 422
    assert client.get("/api/admin/comentarios?limit=501", headers=admin).status_code == 422


def test_comentarios_sin_apodo_no_rompe(admin):
    _crear_usuario("b13|coment-sin-apodo", terminos=True)
    _pausa_con_comentario("b13|coment-sin-apodo", "Esta no me llegó.", 1)
    datos = client.get("/api/admin/comentarios", headers=admin).json()
    assert len(datos) == 1 and datos[0]["apodo"] is None
