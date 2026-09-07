"""WS27 · B1.1 · Cartas de la comunidad: proponer, ver las mías, reenviar, retirar.

Lo que estos tests cuidan:
  · escribir cartas es de premium (free rebota con 403);
  · los límites del contenido se aplican en UN solo lugar y devuelven 422;
  · UNA carta en curso por vez, y retirarla (o que la rechacen) libera el lugar;
  · lo ajeno no existe: ni se lista, ni se reenvía, ni se retira (404, nunca 403);
  · el juez mueve el estado, escribe el veredicto canónico y avisa al autor —
    y si se cae, la carta queda en la mesa de Tomás en vez de perderse.

El juez de verdad (B1.2) no se toca: acá se reemplaza `mindful_api.services.juez.evaluar`
por uno de mentira, porque lo que se prueba es el RECORRIDO, no el criterio.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

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
    Aviso,
    Carta,
    CartaComunidad,
    Usuario,
)
from mindful_api.main import app
from mindful_api.services import juez as juez_mod
from mindful_api.services.avisos import TEXTOS_ESTADO
from mindful_api.services.cartas_comunidad import (
    FRASE_MAX,
    PROMPT_MAX,
    PROMPT_MIN,
    procesar_juez,
)
from mindful_api.services.juez import Veredicto
from tests.test_plan import _headers, hacer_premium

client = TestClient(app)

# Un prompt válido (dentro de 100-220) y una frase válida (≤60).
FRASE_OK = "Hoy el aire alcanza para empezar de nuevo."
PROMPT_OK = (
    "Elige un momento del día de hoy que te haya sostenido y escríbelo en tu diario "
    "con el detalle más pequeño que recuerdes de él."
)
assert len(FRASE_OK) <= FRASE_MAX
assert PROMPT_MIN <= len(PROMPT_OK) <= PROMPT_MAX


# ── Helpers ──────────────────────────────────────────────────────────────────
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
    """Un usuario premium listo para escribir (auto-provisión + plan)."""
    h = _headers(sub)
    client.get("/api/perfil", headers=h)
    hacer_premium(sub)
    return h


def _proponer(headers: dict, **cambios):
    return client.post("/api/cartas-comunidad", headers=headers, json=_cuerpo(**cambios))


def _forzar(propuesta_id: str, **campos) -> None:
    """Deja la propuesta en el estado que el test necesita, sin pasar por el juez."""
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        for campo, valor in campos.items():
            setattr(p, campo, valor)
        s.add(p)
        s.commit()


def _leer(propuesta_id: str) -> dict:
    with SessionLocal() as s:
        p = s.get(CartaComunidad, propuesta_id)
        return {
            "estado": p.estado, "motivo": p.motivo, "veredicto": p.veredicto,
            "concepto": p.concepto, "frase": p.frase, "prompt": p.prompt,
            "categoria": p.categoria_slug, "accion": p.accion_slug, "firma": p.firma,
        }


def _avisos(propuesta_id: str) -> list:
    with SessionLocal() as s:
        return [
            {"tipo": a.tipo, "texto": a.texto, "leido": a.leido}
            for a in s.scalars(
                select(Aviso).where(Aviso.referencia_id == propuesta_id)
                .order_by(Aviso.created_at)
            ).all()
        ]


def _juez_falso(monkeypatch, veredicto) -> None:
    """Reemplaza al juez de verdad. Se resuelve en tiempo de llamada, así que
    alcanza con pisar el atributo del módulo (también lo ve el background)."""
    def evaluar(propuesta, mazo, categorias, acciones):
        assert set(propuesta) == {"categoria", "accion", "frase", "prompt"}
        assert len(mazo) >= 77 and "concepto" in mazo[0]
        assert "gratitud" in categorias and "contemplar" in acciones
        if isinstance(veredicto, Exception):
            raise veredicto
        return veredicto

    monkeypatch.setattr(juez_mod, "evaluar", evaluar)


@pytest.fixture(scope="module", autouse=True)
def _limpiar_b11():
    """Al terminar: fuera los usuarios `b11|` y cualquier carta de comunidad que
    haya quedado en el mazo (otros tests cuentan 77 en `/api/contenido/resumen`)."""
    yield
    with SessionLocal() as s:
        s.execute(delete(Carta).where(Carta.origen == ORIGEN_COMUNIDAD))
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like("b11|%")))
        s.commit()


# ── Quién puede escribir ─────────────────────────────────────────────────────
def test_free_no_puede_proponer():
    h = _headers("b11|free")
    client.get("/api/perfil", headers=h)

    r = _proponer(h)
    assert r.status_code == 403
    assert "premium" in r.json()["detail"].lower()

    # Y tampoco ve nada donde no escribió.
    assert client.get("/api/cartas-comunidad/mias", headers=h).json() == []


def test_premium_propone_y_la_carta_queda_en_revision(monkeypatch):
    # El juez no opina todavía (se apaga con un veredicto `off`): lo que se mira
    # acá es la RESPUESTA del POST, que sale antes de que el juez corra.
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|ok")

    r = _proponer(h)
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["estado"] == ESTADO_EN_REVISION
    assert data["firma"] == FIRMA_ANONIMA
    assert data["motivo"] is None
    assert data["sugerencia"] is None
    assert data["carta_id"] is None
    assert data["personas_acompanadas"] == 0
    assert data["carta"]["frase"] == FRASE_OK
    assert data["carta"]["origen"] == ORIGEN_COMUNIDAD

    with SessionLocal() as s:
        p = s.get(CartaComunidad, data["id"])
        assert p.cesion_aceptada_at is not None  # la cesión queda fechada


# ── Los límites del contenido (422) ──────────────────────────────────────────
@pytest.mark.parametrize(
    "cambios, esperado",
    [
        ({"categoria": "no-existe"}, "pilar"),
        ({"accion": "bailar"}, "acciones"),
        ({"frase": "   "}, "vacía"),
        ({"frase": "x" * (FRASE_MAX + 1)}, str(FRASE_MAX)),
        ({"prompt": "x" * (PROMPT_MIN - 1)}, str(PROMPT_MIN)),
        ({"prompt": "x" * (PROMPT_MAX + 1)}, str(PROMPT_MAX)),
        ({"cesion_aceptada": False}, "cesión"),
    ],
    ids=["categoria", "accion", "frase-vacia", "frase-larga",
         "prompt-corto", "prompt-largo", "sin-cesion"],
)
def test_contenido_invalido_rebota_con_422(cambios, esperado):
    h = _premium("b11|422")
    r = _proponer(h, **cambios)
    assert r.status_code == 422, r.text
    assert esperado in str(r.json()["detail"])
    # Nada se guardó: el usuario sigue libre de escribir.
    assert client.get("/api/cartas-comunidad/mias", headers=h).json() == []


def test_firmar_con_apodo_sin_apodo_rebota():
    h = _premium("b11|sin-apodo")
    r = _proponer(h, firma=FIRMA_APODO)
    assert r.status_code == 422
    assert "apodo" in r.json()["detail"]


def test_firmar_con_apodo_publica_el_apodo_en_el_dorso():
    h = _premium("b11|con-apodo")
    client.put("/api/perfil", headers=h, json={"apodo": "Teo"})

    r = _proponer(h, firma=FIRMA_APODO)
    assert r.status_code == 201, r.text
    assert r.json()["carta"]["firma_publica"] == "Teo"


def test_la_firma_anonima_no_revela_al_autor():
    h = _premium("b11|anonima")
    client.put("/api/perfil", headers=h, json={"apodo": "Pipo"})
    r = _proponer(h, firma=FIRMA_ANONIMA)
    assert r.json()["carta"]["firma_publica"] is None


def test_el_texto_se_mide_ya_strippeado():
    """Una frase de 60 con espacios alrededor entra; el servicio guarda la limpia."""
    h = _premium("b11|strip")
    frase = "a" * FRASE_MAX
    r = _proponer(h, frase=f"   {frase}   ", prompt=f"  {PROMPT_OK}  ")
    assert r.status_code == 201, r.text
    assert r.json()["carta"]["frase"] == frase
    assert r.json()["carta"]["prompt"] == PROMPT_OK


# ── Una carta en curso por vez ───────────────────────────────────────────────
def test_segunda_carta_en_curso_rebota_con_409(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|dos")
    assert _proponer(h).status_code == 201

    r = _proponer(h, frase="Otra frase distinta para probar el candado.")
    assert r.status_code == 409
    assert "en curso" in r.json()["detail"]


def test_retirar_libera_el_lugar_para_otra(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|retira-y-otra")
    primera = _proponer(h).json()["id"]
    assert _proponer(h).status_code == 409

    assert client.delete(f"/api/cartas-comunidad/{primera}", headers=h).status_code == 204
    assert _leer(primera)["estado"] == ESTADO_RETIRADA

    r = _proponer(h)
    assert r.status_code == 201, r.text
    assert r.json()["id"] != primera


def test_una_rechazada_libera_el_lugar_para_otra(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|rechazada-y-otra")
    primera = _proponer(h).json()["id"]
    _forzar(primera, estado=ESTADO_RECHAZADA, motivo="No esta vez.")

    assert _proponer(h).status_code == 201


# ── Aislamiento: lo ajeno no existe ──────────────────────────────────────────
def test_mias_solo_muestra_las_propias(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    ha = _premium("b11|autora")
    hb = _premium("b11|otra")
    mia = _proponer(ha).json()["id"]
    ajena = _proponer(hb).json()["id"]

    ids = [c["id"] for c in client.get("/api/cartas-comunidad/mias", headers=ha).json()]
    assert ids == [mia]
    assert ajena not in ids


def test_tocar_una_carta_ajena_o_inexistente_da_404(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    ha = _premium("b11|duena")
    hb = _premium("b11|intrusa")
    ajena = _proponer(ha).json()["id"]
    antes = _leer(ajena)

    cuerpo = {"frase": FRASE_OK, "prompt": PROMPT_OK}
    # Ajena: 404 (nunca 403 ni 409 — no se revela que existe).
    assert client.put(f"/api/cartas-comunidad/{ajena}", headers=hb, json=cuerpo).status_code == 404
    assert client.delete(f"/api/cartas-comunidad/{ajena}", headers=hb).status_code == 404
    # Inexistente: el mismo 404.
    inventada = "00000000-0000-0000-0000-000000000000"
    assert client.put(f"/api/cartas-comunidad/{inventada}", headers=hb, json=cuerpo).status_code == 404
    assert client.delete(f"/api/cartas-comunidad/{inventada}", headers=hb).status_code == 404
    # Y la carta de la dueña quedó exactamente como estaba.
    assert _leer(ajena) == antes


# ── El juez y su recorrido ───────────────────────────────────────────────────
def _propuesta_en_revision(sub: str) -> str:
    """Una propuesta guardada y devuelta a `en_revision`, lista para juzgar."""
    h = _premium(sub)
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_EN_REVISION, motivo=None, veredicto=None)
    return propuesta_id


def test_juez_aprueba_va_a_la_mesa_de_tomas(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    propuesta_id = _propuesta_en_revision("b11|juez-aprueba")

    procesar_juez(propuesta_id, evaluar=lambda *a: Veredicto(
        resultado="aprueba", concepto="balance-del-dia",
    ))

    fila = _leer(propuesta_id)
    # Aprobar es de Tomás: el juez solo la deja lista.
    assert fila["estado"] == ESTADO_REVISION_DWELLIA
    assert fila["motivo"] is None
    assert fila["concepto"] == "balance-del-dia"
    assert fila["veredicto"] == {
        "resultado": "aprueba", "hallazgos": [], "concepto": "balance-del-dia",
        "fix_sugerido": None, "motivo": None, "fuente": "juez",
    }
    # `revision_dwellia` NO avisa: para el autor sigue "en evaluación".
    assert _avisos(propuesta_id) == []


def test_juez_pide_retoque_devuelve_la_carta_con_sugerencia(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    propuesta_id = _propuesta_en_revision("b11|juez-retoque")

    procesar_juez(propuesta_id, evaluar=lambda *a: Veredicto(
        resultado="requiere_revision",
        hallazgos=[{"regla": "R3.1", "mayor": True, "detalle": "El prompt no invita a escribir."}],
        fix={"frase": "Una frase mejor.", "prompt": "Un prompt mejor."},
        motivo="El prompt tiene que invitar a escribir en el diario.",
    ))

    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_A_REVISAR
    assert fila["motivo"] == "El prompt tiene que invitar a escribir en el diario."
    assert fila["veredicto"]["fix_sugerido"] == {
        "frase": "Una frase mejor.", "prompt": "Un prompt mejor.",
    }
    assert fila["veredicto"]["resultado"] == "requiere_revision"
    assert fila["veredicto"]["fuente"] == "juez"

    avisos = _avisos(propuesta_id)
    assert len(avisos) == 1
    assert avisos[0]["tipo"] == AVISO_CARTA_ESTADO
    assert avisos[0]["texto"] == TEXTOS_ESTADO[ESTADO_A_REVISAR]
    assert avisos[0]["leido"] is False

    # Y el autor la ve con la sugerencia servida.
    h = _headers("b11|juez-retoque")
    mia = client.get("/api/cartas-comunidad/mias", headers=h).json()[0]
    assert mia["estado"] == ESTADO_A_REVISAR
    assert mia["sugerencia"] == {"frase": "Una frase mejor.", "prompt": "Un prompt mejor."}


def test_sin_motivo_redactado_el_motivo_sale_del_primer_hallazgo_mayor(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    propuesta_id = _propuesta_en_revision("b11|juez-hallazgo")

    procesar_juez(propuesta_id, evaluar=lambda *a: Veredicto(
        resultado="requiere_revision",
        hallazgos=[
            {"regla": "R7", "mayor": False, "detalle": "Muletilla menor."},
            {"regla": "R5", "mayor": True, "detalle": "Se parece a otra carta del mazo."},
        ],
    ))

    fila = _leer(propuesta_id)
    assert fila["motivo"] == "Se parece a otra carta del mazo."
    assert fila["veredicto"]["motivo"] == "Se parece a otra carta del mazo."


def test_juez_rechaza(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    propuesta_id = _propuesta_en_revision("b11|juez-rechaza")

    procesar_juez(propuesta_id, evaluar=lambda *a: Veredicto(
        resultado="rechaza",
        hallazgos=[{"regla": "S", "mayor": True, "detalle": "Da un consejo médico."}],
        motivo="Esta carta da un consejo que Dwellia no puede dar.",
    ))

    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_RECHAZADA
    assert fila["motivo"] == "Esta carta da un consejo que Dwellia no puede dar."
    assert fila["veredicto"]["resultado"] == "rechaza"
    assert fila["veredicto"]["fix_sugerido"] is None

    avisos = _avisos(propuesta_id)
    assert len(avisos) == 1
    assert avisos[0]["texto"] == TEXTOS_ESTADO[ESTADO_RECHAZADA]


def test_juez_apagado_manda_la_carta_a_la_mesa_de_tomas(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    propuesta_id = _propuesta_en_revision("b11|juez-off")

    procesar_juez(propuesta_id, evaluar=lambda *a: Veredicto(
        resultado="off", motivo="juez no configurado",
    ))

    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_REVISION_DWELLIA
    assert fila["motivo"] is None          # el autor no ve nuestros problemas
    assert fila["veredicto"]["resultado"] == "off"
    assert _avisos(propuesta_id) == []


def test_un_juez_que_se_cae_no_pierde_la_carta(monkeypatch):
    _juez_falso(monkeypatch, RuntimeError("la API se cayó"))
    propuesta_id = _propuesta_en_revision("b11|juez-explota")

    # No levanta: el background nunca tumba nada.
    procesar_juez(propuesta_id)

    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_REVISION_DWELLIA
    assert fila["motivo"] is None
    assert fila["veredicto"]["resultado"] == "off"
    assert fila["veredicto"]["fuente"] == "juez"
    assert _avisos(propuesta_id) == []


def test_el_juez_no_toca_una_carta_que_ya_no_esta_en_revision(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|juez-tarde")
    propuesta_id = _proponer(h).json()["id"]
    # El autor la retiró mientras el juez pensaba.
    client.delete(f"/api/cartas-comunidad/{propuesta_id}", headers=h)

    procesar_juez(propuesta_id, evaluar=lambda *a: Veredicto(resultado="rechaza",
                                                            motivo="tarde"))

    assert _leer(propuesta_id)["estado"] == ESTADO_RETIRADA
    assert _avisos(propuesta_id) == []


def test_el_post_encola_al_juez(monkeypatch):
    """La request responde `en_revision`, y al terminar el juez ya la movió."""
    _juez_falso(monkeypatch, Veredicto(
        resultado="rechaza", motivo="No esta vez, pero gracias por escribirla.",
    ))
    h = _premium("b11|encola")

    r = _proponer(h)
    assert r.json()["estado"] == ESTADO_EN_REVISION   # lo que vio el autor al enviar

    fila = _leer(r.json()["id"])                      # lo que dejó el background
    assert fila["estado"] == ESTADO_RECHAZADA
    assert fila["motivo"] == "No esta vez, pero gracias por escribirla."
    assert len(_avisos(r.json()["id"])) == 1


# ── Reenviar ─────────────────────────────────────────────────────────────────
def test_reenviar_desde_a_revisar_vuelve_a_pasar_por_el_juez(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|reenvia")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(
        propuesta_id, estado=ESTADO_A_REVISAR, motivo="Necesita un retoque.",
        veredicto={"resultado": "requiere_revision", "hallazgos": [], "concepto": None,
                   "fix_sugerido": {"frase": "Mejor así.", "prompt": None},
                   "motivo": "Necesita un retoque.", "fuente": "juez"},
    )

    nueva_frase = "El mismo camino, mirado de otra manera."
    r = client.put(
        f"/api/cartas-comunidad/{propuesta_id}", headers=h,
        json={"frase": nueva_frase, "prompt": PROMPT_OK, "accion": "caminar"},
    )
    assert r.status_code == 200, r.text
    # Lo que ve el autor al reenviar: otra vez en revisión, sin la sugerencia vieja.
    assert r.json()["estado"] == ESTADO_EN_REVISION
    assert r.json()["motivo"] is None
    assert r.json()["carta"]["frase"] == nueva_frase
    assert r.json()["carta"]["accion"]["slug"] == "caminar"

    fila = _leer(propuesta_id)
    assert fila["frase"] == nueva_frase
    assert fila["accion"] == "caminar"
    assert fila["categoria"] == "gratitud"      # lo que no se manda, no se toca
    # El juez ya corrió de nuevo (juez off → mesa de Tomás) y el veredicto viejo
    # sigue guardado debajo.
    assert fila["estado"] == ESTADO_REVISION_DWELLIA
    assert fila["veredicto"]["resultado"] == "off"
    assert fila["veredicto"]["anterior"]["motivo"] == "Necesita un retoque."


def test_reenviar_revalida_el_contenido(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|reenvia-mal")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=ESTADO_A_REVISAR, motivo="Un retoque.")

    r = client.put(
        f"/api/cartas-comunidad/{propuesta_id}", headers=h,
        json={"frase": "x" * (FRASE_MAX + 1), "prompt": PROMPT_OK},
    )
    assert r.status_code == 422
    assert str(FRASE_MAX) in r.json()["detail"]
    assert _leer(propuesta_id)["estado"] == ESTADO_A_REVISAR   # no se movió


@pytest.mark.parametrize(
    "estado",
    [ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA, ESTADO_APROBADA,
     ESTADO_RECHAZADA, ESTADO_RETIRADA],
)
def test_reenviar_desde_cualquier_otro_estado_rebota_con_409(monkeypatch, estado):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium(f"b11|reenvia-409-{estado}")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=estado)

    r = client.put(
        f"/api/cartas-comunidad/{propuesta_id}", headers=h,
        json={"frase": FRASE_OK, "prompt": PROMPT_OK},
    )
    assert r.status_code == 409
    assert "retoque" in r.json()["detail"]


# ── Retirar ──────────────────────────────────────────────────────────────────
@pytest.mark.parametrize(
    "estado", [ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA, ESTADO_A_REVISAR]
)
def test_retirar_desde_cualquier_estado_en_curso(monkeypatch, estado):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium(f"b11|retira-{estado}")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=estado, motivo="algo")

    assert client.delete(f"/api/cartas-comunidad/{propuesta_id}",
                         headers=h).status_code == 204
    fila = _leer(propuesta_id)
    assert fila["estado"] == ESTADO_RETIRADA
    assert fila["motivo"] is None
    # La fila queda en el historial del autor (no se borra).
    assert client.get("/api/cartas-comunidad/mias", headers=h).json()[0]["id"] == propuesta_id


@pytest.mark.parametrize(
    "estado", [ESTADO_APROBADA, ESTADO_RECHAZADA, ESTADO_RETIRADA]
)
def test_retirar_una_carta_cerrada_rebota_con_409(monkeypatch, estado):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium(f"b11|retira-409-{estado}")
    propuesta_id = _proponer(h).json()["id"]
    _forzar(propuesta_id, estado=estado)

    r = client.delete(f"/api/cartas-comunidad/{propuesta_id}", headers=h)
    assert r.status_code == 409
    assert "retirar" in r.json()["detail"]


# ── La forma de la carta (el front la dibuja con el componente de siempre) ───
def test_la_carta_de_una_propuesta_tiene_la_forma_de_una_carta_del_mazo(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|forma")
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})

    real = client.get("/api/carta-del-dia", headers=h).json()["carta"]
    propuesta_id = _proponer(h).json()["id"]
    mia = client.get("/api/cartas-comunidad/mias", headers=h).json()[0]
    carta = mia["carta"]

    # Equivalencia con el render canónico (`_carta_enriquecida`), campo por campo.
    assert set(carta) == set(real)
    assert set(carta["categoria"]) == set(real["categoria"])
    assert set(carta["accion"]) == set(real["accion"])
    assert carta["id"] == propuesta_id          # todavía no hay carta publicada
    assert carta["categoria"]["slug"] == "gratitud"
    assert carta["accion"]["slug"] == "contemplar"
    assert carta["origen"] == ORIGEN_COMUNIDAD

    # Y proponer no ensucia el mazo: publicar es de B1.3.
    assert client.get("/api/contenido/resumen").json()["cartas"] == 77


def test_mias_ordena_la_mas_nueva_primero(monkeypatch):
    _juez_falso(monkeypatch, Veredicto(resultado="off"))
    h = _premium("b11|orden")
    primera = _proponer(h).json()["id"]
    _forzar(primera, estado=ESTADO_RETIRADA)
    segunda = _proponer(h).json()["id"]

    ids = [c["id"] for c in client.get("/api/cartas-comunidad/mias", headers=h).json()]
    assert ids == [segunda, primera]
