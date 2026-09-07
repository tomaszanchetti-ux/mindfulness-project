"""Q/A ADVERSARIAL de la card B2.1 (WS27) · Distribución + impacto + avisos + adminland.

No valida la card: intenta ROMPERLA. Lo que ya cubren `tests/test_b21_*.py`
(el historial feliz, la bandeja de avisos, el motor sirviendo la carta de la
comunidad, la forma del tablero) NO se repite: acá se ataca lo que quedó afuera.

Nombres de los tests, y qué significan:

  `test_ok_*`   → candado que aguanta. Queda como regresión.
  `test_bug_*`  → BUG real, con `@pytest.mark.xfail(strict=True)`: el test afirma
                  el comportamiento CORRECTO y hoy falla. Cuando alguien lo
                  arregle, el xfail estricto pasa a XPASS y rompe la suite.
  `test_nota_*` → comportamiento documentado y defendible hoy, que Tomás tiene
                  que confirmar como decisión de producto (no es un defecto).

Todo lo que este archivo escribe se borra al empezar Y al terminar cada test:
usuarios `qa21|…` y `demo|qa21…` (que arrastran en cascada entregas, avisos y
propuestas) y las cartas de la comunidad que ELLOS publicaron. El usuario
`demo|qa` de Tomás no se toca. El mazo tiene que volver siempre a 77.

Correr:
    cd apps/api && MINDFUL_DATABASE_URL=… \\
        .venv/bin/pytest -q -p no:warnings tests/test_qa_b21_adversarial.py
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, text

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
    Categoria,
    Entrega,
    Usuario,
)
from mindful_api.main import app
from mindful_api.services import juez as juez_mod
from mindful_api.services.juez import Veredicto
from mindful_api.services.plan import activar_premium

client = TestClient(app)
# Para los 500: sin esto TestClient re-levanta la excepción y no se ve el status.
client_500 = TestClient(app, raise_server_exceptions=False)

MARCA = "qa21|"
MARCA_DEMO = "demo|qa21"          # el usuario demo PROPIO del test del seed
PREFIJO_CARTA = "com-qa21-"

AUTOR = MARCA + "autor"
LECTOR = MARCA + "lector"
OTRO = MARCA + "otro"
ADMIN_SUB = MARCA + "admin"

PILAR = "gratitud"
ACCION = "contemplar"

FRASE_V1 = "Hoy el aire alcanza para empezar de nuevo."
PROMPT_V1 = (
    "Elige un momento del día de hoy que te haya sostenido y escríbelo en tu diario "
    "con el detalle más pequeño que recuerdes de él."
)
FRASE_V2 = "Lo que sostiene tu día casi nunca hace ruido."
PROMPT_V2 = (
    "Escribe en tu diario tres cosas que hoy te sostuvieron sin que las nombraras, "
    "y qué cambiaría si mañana le dieras las gracias en voz alta a una de ellas."
)
FRASE_V3 = "Alguien te sostuvo hoy sin decírtelo."
PROMPT_V3 = (
    "Escribe en tu diario el nombre de alguien que hoy te hizo más liviano el día "
    "sin proponérselo, y qué habrías hecho si esa persona no hubiera estado."
)
FRASE_V4 = "Queda algo tuyo en lo que hoy diste."
PROMPT_V4 = (
    "Escribe en tu diario una cosa que hoy hiciste por alguien sin esperar nada, y "
    "qué se te movió por dentro mientras la hacías, aunque nadie lo haya notado."
)


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


# ── Limpieza QUIRÚRGICA ──────────────────────────────────────────────────────
# Solo lo que escribió ESTE archivo: los usuarios `qa21|` / `demo|qa21`, las
# cartas que ellos publicaron (por autor o por prefijo) y nada más. El `demo|qa`
# de Tomás y sus 4 propuestas sembradas quedan intactos.
def _limpiar() -> None:
    with SessionLocal() as s:
        mios = select(Usuario.id).where(
            Usuario.firebase_uid.like(MARCA + "%")
            | Usuario.firebase_uid.like(MARCA_DEMO + "%")
        )
        # Las cartas que publicaron mis usuarios, ANTES de borrarlos: después el
        # `ondelete=SET NULL` del autor las dejaría huérfanas y sin marca.
        ids = list(s.scalars(
            select(Carta.id).where(
                Carta.origen != ORIGEN_DWELLIA,
                Carta.autor_usuario_id.in_(mios) | Carta.id.like(PREFIJO_CARTA + "%"),
            )
        ).all())
        # Primero los usuarios (la cascada se lleva entregas, avisos y propuestas,
        # que son lo que referencia a las cartas), después las cartas.
        s.execute(
            delete(Usuario).where(
                Usuario.firebase_uid.like(MARCA + "%")
                | Usuario.firebase_uid.like(MARCA_DEMO + "%")
            )
        )
        s.flush()
        if ids:
            s.execute(delete(Carta).where(Carta.id.in_(ids)))
        s.commit()


@pytest.fixture(autouse=True)
def limpio(monkeypatch):
    """Cada test arranca limpio y con el juez APAGADO: la propuesta no se mueve
    sola mientras el test la mira (el criterio del juez no es lo que se prueba)."""
    _limpiar()

    def evaluar(propuesta, mazo, categorias, acciones):
        return Veredicto(resultado="off")

    monkeypatch.setattr(juez_mod, "evaluar", evaluar)
    yield
    _limpiar()


@pytest.fixture
def admin(monkeypatch) -> dict:
    monkeypatch.setattr(settings, "admin_uids", ADMIN_SUB)
    return _headers(ADMIN_SUB)


# ── Siembra ──────────────────────────────────────────────────────────────────
def _usuario(sub: str, apodo=None, premium=False, terminos=True) -> str:
    with SessionLocal() as s:
        u = Usuario(
            firebase_uid=sub, email=f"{sub}@mindful.local", apodo=apodo,
            terminos_aceptados_at=datetime.now(timezone.utc) if terminos else None,
        )
        if premium:
            activar_premium(u, datetime.now(timezone.utc) + timedelta(days=365))
        s.add(u)
        s.commit()
        return u.id


def _premium(sub: str, apodo=None) -> dict:
    _usuario(sub, apodo=apodo, premium=True)
    return _headers(sub)


def _proponer(headers: dict, **cambios):
    cuerpo = {
        "categoria": PILAR, "accion": ACCION,
        "frase": FRASE_V1, "prompt": PROMPT_V1,
        "firma": FIRMA_ANONIMA, "cesion_aceptada": True,
    }
    cuerpo.update(cambios)
    return client.post("/api/cartas-comunidad", headers=headers, json=cuerpo)


def _a_revisar(propuesta_id: str) -> None:
    """Deja la propuesta lista para el reenvío, sin pasar por el juez."""
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        p.estado = ESTADO_A_REVISAR
        p.motivo = "Prueba con algo más concreto."
        s.add(p)
        s.commit()


def _reenviar(headers: dict, propuesta_id: str, frase: str, prompt: str, **extra):
    cuerpo = {"frase": frase, "prompt": prompt}
    cuerpo.update(extra)
    return client.put(f"/api/cartas-comunidad/{propuesta_id}",
                      headers=headers, json=cuerpo)


def _historial(propuesta_id: str) -> list:
    """El historial LEÍDO DE LA BASE: es lo único que prueba que la columna JSON
    se guardó de verdad (mutarla en su lugar no se guardaría, en silencio)."""
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        assert p is not None
        return list(p.historial or [])


def _publicar(autor_id, firma_publica=None, concepto=None, pilar=PILAR,
              accion=ACCION) -> str:
    """La carta de la comunidad YA en el mazo, como la deja `admin.aprobar`."""
    with SessionLocal() as s:
        carta = Carta(
            id=PREFIJO_CARTA + secrets.token_hex(4),
            categoria_slug=pilar, accion_slug=accion,
            concepto=concepto or ("qa21-" + secrets.token_hex(3)),
            frase=FRASE_V2, prompt=PROMPT_V2,
            origen=ORIGEN_COMUNIDAD,
            autor_usuario_id=autor_id,
            firma_publica=firma_publica,
        )
        s.add(carta)
        s.commit()
        return carta.id


def _propuesta_directa(usuario_id: str, estado=ESTADO_REVISION_DWELLIA,
                       carta_id=None, veredicto=None, historial=None,
                       concepto=None) -> str:
    """Una propuesta puesta A MANO (como la deja una migración o el demo-seed)."""
    with SessionLocal() as s:
        p = CartaComunidad(
            usuario_id=usuario_id, categoria_slug=PILAR, accion_slug=ACCION,
            frase=FRASE_V2, prompt=PROMPT_V2, firma=FIRMA_ANONIMA,
            estado=estado, carta_id=carta_id, veredicto=veredicto,
            historial=historial, concepto=concepto,
            cesion_aceptada_at=datetime.now(timezone.utc),
        )
        s.add(p)
        s.commit()
        return p.id


def _entrega(usuario_id: str, carta_id: str, dias_atras: int = 0,
             comentario=None, descartadas=None) -> str:
    with SessionLocal() as s:
        e = Entrega(
            usuario_id=usuario_id, carta_id=carta_id,
            fecha=datetime.now(timezone.utc) - timedelta(days=dias_atras),
            comentario_carta=comentario, descartadas=descartadas,
        )
        s.add(e)
        s.commit()
        return e.id


def _mazo() -> int:
    with SessionLocal() as s:
        return int(s.scalar(select(func.count()).select_from(Carta)) or 0)


# ═════════════════════════════════════════════════════════════════════════════
# 1 · EL HISTORIAL (la v1 del funnel)
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_cuatro_vueltas_guardan_la_redaccion_de_ENTONCES():
    """POST + 3 reenvíos → v1..v4 en orden, y cada versión conserva SU texto.

    Es el candado central del funnel: si `_sumar_redaccion` guardara una
    referencia (o si el reenvío pisara la vuelta anterior), las cuatro versiones
    dirían lo mismo — la última — y Tomás no vería de dónde viene la carta.
    """
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]

    vueltas = [
        (FRASE_V1, PROMPT_V1),
        (FRASE_V2, PROMPT_V2),
        (FRASE_V3, PROMPT_V3),
        (FRASE_V4, PROMPT_V4),
    ]
    for frase, prompt in vueltas[1:]:
        _a_revisar(pid)
        assert _reenviar(h, pid, frase, prompt).status_code == 200

    historial = _historial(pid)
    assert [v["version"] for v in historial] == [1, 2, 3, 4]
    assert [(v["frase"], v["prompt"]) for v in historial] == vueltas
    # Las fechas no retroceden: el funnel se lee de arriba abajo.
    fechas = [v["fecha"] for v in historial]
    assert fechas == sorted(fechas)


def test_ok_un_reenvio_rebotado_no_suma_version():
    """Un 422 del contrato (frase de 61) no puede dejar una vuelta fantasma."""
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    _a_revisar(pid)

    r = _reenviar(h, pid, "x" * 61, PROMPT_V2)
    assert r.status_code == 422
    assert [v["version"] for v in _historial(pid)] == [1]
    # Y el texto de la fila tampoco se movió.
    with SessionLocal() as s:
        assert s.get(CartaComunidad, pid).frase == FRASE_V1


@pytest.mark.parametrize("cuerpo", [
    {"frase": FRASE_V2, "prompt": "corto"},                       # prompt < 100
    {"frase": FRASE_V2, "prompt": PROMPT_V2, "categoria": "no-existe"},
    {"frase": FRASE_V2, "prompt": PROMPT_V2, "accion": "bailar"},
    {"frase": "​​​", "prompt": PROMPT_V2},         # solo invisibles
    {"frase": FRASE_V2, "prompt": PROMPT_V2, "firma": FIRMA_APODO},  # sin apodo
    {"prompt": PROMPT_V2},                                        # falta la frase
    {"frase": FRASE_V2},                                          # falta el prompt
])
def test_ok_ningun_reenvio_rebotado_deja_una_vuelta_fantasma(cuerpo):
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    _a_revisar(pid)
    r = client.put(f"/api/cartas-comunidad/{pid}", headers=h, json=cuerpo)
    assert r.status_code == 422, r.text
    assert [v["version"] for v in _historial(pid)] == [1]
    with SessionLocal() as s:
        p = s.get(CartaComunidad, pid)
        assert (p.frase, p.estado) == (FRASE_V1, ESTADO_A_REVISAR)


def test_ok_una_fila_con_historial_None_no_revienta_el_reenvio():
    """Fila anterior a `l2a3b4c5d6e7` (historial NULL): el reenvío numera igual."""
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    with SessionLocal() as s:
        p = s.get(CartaComunidad, pid)
        p.historial = None
        p.estado = ESTADO_A_REVISAR
        s.add(p)
        s.commit()

    assert _reenviar(h, pid, FRASE_V2, PROMPT_V2).status_code == 200
    historial = _historial(pid)
    assert len(historial) == 1
    assert historial[0]["frase"] == FRASE_V2


def test_nota_sin_historial_la_vuelta_siguiente_se_llama_v1():
    """Una fila vieja SIN historial arranca la numeración en 1, no en 2.

    NOTA de producto: `_sumar_redaccion` numera desde el máximo guardado y una
    fila NULL no guarda ninguno. Es lo único posible (no hay dato del que
    deducirlo), pero en el panel esa carta mostrará "v1" para una redacción que
    en realidad es la segunda. Solo afecta a las propuestas anteriores a la
    migración; hoy en la base de Tomás son 0.
    """
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    with SessionLocal() as s:
        p = s.get(CartaComunidad, pid)
        p.historial = None
        p.estado = ESTADO_A_REVISAR
        s.add(p)
        s.commit()
    _reenviar(h, pid, FRASE_V2, PROMPT_V2)
    assert _historial(pid)[0]["version"] == 1


def test_ok_un_cambio_de_pilar_en_el_reenvio_deja_las_dos_vueltas():
    h = _premium(AUTOR, apodo="Tomito")
    pid = _proponer(h, firma=FIRMA_ANONIMA).json()["id"]
    _a_revisar(pid)
    r = _reenviar(h, pid, FRASE_V2, PROMPT_V2,
                  categoria="vinculos", accion="hacer", firma=FIRMA_APODO)
    assert r.status_code == 200

    historial = _historial(pid)
    assert (historial[0]["categoria"], historial[0]["accion"],
            historial[0]["firma"]) == (PILAR, ACCION, FIRMA_ANONIMA)
    assert (historial[1]["categoria"], historial[1]["accion"],
            historial[1]["firma"]) == ("vinculos", "hacer", FIRMA_APODO)


def test_ok_el_historial_no_viaja_en_mias_y_si_en_el_panel(admin):
    """Contrato: `historial` es del ADMINLAND. El autor no lo recibe en `/mias`."""
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]

    mias = client.get("/api/cartas-comunidad/mias", headers=h).json()
    assert len(mias) == 1
    assert "historial" not in mias[0]

    panel = client.get("/api/admin/cartas?estado=todas", headers=admin).json()
    mia = [i for i in panel if i["id"] == pid][0]
    assert [v["version"] for v in mia["historial"]] == [1]


def test_ok_los_bordes_60_y_220_se_guardan_YA_STRIPPEADOS_en_el_historial():
    """El historial es la evidencia: tiene que decir lo que se guardó, no lo crudo."""
    h = _premium(AUTOR)
    frase = "a" * 60
    prompt = "Escribe en tu diario " + "b" * (220 - len("Escribe en tu diario "))
    assert len(prompt) == 220

    r = _proponer(h, frase="   " + frase + "  ", prompt="\n" + prompt + "\t")
    assert r.status_code == 201, r.text
    v1 = _historial(r.json()["id"])[0]
    assert v1["frase"] == frase and len(v1["frase"]) == 60
    assert v1["prompt"] == prompt and len(v1["prompt"]) == 220


def test_ok_el_reenvio_conserva_las_vueltas_aunque_el_juez_corra_despues():
    """`procesar_juez` reescribe `veredicto`, `estado` y `concepto`. No puede
    llevarse el historial por delante."""
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    _a_revisar(pid)
    _reenviar(h, pid, FRASE_V2, PROMPT_V2)

    from mindful_api.services.cartas_comunidad import procesar_juez

    procesar_juez(pid, evaluar=lambda *a: Veredicto(
        resultado="requiere_revision", motivo="Probemos otra vez.",
        concepto="gratitud-callada",
    ))
    assert [v["version"] for v in _historial(pid)] == [1, 2]


# ═════════════════════════════════════════════════════════════════════════════
# 2 · EL IMPACTO (`personas_acompanadas`)
# ═════════════════════════════════════════════════════════════════════════════
def _impacto(headers: dict) -> int:
    mias = client.get("/api/cartas-comunidad/mias", headers=headers).json()
    return mias[0]["personas_acompanadas"]


def test_ok_dos_usuarios_distintos_son_dos():
    h = _premium(AUTOR)
    autor_id = _uid(AUTOR)
    carta_id = _publicar(autor_id)
    _propuesta_directa(autor_id, estado=ESTADO_APROBADA, carta_id=carta_id)
    _entrega(_usuario(LECTOR), carta_id)
    _entrega(_usuario(OTRO), carta_id)
    assert _impacto(h) == 2


def test_ok_una_propuesta_sin_publicar_acompana_a_cero_aunque_haya_entregas():
    """La propuesta todavía no tiene `carta_id`: aunque exista una carta con el
    mismo texto en el mazo, el impacto es 0 (cuenta la carta, no el contenido)."""
    h = _premium(AUTOR)
    autor_id = _uid(AUTOR)
    carta_id = _publicar(autor_id)
    _propuesta_directa(autor_id, estado=ESTADO_REVISION_DWELLIA, carta_id=None)
    _entrega(_usuario(LECTOR), carta_id)
    assert _impacto(h) == 0


def test_ok_el_mismo_usuario_dos_dias_cuenta_UNA_persona():
    """`personas_acompanadas` cuenta PERSONAS distintas (corregido tras el Q/A):
    la ventana de 7 días no impide que la misma persona vuelva a recibir la carta
    más adelante, y el rótulo del front dice "N personas la recibieron"."""
    h = _premium(AUTOR)
    carta_id = _publicar(_uid(AUTOR))
    _propuesta_directa(_uid(AUTOR), estado=ESTADO_APROBADA, carta_id=carta_id)
    lector = _usuario(LECTOR)
    _entrega(lector, carta_id, dias_atras=0)
    _entrega(lector, carta_id, dias_atras=9)
    assert _impacto(h) == 1


def test_nota_una_entrega_descartada_no_cuenta():
    """Si el lector CAMBIÓ la carta, la vio pero no la vivió: impacto 0.

    NOTA: el motor sí la cuenta como "vista" (`historial_motor` mete las
    descartadas en las ventanas de 7 días), así que el mismo hecho vale como
    visto para el motor y como no-acompañado para el autor. Es defendible
    (acompañar ≠ aparecer), pero es una asimetría que conviene decidir a mano.
    """
    h = _premium(AUTOR)
    carta_id = _publicar(_uid(AUTOR))
    _propuesta_directa(_uid(AUTOR), estado=ESTADO_APROBADA, carta_id=carta_id)
    lector = _usuario(LECTOR)
    otra = _carta_dwellia_del_pilar()
    _entrega(lector, otra, descartadas=[carta_id])
    assert _impacto(h) == 0


def test_nota_si_el_lector_borra_su_Pausa_el_impacto_baja():
    """`DELETE /api/baul/{id}` se lleva la entrega y con ella el impacto.

    NOTA de producto: es coherente con "no queda rastro" (el Baúl es del lector),
    pero el número del autor puede BAJAR entre dos visitas a Crear sin que él
    haya hecho nada. Si el rótulo va a decir "acompañaste a N personas", conviene
    que Tomás sepa que N no es monótono.
    """
    h = _premium(AUTOR)
    autor_id = _uid(AUTOR)
    carta_id = _publicar(autor_id)
    _propuesta_directa(autor_id, estado=ESTADO_APROBADA, carta_id=carta_id)
    _usuario(LECTOR)
    entrega_id = _entrega(_uid(LECTOR), carta_id)
    assert _impacto(h) == 1

    assert client.delete(f"/api/baul/{entrega_id}",
                         headers=_headers(LECTOR)).status_code == 204
    assert _impacto(h) == 0


def test_ok_una_carta_publicada_y_despues_BORRADA_no_da_500():
    """El seed sincroniza el mazo y la suite lo limpia: una carta publicada puede
    desaparecer. `/mias` tiene que seguir respondiendo, con impacto 0."""
    h = _premium(AUTOR)
    carta_id = _publicar(_uid(AUTOR))
    _propuesta_directa(_uid(AUTOR), estado=ESTADO_APROBADA, carta_id=carta_id)
    with SessionLocal() as s:
        s.execute(delete(Carta).where(Carta.id == carta_id))
        s.commit()

    r = client_500.get("/api/cartas-comunidad/mias", headers=h)
    assert r.status_code == 200, r.text
    fila = r.json()[0]
    assert fila["personas_acompanadas"] == 0
    assert fila["estado"] == ESTADO_APROBADA
    # `carta_id` quedó en NULL (FK ondelete=SET NULL) y la carta se re-arma en
    # memoria desde la propuesta: el autor sigue viendo SU carta.
    assert fila["carta_id"] is None
    assert fila["carta"]["frase"] == FRASE_V2


def test_ok_el_panel_tampoco_se_cae_con_la_carta_borrada(admin):
    autor_id = _usuario(AUTOR, premium=True)
    carta_id = _publicar(autor_id)
    _propuesta_directa(autor_id, estado=ESTADO_APROBADA, carta_id=carta_id)
    with SessionLocal() as s:
        s.execute(delete(Carta).where(Carta.id == carta_id))
        s.commit()
    r = client_500.get("/api/admin/cartas?estado=todas", headers=admin)
    assert r.status_code == 200, r.text


# ═════════════════════════════════════════════════════════════════════════════
# 3 · DISTRIBUCIÓN SIN EXCLUSIONES (lo que `test_b21_distribucion` no toca)
# ═════════════════════════════════════════════════════════════════════════════
def _forzar_el_pilar(usuario_id: str) -> None:
    """El ÚNICO historial que deja salir `PILAR` con una sola carta fresca.

    (a) las 6 últimas entregas cubren los otros 5 pilares ⇒ la rotación 6+1 tiene
        que servir `PILAR`; (b) la entrega de hace 7 días carga en `descartadas`
        TODAS las cartas de Dwellia de ese pilar: entran a la ventana de "ya
        vistas" (7 días) pero quedan fuera de la de rotación (6 días), así que
        bloquean las cartas y no el pilar.
    """
    with SessionLocal() as s:
        dwellia = [
            c.id for c in s.scalars(
                select(Carta).where(Carta.categoria_slug == PILAR,
                                    Carta.origen == ORIGEN_DWELLIA)
            ).all()
        ]
        otros = sorted({c for c in s.scalars(select(Categoria.slug)).all()} - {PILAR})
        ahora = datetime.now(timezone.utc)
        entregas = []
        for i, dia in enumerate(range(7, 0, -1)):
            carta_id = s.scalar(
                select(Carta.id).where(Carta.categoria_slug == otros[i % len(otros)])
                .limit(1)
            )
            e = Entrega(usuario_id=usuario_id, carta_id=carta_id,
                        fecha=ahora - timedelta(days=dia))
            s.add(e)
            entregas.append(e)
        s.flush()
        entregas[0].descartadas = dwellia
        s.add(entregas[0])
        s.commit()


def test_ok_el_tercero_Y_el_autor_reciben_la_MISMA_carta_y_el_impacto_dice_2():
    """Sin exclusiones (WS27 §6) y el impacto contando lo que de verdad pasó.

    Une las dos mitades de la card: el motor reparte la carta de la comunidad a
    un tercero Y al propio autor, y `personas_acompanadas` cuenta las dos.
    """
    h_autor = _premium(AUTOR)
    autor_id = _uid(AUTOR)
    carta_id = _publicar(autor_id, firma_publica=None)
    _propuesta_directa(autor_id, estado=ESTADO_APROBADA, carta_id=carta_id)

    lector_id = _usuario(LECTOR)
    for uid, headers in ((lector_id, _headers(LECTOR)), (autor_id, h_autor)):
        _forzar_el_pilar(uid)
        r = client.get("/api/carta-del-dia", headers=headers)
        assert r.status_code == 200, r.text
        assert r.json()["carta"]["id"] == carta_id, (
            "el motor NO sirvió la carta de la comunidad siendo la única fresca "
            f"del pilar (sirvió {r.json()['carta']['id']})"
        )
        assert r.json()["carta"]["origen"] == ORIGEN_COMUNIDAD

    assert _impacto(h_autor) == 2


def test_ok_la_carta_servida_no_revela_el_id_del_autor():
    """El dorso dice "de <apodo>" o nada. `autor_usuario_id` es Mundo 2 y no sale
    nunca: sería atar una carta pública a una persona identificable."""
    _premium(LECTOR)
    autor_id = _usuario(AUTOR, apodo="Tomito")
    carta_id = _publicar(autor_id, firma_publica="Tomito")
    _entrega(_uid(LECTOR), carta_id)

    carta = client.get("/api/carta-del-dia", headers=_headers(LECTOR)).json()["carta"]
    assert set(carta) == {"id", "frase", "prompt", "categoria", "accion",
                          "origen", "firma_publica"}
    assert autor_id not in str(carta)
    assert carta["firma_publica"] == "Tomito"


def test_ok_cambiar_la_carta_puede_caer_en_una_de_la_comunidad():
    """A1.3 (premium) no filtra por origen: el reemplazo puede ser de la comunidad,
    y la carta rechazada queda registrada en `descartadas`."""
    h = _premium(LECTOR)
    lector = _uid(LECTOR)
    carta_com = _publicar(_usuario(AUTOR), concepto="qa21-unico-" + secrets.token_hex(2))

    with SessionLocal() as s:
        dwellia = [
            c.id for c in s.scalars(
                select(Carta).where(Carta.categoria_slug == PILAR,
                                    Carta.origen == ORIGEN_DWELLIA)
            ).all()
        ]
        actual = dwellia[0]
        e = Entrega(usuario_id=lector, carta_id=actual,
                    fecha=datetime.now(timezone.utc),
                    descartadas=dwellia[1:])   # el resto del pilar, ya fuera
        s.add(e)
        s.commit()
        entrega_id = e.id

    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["carta"]["id"] == carta_com
    assert r.json()["carta"]["origen"] == ORIGEN_COMUNIDAD

    with SessionLocal() as s:
        e = s.get(Entrega, entrega_id)
        assert actual in (e.descartadas or [])
        assert e.carta_id == carta_com


def test_ok_el_regalo_de_una_pausa_de_la_comunidad_muestra_origen_y_firma():
    """`/api/c/{token}` pasa por el MISMO `_carta_enriquecida`: si mañana alguien
    dejara de exponer `origen`/`firma_publica`, el regalo mentiría sobre quién la
    escribió."""
    h = _premium(LECTOR)
    lector = _uid(LECTOR)
    carta_com = _publicar(_usuario(AUTOR, apodo="Tomito"), firma_publica="Tomito")
    entrega_id = _entrega(lector, carta_com)

    r = client.post("/api/compartir", headers=h,
                    json={"entrega_id": entrega_id, "modo": "carta_sola"})
    assert r.status_code == 201, r.text
    token = r.json()["token"]

    receptor = _headers(OTRO)
    _usuario(OTRO)
    regalo = client.get(f"/api/c/{token}", headers=receptor)
    assert regalo.status_code == 200, regalo.text
    assert regalo.json()["carta"]["origen"] == ORIGEN_COMUNIDAD
    assert regalo.json()["carta"]["firma_publica"] == "Tomito"


def test_ok_una_carta_de_la_comunidad_anonima_llega_sin_firma_al_regalo():
    h = _premium(LECTOR)
    carta_com = _publicar(_usuario(AUTOR), firma_publica=None)
    entrega_id = _entrega(_uid(LECTOR), carta_com)
    token = client.post("/api/compartir", headers=h,
                        json={"entrega_id": entrega_id,
                              "modo": "carta_sola"}).json()["token"]
    _usuario(OTRO)
    regalo = client.get(f"/api/c/{token}", headers=_headers(OTRO)).json()
    assert regalo["carta"]["origen"] == ORIGEN_COMUNIDAD
    assert regalo["carta"]["firma_publica"] is None


# ═════════════════════════════════════════════════════════════════════════════
# 4 · AVISOS
# ═════════════════════════════════════════════════════════════════════════════
def _aviso(usuario_id: str, texto: str, cuando: datetime, referencia=None,
           leido=False) -> str:
    with SessionLocal() as s:
        a = Aviso(usuario_id=usuario_id, tipo=AVISO_CARTA_ESTADO,
                  referencia_id=referencia, texto=texto, leido=leido,
                  created_at=cuando)
        s.add(a)
        s.commit()
        return a.id


@pytest.mark.parametrize("limite", [0, -1, 201, 1000])
def test_ok_un_limite_fuera_de_rango_es_422(limite):
    _usuario(LECTOR)
    r = client.get(f"/api/avisos?limite={limite}", headers=_headers(LECTOR))
    assert r.status_code == 422


def test_ok_un_limite_que_no_es_numero_es_422():
    _usuario(LECTOR)
    r = client.get("/api/avisos?limite=muchos", headers=_headers(LECTOR))
    assert r.status_code == 422


def test_ok_el_orden_es_estable_con_created_at_IGUALES():
    """Dos avisos del mismo instante (una transición que dispara dos) tienen que
    salir siempre en el mismo orden: la campana no puede bailar entre recargas."""
    uid = _usuario(LECTOR)
    instante = datetime.now(timezone.utc)
    ids = [_aviso(uid, f"Aviso {i}", instante) for i in range(6)]

    lecturas = []
    for _ in range(4):
        r = client.get("/api/avisos", headers=_headers(LECTOR)).json()
        lecturas.append([a["id"] for a in r["avisos"]])
    assert all(l == lecturas[0] for l in lecturas)
    # Y el desempate es `id` descendente (lo que promete el servicio).
    assert lecturas[0] == sorted(ids, reverse=True)


def test_ok_un_aviso_de_una_propuesta_YA_RETIRADA_se_sigue_listando():
    """`referencia_id` no es una FK: el aviso es la memoria, no un espejo."""
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    uid = _uid(AUTOR)
    _aviso(uid, "Tu carta necesita un retoque.", datetime.now(timezone.utc),
           referencia=pid)
    client.delete(f"/api/cartas-comunidad/{pid}", headers=h)

    r = client_500.get("/api/avisos", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["avisos"][0]["referencia_id"] == pid
    with SessionLocal() as s:
        assert s.get(CartaComunidad, pid).estado == ESTADO_RETIRADA


def test_ok_un_aviso_con_referencia_INEXISTENTE_no_rompe_la_bandeja():
    uid = _usuario(LECTOR)
    _aviso(uid, "Aviso huérfano", datetime.now(timezone.utc),
           referencia="no-existe-esta-propuesta")
    r = client_500.get("/api/avisos", headers=_headers(LECTOR))
    assert r.status_code == 200, r.text
    assert r.json()["avisos"][0]["referencia_id"] == "no-existe-esta-propuesta"


def test_ok_marcar_un_aviso_ajeno_es_404_y_no_lo_marca():
    a_id = _aviso(_usuario(AUTOR), "Mío", datetime.now(timezone.utc))
    _usuario(OTRO)
    r = client.put(f"/api/avisos/{a_id}/leido", headers=_headers(OTRO))
    assert r.status_code == 404
    with SessionLocal() as s:
        assert s.get(Aviso, a_id).leido is False


def test_ok_put_leidos_de_uno_no_toca_al_otro_ni_su_contador():
    a_id = _aviso(_usuario(AUTOR), "Mío", datetime.now(timezone.utc))
    b_id = _aviso(_usuario(OTRO), "Suyo", datetime.now(timezone.utc))
    r = client.put("/api/avisos/leidos", headers=_headers(AUTOR))
    assert r.json() == {"marcados": 1, "no_leidos": 0}
    assert client.get("/api/avisos", headers=_headers(OTRO)).json()["no_leidos"] == 1
    with SessionLocal() as s:
        assert s.get(Aviso, a_id).leido is True
        assert s.get(Aviso, b_id).leido is False


def test_ok_marcar_todos_dos_veces_es_idempotente():
    uid = _usuario(LECTOR)
    _aviso(uid, "Uno", datetime.now(timezone.utc))
    h = _headers(LECTOR)
    assert client.put("/api/avisos/leidos", headers=h).json()["marcados"] == 1
    assert client.put("/api/avisos/leidos", headers=h).json()["marcados"] == 0
    assert client.get("/api/avisos", headers=h).json()["no_leidos"] == 0


def test_ok_marcar_uno_dos_veces_devuelve_lo_mismo():
    a_id = _aviso(_usuario(LECTOR), "Uno", datetime.now(timezone.utc))
    h = _headers(LECTOR)
    primero = client.put(f"/api/avisos/{a_id}/leido", headers=h).json()
    segundo = client.put(f"/api/avisos/{a_id}/leido", headers=h).json()
    assert primero["leido"] is True and segundo["leido"] is True
    assert primero["id"] == segundo["id"] == a_id


def test_ok_el_contador_cuenta_TODO_aunque_la_lista_se_recorte():
    uid = _usuario(LECTOR)
    ahora = datetime.now(timezone.utc)
    for i in range(12):
        _aviso(uid, f"Aviso {i}", ahora - timedelta(minutes=i))
    r = client.get("/api/avisos?limite=3", headers=_headers(LECTOR)).json()
    assert len(r["avisos"]) == 3
    assert r["no_leidos"] == 12


def test_ok_la_lista_de_avisos_no_delata_el_usuario_id():
    uid = _usuario(LECTOR)
    _aviso(uid, "Uno", datetime.now(timezone.utc))
    fila = client.get("/api/avisos", headers=_headers(LECTOR)).json()["avisos"][0]
    assert set(fila) == {"id", "tipo", "referencia_id", "texto", "leido", "created_at"}
    assert uid not in str(fila)


# ═════════════════════════════════════════════════════════════════════════════
# 5 · EL RESUMEN DEL ADMINLAND
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_los_conteos_por_pilar_suman_el_total(admin):
    autor = _usuario(AUTOR, premium=True)
    _publicar(autor, pilar="gratitud")
    _publicar(autor, pilar="vinculos", accion="hacer")

    cartas = client.get("/api/admin/resumen", headers=admin).json()["cartas"]
    assert sum(p["total"] for p in cartas["por_pilar"]) == cartas["total"]
    assert sum(p["dwellia"] for p in cartas["por_pilar"]) == cartas["dwellia"]
    assert sum(p["comunidad"] for p in cartas["por_pilar"]) == cartas["comunidad"]
    assert cartas["dwellia"] + cartas["comunidad"] == cartas["total"]
    assert cartas["comunidad"] == 2
    por_slug = {p["slug"]: p for p in cartas["por_pilar"]}
    assert por_slug["gratitud"]["comunidad"] == 1
    assert por_slug["vinculos"]["comunidad"] == 1
    assert por_slug["sentido"]["comunidad"] == 0


def test_ok_crearon_mas_sin_cartas_es_el_total(admin):
    autor = _usuario(AUTOR, premium=True)
    _usuario(LECTOR)
    _propuesta_directa(autor)
    u = client.get("/api/admin/resumen", headers=admin).json()["usuarios"]
    assert u["crearon_cartas"] + u["sin_cartas"] == u["total"]
    assert u["premium"] + u["free"] == u["total"]


def test_ok_con_onboarding_es_exactamente_los_terminos_aceptados(admin):
    _usuario(AUTOR, terminos=True)
    _usuario(LECTOR, terminos=False)
    resumen = client.get("/api/admin/resumen", headers=admin).json()["usuarios"]
    with SessionLocal() as s:
        esperado = int(s.scalar(
            select(func.count()).select_from(Usuario)
            .where(Usuario.terminos_aceptados_at.is_not(None))
        ) or 0)
    assert resumen["con_onboarding"] == esperado
    assert resumen["con_onboarding"] < resumen["total"]


def test_ok_los_comentarios_de_hace_8_dias_quedan_afuera_y_los_de_6_adentro(admin):
    lector = _usuario(LECTOR)
    carta = _carta_dwellia_del_pilar()
    antes = client.get("/api/admin/resumen", headers=admin).json()["comentarios"]

    _entrega(lector, carta, dias_atras=6, comentario="Adentro de la semana.")
    _entrega(lector, carta, dias_atras=8, comentario="Afuera de la semana.")

    despues = client.get("/api/admin/resumen", headers=admin).json()["comentarios"]
    assert despues["total"] == antes["total"] + 2
    assert despues["ultimos_7_dias"] == antes["ultimos_7_dias"] + 1


def test_ok_una_pausa_sin_comentario_no_cuenta(admin):
    lector = _usuario(LECTOR)
    antes = client.get("/api/admin/resumen", headers=admin).json()["comentarios"]
    _entrega(lector, _carta_dwellia_del_pilar(), dias_atras=1)
    despues = client.get("/api/admin/resumen", headers=admin).json()["comentarios"]
    assert despues == antes


def test_nota_una_propuesta_RETIRADA_cuenta_como_creo_cartas(admin):
    """`crearon_cartas` cuenta a quien tiene CUALQUIER propuesta, incluso una que
    retiró y otra que le rechazaron.

    NOTA de producto: es defendible (sí escribió), pero el rótulo del tablero
    dirá "cuánta gente escribe" y esa persona hoy no tiene ninguna carta viva.
    Si Tomás quiere medir participación real hay que excluir `retirada`.
    """
    autor = _usuario(AUTOR, premium=True)
    _propuesta_directa(autor, estado=ESTADO_RETIRADA)
    u = client.get("/api/admin/resumen", headers=admin).json()["usuarios"]
    assert u["crearon_cartas"] >= 1


def test_ok_pendientes_es_en_revision_mas_revision_dwellia_y_coincide(admin):
    autor = _usuario(AUTOR, premium=True)
    _propuesta_directa(autor, estado=ESTADO_EN_REVISION)
    _propuesta_directa(autor, estado=ESTADO_REVISION_DWELLIA)
    _propuesta_directa(autor, estado=ESTADO_RECHAZADA)

    p = client.get("/api/admin/resumen", headers=admin).json()["propuestas"]
    assert p["pendientes"] == p[ESTADO_EN_REVISION] + p[ESTADO_REVISION_DWELLIA]
    bandeja = client.get("/api/admin/cartas?estado=pendientes", headers=admin).json()
    assert len(bandeja) == p["pendientes"]


def test_ok_el_resumen_NO_expone_emails_ni_ids_de_usuarios(admin):
    """El tablero es del sistema. Un email o un uuid ahí adentro sería una fuga
    de Mundo 2 por la puerta de las métricas."""
    autor = _usuario(AUTOR, premium=True, apodo="Tomito")
    _publicar(autor)
    _propuesta_directa(autor)
    _entrega(autor, _carta_dwellia_del_pilar(), comentario="Hola.")

    crudo = client.get("/api/admin/resumen", headers=admin).text
    assert "@" not in crudo
    assert autor not in crudo          # el uuid del usuario
    assert "Tomito" not in crudo
    assert AUTOR not in crudo          # el firebase_uid
    # Y todo lo que hay son números (o los slugs/nombres de los 6 pilares).
    resumen = client.get("/api/admin/resumen", headers=admin).json()
    assert set(resumen) == {"cartas", "propuestas", "usuarios", "comentarios"}
    assert all(isinstance(v, int) for v in resumen["usuarios"].values())
    assert all(isinstance(v, int) for v in resumen["propuestas"].values())


def test_ok_sin_admin_uids_el_tablero_y_la_bandeja_estan_cerrados(monkeypatch):
    monkeypatch.setattr(settings, "admin_uids", "")
    _usuario(ADMIN_SUB)
    for url in ("/api/admin/resumen", "/api/admin/cartas", "/api/admin/comentarios"):
        assert client.get(url, headers=_headers(ADMIN_SUB)).status_code == 403


# ═════════════════════════════════════════════════════════════════════════════
# 6 · `veredicto_resumen` (la v2 del funnel, masticada)
# ═════════════════════════════════════════════════════════════════════════════
def _resumen_de(admin: dict, pid: str) -> dict:
    panel = client.get("/api/admin/cartas?estado=todas", headers=admin).json()
    return [i for i in panel if i["id"] == pid][0]


def test_ok_sin_veredicto_el_resumen_es_None(admin):
    autor = _usuario(AUTOR, premium=True)
    pid = _propuesta_directa(autor, veredicto=None)
    assert _resumen_de(admin, pid)["veredicto_resumen"] is None


def test_ok_un_veredicto_vacio_tambien_es_None(admin):
    autor = _usuario(AUTOR, premium=True)
    pid = _propuesta_directa(autor, veredicto={})
    assert _resumen_de(admin, pid)["veredicto_resumen"] is None


def _volver_a_en_revision(pid: str) -> None:
    """El POST ya corrió el juez en background (`BackgroundTasks` sí se ejecuta
    con `TestClient`), así que la propuesta salió de `en_revision` y `procesar_juez`
    no volvería a opinar. Se la devuelve al estado en que el juez decide."""
    with SessionLocal() as s:
        p = s.get(CartaComunidad, pid)
        p.estado = ESTADO_EN_REVISION
        p.veredicto = None
        s.add(p)
        s.commit()


def test_ok_el_juez_APAGADO_deja_algo_legible(admin):
    """Sin key el juez responde `off`: el panel tiene que decirlo, no quedar mudo."""
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    from mindful_api.services.cartas_comunidad import procesar_juez

    _volver_a_en_revision(pid)
    procesar_juez(pid, evaluar=lambda *a: Veredicto(resultado="off"))
    resumen = _resumen_de(admin, pid)["veredicto_resumen"]
    assert resumen["resultado"] == "off"
    assert resumen["fuente"] == "juez"
    assert resumen["fix"] is None
    with SessionLocal() as s:
        assert s.get(CartaComunidad, pid).estado == ESTADO_REVISION_DWELLIA


def test_ok_un_juez_CAIDO_deja_el_motivo_del_sistema(admin):
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    from mindful_api.services.cartas_comunidad import MOTIVO_JUEZ_CAIDO, procesar_juez

    def explota(*a):
        raise RuntimeError("la API no responde")

    _volver_a_en_revision(pid)
    procesar_juez(pid, evaluar=explota)
    resumen = _resumen_de(admin, pid)["veredicto_resumen"]
    assert resumen["resultado"] == "off"
    assert resumen["motivo"] == MOTIVO_JUEZ_CAIDO


def test_ok_una_sugerencia_de_dwellia_dice_que_es_de_dwellia(admin):
    autor = _usuario(AUTOR, premium=True)
    pid = _propuesta_directa(autor, veredicto={
        "resultado": "aprueba", "hallazgos": [], "fuente": "juez",
    })
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "Bajá un cambio con la primera línea."})
    assert r.status_code == 200, r.text
    assert r.json()["veredicto_resumen"]["fuente"] == "dwellia"


@pytest.mark.parametrize("fix,esperado", [
    ({"frase": "Hoy alcanza con lo que ya está."},
     {"frase": "Hoy alcanza con lo que ya está.", "prompt": None}),
    ({"prompt": PROMPT_V2}, {"frase": None, "prompt": PROMPT_V2}),
])
def test_ok_un_fix_PARCIAL_viaja_canonizado(admin, fix, esperado):
    autor = _usuario(AUTOR, premium=True)
    pid = _propuesta_directa(autor)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "Una sola cosa.", "fix": fix})
    assert r.status_code == 200, r.text
    assert r.json()["veredicto_resumen"]["fix"] == esperado


def test_ok_un_fix_VACIO_no_dibuja_una_caja_en_blanco(admin):
    autor = _usuario(AUTOR, premium=True)
    pid = _propuesta_directa(autor)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "Una sola cosa.",
                          "fix": {"frase": "   ", "prompt": None}})
    assert r.status_code == 200, r.text
    assert r.json()["veredicto_resumen"]["fix"] is None


def test_ok_hallazgos_cuenta_las_reglas_marcadas(admin):
    autor = _usuario(AUTOR, premium=True)
    pid = _propuesta_directa(autor, veredicto={
        "resultado": "requiere_revision", "fuente": "juez",
        "hallazgos": [{"regla": "R1.2", "mayor": True},
                      {"regla": "R7", "mayor": False}],
    })
    assert _resumen_de(admin, pid)["veredicto_resumen"]["hallazgos"] == 2


def test_ok_un_veredicto_solo_con_anterior_no_inventa_un_resumen(admin):
    """Al reenviar, `veredicto` queda como `{"anterior": {...}}`: todavía no hay
    nada nuevo que dijera el juez, así que el panel no debe dibujar la columna."""
    h = _premium(AUTOR)
    pid = _proponer(h).json()["id"]
    with SessionLocal() as s:
        p = s.get(CartaComunidad, pid)
        p.veredicto = {"anterior": {"resultado": "requiere_revision"}}
        s.add(p)
        s.commit()
    assert _resumen_de(admin, pid)["veredicto_resumen"] is None


def test_ok_un_estado_de_filtro_vacio_o_en_mayusculas_es_422(admin):
    for valor in ("", "TODAS", "Pendientes", "aprobadas"):
        r = client.get(f"/api/admin/cartas?estado={valor}", headers=admin)
        assert r.status_code == 422, valor


# ═════════════════════════════════════════════════════════════════════════════
# 6 bis · LOS BUGS
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_no_hay_metricas_por_usuario_en_el_adminland(admin):
    """Decisión de Tomás (WS27, al definir el adminland): NADA por usuario individual.

    El termómetro es general (usuarios totales, premium, gratis, cuántos crearon
    cartas). Si algún día hace falta una vista por usuario, se decide aparte.
    El roadmap quedó alineado con esto en la misma sesión.
    """
    assert client.get("/api/admin/usuarios", headers=admin).status_code == 404


def test_bug_un_hallazgos_que_no_es_lista_tumba_la_bandeja_entera(admin):
    autor = _usuario(AUTOR, premium=True)
    sano = _propuesta_directa(autor, veredicto={
        "resultado": "aprueba", "hallazgos": [], "fuente": "juez"})
    texto = _propuesta_directa(autor, veredicto={
        "resultado": "requiere_revision", "hallazgos": "R1.2", "fuente": "juez"})
    numero = _propuesta_directa(autor, veredicto={
        "resultado": "rechaza", "hallazgos": 7, "fuente": "juez"})

    r = client_500.get("/api/admin/cartas?estado=todas", headers=admin)
    assert r.status_code == 200, "un veredicto raro no puede tumbar la bandeja"
    por_id = {i["id"]: i for i in r.json()}
    assert por_id[sano]["veredicto_resumen"]["hallazgos"] == 0
    # "R1.2" es UN hallazgo mal guardado, no cuatro caracteres.
    assert por_id[texto]["veredicto_resumen"]["hallazgos"] == 1
    assert por_id[numero]["veredicto_resumen"]["hallazgos"] == 0


def test_bug_un_historial_que_no_es_lista_tumba_la_bandeja_entera(admin):
    autor = _usuario(AUTOR, premium=True)
    diccionario = _propuesta_directa(autor, historial={"version": 1, "frase": "x"})
    numero = _propuesta_directa(autor, historial=5)

    r = client_500.get("/api/admin/cartas?estado=todas", headers=admin)
    assert r.status_code == 200, "un historial raro no puede tumbar la bandeja"
    por_id = {i["id"]: i for i in r.json()}
    # Lo que no es una lista de redacciones se ignora: el funnel queda vacío,
    # nunca lleno de basura.
    assert por_id[diccionario]["historial"] == []
    assert por_id[numero]["historial"] == []


def test_bug_a_revisar_revienta_si_el_veredicto_no_es_un_dict(admin):
    autor = _usuario(AUTOR, premium=True)
    pid = _propuesta_directa(autor, veredicto=["lo", "que", "sea"])
    r = client_500.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                        json={"sugerencia": "Probemos con algo más chico."})
    assert r.status_code == 200, r.text
    with SessionLocal() as s:
        assert s.get(CartaComunidad, pid).estado == ESTADO_A_REVISAR


# ═════════════════════════════════════════════════════════════════════════════
# 7 · `es_admin` (lo que dibuja —o esconde— la pestaña /admin del front)
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_con_admin_uids_vacio_nadie_es_admin(monkeypatch):
    monkeypatch.setattr(settings, "admin_uids", "")
    _usuario(ADMIN_SUB)
    _usuario(AUTOR)
    for sub in (ADMIN_SUB, AUTOR):
        assert client.get("/api/perfil", headers=_headers(sub)).json()["es_admin"] is False


def test_ok_es_admin_cambia_EN_CALIENTE_sin_reiniciar(monkeypatch):
    _usuario(AUTOR)
    h = _headers(AUTOR)
    monkeypatch.setattr(settings, "admin_uids", "")
    assert client.get("/api/perfil", headers=h).json()["es_admin"] is False
    monkeypatch.setattr(settings, "admin_uids", f"otro|uid,{AUTOR}, tercero|uid ")
    assert client.get("/api/perfil", headers=h).json()["es_admin"] is True
    assert client.get("/api/admin/resumen", headers=h).status_code == 200
    monkeypatch.setattr(settings, "admin_uids", "otro|uid")
    assert client.get("/api/perfil", headers=h).json()["es_admin"] is False
    assert client.get("/api/admin/resumen", headers=h).status_code == 403


def test_ok_es_admin_no_se_contagia_por_prefijo(monkeypatch):
    """`qa21|admin-falso` no es `qa21|admin`: la lista se compara ENTERA."""
    monkeypatch.setattr(settings, "admin_uids", ADMIN_SUB)
    _usuario(ADMIN_SUB + "-falso")
    h = _headers(ADMIN_SUB + "-falso")
    assert client.get("/api/perfil", headers=h).json()["es_admin"] is False
    assert client.get("/api/admin/resumen", headers=h).status_code == 403


def test_nota_en_dev_el_usuario_por_defecto_es_admin_si_esta_declarado(monkeypatch):
    """RIESGO ya anotado por el Q/A de B1.3, verificado otra vez desde B2.1.

    En `auth_mode=dev` una request SIN headers se resuelve como `dev|user`. Si
    `MINDFUL_ADMIN_UIDS` contiene `dev|user`, cualquiera que llegue a esa API
    entra al adminland sin identificarse. En producción `auth_mode=firebase` y la
    lista es el uid de Google de Tomás, así que hoy no aplica; el candado es no
    poner nunca `dev|user` en `MINDFUL_ADMIN_UIDS`.
    """
    monkeypatch.setattr(settings, "admin_uids", "dev|user")
    assert client.get("/api/perfil").json()["es_admin"] is True
    assert client.get("/api/admin/resumen").status_code == 200
    with SessionLocal() as s:      # no dejar rastro del usuario de rebote
        s.execute(delete(Usuario).where(Usuario.firebase_uid == "dev|user"))
        s.commit()


# ═════════════════════════════════════════════════════════════════════════════
# 8 · LA MIGRACIÓN `l2a3b4c5d6e7`
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_la_columna_recibe_comunidad_ya_no_existe():
    """Sin interruptor (WS27 §6): una columna que nadie lee es una promesa que
    nadie cumple. Se pregunta a la BASE, no al modelo."""
    with SessionLocal() as s:
        columnas = {
            r[0] for r in s.execute(text(
                "select column_name from information_schema.columns "
                "where table_name = 'usuarios'"
            )).all()
        }
    assert "recibe_comunidad" not in columnas
    assert {"plan", "plan_hasta", "apodo"} <= columnas


def test_ok_la_columna_historial_si_existe_y_es_json():
    with SessionLocal() as s:
        fila = s.execute(text(
            "select data_type, is_nullable from information_schema.columns "
            "where table_name = 'cartas_comunidad' and column_name = 'historial'"
        )).first()
    assert fila is not None, "falta cartas_comunidad.historial"
    assert fila[0] == "json"
    assert fila[1] == "YES"


def test_ok_la_base_esta_en_la_cabeza_de_la_migracion():
    with SessionLocal() as s:
        assert s.scalar(text("select version_num from alembic_version")) == "l2a3b4c5d6e7"


def test_ok_put_perfil_con_recibe_comunidad_se_ignora_sin_500():
    """El front viejo (o un cliente cacheado) todavía puede mandar el interruptor."""
    _usuario(AUTOR)
    r = client_500.put("/api/perfil", headers=_headers(AUTOR),
                       json={"apodo": "Tomito", "recibe_comunidad": True})
    assert r.status_code == 200, r.text
    assert r.json()["apodo"] == "Tomito"
    assert "recibe_comunidad" not in r.json()


# ═════════════════════════════════════════════════════════════════════════════
# 9 · EL SEED DE Q/A (`make demo-seed`)
# ═════════════════════════════════════════════════════════════════════════════
def _contar(sql: str) -> int:
    with SessionLocal() as s:
        return int(s.scalar(text(sql)) or 0)


def test_ok_el_seed_ABORTA_en_modo_firebase_sin_tocar_la_base(monkeypatch):
    """Sembrar Pausas falsas en producción sería mentirle al usuario sobre su
    propia historia. El candado tiene que morder ANTES de abrir una sesión."""
    from mindful_api import demo_seed

    antes = (_contar("select count(*) from cartas_comunidad"),
             _contar("select count(*) from cartas"),
             _contar("select count(*) from avisos"),
             _contar("select count(*) from entregas"))

    monkeypatch.setattr(settings, "auth_mode", "firebase")
    with pytest.raises(SystemExit) as exc:
        demo_seed.sembrar()
    assert "SOLO local" in str(exc.value)

    despues = (_contar("select count(*) from cartas_comunidad"),
               _contar("select count(*) from cartas"),
               _contar("select count(*) from avisos"),
               _contar("select count(*) from entregas"))
    assert despues == antes


def test_ok_sembrar_comunidad_dos_veces_no_duplica_nada():
    """Idempotencia por la marca `demo-seed-` en `concepto`. Se corre sobre un
    usuario demo PROPIO del test (`demo|qa21`), nunca sobre el de Tomás."""
    from mindful_api import demo_seed

    sub = MARCA_DEMO + "|uno"
    with SessionLocal() as s:
        u = Usuario(firebase_uid=sub, email=f"{sub}@mindful.local", apodo="Qa21",
                    terminos_aceptados_at=datetime.now(timezone.utc))
        s.add(u)
        s.commit()
        uid = u.id

    def _cuantas() -> tuple:
        with SessionLocal() as s:
            propuestas = int(s.scalar(
                select(func.count()).select_from(CartaComunidad)
                .where(CartaComunidad.usuario_id == uid)
                .where(CartaComunidad.concepto.like(demo_seed.MARCA_CC + "%"))
            ) or 0)
            avisos = int(s.scalar(
                select(func.count()).select_from(Aviso)
                .where(Aviso.usuario_id == uid)
            ) or 0)
            cartas = int(s.scalar(
                select(func.count()).select_from(Carta)
                .where(Carta.autor_usuario_id == uid)
            ) or 0)
        return propuestas, avisos, cartas

    with SessionLocal() as s:
        primera = demo_seed.sembrar_comunidad(s, s.get(Usuario, uid))
    assert primera["propuestas"] == 4
    assert primera["saltado"] is False
    tras_una = _cuantas()
    assert tras_una == (4, 3, 1)     # 4 propuestas · 3 avisos · 1 carta publicada

    with SessionLocal() as s:
        segunda = demo_seed.sembrar_comunidad(s, s.get(Usuario, uid))
    assert segunda["saltado"] is True
    assert _cuantas() == tras_una


def test_ok_las_cartas_del_seed_cumplen_el_contrato_del_mazo():
    """Frase ≤60, prompt 100-220 y la palabra "diario" (R3.1 del canon): el panel
    los vuelve a medir al aprobar, así que una sembrada fuera de rango le daría
    un 422 a Tomás en pleno Q/A."""
    from mindful_api.demo_seed import CARTAS_COMUNIDAD
    from mindful_api.services.cartas_comunidad import FRASE_MAX, PROMPT_MAX, PROMPT_MIN

    assert len(CARTAS_COMUNIDAD) == 4
    for (clave, estado, categoria, accion, frase, prompt, _m, _v,
         anteriores, _d) in CARTAS_COMUNIDAD:
        assert len(frase.strip()) <= FRASE_MAX, clave
        assert PROMPT_MIN <= len(prompt.strip()) <= PROMPT_MAX, clave
        assert "diario" in prompt.lower(), clave
        for (f, p) in anteriores:                 # también las vueltas viejas
            assert len(f.strip()) <= FRASE_MAX, clave
            assert PROMPT_MIN <= len(p.strip()) <= PROMPT_MAX, clave


def test_ok_el_seed_pone_los_cuatro_estados_visibles_y_una_sola_sin_leer():
    from mindful_api.demo_seed import CARTAS_COMUNIDAD

    estados = {fila[1] for fila in CARTAS_COMUNIDAD}
    assert estados == {ESTADO_REVISION_DWELLIA, ESTADO_A_REVISAR,
                       ESTADO_RECHAZADA, ESTADO_APROBADA}


# ═════════════════════════════════════════════════════════════════════════════
# 10 · El mazo vuelve a 77
# ═════════════════════════════════════════════════════════════════════════════
def test_zzz_el_mazo_queda_en_77():
    assert _mazo() == 77
    with SessionLocal() as s:
        assert int(s.scalar(
            select(func.count()).select_from(Carta)
            .where(Carta.origen != ORIGEN_DWELLIA)
        ) or 0) == 0


# ── utilidades que usan varios bloques ───────────────────────────────────────
def _uid(sub: str) -> str:
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
        assert u is not None, f"no existe el usuario {sub}"
        return u.id


def _carta_dwellia_del_pilar() -> str:
    with SessionLocal() as s:
        return s.scalar(
            select(Carta.id)
            .where(Carta.categoria_slug == PILAR, Carta.origen == ORIGEN_DWELLIA)
            .order_by(Carta.id).limit(1)
        )
