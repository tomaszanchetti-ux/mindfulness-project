"""M2 · motor puro (WS22): rotación 6+1, dedup por carta Y concepto, pool completo.

Corre contra el cartas.json real (la fuente de verdad) — si el contenido rompe un
invariante del motor (p.ej. un pilar sin cartas en un lado del eje), acá explota.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

import pytest

from mindful_api.services.seleccion import (
    EJE_MOVIMIENTO,
    EJE_QUIETUD,
    VENTANA_NO_REPETIR,
    Entrega,
    Perfil,
    SinCandidatas,
    cambiar_carta,
    elegir_carta,
)

DATA = Path(__file__).resolve().parents[3] / "M0_Motor_de_Contenido" / "data"
CARTAS = json.loads((DATA / "cartas.json").read_text(encoding="utf-8"))
CATEGORIAS = {c["categoria"] for c in CARTAS}


def _simular(dias: int, seed: int) -> list[Entrega]:
    """Simula `dias` entregas consecutivas y devuelve el historial."""
    rng = random.Random(seed)
    historial: list[Entrega] = []
    for i in range(dias):
        perfil = Perfil(historial=historial)
        carta = elegir_carta(perfil, CARTAS, rng=rng)
        historial.append(Entrega(
            carta_id=carta["id"], categoria=carta["categoria"],
            accion=carta["accion"], dia=1000 + i, concepto=carta["concepto"],
        ))
    return historial


def test_contenido_sin_escribir_como_accion():
    # WS22: escribir es el cierre universal, no una acción inicial del enum.
    assert all(c["accion"] != "escribir" for c in CARTAS)


def test_contenido_cubre_ambos_lados_del_eje():
    # Requisito del cambio de carta v2: cada pilar tiene quietud Y movimiento.
    for cat in CATEGORIAS:
        acciones = {c["accion"] for c in CARTAS if c["categoria"] == cat}
        assert acciones & EJE_QUIETUD, f"{cat}: sin cartas de quietud"
        assert acciones & EJE_MOVIMIENTO, f"{cat}: sin cartas de movimiento"


def test_primera_carta_sale_de_todo_el_mazo():
    carta = elegir_carta(Perfil(), CARTAS, rng=random.Random(7))
    assert carta in CARTAS


def test_rotacion_primeros_6_dias_cubren_los_6_pilares():
    for seed in range(10):
        historial = _simular(6, seed)
        assert {e.categoria for e in historial} == CATEGORIAS


def test_rotacion_todo_pilar_vuelve_en_9_dias_o_menos():
    # 6 días de rotación + comodín (+1 de auto-corrección) → gap máximo ~9.
    for seed in range(5):
        historial = _simular(60, seed)
        ultimo: dict[str, int] = {}
        for e in historial:
            if e.categoria in ultimo:
                assert e.dia - ultimo[e.categoria] <= 9, (
                    f"{e.categoria} desapareció {e.dia - ultimo[e.categoria]} días (seed {seed})"
                )
            ultimo[e.categoria] = e.dia


def test_ni_carta_ni_concepto_se_repiten_en_la_ventana():
    for seed in range(5):
        historial = _simular(90, seed)
        for i, e in enumerate(historial):
            ventana = [v for v in historial[:i]
                       if v.dia > e.dia - VENTANA_NO_REPETIR]
            assert e.carta_id not in {v.carta_id for v in ventana}
            assert e.concepto not in {v.concepto for v in ventana}, (
                f"concepto '{e.concepto}' repetido en la ventana (seed {seed}, día {e.dia})"
            )


def test_largo_plazo_no_rompe_y_no_repite_la_de_ayer():
    historial = _simular(120, 11)
    assert len(historial) == 120
    for ayer, hoy in zip(historial, historial[1:]):
        assert hoy.carta_id != ayer.carta_id


# ─────────────────────────────────────────────────────────────────────────────
# WS24 · A1.3 · cambiar la carta del día (motor puro)
# ─────────────────────────────────────────────────────────────────────────────
HOY = 1000


def _c(id_: str, categoria: str, accion: str, concepto: str) -> dict:
    """Carta sintética: el escenario del candado se CONSTRUYE, no se busca en el mazo."""
    return {"id": id_, "categoria": categoria, "accion": accion, "concepto": concepto}


def _eje_de(accion: str) -> str:
    return "quietud" if accion in EJE_QUIETUD else "movimiento"


def test_cambiar_cruza_el_eje_en_los_6_pilares():
    # La válvula del "hoy no quiero moverme": mismo pilar, el otro lado del eje.
    for i, actual in enumerate(CARTAS):
        nueva = cambiar_carta(Perfil(), CARTAS, actual, set(), HOY,
                              rng=random.Random(i))
        assert nueva["categoria"] == actual["categoria"]
        assert nueva["id"] != actual["id"]
        assert _eje_de(nueva["accion"]) != _eje_de(actual["accion"]), (
            f"{actual['id']} ({actual['accion']}) → {nueva['id']} ({nueva['accion']})"
        )


def test_cambiar_fallback_mismo_pilar_sin_cruzar_el_eje():
    # Pilar sin cartas del otro lado → nivel 2: mismo pilar, mismo eje.
    actual = _c("a1", "p", "contemplar", "c-a1")
    pool = [actual, _c("a2", "p", "respirar", "c-a2"), _c("z1", "otro", "hacer", "c-z1")]
    nueva = cambiar_carta(Perfil(), pool, actual, set(), HOY, rng=random.Random(1))
    assert nueva["id"] == "a2"


def test_cambiar_respeta_la_ventana_de_carta():
    actual = _c("a1", "p", "contemplar", "c-a1")
    m1 = _c("m1", "p", "caminar", "c-m1")
    m2 = _c("m2", "p", "hacer", "c-m2")
    pool = [actual, m1, m2, _c("z1", "otro", "hacer", "c-z1")]
    perfil = Perfil(historial=[
        Entrega(carta_id="m1", categoria="p", accion="caminar", dia=HOY - 2, concepto="c-m1"),
        Entrega(carta_id="z1", categoria="otro", accion="hacer", dia=HOY - 1, concepto="c-z1"),
    ])
    nueva = cambiar_carta(perfil, pool, actual, set(), HOY, rng=random.Random(2))
    assert nueva["id"] == "m2"  # m1 está dentro de los 7 días


def test_cambiar_respeta_la_ventana_de_concepto():
    actual = _c("a1", "p", "contemplar", "c-a1")
    pool = [actual, _c("m1", "p", "caminar", "c-m1"), _c("m2", "p", "hacer", "c-m2"),
            _c("z1", "otro", "hacer", "c-m2")]  # gemela de m2 en otro pilar
    perfil = Perfil(historial=[
        Entrega(carta_id="z1", categoria="otro", accion="hacer", dia=HOY - 2, concepto="c-m2"),
        Entrega(carta_id="z9", categoria="otro", accion="hacer", dia=HOY - 1, concepto="c-z9"),
    ])
    nueva = cambiar_carta(perfil, pool, actual, set(), HOY, rng=random.Random(3))
    assert nueva["id"] == "m1"  # m2 vive la misma experiencia con otra etiqueta


def test_cambiar_no_ofrece_una_gemela_de_la_descartada():
    # La carta que rechazó y su gemela son la misma experiencia: ninguna vuelve.
    actual = _c("a1", "p", "contemplar", "c-a1")
    pool = [actual, _c("m1", "p", "caminar", "c-m1"), _c("m2", "p", "hacer", "c-m1"),
            _c("m3", "p", "hacer", "c-m3")]
    nueva = cambiar_carta(Perfil(), pool, actual, {"m1"}, HOY, rng=random.Random(4))
    assert nueva["id"] == "m3"


def test_cambiar_suelta_el_concepto_antes_que_la_carta():
    # Nivel 3: la única del pilar comparte concepto con algo reciente → igual sale.
    actual = _c("a1", "p", "contemplar", "c-a1")
    pool = [actual, _c("m1", "p", "caminar", "c-m1"), _c("z1", "otro", "hacer", "c-m1")]
    perfil = Perfil(historial=[
        Entrega(carta_id="z1", categoria="otro", accion="hacer", dia=HOY - 1, concepto="c-m1"),
    ])
    nueva = cambiar_carta(perfil, pool, actual, set(), HOY, rng=random.Random(5))
    assert nueva["id"] == "m1"


def test_cambiar_ultimo_fallback_cualquiera_del_pilar():
    # Nivel 4: la única del pilar está DENTRO de la ventana de carta → igual sale.
    actual = _c("a1", "p", "contemplar", "c-a1")
    pool = [actual, _c("m1", "p", "caminar", "c-m1"), _c("z1", "otro", "hacer", "c-z1")]
    perfil = Perfil(historial=[
        Entrega(carta_id="m1", categoria="p", accion="caminar", dia=HOY - 3, concepto="c-m1"),
        Entrega(carta_id="z1", categoria="otro", accion="hacer", dia=HOY - 1, concepto="c-z1"),
    ])
    nueva = cambiar_carta(perfil, pool, actual, set(), HOY, rng=random.Random(6))
    assert nueva["id"] == "m1"


def test_cambiar_reintenta_el_cruce_del_eje_en_cada_nivel():
    # B1: la ÚNICA carta que cruza el eje tiene concepto repetido → igual se sirve.
    # `frescas` queda vacío (las dos candidatas repiten concepto), así que el nivel
    # se abre a `sin_repetir` — y ahí se vuelve a intentar cruzar el eje antes de
    # conformarse con el mismo eje. Sin eso, el azar podía servir la de movimiento.
    actual = _c("a1", "p", "hacer", "c-a1")            # movimiento
    cruza = _c("q1", "p", "contemplar", "c-rep")       # quietud, concepto repetido
    mismo = _c("m1", "p", "caminar", "c-rep2")         # movimiento, concepto repetido
    pool = [actual, cruza, mismo, _c("z1", "otro", "hacer", "c-z1")]
    perfil = Perfil(historial=[
        Entrega(carta_id="z8", categoria="otro", accion="respirar",
                dia=HOY - 3, concepto="c-rep"),
        Entrega(carta_id="z9", categoria="otro", accion="hacer",
                dia=HOY - 1, concepto="c-rep2"),
    ])
    for seed in range(10):
        nueva = cambiar_carta(perfil, pool, actual, set(), HOY, rng=random.Random(seed))
        assert nueva["id"] == "q1", f"seed {seed} → {nueva['id']}"
        assert _eje_de(nueva["accion"]) != _eje_de(actual["accion"])


def test_cambiar_no_bloquea_una_carta_de_hace_treinta_dias():
    # B2: "nunca la de ayer" vale solo si la última entrega fue AYER de verdad.
    # El usuario volvió después de un mes: esa carta ya salió de las dos ventanas
    # de 7 días y no puede seguir bloqueando el único cambio posible.
    actual = _c("a1", "p", "hacer", "c-a1")
    vieja = _c("b1", "p", "contemplar", "c-b1")
    perfil = Perfil(historial=[
        Entrega(carta_id="b1", categoria="p", accion="contemplar",
                dia=HOY - 30, concepto="c-b1"),
    ])
    nueva = cambiar_carta(perfil, [actual, vieja], actual, set(), HOY,
                          rng=random.Random(9))
    assert nueva["id"] == "b1"
    assert _eje_de(nueva["accion"]) != _eje_de(actual["accion"])


def test_cambiar_nunca_devuelve_la_de_ayer():
    actual = _c("a1", "p", "contemplar", "c-a1")
    pool = [actual, _c("m1", "p", "caminar", "c-m1")]
    perfil = Perfil(historial=[
        Entrega(carta_id="m1", categoria="p", accion="caminar", dia=HOY - 1, concepto="c-m1"),
    ])
    with pytest.raises(SinCandidatas):
        cambiar_carta(perfil, pool, actual, set(), HOY, rng=random.Random(7))


def test_cambiar_sin_candidatas_no_inventa():
    actual = _c("a1", "p", "contemplar", "c-a1")
    with pytest.raises(SinCandidatas):
        cambiar_carta(Perfil(), [actual, _c("z1", "otro", "hacer", "c-z1")],
                      actual, set(), HOY, rng=random.Random(8))


def test_cambiar_tres_veces_nunca_repite_ni_la_actual_ni_las_descartadas():
    # El máximo premium: 3 cambios sobre el mazo real, para los 6 pilares.
    for i, primera in enumerate(CARTAS):
        rng = random.Random(100 + i)
        actual = primera
        descartadas: set = set()
        for _ in range(3):
            nueva = cambiar_carta(Perfil(), CARTAS, actual, descartadas, HOY, rng=rng)
            assert nueva["categoria"] == primera["categoria"]
            assert nueva["id"] != actual["id"]
            assert nueva["id"] not in descartadas
            descartadas.add(actual["id"])
            actual = nueva


def test_cambiar_es_deterministico_con_seed():
    actual = CARTAS[0]
    uno = cambiar_carta(Perfil(), CARTAS, actual, set(), HOY, rng=random.Random(42))
    dos = cambiar_carta(Perfil(), CARTAS, actual, set(), HOY, rng=random.Random(42))
    assert uno["id"] == dos["id"]
