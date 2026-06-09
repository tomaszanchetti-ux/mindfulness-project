"""M2 · El corazón: elegir la carta del día. PORT FIEL de M2_Entrega_del_Dia/entrega.py.

La lógica es idéntica a la cerrada en WS04 (Madre_del_Motor.md). Sólo cambian las
fuentes: el `pool` sale de la tabla global `cartas` y el `historial` de la tabla
privada `entregas` (filtrada por user_id) — lo arma `services/entrega.py`.

Capas (§Madre): categoría = filtro duro · acción = preferencia blanda aprendida de
las ⭐. No-repetición 7 días. Primera carta random. Sorteo ponderado con piso.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# ── Parámetros del motor (un solo lugar para tocarlos) ───────────────────────
VENTANA_NO_REPETIR = 7        # días: no repetir una carta vista en esta ventana
PISO_AFINIDAD = 0.35          # peso mínimo de cualquier modalidad: nunca llega a 0
CASTIGO_MISMA_ACCION = 0.5    # multiplicador si la acción es la de ayer (variedad)
CASTIGO_MISMA_CATEGORIA = 0.7 # multiplicador si la categoría es la de ayer
ESTRELLA_NEUTRA = 3.0         # 1-5; el dial de afinidad arranca acá (humilde)


@dataclass
class Entrega:
    """Una fila de `entregas` (vista liviana para el motor)."""

    carta_id: str
    categoria: str
    accion: str
    dia: int                          # día como ordinal de fecha (no índice secuencial)
    estrellas: Optional[int] = None   # 1-5; None si no puntuó
    completada: bool = False


@dataclass
class Perfil:
    categorias: list[str]
    historial: list[Entrega] = field(default_factory=list)


def afinidad_por_accion(historial: list[Entrega]) -> dict[str, float]:
    """Promedio de ⭐ por acción puntuada. Sin puntuaciones → vacío → sorteo parejo."""
    suma: dict[str, float] = defaultdict(float)
    cuenta: dict[str, int] = defaultdict(int)
    for e in historial:
        if e.estrellas is not None:
            suma[e.accion] += e.estrellas
            cuenta[e.accion] += 1
    return {a: suma[a] / cuenta[a] for a in cuenta}


def _peso_accion(afinidad: float, modo: str) -> float:
    delta = (afinidad - ESTRELLA_NEUTRA) / 2.0   # rango -1..+1
    factor = 0.5 if modo == "v1" else 1.3        # cuánto manda la preferencia
    return max(PISO_AFINIDAD, 1.0 + delta * factor)


def elegir_carta(perfil: Perfil, cartas: list[dict], modo: str = "v1",
                 rng: Optional[random.Random] = None) -> dict:
    rng = rng or random.Random()

    # 2. Pool = sólo mis categorías (filtro duro)
    pool = [c for c in cartas if c["categoria"] in perfil.categorias]

    # 1. ¿Primera carta? Historial vacío → sorteo limpio.
    if not perfil.historial:
        return rng.choice(pool)

    # 3. Saco las repetidas de los últimos 7 días
    dia_hoy = perfil.historial[-1].dia + 1
    vistas = {e.carta_id for e in perfil.historial
              if e.dia > dia_hoy - 1 - VENTANA_NO_REPETIR}
    candidatas = [c for c in pool if c["id"] not in vistas]
    if not candidatas:  # pool minúsculo → relajo a "que no sea la de ayer"
        ayer_id = perfil.historial[-1].carta_id
        candidatas = [c for c in pool if c["id"] != ayer_id] or pool

    # v2: comodín. Si ya probó las 5 modalidades, ~1 vez/semana fuerzo una olvidada.
    afin = afinidad_por_accion(perfil.historial)
    if modo == "v2" and len(afin) >= 5 and rng.random() < 1 / 7:
        usos: dict[str, int] = defaultdict(int)
        for e in perfil.historial[-14:]:
            usos[e.accion] += 1
        olvidada = min(afin, key=lambda a: usos[a])
        olvidadas = [c for c in candidatas if c["accion"] == olvidada]
        if olvidadas:
            return rng.choice(olvidadas)

    # 4. Peso a cada candidata
    ayer = perfil.historial[-1]
    pesos = []
    for c in candidatas:
        peso = _peso_accion(afin.get(c["accion"], ESTRELLA_NEUTRA), modo)
        if c["accion"] == ayer.accion:
            peso *= CASTIGO_MISMA_ACCION
        if c["categoria"] == ayer.categoria:
            peso *= CASTIGO_MISMA_CATEGORIA
        pesos.append(max(PISO_AFINIDAD * 0.5, peso))

    # 5. Sorteo ponderado: a más peso, más chance; el azar decide.
    return rng.choices(candidatas, weights=pesos, k=1)[0]
