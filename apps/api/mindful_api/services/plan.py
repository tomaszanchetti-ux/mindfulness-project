"""WS24 · El plan del usuario y sus límites — UN solo lugar (Roadmap v2 §1).

Regla de ingeniería: el backend aplica los límites; el front solo los muestra.
Ningún servicio hardcodea "150" o "1 foto": pide `limites(usuario)`.

Premium vigente ⇔ plan == "premium" y plan_hasta en el futuro. Al vencer,
`limites()` devuelve free solo, sin job de vencimiento (la verdad es la fecha).
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Optional

from ..db.models import Usuario

PLAN_FREE = "free"
PLAN_PREMIUM = "premium"
PRECIO_PREMIUM_EUR_ANUAL = 8.99

# Feedback privado sobre la carta: igual para free y premium, por eso no vive en
# `Limites` — pero sí acá, con el resto de los límites (un solo lugar).
COMENTARIO_CARTA_MAX = 150


@dataclass(frozen=True)
class Limites:
    """WS25 · ya no existe `compartir_ejercicio`: enviar una Pausa a alguien es de
    todos, free y premium por igual. Lo que viaja no lo elige el plan (ni el
    usuario): viaja la ficha ENTERA tal como está al momento de enviarla."""

    plan: str
    reflexion_max: int          # caracteres de la reflexión (y de la nota de compartir)
    fotos_max: int              # fotos por Pausa
    cambios_carta: int          # veces por día que puede cambiar la carta (0 = no puede)
    propone_cartas: bool        # puede escribir cartas para la comunidad (Bloque B)
    recomendaciones: bool       # puede subir recomendaciones al perfil (Bloque C)

    def dict(self) -> dict:
        return asdict(self)


LIMITES_FREE = Limites(
    plan=PLAN_FREE, reflexion_max=150, fotos_max=1,
    cambios_carta=0, propone_cartas=False, recomendaciones=False,
)
LIMITES_PREMIUM = Limites(
    plan=PLAN_PREMIUM, reflexion_max=500, fotos_max=3,
    cambios_carta=3, propone_cartas=True, recomendaciones=True,
)


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def es_premium(usuario: Usuario, ahora: Optional[datetime] = None) -> bool:
    if usuario.plan != PLAN_PREMIUM or usuario.plan_hasta is None:
        return False
    hasta = usuario.plan_hasta
    if hasta.tzinfo is None:
        hasta = hasta.replace(tzinfo=timezone.utc)
    return hasta > (ahora or _ahora())


def limites(usuario: Usuario) -> Limites:
    return LIMITES_PREMIUM if es_premium(usuario) else LIMITES_FREE


def activar_premium(usuario: Usuario, hasta: datetime) -> None:
    """La usa el webhook de Stripe (A1.2) y los tests. NO hace commit."""
    usuario.plan = PLAN_PREMIUM
    usuario.plan_hasta = hasta


def vencer_premium(usuario: Usuario) -> None:
    """Baja explícita (suscripción cancelada y vencida). NO hace commit."""
    usuario.plan = PLAN_FREE
    usuario.plan_hasta = None
