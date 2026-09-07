"""WS27 · B2.1 · El historial de redacciones (la v1 del funnel del adminland).

El funnel que pidió Tomás tiene tres columnas: **v1** lo que escribió el autor →
**v2** lo que dijo el juez (o el retoque de Dwellia) → **vFinal** la decisión. Las
dos últimas ya vivían en la fila (`veredicto` con su `anterior`, y
`estado`/`motivo`/`carta_id`); la primera NO: el reenvío pisaba `frase` y `prompt`
y el texto original se perdía. Tomás abría el panel y no podía saber de dónde
venía la carta que estaba mirando.

`cartas_comunidad.historial` (migración `l2a3b4c5d6e7`) guarda una entrada por
vuelta: v1 al enviarla y v(n+1) en cada reenvío, con la carta entera (frase,
prompt, pilar, acción, firma), la fecha UTC y quién la escribió.

Lo que estos tests cuidan:
1. **Se escribe al crear** — v1, con los siete campos del contrato.
2. **Se SUMA al reenviar** — la vuelta anterior se conserva; el reenvío ya no
   pisa nada. Y la numeración avanza (v2, v3…), no se reinicia.
3. **Se guarda de verdad** — `historial` es una columna JSON: si se mutara en su
   lugar (`.append()`), SQLAlchemy no vería el cambio y la fila se guardaría sin
   él, en silencio. Por eso todo se relee de la base, nunca de la respuesta.
4. **Llega al panel** — `GET /api/admin/cartas` devuelve `historial` en cada ítem.

El juez de verdad no se toca: acá se lo reemplaza por uno de mentira, porque lo
que se prueba es el RASTRO, no el criterio.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    ESTADO_A_REVISAR,
    ESTADO_EN_REVISION,
    ESTADO_REVISION_DWELLIA,
    FIRMA_ANONIMA,
    FIRMA_APODO,
    ORIGEN_COMUNIDAD,
    Carta,
    CartaComunidad,
    Usuario,
)
from mindful_api.main import app
from mindful_api.services import juez as juez_mod
from mindful_api.services.juez import Veredicto

client = TestClient(app)

MARCA = "b21h|"
AUTOR = MARCA + "autor"
ADMIN = MARCA + "admin"

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

CAMPOS = {"version", "frase", "prompt", "categoria", "accion", "firma", "fecha", "por"}


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


def _limpiar() -> None:
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(MARCA + "%")))
        s.execute(delete(Carta).where(Carta.origen == ORIGEN_COMUNIDAD))
        s.commit()


@pytest.fixture(autouse=True)
def limpio(monkeypatch):
    """Cada test arranca limpio, con el juez apagado (veredicto `off`: la propuesta
    va a la mesa de Tomás y no se mueve sola mientras el test la mira)."""
    _limpiar()

    def evaluar(propuesta, mazo, categorias, acciones):
        return Veredicto(resultado="off")

    monkeypatch.setattr(juez_mod, "evaluar", evaluar)
    yield
    _limpiar()


def _premium(sub: str) -> dict:
    """Un usuario premium listo para escribir (auto-provisión dev + plan)."""
    from datetime import datetime, timedelta, timezone

    from mindful_api.services.plan import activar_premium

    h = _headers(sub)
    client.get("/api/perfil", headers=h)
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
        activar_premium(u, datetime.now(timezone.utc) + timedelta(days=365))
        s.commit()
    return h


def _proponer(headers: dict, **cambios):
    cuerpo = {
        "categoria": "gratitud", "accion": "contemplar",
        "frase": FRASE_V1, "prompt": PROMPT_V1,
        "firma": FIRMA_ANONIMA, "cesion_aceptada": True,
    }
    cuerpo.update(cambios)
    return client.post("/api/cartas-comunidad", headers=headers, json=cuerpo)


def _historial(propuesta_id: str) -> list:
    """El historial LEÍDO DE LA BASE (no el de la respuesta): es lo único que
    prueba que la columna JSON se guardó de verdad."""
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        assert p is not None
        return list(p.historial or [])


def _a_revisar(propuesta_id: str) -> None:
    """Deja la propuesta lista para el reenvío, sin pasar por el juez."""
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        p.estado = ESTADO_A_REVISAR
        p.motivo = "Prueba con algo más concreto."
        s.add(p)
        s.commit()


# ═════════════════════════════════════════════════════════════════════════════
# 1 · La v1 se escribe al enviar
# ═════════════════════════════════════════════════════════════════════════════
def test_al_crear_queda_la_version_1_completa():
    h = _premium(AUTOR)
    propuesta = _proponer(h).json()["id"]

    historial = _historial(propuesta)
    assert len(historial) == 1
    v1 = historial[0]
    assert set(v1) == CAMPOS
    assert v1["version"] == 1
    assert v1["frase"] == FRASE_V1
    assert v1["prompt"] == PROMPT_V1
    assert v1["categoria"] == "gratitud"
    assert v1["accion"] == "contemplar"
    assert v1["firma"] == FIRMA_ANONIMA
    assert v1["por"] == "usuario"
    # La fecha es ISO 8601 con zona (UTC): el panel la muestra, no la interpreta.
    assert v1["fecha"].endswith("+00:00")


def test_la_version_1_guarda_el_texto_LIMPIO_no_el_crudo():
    """El historial tiene que decir lo que la carta DICE. `_limpiar_texto` colapsa
    espacios y saca los invisibles antes de guardar; la v1 se toma después de eso,
    o sea que el funnel muestra el mismo texto que la carta."""
    h = _premium(AUTOR)
    sucia = "  Hoy   el aire\nalcanza para empezar de nuevo.  "
    propuesta = _proponer(h, frase=sucia).json()["id"]

    v1 = _historial(propuesta)[0]
    assert v1["frase"] == "Hoy el aire alcanza para empezar de nuevo."


# ═════════════════════════════════════════════════════════════════════════════
# 2 · El reenvío SUMA, no pisa
# ═════════════════════════════════════════════════════════════════════════════
def test_reenviar_agrega_la_version_2_y_conserva_la_1():
    h = _premium(AUTOR)
    propuesta = _proponer(h).json()["id"]
    _a_revisar(propuesta)

    r = client.put(f"/api/cartas-comunidad/{propuesta}", headers=h,
                   json={"frase": FRASE_V2, "prompt": PROMPT_V2, "firma": FIRMA_ANONIMA})
    assert r.status_code == 200

    historial = _historial(propuesta)
    assert [v["version"] for v in historial] == [1, 2]
    assert historial[0]["frase"] == FRASE_V1, "el reenvío pisó la redacción original"
    assert historial[0]["prompt"] == PROMPT_V1
    assert historial[1]["frase"] == FRASE_V2
    assert historial[1]["prompt"] == PROMPT_V2

    # Y la fila quedó con el texto nuevo y fuera del "necesita un retoque": el
    # reenvío la manda de vuelta al juez (que acá está apagado, así que termina en
    # la mesa de Tomás).
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta)
        assert p.frase == FRASE_V2 and p.prompt == PROMPT_V2
        assert p.estado in (ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA)


def test_tres_vueltas_numeran_1_2_3():
    """`a_revisar → PUT → a_revisar` no tiene techo: el historial tampoco lo pierde."""
    h = _premium(AUTOR)
    propuesta = _proponer(h).json()["id"]

    _a_revisar(propuesta)
    client.put(f"/api/cartas-comunidad/{propuesta}", headers=h,
               json={"frase": FRASE_V2, "prompt": PROMPT_V2})
    _a_revisar(propuesta)
    client.put(f"/api/cartas-comunidad/{propuesta}", headers=h,
               json={"frase": FRASE_V3, "prompt": PROMPT_V3})

    historial = _historial(propuesta)
    assert [v["version"] for v in historial] == [1, 2, 3]
    assert [v["frase"] for v in historial] == [FRASE_V1, FRASE_V2, FRASE_V3]


def test_el_reenvio_guarda_el_pilar_la_accion_y_la_firma_de_ESA_vuelta():
    """El autor puede cambiar de pilar, de acción y de firma al reenviar. El
    funnel tiene que mostrar la carta COMPLETA de cada vuelta, no solo el texto."""
    h = _premium(AUTOR)
    client.put("/api/perfil", headers=h, json={"apodo": "Ana"})
    propuesta = _proponer(h).json()["id"]
    _a_revisar(propuesta)

    client.put(
        f"/api/cartas-comunidad/{propuesta}", headers=h,
        json={"categoria": "vinculos", "accion": "hacer",
              "frase": FRASE_V2, "prompt": PROMPT_V2, "firma": FIRMA_APODO},
    )

    v1, v2 = _historial(propuesta)
    assert (v1["categoria"], v1["accion"], v1["firma"]) == (
        "gratitud", "contemplar", FIRMA_ANONIMA)
    assert (v2["categoria"], v2["accion"], v2["firma"]) == (
        "vinculos", "hacer", FIRMA_APODO)


def test_un_reenvio_rechazado_no_deja_rastro():
    """Un 422 no es una vuelta: si el texto nuevo no pasa los límites, la carta no
    cambió y el historial tampoco puede haber cambiado."""
    h = _premium(AUTOR)
    propuesta = _proponer(h).json()["id"]
    _a_revisar(propuesta)

    r = client.put(f"/api/cartas-comunidad/{propuesta}", headers=h,
                   json={"frase": "x" * 61, "prompt": PROMPT_V2})
    assert r.status_code == 422

    historial = _historial(propuesta)
    assert [v["version"] for v in historial] == [1]
    assert historial[0]["frase"] == FRASE_V1


# ═════════════════════════════════════════════════════════════════════════════
# 3 · El funnel llega al panel
# ═════════════════════════════════════════════════════════════════════════════
def test_admin_cartas_devuelve_el_historial(monkeypatch):
    monkeypatch.setattr(settings, "admin_uids", ADMIN)
    h = _premium(AUTOR)
    propuesta = _proponer(h).json()["id"]
    _a_revisar(propuesta)
    client.put(f"/api/cartas-comunidad/{propuesta}", headers=h,
               json={"frase": FRASE_V2, "prompt": PROMPT_V2})

    items = client.get("/api/admin/cartas?estado=todas",
                       headers=_headers(ADMIN)).json()
    fila = next(i for i in items if i["id"] == propuesta)
    assert [v["version"] for v in fila["historial"]] == [1, 2]
    assert fila["historial"][0]["frase"] == FRASE_V1
    assert fila["historial"][1]["frase"] == FRASE_V2


def test_una_propuesta_sin_historial_devuelve_lista_vacia(monkeypatch):
    """Las filas anteriores a la migración (y las sembradas a mano) traen NULL.
    El panel itera una lista: nunca recibe None."""
    monkeypatch.setattr(settings, "admin_uids", ADMIN)
    h = _premium(AUTOR)
    propuesta = _proponer(h).json()["id"]
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta)
        p.historial = None
        s.add(p)
        s.commit()

    items = client.get("/api/admin/cartas?estado=todas",
                       headers=_headers(ADMIN)).json()
    fila = next(i for i in items if i["id"] == propuesta)
    assert fila["historial"] == []


def test_la_numeracion_no_se_reinicia_con_un_historial_incompleto():
    """Si una fila llega con el historial a medias (sembrada a mano, migrada), la
    vuelta siguiente sigue al máximo que haya, no al largo de la lista."""
    h = _premium(AUTOR)
    propuesta = _proponer(h).json()["id"]
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta)
        # Una sola entrada, pero numerada 5: hubo vueltas que no se guardaron.
        p.historial = [dict(p.historial[0], version=5)]
        p.estado = ESTADO_A_REVISAR
        s.add(p)
        s.commit()

    client.put(f"/api/cartas-comunidad/{propuesta}", headers=h,
               json={"frase": FRASE_V2, "prompt": PROMPT_V2})
    assert [v["version"] for v in _historial(propuesta)] == [5, 6]
