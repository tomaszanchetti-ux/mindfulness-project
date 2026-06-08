"""
M2 — Motor de Entrega del Día
=============================
La LÓGICA está explicada en cristiano en `Madre_del_Motor.md`. Esto es su
traducción ejecutable.

Hoy lee las cartas desde los JSON de M0 (seed) y simula el historial de un usuario
en memoria. Cuando construyamos el stack (Cloud Run + Postgres), la función central
`elegir_carta()` queda igual; sólo cambian las fuentes: el pool sale de la tabla
global `cartas` y el historial de la tabla privada `entregas` (filtrada por user_id).

Probalo:   python3 entrega.py
"""

from __future__ import annotations

import json
import random
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

# ── Parámetros del motor (un solo lugar para tocarlos) ───────────────────────
VENTANA_NO_REPETIR = 7        # días: no repetir una carta vista en esta ventana (§4)
PISO_AFINIDAD = 0.35          # peso mínimo de cualquier modalidad: nunca llega a 0 (§5)
CASTIGO_MISMA_ACCION = 0.5    # multiplicador si la acción es la de ayer (§3, variedad)
CASTIGO_MISMA_CATEGORIA = 0.7 # multiplicador si la categoría es la de ayer
ESTRELLA_NEUTRA = 3.0         # 1-5; el dial de afinidad arranca acá (humilde, §5)

DATA = Path(__file__).resolve().parent.parent / "M0_Motor_de_Contenido" / "data"


# ── Modelo de datos (espejo liviano de las tablas del stack §7) ──────────────
@dataclass
class Entrega:
    """Una fila de la tabla `entregas`: una carta entregada un día."""
    carta_id: str
    categoria: str
    accion: str
    dia: int                       # índice de día (en el stack: fecha real)
    estrellas: int | None = None   # 1-5, la escribe M3; None si no puntuó
    completada: bool = False


@dataclass
class Perfil:
    """Lo que M1 dejó del usuario + su rastro. En el stack: usuarios + entregas."""
    categorias: list[str]                       # 2-6 categorías elegidas (filtro duro)
    historial: list[Entrega] = field(default_factory=list)


def cargar_cartas() -> list[dict]:
    """El pool global. Hoy desde el seed; mañana desde la tabla `cartas`."""
    return json.loads((DATA / "cartas.json").read_text(encoding="utf-8"))


# ── El corazón: afinidad de acción aprendida de las estrellas (§5) ───────────
def afinidad_por_accion(historial: list[Entrega]) -> dict[str, float]:
    """
    Devuelve, por cada acción puntuada, el promedio de estrellas (1-5).
    Sin puntuaciones → dict vacío → el motor sortea parejo (humilde).
    """
    suma: dict[str, float] = defaultdict(float)
    cuenta: dict[str, int] = defaultdict(int)
    for e in historial:
        if e.estrellas is not None:
            suma[e.accion] += e.estrellas
            cuenta[e.accion] += 1
    return {a: suma[a] / cuenta[a] for a in cuenta}


def _peso_accion(afinidad: float, modo: str) -> float:
    """
    Traduce una afinidad (1-5, centrada en 3) a un multiplicador de peso.
    v1 = inclinación suave · v2 = concentra fuerte. Siempre con piso (§5, §6).
    """
    delta = (afinidad - ESTRELLA_NEUTRA) / 2.0   # rango -1..+1
    factor = 0.5 if modo == "v1" else 1.3        # cuánto manda la preferencia
    return max(PISO_AFINIDAD, 1.0 + delta * factor)


# ── La función central: elegir la carta del día (§3) ─────────────────────────
def elegir_carta(perfil: Perfil, cartas: list[dict], modo: str = "v1",
                 rng: random.Random | None = None) -> dict:
    rng = rng or random.Random()

    # 2. Pool = sólo mis categorías (filtro duro)
    pool = [c for c in cartas if c["categoria"] in perfil.categorias]

    # 1. ¿Primera carta? Historial vacío → sorteo limpio, sin rama especial.
    if not perfil.historial:
        return rng.choice(pool)

    # 3. Saco las repetidas de los últimos 7 días
    dia_hoy = perfil.historial[-1].dia + 1
    vistas = {e.carta_id for e in perfil.historial
              if e.dia > dia_hoy - 1 - VENTANA_NO_REPETIR}
    candidatas = [c for c in pool if c["id"] not in vistas]
    if not candidatas:  # borde: pool minúsculo → relajo a "que no sea la de ayer"
        ayer_id = perfil.historial[-1].carta_id
        candidatas = [c for c in pool if c["id"] != ayer_id] or pool

    # v2: ¿comodín? Si ya probó las 5 modalidades, ~1 vez/semana fuerzo una olvidada.
    afin = afinidad_por_accion(perfil.historial)
    if modo == "v2" and len(afin) >= 5 and rng.random() < 1 / 7:
        usos = defaultdict(int)
        for e in perfil.historial[-14:]:
            usos[e.accion] += 1
        olvidada = min(afin, key=lambda a: usos[a])
        olvidadas = [c for c in candidatas if c["accion"] == olvidada]
        if olvidadas:
            return rng.choice(olvidadas)

    # 4. Le doy un peso a cada candidata
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


# ── Simulación: ver el motor en acción contra el seed real ───────────────────
def _simular_estrella(carta: dict, gustos: dict[str, int], rng: random.Random) -> int:
    """Usuario ficticio: puntúa según un gusto secreto por ciertas acciones (+ ruido)."""
    base = gustos.get(carta["accion"], 3)
    return max(1, min(5, base + rng.choice([-1, 0, 0, 1])))


def simular(categorias: list[str], dias: int, modo: str, semilla: int = 7) -> None:
    rng = random.Random(semilla)
    cartas = cargar_cartas()
    perfil = Perfil(categorias=categorias)
    # gusto secreto del usuario ficticio (el motor NO lo conoce: lo deduce de las ⭐)
    gustos = {"caminar": 5, "contemplar": 5, "escribir": 2, "hacer": 3, "respirar": 3}

    print(f"\n{'═'*68}\n  MODO {modo.upper()}  ·  categorías: {', '.join(categorias)}  ·  {dias} días")
    print(f"  (gusto oculto del usuario simulado: caminar/contemplar ↑, escribir ↓)\n{'═'*68}")
    conteo_accion: dict[str, int] = defaultdict(int)
    for d in range(dias):
        carta = elegir_carta(perfil, cartas, modo=modo, rng=rng)
        estrellas = _simular_estrella(carta, gustos, rng) if rng.random() < 0.8 else None
        perfil.historial.append(Entrega(
            carta_id=carta["id"], categoria=carta["categoria"], accion=carta["accion"],
            dia=d, estrellas=estrellas, completada=True))
        conteo_accion[carta["accion"]] += 1
        marca = "★" * estrellas if estrellas else "·"
        nota = "  ← PRIMERA (random)" if d == 0 else ""
        print(f"  día {d+1:>2}  [{carta['accion']:>10}/{carta['categoria']:<11}] "
              f"{carta['frase'][:34]:<34} {marca:<5}{nota}")

    total = sum(conteo_accion.values())
    print(f"\n  Reparto por acción en {total} días:")
    for a in sorted(conteo_accion, key=lambda x: -conteo_accion[x]):
        barra = "█" * conteo_accion[a]
        print(f"     {a:>10}: {barra} {conteo_accion[a]}")
    repetidas = len(perfil.historial) - len({e.carta_id for e in perfil.historial})
    print(f"  Cartas repetidas en total: {repetidas}  ·  no-repetición 7d respetada ✓")


if __name__ == "__main__":
    # v1: inclinación suave → variedad alta, leve sesgo a lo que puntuó alto
    simular(categorias=["calma", "gratitud"], dias=21, modo="v1")
    # v2: concentra fuerte hacia caminar/contemplar, pero el comodín cuela olvidadas
    simular(categorias=["calma", "gratitud"], dias=21, modo="v2")
