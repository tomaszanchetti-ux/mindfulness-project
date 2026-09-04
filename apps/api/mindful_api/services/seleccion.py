"""M2 · El corazón: elegir la carta del día.

WS22 — NADA SE ELIGE (deroga el filtro de acciones de WS10; completa el arco de
WS17): los pilares van TODOS cada semana (rotación 6+1) y, dentro del pilar del
día, el pool son TODAS sus cartas (las 4 acciones iniciales viables). "Escribir"
ya no es una acción del enum: es el cierre universal de toda pausa (canon §0).
La válvula del "hoy no quiero moverme" es el cambio de carta (v2 premium), que
cruza el eje quietud (contemplar·respirar) ↔ movimiento (caminar/pasear·hacer).

La semana del usuario ES la rotación:
  · Día "normal": se sirve una categoría que NO apareció en los últimos 6 días
    (elegida al azar entre las pendientes → el orden de la semana sorprende).
  · Si las 6 ya aparecieron en la ventana → día COMODÍN: cualquier categoría
    salvo la de ayer. (v2: el comodín aprende de las ⭐ del usuario.)
  · La rotación se auto-corrige sola tras el comodín (la ventana destraba la
    categoría más vieja al día siguiente).

Dentro de la categoría del día, dos ventanas de no-repetición de 7 días:
  · por CARTA (no ver la misma carta) y
  · por CONCEPTO (no vivir la misma experiencia con otra etiqueta — cartas
    "gemelas" comparten `concepto`, ver canon_cartas.md R5).
Fallback elegante si el pool se achica: suelta primero el concepto, después la
carta (nunca la de ayer), nunca rompe.

Capa blanda intacta (WS04): preferencia de acción aprendida de las ⭐, sorteo
ponderado con piso (ninguna acción llega a 0) y castigo a repetir la acción
de ayer. El castigo por categoría desaparece: la rotación lo garantiza mejor.
"""

from __future__ import annotations

import random
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

# ── Parámetros del motor (un solo lugar para tocarlos) ───────────────────────
VENTANA_NO_REPETIR = 7        # días: no repetir carta NI concepto vistos en esta ventana
VENTANA_ROTACION = 6          # días: una categoría no vuelve hasta pasar por las demás
PISO_AFINIDAD = 0.35          # peso mínimo de cualquier acción: nunca llega a 0
CASTIGO_MISMA_ACCION = 0.5    # multiplicador si la acción es la de ayer (variedad)
ESTRELLA_NEUTRA = 3.0         # 1-5; el dial de afinidad arranca acá (humilde)
TOTAL_ACCIONES = 4            # WS22: contemplar · respirar · caminar (pasear) · hacer

# Eje quietud↔movimiento (WS22): lo usa el cambio de carta v2 (cruza el eje).
EJE_QUIETUD = {"contemplar", "respirar"}
EJE_MOVIMIENTO = {"caminar", "hacer"}


@dataclass
class Entrega:
    """Una fila de `entregas` (vista liviana para el motor)."""

    carta_id: str
    categoria: str
    accion: str
    dia: int                          # día como ordinal de fecha (no índice secuencial)
    concepto: Optional[str] = None    # WS17: huella de dedup (viene del join con cartas)
    estrellas: Optional[int] = None   # 1-5; None si no puntuó
    completada: bool = False


@dataclass
class Perfil:
    """WS22: nada se elige — ni pilares (WS17) ni acciones. Solo el historial."""

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


def _categoria_del_dia(historial: list[Entrega], todas: set[str], dia_hoy: int,
                       rng: random.Random) -> str:
    """Rotación 6+1: una categoría pendiente al azar; si no quedan, comodín."""
    recientes = {e.categoria for e in historial
                 if e.dia > dia_hoy - 1 - VENTANA_ROTACION}
    pendientes = sorted(todas - recientes)
    if pendientes:
        return rng.choice(pendientes)
    # Comodín: cualquier categoría salvo la de ayer (v2: ponderado por gustos).
    ayer = historial[-1].categoria
    opciones = sorted(todas - {ayer}) or sorted(todas)
    return rng.choice(opciones)


def elegir_carta(perfil: Perfil, cartas: list[dict], modo: str = "v1",
                 rng: Optional[random.Random] = None) -> dict:
    rng = rng or random.Random()

    # 1. Pool = TODO el mazo (WS22: nada se filtra; toda categoría tiene cartas
    #    en ambos lados del eje quietud↔movimiento → la rotación nunca queda vacía).
    pool = list(cartas)

    # 2. ¿Primera carta? Historial vacío → sorteo limpio sobre todo el pool.
    if not perfil.historial:
        return rng.choice(pool)

    dia_hoy = perfil.historial[-1].dia + 1

    # 3. Rotación: la categoría de hoy (pendiente de la semana, o comodín).
    todas = {c["categoria"] for c in cartas}
    categoria_hoy = _categoria_del_dia(perfil.historial, todas, dia_hoy, rng)
    candidatas = [c for c in pool if c["categoria"] == categoria_hoy]

    # 4. Ventanas de no-repetición (7 días): ni la misma carta NI el mismo concepto.
    en_ventana = [e for e in perfil.historial
                  if e.dia > dia_hoy - 1 - VENTANA_NO_REPETIR]
    vistas = {e.carta_id for e in en_ventana}
    conceptos_vistos = {e.concepto for e in en_ventana if e.concepto}

    frescas = [c for c in candidatas
               if c["id"] not in vistas and c.get("concepto") not in conceptos_vistos]
    if not frescas:  # pool chico → suelto el dedup por concepto
        frescas = [c for c in candidatas if c["id"] not in vistas]
    if not frescas:  # más chico aún → al menos que no sea la de ayer
        ayer_id = perfil.historial[-1].carta_id
        frescas = [c for c in candidatas if c["id"] != ayer_id] or candidatas

    # v2: comodín de acción. Si ya probó las 4, ~1 vez/semana fuerzo una olvidada.
    afin = afinidad_por_accion(perfil.historial)
    if modo == "v2" and len(afin) >= TOTAL_ACCIONES and rng.random() < 1 / 7:
        usos: dict[str, int] = defaultdict(int)
        for e in perfil.historial[-14:]:
            usos[e.accion] += 1
        olvidada = min(afin, key=lambda a: usos[a])
        olvidadas = [c for c in frescas if c["accion"] == olvidada]
        if olvidadas:
            return rng.choice(olvidadas)

    # 5. Peso a cada candidata (afinidad de modalidad + variedad vs ayer).
    ayer = perfil.historial[-1]
    pesos = []
    for c in frescas:
        peso = _peso_accion(afin.get(c["accion"], ESTRELLA_NEUTRA), modo)
        if c["accion"] == ayer.accion:
            peso *= CASTIGO_MISMA_ACCION
        pesos.append(max(PISO_AFINIDAD * 0.5, peso))

    # 6. Sorteo ponderado: a más peso, más chance; el azar decide.
    return rng.choices(frescas, weights=pesos, k=1)[0]


# ─────────────────────────────────────────────────────────────────────────────
# WS24 · A1.3 · Cambiar la carta del día (premium, hasta 3 veces)
#
# La válvula del "hoy no quiero moverme": misma pausa, mismo pilar, OTRO eje.
# Sigue llegando UNA carta por día; el cambio la reemplaza, no la duplica.
# ─────────────────────────────────────────────────────────────────────────────
class SinCandidatas(Exception):
    """El pilar se quedó sin cartas para ofrecer (el servicio lo traduce a 409)."""


def _eje_contrario(accion: str) -> set:
    """Quietud ↔ movimiento. Acción fuera del eje → conjunto vacío (no fuerza nada)."""
    if accion in EJE_QUIETUD:
        return EJE_MOVIMIENTO
    if accion in EJE_MOVIMIENTO:
        return EJE_QUIETUD
    return set()


def _sortear_ponderado(candidatas: list[dict], historial: list[Entrega],
                       rng: random.Random) -> dict:
    """Mismo criterio blando que `elegir_carta`: las ⭐ inclinan, nunca deciden."""
    afin = afinidad_por_accion(historial)
    pesos = [
        max(PISO_AFINIDAD * 0.5, _peso_accion(afin.get(c["accion"], ESTRELLA_NEUTRA), "v2"))
        for c in candidatas
    ]
    return rng.choices(candidatas, weights=pesos, k=1)[0]


def cambiar_carta(perfil: Perfil, pool: list[dict], actual: dict,
                  descartadas: set, hoy: int,
                  rng: Optional[random.Random] = None) -> dict:
    """La carta de reemplazo de hoy. Determinística bajo `rng`, como `elegir_carta`.

    `perfil.historial` NO incluye la entrega de hoy (si no, la carta que se está
    cambiando se bloquearía a sí misma y ensuciaría la ventana de concepto).
    `descartadas` son los ids ya rechazados hoy; `hoy` es el ordinal de la fecha.

    Cascada de fallbacks (nunca rompe salvo que el pilar quede realmente vacío):
      1. Cruza el eje, con las dos ventanas de 7 días (carta y concepto).
      2. Mismo pilar sin cruzar el eje, con las dos ventanas.
      3. Suelta la ventana de concepto (queda la de carta).
      4. Cualquier carta del pilar que no esté descartada.
    En los cuatro niveles: nunca la actual, nunca una descartada hoy, nunca la de
    ayer. Sin candidatas → `SinCandidatas`.
    """
    rng = rng or random.Random()

    # Lo que hoy ya no puede volver: la carta en pantalla + las que descartó.
    fuera = set(descartadas) | {actual["id"]}
    ayer_id = perfil.historial[-1].carta_id if perfil.historial else None

    candidatas = [
        c for c in pool
        if c["categoria"] == actual["categoria"]
        and c["id"] not in fuera
        and c["id"] != ayer_id
    ]

    # Ventanas de no-repetición (idénticas a las de `elegir_carta`).
    en_ventana = [e for e in perfil.historial if e.dia > hoy - 1 - VENTANA_NO_REPETIR]
    vistas = {e.carta_id for e in en_ventana}
    conceptos_vistos = {e.concepto for e in en_ventana if e.concepto}
    # Una "gemela" de la carta que acaba de rechazar es la misma experiencia con
    # otra etiqueta: los conceptos de hoy también cuentan (canon_cartas.md R5).
    conceptos_vistos |= {c.get("concepto") for c in pool
                         if c["id"] in fuera and c.get("concepto")}

    sin_repetir = [c for c in candidatas if c["id"] not in vistas]
    frescas = [c for c in sin_repetir if c.get("concepto") not in conceptos_vistos]
    contrario = _eje_contrario(actual["accion"])

    for nivel in (
        [c for c in frescas if c["accion"] in contrario],   # 1. cruza el eje
        frescas,                                            # 2. mismo pilar, mismo eje
        sin_repetir,                                        # 3. suelto el concepto
        candidatas,                                         # 4. lo que quede del pilar
    ):
        if nivel:
            return _sortear_ponderado(nivel, perfil.historial, rng)

    raise SinCandidatas("No quedan cartas para cambiar hoy")
