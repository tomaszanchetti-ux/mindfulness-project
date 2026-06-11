"""M2 · motor puro (WS17): rotación 6+1, dedup por carta Y concepto, piso escribir.

Corre contra el cartas.json real (la fuente de verdad) — si el contenido rompe un
invariante del motor (p.ej. una categoría sin cartas de "escribir"), acá explota.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from mindful_api.services.seleccion import (
    ACCION_PISO,
    VENTANA_NO_REPETIR,
    Entrega,
    Perfil,
    elegir_carta,
)

DATA = Path(__file__).resolve().parents[3] / "M0_Motor_de_Contenido" / "data"
CARTAS = json.loads((DATA / "cartas.json").read_text(encoding="utf-8"))
CATEGORIAS = {c["categoria"] for c in CARTAS}


def _simular(dias: int, acciones: list[str], seed: int) -> list[Entrega]:
    """Simula `dias` entregas consecutivas y devuelve el historial."""
    rng = random.Random(seed)
    historial: list[Entrega] = []
    for i in range(dias):
        perfil = Perfil(acciones=acciones, historial=historial)
        carta = elegir_carta(perfil, CARTAS, rng=rng)
        historial.append(Entrega(
            carta_id=carta["id"], categoria=carta["categoria"],
            accion=carta["accion"], dia=1000 + i, concepto=carta["concepto"],
        ))
    return historial


def test_contenido_cumple_invariante_del_piso():
    # Toda categoría tiene cartas de "escribir": la rotación nunca queda vacía.
    for cat in CATEGORIAS:
        assert any(c["categoria"] == cat and c["accion"] == ACCION_PISO for c in CARTAS)


def test_primera_carta_sale_de_todo_el_mazo():
    carta = elegir_carta(Perfil(), CARTAS, rng=random.Random(7))
    assert carta in CARTAS


def test_rotacion_primeros_6_dias_cubren_los_6_campos():
    for seed in range(10):
        historial = _simular(6, [], seed)
        assert {e.categoria for e in historial} == CATEGORIAS


def test_rotacion_toda_categoria_vuelve_en_9_dias_o_menos():
    # 6 días de rotación + comodín (+1 de auto-corrección) → gap máximo ~9.
    for seed in range(5):
        historial = _simular(60, [], seed)
        ultimo: dict[str, int] = {}
        for e in historial:
            if e.categoria in ultimo:
                assert e.dia - ultimo[e.categoria] <= 9, (
                    f"{e.categoria} desapareció {e.dia - ultimo[e.categoria]} días (seed {seed})"
                )
            ultimo[e.categoria] = e.dia


def test_ni_carta_ni_concepto_se_repiten_en_la_ventana():
    for seed in range(5):
        historial = _simular(90, [], seed)
        for i, e in enumerate(historial):
            ventana = [v for v in historial[:i]
                       if v.dia > e.dia - VENTANA_NO_REPETIR]
            assert e.carta_id not in {v.carta_id for v in ventana}
            assert e.concepto not in {v.concepto for v in ventana}, (
                f"concepto '{e.concepto}' repetido en la ventana (seed {seed}, día {e.dia})"
            )


def test_filtro_de_modalidades_respeta_piso_escribir():
    historial = _simular(30, ["respirar"], 3)
    assert all(e.accion in {"respirar", ACCION_PISO} for e in historial)
    # La rotación sigue cubriendo los 6 campos (vía el piso "escribir").
    assert {e.categoria for e in historial[:6]} == CATEGORIAS


def test_pool_minimo_no_rompe_y_no_repite_la_de_ayer():
    # Solo "escribir" (pool 18 cartas, 3 por categoría): el caso más chico posible.
    historial = _simular(45, [ACCION_PISO], 11)
    assert len(historial) == 45
    for ayer, hoy in zip(historial, historial[1:]):
        assert hoy.carta_id != ayer.carta_id
