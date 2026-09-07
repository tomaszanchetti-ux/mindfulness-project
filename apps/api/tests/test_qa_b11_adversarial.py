"""Q/A ADVERSARIAL de la card B1.1 (WS27) · cartas de la comunidad (API).

No valida la card: intenta ROMPERLA. Cada test lleva el veredicto en el nombre:

  `test_ok_*`      → candado que aguanta (queda como test de regresión).
  `test_reparo_*`  → comportamiento defendible pero desalineado con el docstring
                     o con lo que el front/el negocio necesita.
  `test_bug_*`     → defecto real. Afirma el comportamiento BUENO.

Los siete BUG-B11-1…7 y los cuatro reparos YA ESTÁN CORREGIDOS: los `xfail` se
fueron y cada test quedó como candado de regresión, con un comentario arriba que
cuenta qué hacía mal la card antes. Los reparos llevan `r1`…`r4` en el nombre y
afirman la decisión del orquestador, no lo que la card hacía cuando se escribió
el Q/A.

Lo que ya cubre `tests/test_b11_cartas_comunidad.py` no se repite: acá van los
bordes, las carreras, los veredictos malformados y el cruce con B1.3.

    MINDFUL_DATABASE_URL=… .venv/bin/pytest -q -p no:warnings \\
        tests/test_qa_b11_adversarial.py
"""

from __future__ import annotations

import threading
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    ESTADO_A_REVISAR,
    ESTADO_APROBADA,
    ESTADO_EN_REVISION,
    ESTADO_RECHAZADA,
    ESTADO_RETIRADA,
    ESTADO_REVISION_DWELLIA,
    ESTADOS_EN_CURSO,
    FIRMA_ANONIMA,
    FIRMA_APODO,
    ORIGEN_COMUNIDAD,
    Aviso,
    Carta,
    CartaComunidad,
    Entrega,
    PushSuscripcion,
    Usuario,
)
from mindful_api.main import app
from mindful_api.services import admin as admin_mod
from mindful_api.services import avisos as avisos_mod
from mindful_api.services import cartas_comunidad as cartas_mod
from mindful_api.services import juez as juez_mod
from mindful_api.services.cartas_comunidad import (
    FRASE_MAX,
    PROMPT_MAX,
    PROMPT_MIN,
    crear_propuesta,
    procesar_juez,
    retirar_propuesta,
)
from mindful_api.services.juez import Veredicto
from mindful_api.services.plan import activar_premium
from tests.test_plan import _headers, hacer_premium

client = TestClient(app)
# Un segundo cliente que NO relanza la excepción del servidor: así un 500 se ve
# como lo vería el usuario (una respuesta 500), en vez de tumbar el test.
client_crudo = TestClient(app, raise_server_exceptions=False)

FRASE_OK = "El aire alcanza para empezar de nuevo."
PROMPT_OK = (
    "Elige un momento del día de hoy que te haya sostenido y escríbelo en tu diario "
    "con el detalle más pequeño que recuerdes de él."
)
assert len(FRASE_OK) <= FRASE_MAX
assert PROMPT_MIN <= len(PROMPT_OK) <= PROMPT_MAX


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────
def _cuerpo(**cambios) -> dict:
    cuerpo = {
        "categoria": "gratitud",
        "accion": "contemplar",
        "frase": FRASE_OK,
        "prompt": PROMPT_OK,
        "firma": FIRMA_ANONIMA,
        "cesion_aceptada": True,
    }
    cuerpo.update(cambios)
    return cuerpo


def _premium(sub: str) -> dict:
    h = _headers(sub)
    client.get("/api/perfil", headers=h)
    hacer_premium(sub)
    return h


def _vencer_premium(sub: str) -> None:
    """`plan=premium` pero `plan_hasta` en el pasado: la etiqueta miente, la fecha manda."""
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
        activar_premium(u, datetime.now(timezone.utc) - timedelta(days=1))
        s.commit()


def _proponer(headers: dict, **cambios):
    return client.post("/api/cartas-comunidad", headers=headers, json=_cuerpo(**cambios))


def _forzar(propuesta_id: str, **campos) -> None:
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        for campo, valor in campos.items():
            setattr(p, campo, valor)
        s.add(p)
        s.commit()


def _leer(propuesta_id: str) -> dict:
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        if p is None:
            return {}
        return {
            "estado": p.estado, "motivo": p.motivo, "veredicto": p.veredicto,
            "concepto": p.concepto, "frase": p.frase, "prompt": p.prompt,
            "categoria": p.categoria_slug, "accion": p.accion_slug,
            "firma": p.firma, "carta_id": p.carta_id,
        }


def _avisos(propuesta_id: str) -> list:
    with SessionLocal() as s:
        return [
            a.texto for a in s.scalars(
                select(Aviso).where(Aviso.referencia_id == propuesta_id)
                .order_by(Aviso.created_at)
            ).all()
        ]


def _en_curso_de(sub: str) -> list:
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
        return [
            p.id for p in s.scalars(
                select(CartaComunidad)
                .where(CartaComunidad.usuario_id == u.id)
                .where(CartaComunidad.estado.in_(ESTADOS_EN_CURSO))
            ).all()
        ]


def _juez_off(monkeypatch) -> None:
    """El juez de módulo, apagado: los tests que quieren juzgar llaman a
    `procesar_juez(..., evaluar=...)` explícitamente."""
    monkeypatch.setattr(juez_mod, "evaluar", lambda *a, **k: Veredicto(resultado="off"))


def _propuesta_en_revision(sub: str) -> str:
    """Una propuesta guardada y devuelta a `en_revision`, virgen de veredicto."""
    h = _premium(sub)
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_EN_REVISION, motivo=None, veredicto=None)
    return propuesta_id


@pytest.fixture(scope="module", autouse=True)
def _limpiar_qa11():
    """La base tiene que quedar como estaba: 77 cartas y sin usuarios `qa11|`."""
    yield
    with SessionLocal() as s:
        # Los usuarios primero: arrastran (CASCADE) sus propuestas, entregas y avisos.
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like("qa11|%")))
        s.commit()
        s.execute(delete(Carta).where(Carta.origen == ORIGEN_COMUNIDAD))
        s.commit()
        assert s.scalar(select(func.count()).select_from(Carta)) == 77
        assert s.scalar(
            select(func.count()).select_from(Usuario)
            .where(Usuario.firebase_uid.like("qa11|%"))
        ) == 0


# ─────────────────────────────────────────────────────────────────────────────
# 1 · Bordes del contenido
# ─────────────────────────────────────────────────────────────────────────────
@pytest.mark.parametrize("largo", [PROMPT_MIN, PROMPT_MAX],
                         ids=[str(PROMPT_MIN), str(PROMPT_MAX)])
def test_ok_el_prompt_en_los_extremos_exactos_entra(monkeypatch, largo):
    """PROMPT_MIN y PROMPT_MAX son INCLUSIVE (mín-1 y máx+1 ya rebotan en la
    suite de la card)."""
    _juez_off(monkeypatch)
    h = _premium(f"qa11|prompt-{largo}")
    r = _proponer(h, prompt="a" * largo)
    assert r.status_code == 201, r.text
    assert len(r.json()["carta"]["prompt"]) == largo


def test_ok_los_extremos_se_miden_despues_del_strip(monkeypatch):
    """Un prompt de PROMPT_MAX con espacios alrededor entra; uno de PROMPT_MAX+1 no
    se salva metiéndole espacios (el strip se aplica antes de medir, en los dos
    sentidos)."""
    _juez_off(monkeypatch)
    h = _premium("qa11|strip-borde")
    assert _proponer(h, prompt="  " + "a" * PROMPT_MAX + "  ").status_code == 201

    h2 = _premium("qa11|strip-borde-2")
    r = _proponer(h2, prompt="  " + "a" * (PROMPT_MAX + 1) + "  ")
    assert r.status_code == 422
    assert str(PROMPT_MAX) in r.json()["detail"]


def test_ok_el_prompt_en_blanco_rebota_por_corto(monkeypatch):
    """Solo espacios ⇒ 0 caracteres útiles ⇒ el mensaje del rango (no un 500)."""
    _juez_off(monkeypatch)
    h = _premium("qa11|prompt-blanco")
    r = _proponer(h, prompt="   \n\t  ")
    assert r.status_code == 422
    assert str(PROMPT_MIN) in r.json()["detail"]


def test_ok_los_limites_cuentan_caracteres_no_bytes(monkeypatch):
    """FRASE_MAX acentos/emoji entran (son caracteres, no bytes: pesan bastante
    más) y se guardan intactos."""
    _juez_off(monkeypatch)
    h = _premium("qa11|unicode")
    frase = ("áé🌱" * 20)[:FRASE_MAX]         # FRASE_MAX code points
    assert len(frase) == FRASE_MAX
    assert len(frase.encode("utf-8")) > FRASE_MAX   # y muchos más bytes
    r = _proponer(h, frase=frase)
    assert r.status_code == 201, r.text
    assert r.json()["carta"]["frase"] == frase
    assert _leer(r.json()["id"])["frase"] == frase


def test_reparo_r4_la_frase_colapsa_los_saltos_de_linea(monkeypatch):
    """REPARO 4 (decisión del orquestador): un `\\n` en la frase del frente llegaba
    tal cual al render, con saltos que el diseño de `Card` no previó. Ahora los
    saltos, los tabs y los espacios repetidos se colapsan a UN espacio antes de
    medir y de guardar: lo que se guarda es lo que se lee."""
    _juez_off(monkeypatch)
    h = _premium("qa11|salto")
    frase = "Primera línea\nsegunda   línea\tdel frente."
    r = _proponer(h, frase=frase)
    assert r.status_code == 201, r.text
    limpia = "Primera línea segunda línea del frente."
    assert r.json()["carta"]["frase"] == limpia
    assert _leer(r.json()["id"])["frase"] == limpia


# BUG-B11-4 (corregido): los caracteres de ancho cero burlaban el candado de "no
# puede quedar vacía" y una carta visualmente en blanco se guardaba y llegaba al
# juez. `_limpiar_texto` tira las categorías Unicode `Cf`/`Cc` antes de medir.
def test_bug_una_carta_invisible_pasa_la_validacion(monkeypatch):
    _juez_off(monkeypatch)
    h = _premium("qa11|invisible")
    r = _proponer(h, frase="\u200b" * 20, prompt="\u200b" * 150)   # espacios de ancho cero
    assert r.status_code == 422, "una carta sin un solo carácter visible no debería entrar"


# BUG-B11-7 (corregido): un `\u0000` dentro de la frase (JSON válido, Pydantic lo
# acepta y `strip()` no lo saca) llegaba crudo al INSERT, Postgres lo rechazaba y
# cualquier cliente tumbaba el endpoint con un carácter. Lo saca la misma limpieza
# del BUG-B11-4 (categoría `Cc`); lo que quede vacío, 422 — jamás un 500.
def test_bug_un_byte_nulo_en_la_frase_tumba_el_endpoint(monkeypatch):
    _juez_off(monkeypatch)
    h = _premium("qa11|nul")
    r = client_crudo.post(
        "/api/cartas-comunidad", headers=h,
        json=_cuerpo(frase="Una frase con \u0000 un byte nulo adentro."),
    )
    assert r.status_code < 500, f"500 con un NUL en la frase: {r.text[:200]}"


# ─────────────────────────────────────────────────────────────────────────────
# 2 · El plan
# ─────────────────────────────────────────────────────────────────────────────
def test_ok_un_premium_vencido_no_puede_proponer(monkeypatch):
    """La etiqueta dice premium, la fecha dice que no: manda la fecha."""
    _juez_off(monkeypatch)
    h = _premium("qa11|vencido")
    _vencer_premium("qa11|vencido")
    r = _proponer(h)
    assert r.status_code == 403
    assert "premium" in r.json()["detail"].lower()


def test_reparo_r1_un_premium_vencido_ya_no_puede_reenviar(monkeypatch):
    """REPARO 1 (decisión del orquestador): REENVIAR dispara otra corrida del juez
    —o sea otra llamada paga a Anthropic— y sin techo (`a_revisar → PUT →
    a_revisar → …`), así que ahora pide plan igual que proponer. RETIRAR sigue
    abierto sin plan: nadie queda atrapado en su propia carta."""
    _juez_off(monkeypatch)
    h = _premium("qa11|vence-en-medio")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_A_REVISAR, motivo="Un retoque.")
    _vencer_premium("qa11|vence-en-medio")

    r = client.put(
        f"/api/cartas-comunidad/{propuesta_id}", headers=h,
        json={"frase": "Otra frase, ya sin plan vigente.", "prompt": PROMPT_OK},
    )
    assert r.status_code == 403, r.text
    assert "premium" in r.json()["detail"].lower()
    # Ni se movió el estado ni se gastó una corrida del juez.
    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_A_REVISAR
    assert fila["frase"] == FRASE_OK

    # Retirar sí sigue abierto.
    assert client.delete(f"/api/cartas-comunidad/{propuesta_id}",
                         headers=h).status_code == 204


# ─────────────────────────────────────────────────────────────────────────────
# 3 · Una en curso · la carrera de los dos POST
# ─────────────────────────────────────────────────────────────────────────────
def test_ok_dos_post_simultaneos_dejan_una_sola_en_curso(monkeypatch):
    """El `SELECT … FOR UPDATE` sobre `usuarios` es real: dos hilos que entran a la
    vez a `crear_propuesta` no crean dos cartas en curso."""
    _juez_off(monkeypatch)
    sub = "qa11|carrera"
    _premium(sub)
    datos = SimpleNamespace(
        categoria="gratitud", accion="contemplar", frase=FRASE_OK,
        prompt=PROMPT_OK, firma=FIRMA_ANONIMA, cesion_aceptada=True,
    )
    barrera = threading.Barrier(2, timeout=15)
    resultados = []

    def intento():
        s = SessionLocal()
        try:
            u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
            barrera.wait()
            crear_propuesta(s, u, datos, None)
            resultados.append(201)
        except Exception as exc:  # noqa: BLE001
            resultados.append(getattr(exc, "status_code", repr(exc)))
        finally:
            s.close()

    hilos = [threading.Thread(target=intento) for _ in range(2)]
    for t in hilos:
        t.start()
    for t in hilos:
        t.join(timeout=30)
        assert not t.is_alive(), "el candado se colgó (deadlock)"

    assert sorted(resultados, key=str) == [201, 409], resultados
    assert len(_en_curso_de(sub)) == 1


# ─────────────────────────────────────────────────────────────────────────────
# 4 · Aislamiento
# ─────────────────────────────────────────────────────────────────────────────
def test_ok_el_404_de_lo_ajeno_es_identico_al_de_lo_inexistente(monkeypatch):
    """Ni el código ni el cuerpo distinguen 'existe pero no es tuya' de 'no existe':
    el id ajeno no es un oráculo de existencia."""
    _juez_off(monkeypatch)
    ha = _premium("qa11|duenia")
    hb = _premium("qa11|mirona")
    ajena = _proponer(ha).json()["id"]
    inventada = "00000000-0000-0000-0000-000000000000"

    r_ajena = client.delete(f"/api/cartas-comunidad/{ajena}", headers=hb)
    r_nada = client.delete(f"/api/cartas-comunidad/{inventada}", headers=hb)
    assert r_ajena.status_code == r_nada.status_code == 404
    assert r_ajena.json() == r_nada.json()


@pytest.mark.parametrize(
    "id_raro",
    ["x" * 400, "a b c", "../../etc/passwd", "🌱", "' OR 1=1 --", "%20"],
    ids=["larguisimo", "espacios", "traversal", "emoji", "sqli", "encodeado"],
)
def test_ok_ids_raros_dan_404_y_nunca_500(monkeypatch, id_raro):
    _juez_off(monkeypatch)
    h = _premium("qa11|ids-raros")
    assert client.delete(f"/api/cartas-comunidad/{id_raro}", headers=h).status_code == 404
    r = client.put(
        f"/api/cartas-comunidad/{id_raro}", headers=h,
        json={"frase": FRASE_OK, "prompt": PROMPT_OK},
    )
    assert r.status_code == 404, r.text


# ─────────────────────────────────────────────────────────────────────────────
# 5 · El juez en background
# ─────────────────────────────────────────────────────────────────────────────
# BUG-B11-1 (corregido): el chequeo de estado del juez era RANCIO — se hacía antes
# de evaluar y no se repetía al guardar, así que el veredicto pisaba la decisión
# tomada mientras el modelo pensaba (acá: una carta ya APROBADA y publicada
# quedaba 'rechazada' con la carta viva en el mazo). Ahora se relee con FOR UPDATE.
def test_bug_el_juez_pisa_una_aprobacion_tomada_mientras_evaluaba(monkeypatch):
    _juez_off(monkeypatch)
    propuesta_id = _propuesta_en_revision("qa11|pisa-admin")

    def evaluar_lento(*a, **k):
        # Mientras el modelo "piensa", Tomás la aprueba desde el panel
        # (`DESDE_APROBAR` incluye `en_revision`, o sea que es un click legal).
        with SessionLocal() as s2:
            admin_mod.aprobar(s2, propuesta_id)
        return Veredicto(resultado="rechaza", motivo="Llegué tarde.")

    procesar_juez(propuesta_id, evaluar=evaluar_lento)

    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_APROBADA, (
        "el juez no debe decidir sobre una carta que ya se decidió"
    )
    assert len(_avisos(propuesta_id)) == 1, "el autor no puede recibir dos avisos opuestos"


# BUG-B11-1 (corregido): misma causa — el autor retiraba la carta mientras el juez
# evaluaba, escribía otra, y el veredicto RESUCITABA la retirada: quedaba con DOS
# cartas en curso, rompiendo la regla de "una por vez".
def test_bug_el_juez_resucita_una_carta_retirada_mientras_evaluaba(monkeypatch):
    _juez_off(monkeypatch)
    sub = "qa11|pisa-retiro"
    h = _premium(sub)
    primera = _proponer(h).json()["id"]
    _forzar(primera, estado=ESTADO_EN_REVISION, motivo=None, veredicto=None)

    def evaluar_lento(*a, **k):
        # El autor no quiere esperar: la retira y escribe otra.
        with SessionLocal() as s2:
            u2 = s2.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
            retirar_propuesta(s2, u2, primera)
        assert _proponer(h).status_code == 201
        return Veredicto(resultado="requiere_revision", motivo="Un retoque.")

    procesar_juez(primera, evaluar=evaluar_lento)

    assert _leer(primera)["estado"] == ESTADO_RETIRADA, "lo retirado, retirado queda"
    assert len(_en_curso_de(sub)) == 1, "una carta en curso por vez"


# BUG-B11-2 (corregido): el guardado del veredicto no estaba blindado — un
# `concepto` de más de 80 caracteres (la columna es varchar(80) y `juez.evaluar` no
# lo recorta) reventaba el commit, hacía rollback y dejaba la propuesta CLAVADA en
# `en_revision`: sin aviso, sin reintento y ocupando el único lugar del autor.
def test_bug_un_concepto_largo_deja_la_carta_clavada_en_revision(monkeypatch):
    _juez_off(monkeypatch)
    propuesta_id = _propuesta_en_revision("qa11|concepto-largo")

    procesar_juez(propuesta_id, evaluar=lambda *a, **k: Veredicto(
        resultado="aprueba", concepto="un-concepto-" * 20,   # 240 caracteres
    ))

    assert _leer(propuesta_id)["estado"] == ESTADO_REVISION_DWELLIA


# BUG-B11-2 (corregido): misma causa — unos `hallazgos` que no eran
# JSON-serializables reventaban el commit y la propuesta quedaba clavada en
# `en_revision`. Ahora pasan por `_json_seguro` (`default=str`).
def test_bug_hallazgos_no_serializables_dejan_la_carta_clavada(monkeypatch):
    _juez_off(monkeypatch)
    propuesta_id = _propuesta_en_revision("qa11|hallazgos-raros")

    procesar_juez(propuesta_id, evaluar=lambda *a, **k: Veredicto(
        resultado="requiere_revision",
        hallazgos=[object()],
        motivo="Necesita un retoque.",
    ))

    assert _leer(propuesta_id)["estado"] == ESTADO_A_REVISAR


# BUG-B11-2 (corregido): misma causa — si el aviso levantaba (push roto), el
# rollback se llevaba puesta la TRANSICIÓN y la carta se quedaba en `en_revision`
# por un problema del canal de notificación. Ahora la transición se commitea
# ANTES y el aviso corre en su propio try.
def test_bug_un_aviso_que_levanta_se_lleva_la_transicion(monkeypatch):
    _juez_off(monkeypatch)
    propuesta_id = _propuesta_en_revision("qa11|push-roto")
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == "qa11|push-roto"))
        s.add(PushSuscripcion(
            usuario_id=u.id, endpoint="https://push.qa11.local/roto",
            p256dh="x", auth="y",
        ))
        s.commit()

    def explota(*a, **k):
        raise RuntimeError("el push service devolvió basura")

    monkeypatch.setattr(avisos_mod, "enviar_push", explota)
    procesar_juez(propuesta_id, evaluar=lambda *a, **k: Veredicto(
        resultado="rechaza", motivo="No esta vez.",
    ))

    assert _leer(propuesta_id)["estado"] == ESTADO_RECHAZADA

    # Y el candado PROPIO de B1.1: que el push esté envuelto en `crear_aviso` es
    # de B0 y mañana puede cambiar. Acá levanta el aviso ENTERO —cualquier
    # problema del canal de notificación— y la transición tiene que seguir en pie
    # igual: se commitea ANTES de avisar.
    otra_id = _propuesta_en_revision("qa11|aviso-roto")

    def aviso_roto(*a, **k):
        raise RuntimeError("el canal de avisos se cayó entero")

    monkeypatch.setattr(cartas_mod, "avisar_estado_carta", aviso_roto)
    procesar_juez(otra_id, evaluar=lambda *a, **k: Veredicto(
        resultado="rechaza", motivo="Tampoco esta vez.",
    ))

    assert _leer(otra_id)["estado"] == ESTADO_RECHAZADA
    assert _avisos(otra_id) == []


def test_ok_un_resultado_desconocido_va_a_la_mesa_de_tomas(monkeypatch):
    """`resultado='banana'` no es un rechazo: lo que no entendemos lo mira Tomás.
    El valor crudo se guarda igual (no se inventa un veredicto)."""
    _juez_off(monkeypatch)
    propuesta_id = _propuesta_en_revision("qa11|banana")

    procesar_juez(propuesta_id, evaluar=lambda *a, **k: Veredicto(
        resultado="banana", motivo="cualquier cosa",
    ))

    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_REVISION_DWELLIA
    assert fila["motivo"] is None                     # no se le muestra al autor
    assert fila["veredicto"]["resultado"] == "banana"
    assert _avisos(propuesta_id) == []


@pytest.mark.parametrize(
    "caso, fix, esperado",
    [
        ("string", "un texto suelto", None),
        ("lista", ["frase", "prompt"], None),
        ("vacio", {}, None),
        ("blanco", {"frase": "   "}, None),
        ("solo-frase", {"frase": "Solo la frase."},
         {"frase": "Solo la frase.", "prompt": None}),
    ],
    ids=lambda v: v if isinstance(v, str) else "",
)
def test_ok_un_fix_malformado_no_ensucia_la_sugerencia(monkeypatch, caso, fix, esperado):
    """`_fix_sugerido` canoniza: o `{"frase","prompt"}` o nada. Nunca a medias."""
    _juez_off(monkeypatch)
    propuesta_id = _propuesta_en_revision(f"qa11|fix-{caso}")

    procesar_juez(propuesta_id, evaluar=lambda *a, **k: Veredicto(
        resultado="requiere_revision", fix=fix, motivo="Un retoque.",
    ))

    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_A_REVISAR
    assert fila["veredicto"]["fix_sugerido"] == esperado


def test_ok_una_propuesta_borrada_entre_medio_no_rompe_al_juez(monkeypatch):
    """La fila desaparece mientras el juez pensaba: no levanta y no escribe nada."""
    _juez_off(monkeypatch)
    propuesta_id = _propuesta_en_revision("qa11|borrada")

    def evaluar_lento(*a, **k):
        with SessionLocal() as s2:
            s2.execute(delete(CartaComunidad).where(CartaComunidad.id == propuesta_id))
            s2.commit()
        return Veredicto(resultado="rechaza", motivo="tarde")

    procesar_juez(propuesta_id, evaluar=evaluar_lento)      # no levanta
    assert _leer(propuesta_id) == {}
    assert _avisos(propuesta_id) == []


# BUG-B11-3 (corregido): `_veredicto_json` TIRABA el `detalle` del Veredicto — el
# informe de la capa 1, la respuesta cruda del modelo y el consumo de tokens. B1.3
# le promete a Tomás que lee "literalmente lo que dijo el juez" y lo que guardaba
# era un resumen. Ahora se guarda saneado, y solo cuando hay algo que guardar.
def test_bug_el_veredicto_guardado_pierde_la_evidencia_del_juez(monkeypatch):
    _juez_off(monkeypatch)
    propuesta_id = _propuesta_en_revision("qa11|detalle")

    procesar_juez(propuesta_id, evaluar=lambda *a, **k: Veredicto(
        resultado="aprueba",
        concepto="aire-de-la-manana",
        detalle={"capa1": {"errores": [], "similares": []},
                 "modelo": {"crudo": {"veredicto": "aprueba"}}},
    ))

    assert _leer(propuesta_id)["veredicto"].get("detalle") is not None


# ─────────────────────────────────────────────────────────────────────────────
# 6 · Reenviar
# ─────────────────────────────────────────────────────────────────────────────
def test_ok_reenviar_cambia_pilar_y_accion_juntos(monkeypatch):
    _juez_off(monkeypatch)
    h = _premium("qa11|reenvia-par")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_A_REVISAR, motivo="Un retoque.")

    r = client.put(
        f"/api/cartas-comunidad/{propuesta_id}", headers=h,
        json={"frase": FRASE_OK, "prompt": PROMPT_OK,
              "categoria": "sentido", "accion": "caminar"},
    )
    assert r.status_code == 200, r.text
    fila = _leer(propuesta_id)
    assert (fila["categoria"], fila["accion"]) == ("sentido", "caminar")


def test_ok_reenviar_firmando_con_un_apodo_que_no_existe_rebota(monkeypatch):
    """El PUT revalida la firma con el MISMO mensaje que el POST, y no mueve el estado."""
    _juez_off(monkeypatch)
    h = _premium("qa11|reenvia-firma")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_A_REVISAR, motivo="Un retoque.")

    r = client.put(
        f"/api/cartas-comunidad/{propuesta_id}", headers=h,
        json={"frase": FRASE_OK, "prompt": PROMPT_OK, "firma": FIRMA_APODO},
    )
    assert r.status_code == 422
    assert "apodo" in r.json()["detail"]
    assert _leer(propuesta_id)["estado"] == ESTADO_A_REVISAR


def test_reparo_r2_reenviar_solo_la_frase_rebota_con_un_422_en_espanol(monkeypatch):
    """REPARO 2 (decisión del orquestador): `categoria`, `accion` y `firma` son
    opcionales (lo que no se manda, no se toca) pero `frase` y `prompt` son
    OBLIGATORIOS — el reenvío manda la carta entera. Mandar solo la frase seguía
    rebotando, pero con el 422 CRUDO de Pydantic ('Field required'); ahora el que
    falta se reclama en español, como el resto de la card."""
    _juez_off(monkeypatch)
    h = _premium("qa11|reenvia-parcial")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_A_REVISAR, motivo="Un retoque.")

    r = client.put(
        f"/api/cartas-comunidad/{propuesta_id}", headers=h,
        json={"frase": "Solo mando la frase nueva."},
    )
    assert r.status_code == 422
    detalle = r.json()["detail"]
    assert isinstance(detalle, str), detalle
    assert detalle == "Falta el prompt de la carta."
    assert _leer(propuesta_id)["prompt"] == PROMPT_OK      # el viejo sigue ahí

    # Y al revés: sin la frase, el mismo trato.
    r = client.put(
        f"/api/cartas-comunidad/{propuesta_id}", headers=h,
        json={"prompt": PROMPT_OK},
    )
    assert r.status_code == 422
    assert r.json()["detail"] == "Falta la frase de la carta."
    assert _leer(propuesta_id)["estado"] == ESTADO_A_REVISAR


def test_reparo_r3_el_veredicto_anterior_guarda_solo_una_vuelta(monkeypatch):
    """REPARO 3 (decisión del orquestador): cada reenvío metía el veredicto entero
    adentro de `anterior`, incluido el `anterior` que ya traía, así que tras N
    vueltas la columna JSON guardaba N veredictos anidados que nadie podaba. Ahora
    se guarda SOLO la vuelta inmediatamente anterior, podada un nivel."""
    _juez_off(monkeypatch)
    h = _premium("qa11|anidado")
    propuesta_id = _proponer(h).json()["id"]

    for vuelta in range(3):
        _forzar(propuesta_id, estado=ESTADO_A_REVISAR, motivo=f"Retoque {vuelta}.")
        client.put(
            f"/api/cartas-comunidad/{propuesta_id}", headers=h,
            json={"frase": f"Vuelta número {vuelta} de la misma carta.",
                  "prompt": PROMPT_OK},
        )

    v = _leer(propuesta_id)["veredicto"]
    assert v["anterior"] is not None                  # la vuelta anterior, sí
    assert "anterior" not in v["anterior"]            # y nada más abajo


# ─────────────────────────────────────────────────────────────────────────────
# 7 · `mias`
# ─────────────────────────────────────────────────────────────────────────────
def test_ok_mias_con_created_at_identicos_no_baila_entre_recargas(monkeypatch):
    """Empate en `created_at` ⇒ desempata el `id` (uuid): el orden NO es
    cronológico, pero es ESTABLE, que es lo que una lista revisable necesita."""
    _juez_off(monkeypatch)
    h = _premium("qa11|empate")
    primera = _proponer(h).json()["id"]
    _forzar(primera, estado=ESTADO_RETIRADA)
    segunda = _proponer(h).json()["id"]

    mismo_instante = datetime.now(timezone.utc)
    _forzar(primera, created_at=mismo_instante)
    _forzar(segunda, created_at=mismo_instante)

    esperado = sorted([primera, segunda], reverse=True)
    for _ in range(3):
        ids = [c["id"] for c in client.get("/api/cartas-comunidad/mias",
                                           headers=h).json()]
        assert ids == esperado


def test_ok_la_sugerencia_escrita_por_dwellia_llega_al_autor(monkeypatch):
    """B1.3 escribe el retoque en la MISMA clave (`veredicto.fix_sugerido`, con
    `fuente: dwellia`) y B1.1 lo sirve sin saber quién lo escribió."""
    _juez_off(monkeypatch)
    h = _premium("qa11|fix-dwellia")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_REVISION_DWELLIA, veredicto=None)

    with SessionLocal() as s:
        admin_mod.marcar_a_revisar(
            s, propuesta_id, "Acortá la frase.",
            fix={"frase": "Una frase de Dwellia.", "prompt": "Un prompt de Dwellia."},
        )

    mia = client.get("/api/cartas-comunidad/mias", headers=h).json()[0]
    assert mia["estado"] == ESTADO_A_REVISAR
    assert mia["motivo"] == "Acortá la frase."
    assert mia["sugerencia"] == {"frase": "Una frase de Dwellia.",
                                 "prompt": "Un prompt de Dwellia."}
    assert _leer(propuesta_id)["veredicto"]["fuente"] == "dwellia"


# BUG-B11-5 (corregido): `_salida` servía `veredicto['fix_sugerido']` CRUDO, sin
# pasarlo por `_fix_sugerido`. Si el panel mandaba el formulario de retoque vacío,
# el autor recibía `sugerencia={'frase': None, 'prompt': None}` — un cuadro de
# sugerencia que el front dibuja en blanco en vez de no dibujarlo.
def test_bug_un_retoque_vacio_de_dwellia_llega_como_sugerencia_fantasma(monkeypatch):
    _juez_off(monkeypatch)
    # OJO con el sub: `qa11|fix-vacio` ya lo usa el caso "vacio" de
    # `test_ok_un_fix_malformado_no_ensucia_la_sugerencia`, que le deja una carta
    # EN CURSO — proponer acá rebotaba con un 409 y el test nunca llegaba a mirar
    # el bug (fallaba con un `KeyError: 'id'` que el xfail tapaba).
    h = _premium("qa11|retoque-vacio")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_REVISION_DWELLIA, veredicto=None)

    # Tal cual lo arma el router de B1.3 con `fix: {}` (`FixSugerido().model_dump()`).
    monkeypatch.setattr(settings, "admin_uids", "qa11|jefa")
    ha = _headers("qa11|jefa")
    client.get("/api/perfil", headers=ha)
    r = client.post(
        f"/api/admin/cartas/{propuesta_id}/a-revisar", headers=ha,
        json={"sugerencia": "Mirá la frase.", "fix": {}},
    )
    assert r.status_code == 200, r.text

    mia = client.get("/api/cartas-comunidad/mias", headers=h).json()[0]
    assert mia["sugerencia"] is None

    # Y el candado del lado de B1.1, que es donde vivía el bug: aunque en la
    # columna HAYA un retoque fantasma (una fila vieja, o cualquier otro que
    # escriba `fix_sugerido` sin canonizarlo), `mias` no lo sirve.
    _forzar(propuesta_id, veredicto={
        "fuente": "dwellia", "fix_sugerido": {"frase": None, "prompt": "   "},
    })
    mia = client.get("/api/cartas-comunidad/mias", headers=h).json()[0]
    assert mia["sugerencia"] is None


def test_ok_personas_acompanadas_cuenta_las_entregas_de_la_carta(monkeypatch):
    """Cuando se escribió este Q/A (B1.1) el campo era un placeholder fijo en 0 y
    el test afirmaba justamente eso. **B2.1 lo llenó**: es el conteo de `entregas`
    de la carta publicada. El candado se da vuelta y ahora afirma la cuenta —
    incluida la del propio autor, que también puede recibir su carta (no hay
    exclusiones: WS27 §6)."""
    _juez_off(monkeypatch)
    h = _premium("qa11|impacto")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_REVISION_DWELLIA)
    with SessionLocal() as s:
        item = admin_mod.aprobar(s, propuesta_id)
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == "qa11|impacto"))
        s.add(Entrega(usuario_id=u.id, carta_id=item["carta_id"]))
        s.commit()

    mia = client.get("/api/cartas-comunidad/mias", headers=h).json()[0]
    assert mia["personas_acompanadas"] == 1


# ─────────────────────────────────────────────────────────────────────────────
# 8 · Cruce con B1.3 (aprobar = cargar)
# ─────────────────────────────────────────────────────────────────────────────
def test_ok_una_aprobada_se_ve_cerrada_no_se_retira_y_libera_el_lugar(monkeypatch):
    _juez_off(monkeypatch)
    h = _premium("qa11|aprobada")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_REVISION_DWELLIA)
    with SessionLocal() as s:
        admin_mod.aprobar(s, propuesta_id)

    mia = client.get("/api/cartas-comunidad/mias", headers=h).json()[0]
    assert mia["estado"] == ESTADO_APROBADA
    assert mia["carta_id"] is not None and mia["carta_id"].startswith("com-")

    # Ya está en el mazo: no se puede "retirar" lo que la comunidad ya recibe.
    r = client.delete(f"/api/cartas-comunidad/{propuesta_id}", headers=h)
    assert r.status_code == 409
    # Y el autor queda libre para escribir la siguiente.
    assert _proponer(h, frase="La segunda carta de la misma autora.").status_code == 201


# BUG-B11-6 (corregido): para una carta YA APROBADA, `mias.carta` seguía siendo una
# carta SINTÉTICA (id = id de la propuesta, firma calculada con el apodo de HOY) en
# vez de la fila publicada en `cartas`: si el autor cambiaba su apodo después de
# aprobada, la app le mostraba una firma que la comunidad no ve.
def test_bug_mias_de_una_aprobada_no_muestra_la_carta_publicada(monkeypatch):
    _juez_off(monkeypatch)
    h = _premium("qa11|firma-cambia")
    client.put("/api/perfil", headers=h, json={"apodo": "Teo"})
    propuesta_id = _proponer(h, firma=FIRMA_APODO).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_REVISION_DWELLIA)
    with SessionLocal() as s:
        carta_id = admin_mod.aprobar(s, propuesta_id)["carta_id"]

    # El autor se cambia el apodo DESPUÉS de que su carta ya está en el mazo.
    client.put("/api/perfil", headers=h, json={"apodo": "Pipo"})
    with SessionLocal() as s:
        publicada = s.get(Carta, carta_id)
        assert publicada.firma_publica == "Teo"      # lo que ve la comunidad

    mia = client.get("/api/cartas-comunidad/mias", headers=h).json()[0]
    assert mia["carta"]["id"] == carta_id
    assert mia["carta"]["firma_publica"] == "Teo"


# ─────────────────────────────────────────────────────────────────────────────
# 9 · El borde Pydantic (nada tiene que dar 500)
# ─────────────────────────────────────────────────────────────────────────────
def test_ok_los_campos_de_mas_se_ignoran(monkeypatch):
    """Nadie se autoaprueba desde el body: `estado`, `carta_id` y `veredicto` no
    son campos de entrada y el modelo los descarta en silencio."""
    _juez_off(monkeypatch)
    h = _premium("qa11|extras")
    r = client.post(
        "/api/cartas-comunidad", headers=h,
        json=_cuerpo(estado=ESTADO_APROBADA, carta_id="grat-con-01",
                     veredicto={"resultado": "aprueba"}, usuario_id="otro",
                     personas_acompanadas=9999),
    )
    assert r.status_code == 201, r.text
    assert r.json()["estado"] == ESTADO_EN_REVISION      # no el que mandó el body
    assert r.json()["carta_id"] is None
    assert r.json()["personas_acompanadas"] == 0
    fila = _leer(r.json()["id"])
    assert fila["estado"] != ESTADO_APROBADA             # el juez la movió, no el body
    assert fila["carta_id"] is None


@pytest.mark.parametrize(
    "cuerpo",
    [
        {},
        [],
        {"categoria": "gratitud"},
        _cuerpo(firma="seudonimo"),
        _cuerpo(firma=None),
        _cuerpo(frase=None),
        _cuerpo(frase=123),
        _cuerpo(cesion_aceptada="sí"),
        _cuerpo(categoria="g" * 41),
        _cuerpo(frase="x" * 5001),
        {k: v for k, v in _cuerpo().items() if k != "cesion_aceptada"},
    ],
    ids=["vacio", "lista", "incompleto", "firma-rara", "firma-null", "frase-null",
         "frase-numero", "cesion-string", "categoria-larga", "frase-gigante",
         "sin-cesion"],
)
def test_ok_un_body_invalido_siempre_es_422_nunca_500(monkeypatch, cuerpo):
    _juez_off(monkeypatch)
    h = _premium("qa11|body")
    r = client.post("/api/cartas-comunidad", headers=h, json=cuerpo)
    assert r.status_code == 422, f"{r.status_code}: {r.text}"
    assert client.get("/api/cartas-comunidad/mias", headers=h).json() == []
