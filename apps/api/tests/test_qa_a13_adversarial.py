"""Q/A ADVERSARIAL de la card A1.3 (WS24) · cambiar la carta del día.

No valida la card: intenta ROMPERLA. Cada test lleva el veredicto en el nombre
(`test_ok_*` = candado que aguanta, `test_reparo_*` = comportamiento defendible
pero desalineado con el docstring o con lo que el front necesita).

Los hallazgos B1, B2, R1, R2, R4 y R7 YA ESTÁN CORREGIDOS: sus tests se
invirtieron (afirman el comportamiento bueno) y perdieron el `bug`/`reparo` del
nombre — son los candados de la corrección. Siguen abiertos, como deuda
registrada, los dos `test_reparo_*` del final: R3 (la carta descartada es
invisible para las ventanas de 7 días) y R5 (mover la zona horaria al este
congela la entrega de hoy).

Se ejecuta aparte de la suite (`qa_*`, no `test_*` de archivo) para no ensuciar
el CI ajeno: `.venv/bin/python -m pytest -q -p no:warnings tests/qa_a13_adversarial.py`
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Entrega as EntregaDB
from mindful_api.db.models import Usuario
from mindful_api.main import app
from mindful_api.services.seleccion import (
    CASTIGO_MISMA_ACCION,
    EJE_MOVIMIENTO,
    EJE_QUIETUD,
    Entrega,
    Perfil,
    SinCandidatas,
    _peso_accion,
    _sortear_ponderado,
    cambiar_carta,
)
from tests.test_plan import _headers, hacer_premium

client = TestClient(app)
HOY = datetime.now(timezone.utc).date().toordinal()


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _onboard(sub: str) -> dict:
    h = _headers(sub)
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def _premium(sub: str, dias: int = 365) -> dict:
    h = _onboard(sub)
    hacer_premium(sub, dias=dias)
    return h


def _c(id_: str, categoria: str, accion: str, concepto: str) -> dict:
    return {"id": id_, "categoria": categoria, "accion": accion, "concepto": concepto}


def _eje(accion: str) -> str:
    return "quietud" if accion in EJE_QUIETUD else "movimiento"


def _fila(entrega_id: str) -> dict:
    """Lee la fila real de `entregas` (la verdad, no la respuesta del endpoint)."""
    with SessionLocal() as s:
        e = s.get(EntregaDB, entrega_id)
        return {"carta_id": e.carta_id, "cambios": e.cambios,
                "descartadas": list(e.descartadas or [])}


def _mover_fecha(entrega_id: str, dias: int) -> None:
    with SessionLocal() as s:
        e = s.get(EntregaDB, entrega_id)
        e.fecha = datetime.now(timezone.utc) + timedelta(days=dias)
        s.add(e)
        s.commit()


def _set_plan_hasta(sub: str, dias: int) -> None:
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
        assert u is not None, f"{sub} desapareció (¿otra corrida borró el Mundo 2?)"
        u.plan = "premium"
        u.plan_hasta = datetime.now(timezone.utc) + timedelta(days=dias)
        s.add(u)
        s.commit()


# ═════════════════════════════════════════════════════════════════════════════
# MOTOR PURO — ataques al orden de la cascada y al concepto de "ayer"
# ═════════════════════════════════════════════════════════════════════════════
def test_el_cruce_del_eje_se_reintenta_en_cada_nivel_de_la_cascada():
    """B1 corregido: el eje no se abandona al abrir el siguiente nivel de la cascada.

    Escenario construido: el pilar tiene UNA carta de quietud (cruza el eje) y una
    de movimiento (no cruza), y las DOS tienen el concepto ya visto → `frescas`
    queda vacío. Antes, el nivel 3 era `sin_repetir` a secas y el sorteo podía
    servir la de movimiento al usuario que pidió justamente no moverse (con la
    seed 0 lo hacía). Ahora cada conjunto se intenta primero cruzando el eje, así
    que la de quietud gana SIEMPRE, sin depender del azar.
    """
    actual = _c("a1", "p", "hacer", "c-a1")           # movimiento
    quietud = _c("q1", "p", "contemplar", "c-rep")    # cruza el eje, concepto repetido
    movim = _c("m1", "p", "caminar", "c-rep2")        # NO cruza el eje, concepto repetido
    pool = [actual, quietud, movim]
    perfil = Perfil(historial=[
        Entrega(carta_id="z8", categoria="otro", accion="respirar",
                dia=HOY - 3, concepto="c-rep"),
        Entrega(carta_id="z9", categoria="otro", accion="hacer",
                dia=HOY - 1, concepto="c-rep2"),
    ])

    for seed in range(10):
        nueva = cambiar_carta(perfil, pool, actual, set(), HOY,
                              rng=random.Random(seed))
        assert nueva["id"] == "q1", f"seed {seed} → {nueva['id']}"
        assert _eje(nueva["accion"]) != _eje(actual["accion"])


def test_la_carta_de_hace_un_mes_no_cuenta_como_la_de_ayer():
    """B2 corregido: "nunca la de ayer" vale solo si la última entrega fue AYER.

    Antes `ayer_id = historial[-1].carta_id` era "lo último que vio, cuando sea", y
    esa exclusión dura convertía en 409 "No quedan cartas para cambiar hoy" un caso
    con respuesta: la carta está fuera de las dos ventanas de 7 días (se vio hace
    30 días). Ahora se sirve — y encima cruzando el eje.
    """
    actual = _c("a1", "p", "hacer", "c-a1")
    vieja = _c("b1", "p", "contemplar", "c-b1")
    perfil = Perfil(historial=[
        Entrega(carta_id="b1", categoria="p", accion="contemplar",
                dia=HOY - 30, concepto="c-b1"),
    ])

    nueva = cambiar_carta(perfil, [actual, vieja], actual, set(), HOY,
                          rng=random.Random(0))
    assert nueva["id"] == "b1"
    assert _eje(nueva["accion"]) != _eje(actual["accion"])


def test_la_de_ayer_de_verdad_sigue_excluida():
    """El candado no se aflojó: si la última entrega ES de `hoy - 1`, no vuelve."""
    actual = _c("a1", "p", "hacer", "c-a1")
    ayer = _c("b1", "p", "contemplar", "c-b1")
    perfil = Perfil(historial=[
        Entrega(carta_id="b1", categoria="p", accion="contemplar",
                dia=HOY - 1, concepto="c-b1"),
    ])

    with pytest.raises(SinCandidatas):
        cambiar_carta(perfil, [actual, ayer], actual, set(), HOY,
                      rng=random.Random(0))


def test_el_cambio_pondera_las_estrellas_con_el_mismo_dial_que_la_entrega():
    """R1 corregido: `_sortear_ponderado` usa el modo "v1", el de la entrega diaria.

    `obtener_carta_del_dia` llama `elegir_carta(..., modo="v1")` (factor 0.5); antes
    el cambio usaba "v2" (factor 1.3) y la preferencia mandaba 2,6× más. Evidencia
    sobre el sorteo REAL: entre una acción de 5⭐ y una de 1⭐ el sesgo es 3:1 → la
    de 5⭐ sale ~75 % de las veces, no ~87 % como daba el modo "v2".
    """
    ratio = _peso_accion(5.0, "v1") / _peso_accion(1.0, "v1")
    assert ratio == pytest.approx(3.0)

    historial = (
        [Entrega(carta_id=f"h{i}", categoria="p", accion="contemplar",
                 dia=HOY - 20 + i, concepto=f"ch{i}", estrellas=5) for i in range(3)]
        + [Entrega(carta_id=f"g{i}", categoria="p", accion="caminar",
                   dia=HOY - 15 + i, concepto=f"cg{i}", estrellas=1) for i in range(3)]
    )
    cands = [_c("x", "p", "contemplar", "cx"), _c("y", "p", "caminar", "cy")]
    rng = random.Random(123)
    n = 4000
    salidas = [_sortear_ponderado(cands, historial, rng)["id"] for _ in range(n)]
    esperado_v1 = n * ratio / (1 + ratio)          # 3000 de 4000 (v2 daría ~3474)
    assert abs(salidas.count("x") - esperado_v1) < 120, salidas.count("x")


def test_el_cambio_castiga_repetir_la_accion_de_la_carta_rechazada():
    """R2 corregido: repetir la acción que el usuario acaba de rechazar pesa ×0.5.

    Es el equivalente del castigo que `elegir_carta` aplica contra la acción de
    ayer. Evidencia estadística sobre `cambiar_carta` entero (no solo el sorteo):
    un pilar SIN cartas del otro eje deja dos candidatas del mismo eje, una con la
    acción de la carta actual → salen ~33/67, no ~50/50.
    """
    assert CASTIGO_MISMA_ACCION == 0.5
    actual = _c("a1", "p", "contemplar", "c-a1")
    pool = [actual, _c("x", "p", "contemplar", "cx"), _c("y", "p", "respirar", "cy")]
    rng = random.Random(123)
    n = 3000
    salidas = [cambiar_carta(Perfil(), pool, actual, set(), HOY, rng=rng)["id"]
               for _ in range(n)]
    assert abs(salidas.count("x") - n / 3) < 110, salidas.count("x")

    # Sin `accion_actual` no hay castigo: el sorteo vuelve a ser parejo (~50/50).
    cands = [_c("x", "p", "contemplar", "cx"), _c("y", "p", "respirar", "cy")]
    rng = random.Random(7)
    parejo = [_sortear_ponderado(cands, [], rng)["id"] for _ in range(n)]
    assert abs(parejo.count("x") - n / 2) < 110, parejo.count("x")


def test_ok_la_gemela_de_la_descartada_no_vuelve_en_el_mismo_dia():
    """Descartar una carta descarta su concepto (canon R5). Ese candado muerde."""
    actual = _c("a1", "p", "hacer", "c-a1")
    gemela = _c("g1", "p", "contemplar", "c-gem")
    otra = _c("o1", "p", "respirar", "c-otra")
    pool = [actual, gemela, otra, _c("d1", "p", "contemplar", "c-gem")]
    # d1 ya descartada hoy → su concepto (c-gem) queda fuera → g1 tampoco vuelve.
    nueva = cambiar_carta(Perfil(), pool, actual, {"d1"}, HOY, rng=random.Random(3))
    assert nueva["id"] == "o1"


# ═════════════════════════════════════════════════════════════════════════════
# SERVICIO — candados 404 / 403 / 409
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_entrega_inexistente_da_404_no_500():
    h = _premium("qa13|fantasma")
    r = client.post(f"/api/entregas/{uuid.uuid4()}/cambiar", headers=h)
    assert r.status_code == 404


def test_ok_id_basura_da_404_no_500():
    h = _premium("qa13|basura")
    r = client.post("/api/entregas/no-es-un-uuid/cambiar", headers=h)
    assert r.status_code == 404


def test_ok_el_free_intruso_ve_404_antes_que_403():
    """El aislamiento gana al plan: un free ajeno NO aprende que la entrega existe."""
    ha = _premium("qa13|dueno2")
    hb = _onboard("qa13|intruso-free")
    entrega_a = client.get("/api/carta-del-dia", headers=ha).json()["entrega"]["id"]

    r = client.post(f"/api/entregas/{entrega_a}/cambiar", headers=hb)
    assert r.status_code == 404, r.text
    assert _fila(entrega_a)["cambios"] == 0


def test_ok_premium_vencido_es_free_403():
    h = _premium("qa13|vencido", dias=-1)
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 403


def test_ok_los_cambios_no_se_resetean_al_renovar_la_suscripcion():
    """El contador vive en la fila del día, no en la suscripción: renovar no regala."""
    sub = "qa13|renueva"
    h = _premium(sub)
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    for _ in range(3):
        assert client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).status_code == 200

    _set_plan_hasta(sub, dias=-1)                       # vence
    assert client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).status_code == 403
    _set_plan_hasta(sub, dias=365)                      # renueva
    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 409 and "3 veces" in r.json()["detail"]
    assert _fila(entrega_id)["cambios"] == 3


def test_ok_entrega_de_ayer_no_se_cambia():
    h = _premium("qa13|ayer")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    _mover_fecha(entrega_id, dias=-1)

    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 409
    assert "hoy" in r.json()["detail"].lower()
    assert _fila(entrega_id)["cambios"] == 0


def test_ok_el_cupo_de_3_es_por_dia_no_por_usuario():
    """Gasta los 3 de hoy, la entrega envejece, mañana vuelve a tener 3."""
    h = _premium("qa13|pordia")
    e1 = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    for _ in range(3):
        client.post(f"/api/entregas/{e1}/cambiar", headers=h)
    _mover_fecha(e1, dias=-1)

    e2 = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    assert e2 != e1
    r = client.post(f"/api/entregas/{e2}/cambiar", headers=h)
    assert r.status_code == 200, r.text
    assert r.json()["cambios"] == 1 and r.json()["cambios_restantes"] == 2


# ── Estados intermedios de cierre ────────────────────────────────────────────
def test_ok_solo_estrellas_ya_cierra_la_pausa():
    h = _premium("qa13|estrellas")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    client.put(f"/api/entregas/{entrega_id}/cierre", headers=h,
               json={"estrellas": 4, "completada": False})

    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 409 and "cerrada" in r.json()["detail"]


def test_reparo_un_cierre_vacio_con_completada_false_deja_cambiar():
    """`PUT /cierre {"completada": false}` no marca nada → la carta sigue cambiable.

    Defendible (no vivió la pausa), pero el endpoint se llama "cierre": el front
    puede llamarlo al salir de la pantalla y el usuario sigue con sus 3 cambios.
    """
    h = _premium("qa13|cierre-vacio")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    r0 = client.put(f"/api/entregas/{entrega_id}/cierre", headers=h,
                    json={"completada": False})
    assert r0.status_code == 200

    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 200, r.text


def test_un_comentario_privado_ya_cierra_la_pausa():
    """R4 corregido: `comentario_carta` cuenta como pausa vivida.

    El front solo muestra el comentario DESPUÉS de elegir las estrellas, así que si
    hay comentario la Pausa ya se vivió. Antes se podía comentar y después cambiar,
    y el comentario quedaba pegado a la entrega apuntando a OTRA carta.
    """
    h = _premium("qa13|comentario")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    antes = _fila(entrega_id)["carta_id"]
    client.put(f"/api/entregas/{entrega_id}/cierre", headers=h,
               json={"comentario_carta": "esta carta no me dice nada",
                     "completada": False})

    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 409, r.text
    assert "cerrada" in r.json()["detail"]
    fila = _fila(entrega_id)
    assert fila["carta_id"] == antes and fila["cambios"] == 0


def test_ok_reflexion_vacia_no_cuenta_como_cerrada():
    h = _premium("qa13|reflex-vacia")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    client.put(f"/api/entregas/{entrega_id}/cierre", headers=h,
               json={"reflexion": "", "completada": False})
    assert client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).status_code == 200


# ── Descartadas / persistencia ───────────────────────────────────────────────
def test_ok_descartadas_guarda_tres_ids_distintos_en_orden():
    h = _premium("qa13|descartadas")
    inicial = client.get("/api/carta-del-dia", headers=h).json()
    entrega_id = inicial["entrega"]["id"]
    esperadas = [inicial["carta"]["id"]]

    for i in (1, 2, 3):
        data = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).json()
        fila = _fila(entrega_id)
        assert fila["descartadas"] == esperadas, fila
        assert fila["cambios"] == i
        assert fila["carta_id"] == data["carta"]["id"]
        esperadas.append(data["carta"]["id"])

    fila = _fila(entrega_id)
    assert len(set(fila["descartadas"])) == 3
    assert fila["carta_id"] not in fila["descartadas"]


def test_reparo_el_contador_al_recargar_solo_existe_desde_a13b():
    """En `c3636ac` (la card) el contador se perdía al recargar: `cambios` y
    `cambios_restantes` viajaban SOLO en la respuesta del POST, así que el front
    no podía pintar "te quedan 2" ni apagar el botón y el usuario descubría el
    tope con un 409. Lo tapó `e1ddeb4` (A1.3b) agregando `entrega.cambios` al
    `_salida` común. Este test es el candado de esa reparación.
    """
    h = _premium("qa13|contador")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    post = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).json()
    assert post["cambios"] == 1 and post["cambios_restantes"] == 2

    get = client.get("/api/carta-del-dia", headers=h).json()
    assert get["entrega"]["cambios"] == 1
    # `cambios_restantes` sigue sin viajar en el GET: el front lo calcula con
    # `limites.cambios_carta` del perfil (contrato de types.ts, ambos opcionales).
    assert "cambios_restantes" not in get and "cambios_restantes" not in get["entrega"]


def test_ok_el_contrato_coincide_con_types_ts():
    """`cambios`/`cambios_restantes` a la RAÍZ (no dentro de `entrega`), como el front."""
    h = _premium("qa13|contrato")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    d = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).json()

    assert set(d) == {"entrega", "carta", "cambios", "cambios_restantes"}
    assert set(d["entrega"]) == {
        "id", "fecha", "estrellas", "completada", "reflexion",
        # WS29 · C1.2: quién me hizo llegar la carta y si es una Pausa extra.
        "de", "extra",
        "comentario_carta", "cambios", "ya_existia",
    }
    assert d["entrega"]["ya_existia"] is True
    # WS27 · B0: la carta declara además de dónde viene y quién la firma.
    assert set(d["carta"]) == {"id", "frase", "prompt", "categoria", "accion",
                               "origen", "firma_publica"}


def test_ok_la_rotacion_de_manana_cuenta_el_pilar_de_hoy_aunque_haya_cambiado():
    """`obtener_carta_del_dia` mira `entregas.carta_id`: el pilar de hoy es el del
    cambio (mismo pilar), así que mañana la rotación lo sigue viendo "visto" y
    ninguna descartada puede volver mañana (su pilar queda bloqueado 6 días)."""
    h = _premium("qa13|rotacion")
    hoy = client.get("/api/carta-del-dia", headers=h).json()
    entrega_id = hoy["entrega"]["id"]
    pilar = hoy["carta"]["categoria"]["slug"]

    cambiada = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).json()
    assert cambiada["carta"]["categoria"]["slug"] == pilar
    descartadas = set(_fila(entrega_id)["descartadas"])

    _mover_fecha(entrega_id, dias=-1)
    manana = client.get("/api/carta-del-dia", headers=h).json()
    assert manana["entrega"]["id"] != entrega_id
    assert manana["carta"]["categoria"]["slug"] != pilar
    assert manana["carta"]["id"] not in descartadas


def test_reparo_la_carta_descartada_es_invisible_para_la_ventana_de_7_dias():
    """El usuario VIO la carta descartada, pero `entregas` ya no la nombra.

    `elegir_carta` arma sus ventanas desde `entregas.carta_id` (y su concepto):
    la descartada —y su gemela— quedan libres para volver en cuanto la rotación
    destrabe el pilar. No rompe nada; es una fuga silenciosa del "no repetir".
    """
    h = _premium("qa13|invisible")
    inicial = client.get("/api/carta-del-dia", headers=h).json()
    entrega_id = inicial["entrega"]["id"]
    vieja = inicial["carta"]["id"]
    client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)

    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == "qa13|invisible"))
        ids = [e.carta_id for e in s.scalars(
            select(EntregaDB).where(EntregaDB.usuario_id == u.id)).all()]
    assert vieja not in ids                       # ninguna ventana la ve
    assert vieja in _fila(entrega_id)["descartadas"]  # solo vive en el JSON


# ── Cupo atómico (R7) ────────────────────────────────────────────────────────
def test_el_cupo_se_lee_con_bloqueo_de_fila():
    """R7 corregido: la entrega se carga con `SELECT ... FOR UPDATE`.

    Candado determinístico: se espía el SQL que sale al motor durante un POST y se
    exige que la lectura de `entregas` lleve `FOR UPDATE`. Sin eso, dos POST
    simultáneos leen `cambios` antes de que el otro commitee y los dos pasan el tope.
    """
    from sqlalchemy import event

    from mindful_api.db.base import engine

    h = _premium("qa13|forupdate")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]

    sentencias: list[str] = []

    def _espia(conn, cursor, statement, parameters, context, executemany):
        sentencias.append(" ".join(statement.split()).upper())

    event.listen(engine, "before_cursor_execute", _espia)
    try:
        r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    finally:
        event.remove(engine, "before_cursor_execute", _espia)

    assert r.status_code == 200, r.text
    bloqueos = [q for q in sentencias
                if "FOR UPDATE" in q and "FROM ENTREGAS" in q]
    assert bloqueos, [q for q in sentencias if "ENTREGAS" in q][:5]


def test_dos_cambios_simultaneos_no_superan_el_cupo(monkeypatch):
    """R7 corregido: dos POST a la vez se SERIALIZAN, el segundo se lleva su 409.

    Reproducción del leer-y-después-escribir: se deja un solo cambio disponible
    (2 de 3 gastados) y se frena al primer hilo DESPUÉS de que leyó la fila y antes
    de que commitee (retraso puesto en el motor `cambiar_carta`, el colaborador que
    corre entre la lectura y el `commit`). Sin `FOR UPDATE` los dos leían
    `cambios == 2`, los dos pasaban el tope y el usuario se llevaba 4 cambios.
    """
    import threading
    import time

    from mindful_api.db.base import SessionLocal
    from mindful_api.services import cambio as cambio_svc

    sub = "qa13|race-cambios"
    h = _premium(sub)
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    for _ in range(2):                       # gasta 2 de los 3: queda UNO
        assert client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h).status_code == 200
    assert _fila(entrega_id)["cambios"] == 2

    real = cambio_svc.cambiar_carta
    primero = threading.Event()

    def lento(*a, **kw):
        if not primero.is_set():             # el primer hilo ya leyó la fila
            primero.set()
            time.sleep(1.0)                  # ...y se demora antes de commitear
        return real(*a, **kw)

    monkeypatch.setattr(cambio_svc, "cambiar_carta", lento)

    codigos: list[int] = []
    lock = threading.Lock()

    def cambiar():
        with SessionLocal() as s:
            u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
            try:
                cambio_svc.cambiar_carta_del_dia(s, u, entrega_id)
                codigo = 200
            except Exception as exc:         # noqa: BLE001
                codigo = getattr(exc, "status_code", 500)
            with lock:
                codigos.append(codigo)

    a = threading.Thread(target=cambiar)
    a.start()
    primero.wait(timeout=10)                 # el primero ya tiene la fila tomada
    time.sleep(0.2)
    b = threading.Thread(target=cambiar)
    b.start()
    for hilo in (a, b):
        hilo.join(timeout=20)
        assert not hilo.is_alive(), "un hilo quedó colgado en el lock"

    assert sorted(codigos) == [200, 409], codigos
    fila = _fila(entrega_id)
    assert fila["cambios"] == 3, fila        # el cupo no se pasó
    assert len(fila["descartadas"]) == 3, fila


# ── Cascada agotada y TZ ─────────────────────────────────────────────────────
def test_ok_sin_candidatas_es_409_y_no_consume_el_cambio(monkeypatch):
    """La rama `except SinCandidatas` existe: se ejecuta y no deja la fila sucia."""
    h = _premium("qa13|agotado")
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]

    def _vacio(*a, **k):
        raise SinCandidatas("pilar vacío")

    monkeypatch.setattr("mindful_api.services.cambio.cambiar_carta", _vacio)
    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 409
    assert "No quedan cartas para cambiar hoy" in r.json()["detail"]

    fila = _fila(entrega_id)
    assert fila["cambios"] == 0 and fila["descartadas"] == []


def test_reparo_mover_la_tz_al_este_congela_la_entrega_de_hoy():
    """La entrega es de "hoy" en la TZ ACTUAL del usuario, no en la de creación.

    Un usuario en Madrid que viaja/edita su TZ a Kiritimati (UTC+14) puede ver su
    entrega de esta mañana caer a "ayer" y perder los cambios que le quedaban.
    """
    madrid, kiri = ZoneInfo("Europe/Madrid"), ZoneInfo("Pacific/Kiritimati")
    ahora = datetime.now(timezone.utc)
    # Instante que sigue siendo HOY en Madrid pero ya es AYER en Kiritimati (+14).
    fecha = next(
        (f for f in (ahora - timedelta(hours=k) for k in range(24))
         if f.astimezone(madrid).date() == ahora.astimezone(madrid).date()
         and f.astimezone(kiri).date() != ahora.astimezone(kiri).date()),
        None,
    )
    if fecha is None:  # antes de las 10:00 UTC ese instante no existe
        pytest.skip("la franja Madrid-hoy / Kiritimati-ayer no existe a esta hora")

    sub = "qa13|tz"
    h = _premium(sub)
    entrega_id = client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]
    with SessionLocal() as s:
        e = s.get(EntregaDB, entrega_id)
        e.fecha = fecha
        s.add(e)
        s.commit()

    client.put("/api/perfil", headers=h, json={"tz": "Pacific/Kiritimati"})
    r = client.post(f"/api/entregas/{entrega_id}/cambiar", headers=h)
    assert r.status_code == 409, r.text
    assert "Solo puedes cambiar la carta de hoy" in r.json()["detail"]

    # Peor: la carta del día vuelve a repartir → dos cartas en la misma jornada real.
    nueva = client.get("/api/carta-del-dia", headers=h).json()
    assert nueva["entrega"]["id"] != entrega_id
    assert nueva["entrega"]["ya_existia"] is False
