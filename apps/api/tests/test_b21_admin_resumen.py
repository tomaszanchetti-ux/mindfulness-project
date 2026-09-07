"""WS27 · B2.1 · Adminland (API): el tablero y el filtro `pendientes`.

Decisión de Tomás (WS27 §6): el adminland es **simple y útil**, y **NADA por
usuario individual**. El tablero es del SISTEMA y sirve para una sola cosa: ver si
un pilar quedó desparejo, para escribir cartas de Dwellia y emparejarlo. Por eso
`GET /api/admin/resumen` tiene cuatro bloques y ninguno nombra a nadie.

Cómo se prueba, y por qué así:

· **Con datos CONSTRUIDOS y por DIFERENCIA.** El tablero cuenta toda la base, y la
  base la comparten todas las cards (y los `demo|` de Tomás). Un número absoluto
  ("7 usuarios") sería un test que se rompe cuando otro módulo siembra una fila.
  Se toma el tablero ANTES, se construye el escenario, se vuelve a pedir y se mide
  la DIFERENCIA: eso sí es del test.
· **Lo absoluto que sí se afirma es la FORMA**: los seis pilares, siempre los
  seis, siempre en el orden del reloj; los seis estados, aunque valgan 0. Un
  tablero al que le faltan las casillas vacías esconde justo lo que se va a mirar.
· **El premium vencido cuenta como free.** Es la regla de `services/plan`
  (`plan == premium` Y `plan_hasta` en el futuro): si el tablero la duplicara mal,
  Tomás leería una cifra de negocio equivocada.

Usuarios `b21r|…` y cartas `com-b21r…`: se borran al empezar y al terminar cada
test. El mazo tiene que volver siempre a 77.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    ESTADO_A_REVISAR,
    ESTADO_APROBADA,
    ESTADO_EN_REVISION,
    ESTADO_RECHAZADA,
    ESTADO_RETIRADA,
    ESTADO_REVISION_DWELLIA,
    ESTADOS_CARTA_COMUNIDAD,
    ORIGEN_COMUNIDAD,
    Carta,
    CartaComunidad,
    Entrega,
    Usuario,
)
from mindful_api.main import app
from mindful_api.services.admin import ORDEN_PILARES
from mindful_api.services.plan import PLAN_PREMIUM

client = TestClient(app)

MARCA = "b21r|"
PREFIJO_CARTA = "com-b21r-"
ADMIN = MARCA + "admin"

PROMPT_OK = (
    "Escribe en tu diario tres cosas que hoy te sostuvieron sin que las nombraras, "
    "y qué cambiaría si mañana le dieras las gracias en voz alta a una de ellas."
)
FRASE_OK = "Lo que sostiene tu día casi nunca hace ruido."


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


def _limpiar() -> None:
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(MARCA + "%")))
        s.execute(delete(Carta).where(Carta.id.like(PREFIJO_CARTA + "%")))
        s.commit()


@pytest.fixture(autouse=True)
def limpio():
    _limpiar()
    yield
    _limpiar()


@pytest.fixture
def admin(monkeypatch) -> dict:
    """Declara `b21r|admin` como administración y lo crea (para que exista la fila)."""
    monkeypatch.setattr(settings, "admin_uids", ADMIN)
    _usuario(ADMIN)
    return _headers(ADMIN)


# ── Siembra ──────────────────────────────────────────────────────────────────
def _usuario(sub: str, terminos: bool = False, plan=None, dias_plan: int = 365) -> str:
    with SessionLocal() as s:
        u = Usuario(firebase_uid=sub, email=f"{sub}@mindful.local")
        if terminos:
            u.terminos_aceptados_at = datetime.now(timezone.utc)
        if plan is not None:
            u.plan = plan
            u.plan_hasta = datetime.now(timezone.utc) + timedelta(days=dias_plan)
        s.add(u)
        s.commit()
        return u.id


def _propuesta(usuario_id: str, estado: str, categoria: str = "gratitud") -> str:
    with SessionLocal() as s:
        p = CartaComunidad(
            usuario_id=usuario_id, categoria_slug=categoria, accion_slug="contemplar",
            frase=FRASE_OK, prompt=PROMPT_OK, estado=estado,
            cesion_aceptada_at=datetime.now(timezone.utc),
        )
        s.add(p)
        s.commit()
        return p.id


def _publicar(categoria: str, autor_id=None) -> str:
    with SessionLocal() as s:
        c = Carta(
            id=PREFIJO_CARTA + secrets.token_hex(4),
            categoria_slug=categoria, accion_slug="contemplar",
            concepto="b21r-" + secrets.token_hex(3),
            frase=FRASE_OK, prompt=PROMPT_OK,
            origen=ORIGEN_COMUNIDAD, autor_usuario_id=autor_id,
        )
        s.add(c)
        s.commit()
        return c.id


def _entrega_con_comentario(usuario_id: str, comentario: str, dias: int) -> None:
    with SessionLocal() as s:
        carta_id = s.scalar(select(Carta.id).limit(1))
        s.add(Entrega(
            usuario_id=usuario_id, carta_id=carta_id,
            fecha=datetime.now(timezone.utc) - timedelta(days=dias),
            completada=True, comentario_carta=comentario,
        ))
        s.commit()


def _resumen(admin_headers: dict) -> dict:
    r = client.get("/api/admin/resumen", headers=admin_headers)
    assert r.status_code == 200
    return r.json()


def _por_pilar(resumen: dict) -> dict:
    return {p["slug"]: p for p in resumen["cartas"]["por_pilar"]}


# ═════════════════════════════════════════════════════════════════════════════
# 1 · La puerta
# ═════════════════════════════════════════════════════════════════════════════
def test_sin_admin_uids_el_tablero_esta_cerrado(monkeypatch):
    monkeypatch.setattr(settings, "admin_uids", "")
    r = client.get("/api/admin/resumen", headers=_headers(ADMIN))
    assert r.status_code == 403
    assert r.json()["detail"] == "Solo administración"


def test_otro_uid_no_ve_el_tablero(admin):
    assert client.get(
        "/api/admin/resumen", headers=_headers(MARCA + "intruso")
    ).status_code == 403


# ═════════════════════════════════════════════════════════════════════════════
# 2 · La forma
# ═════════════════════════════════════════════════════════════════════════════
def test_la_forma_del_tablero(admin):
    r = _resumen(admin)
    assert set(r) == {"cartas", "propuestas", "usuarios", "comentarios"}
    assert set(r["cartas"]) == {"total", "dwellia", "comunidad", "por_pilar"}
    assert set(r["propuestas"]) == set(ESTADOS_CARTA_COMUNIDAD) | {"pendientes"}
    assert set(r["usuarios"]) == {
        "total", "con_onboarding", "premium", "free", "crearon_cartas", "sin_cartas",
    }
    assert set(r["comentarios"]) == {"total", "ultimos_7_dias"}


def test_los_seis_pilares_salen_siempre_y_en_el_orden_del_reloj(admin):
    """Amor propio · gratitud · vínculos · sentido · perspectiva · resiliencia.

    Es el orden del hexágono de la app. Ordenar por nombre o por conteo haría que
    la columna baile en cada recarga y el tablero dejaría de leerse de un vistazo.
    """
    pilares = _resumen(admin)["cartas"]["por_pilar"]
    assert [p["slug"] for p in pilares] == list(ORDEN_PILARES)
    for p in pilares:
        assert set(p) == {"slug", "nombre", "total", "dwellia", "comunidad"}
        assert p["nombre"], "el pilar viaja con su nombre visible, no solo el slug"
        assert p["total"] == p["dwellia"] + p["comunidad"]


def test_el_mazo_limpio_son_77_cartas_propias_y_ninguna_de_la_comunidad(admin):
    cartas = _resumen(admin)["cartas"]
    assert cartas["total"] == 77
    assert cartas["dwellia"] == 77
    assert cartas["comunidad"] == 0
    assert sum(p["total"] for p in cartas["por_pilar"]) == 77


# ═════════════════════════════════════════════════════════════════════════════
# 3 · Las cartas por pilar y origen
# ═════════════════════════════════════════════════════════════════════════════
def test_una_carta_de_la_comunidad_suma_en_SU_pilar(admin):
    antes = _resumen(admin)
    antes_pilar = _por_pilar(antes)

    _publicar("vinculos")
    _publicar("vinculos")
    _publicar("resiliencia")

    despues = _resumen(admin)
    assert despues["cartas"]["total"] - antes["cartas"]["total"] == 3
    assert despues["cartas"]["comunidad"] - antes["cartas"]["comunidad"] == 3
    assert despues["cartas"]["dwellia"] == antes["cartas"]["dwellia"], (
        "publicar de la comunidad no puede tocar el conteo de las nuestras"
    )

    ahora = _por_pilar(despues)
    assert ahora["vinculos"]["comunidad"] - antes_pilar["vinculos"]["comunidad"] == 2
    assert ahora["vinculos"]["dwellia"] == antes_pilar["vinculos"]["dwellia"]
    assert ahora["resiliencia"]["comunidad"] - antes_pilar["resiliencia"]["comunidad"] == 1
    # Y los pilares que no tocó nadie quedan clavados.
    assert ahora["gratitud"] == antes_pilar["gratitud"]


# ═════════════════════════════════════════════════════════════════════════════
# 4 · Las propuestas por estado
# ═════════════════════════════════════════════════════════════════════════════
def test_las_propuestas_se_cuentan_por_estado_y_pendientes_suma_las_dos(admin):
    antes = _resumen(admin)["propuestas"]
    autor = _usuario(MARCA + "autor")

    _propuesta(autor, ESTADO_EN_REVISION)
    _propuesta(autor, ESTADO_REVISION_DWELLIA)
    _propuesta(autor, ESTADO_REVISION_DWELLIA)
    _propuesta(autor, ESTADO_A_REVISAR)
    _propuesta(autor, ESTADO_APROBADA)
    _propuesta(autor, ESTADO_RECHAZADA)
    _propuesta(autor, ESTADO_RETIRADA)

    despues = _resumen(admin)["propuestas"]
    delta = {k: despues[k] - antes[k] for k in despues}
    assert delta == {
        ESTADO_EN_REVISION: 1,
        ESTADO_REVISION_DWELLIA: 2,
        ESTADO_A_REVISAR: 1,
        ESTADO_APROBADA: 1,
        ESTADO_RECHAZADA: 1,
        ESTADO_RETIRADA: 1,
        # Lo que espera una mirada: el juez todavía la tiene + la mesa de Tomás.
        "pendientes": 3,
    }
    assert despues["pendientes"] == (
        despues[ESTADO_EN_REVISION] + despues[ESTADO_REVISION_DWELLIA]
    )


def test_el_filtro_pendientes_de_la_bandeja_dice_lo_mismo_que_el_tablero(admin):
    """El número del tablero y la lista que abre al tocarlo tienen que coincidir:
    si no, Tomás ve un 3 y entra a una lista de 2."""
    autor = _usuario(MARCA + "autor")
    mias = {
        _propuesta(autor, ESTADO_EN_REVISION),
        _propuesta(autor, ESTADO_REVISION_DWELLIA),
    }
    _propuesta(autor, ESTADO_A_REVISAR)
    _propuesta(autor, ESTADO_RECHAZADA)

    lista = client.get("/api/admin/cartas?estado=pendientes", headers=admin).json()
    ids = {i["id"] for i in lista}
    assert mias <= ids
    assert all(
        i["estado"] in (ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA) for i in lista
    )
    assert len(lista) == _resumen(admin)["propuestas"]["pendientes"]


def test_un_estado_inventado_es_422(admin):
    r = client.get("/api/admin/cartas?estado=pendiente", headers=admin)
    assert r.status_code == 422
    assert "pendientes" in r.json()["detail"]


# ═════════════════════════════════════════════════════════════════════════════
# 5 · La gente
# ═════════════════════════════════════════════════════════════════════════════
def test_los_usuarios_se_cuentan_por_onboarding_plan_y_si_escriben(admin):
    antes = _resumen(admin)["usuarios"]

    _usuario(MARCA + "sin-nada")
    _usuario(MARCA + "onboardeado", terminos=True)
    _usuario(MARCA + "premium", terminos=True, plan=PLAN_PREMIUM)
    escritor = _usuario(MARCA + "escritor", terminos=True, plan=PLAN_PREMIUM)
    _propuesta(escritor, ESTADO_REVISION_DWELLIA)
    _propuesta(escritor, ESTADO_APROBADA)      # dos cartas, UN autor

    despues = _resumen(admin)["usuarios"]
    delta = {k: despues[k] - antes[k] for k in despues}
    assert delta["total"] == 4
    assert delta["con_onboarding"] == 3
    assert delta["premium"] == 2
    assert delta["free"] == 2
    assert delta["crearon_cartas"] == 1, "dos propuestas del mismo autor son UN autor"
    assert delta["sin_cartas"] == 3
    # Las dos particiones tienen que cerrar contra el total, siempre.
    assert despues["premium"] + despues["free"] == despues["total"]
    assert despues["crearon_cartas"] + despues["sin_cartas"] == despues["total"]


def test_un_premium_vencido_cuenta_como_free(admin):
    """La verdad del plan es la FECHA (`services/plan.es_premium`), no la etiqueta."""
    antes = _resumen(admin)["usuarios"]
    _usuario(MARCA + "vencido", terminos=True, plan=PLAN_PREMIUM, dias_plan=-1)

    despues = _resumen(admin)["usuarios"]
    assert despues["total"] - antes["total"] == 1
    assert despues["premium"] == antes["premium"], "un premium vencido no es premium"
    assert despues["free"] - antes["free"] == 1


def test_borrar_al_autor_se_lleva_sus_propuestas_del_tablero(admin):
    """El CASCADE de `usuarios` limpia `cartas_comunidad`: el tablero no puede
    quedar contando propuestas de una cuenta que ya no existe."""
    antes = _resumen(admin)
    autor = _usuario(MARCA + "efimero")
    _propuesta(autor, ESTADO_REVISION_DWELLIA)
    assert _resumen(admin)["propuestas"]["pendientes"] > antes["propuestas"]["pendientes"]

    with SessionLocal() as s:
        s.delete(s.get(Usuario, autor))
        s.commit()

    despues = _resumen(admin)
    assert despues["propuestas"] == antes["propuestas"]
    assert despues["usuarios"] == antes["usuarios"]


# ═════════════════════════════════════════════════════════════════════════════
# 6 · Los comentarios
# ═════════════════════════════════════════════════════════════════════════════
def test_los_comentarios_se_cuentan_enteros_y_de_la_ultima_semana(admin):
    antes = _resumen(admin)["comentarios"]
    lector = _usuario(MARCA + "lector", terminos=True)

    _entrega_con_comentario(lector, "Me llegó justo hoy.", dias=1)
    _entrega_con_comentario(lector, "Prefiero cartas más cortas.", dias=6)
    _entrega_con_comentario(lector, "Este es viejo.", dias=30)

    despues = _resumen(admin)["comentarios"]
    assert despues["total"] - antes["total"] == 3
    assert despues["ultimos_7_dias"] - antes["ultimos_7_dias"] == 2


def test_una_pausa_sin_comentario_no_cuenta(admin):
    antes = _resumen(admin)["comentarios"]
    lector = _usuario(MARCA + "callado", terminos=True)
    with SessionLocal() as s:
        carta_id = s.scalar(select(Carta.id).limit(1))
        s.add(Entrega(usuario_id=lector, carta_id=carta_id, completada=True))
        s.commit()

    assert _resumen(admin)["comentarios"] == antes


# ═════════════════════════════════════════════════════════════════════════════
# 7 · Cierre
# ═════════════════════════════════════════════════════════════════════════════
def test_zz_el_mazo_queda_en_77():
    with SessionLocal() as s:
        assert len(s.scalars(select(Carta)).all()) == 77
