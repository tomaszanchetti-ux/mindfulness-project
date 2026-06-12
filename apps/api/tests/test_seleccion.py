"""M2 · motor puro (WS22): rotación 6+1, dedup por carta Y concepto, pool completo.

Corre contra el cartas.json real (la fuente de verdad) — si el contenido rompe un
invariante del motor (p.ej. un pilar sin cartas en un lado del eje), acá explota.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from mindful_api.services.seleccion import (
    EJE_MOVIMIENTO,
    EJE_QUIETUD,
    VENTANA_NO_REPETIR,
    Entrega,
    Perfil,
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
