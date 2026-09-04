"""WS24 · A1.2 · Pagos (Stripe). Checkout anual premium · webhook · portal.

Se cobra por WEB, sin tiendas. El front solo abre la URL que devolvemos; quien
activa premium es el webhook (nadie se hace premium desde el navegador).

Sin `MINDFUL_STRIPE_SECRET_KEY` los pagos están apagados: checkout y portal dan
503 y `/estado` avisa `configurado: false` para que el front esconda el botón.
"""

from __future__ import annotations

import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..config import settings
from ..db.base import get_session
from ..db.models import Usuario
from ..services import stripe as pagos_stripe
from ..services.plan import limites

router = APIRouter(prefix="/api/pagos", tags=["pagos"])


@router.get("/estado")
def estado(usuario: Usuario = Depends(get_current_user)) -> dict:
    """Lo que el front necesita para decidir si muestra el botón de premium."""
    lim = limites(usuario)
    return {
        "plan": lim.plan,
        "plan_hasta": usuario.plan_hasta if lim.plan == "premium" else None,
        "configurado": pagos_stripe.esta_configurado(),
    }


@router.post("/checkout")
def checkout(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Abre el Checkout de la suscripción anual. Devuelve la URL a la que ir."""
    return {"url": pagos_stripe.crear_checkout(s, usuario)}


@router.post("/portal")
def portal(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Portal de facturación de Stripe (cambiar tarjeta, facturas, cancelar)."""
    return {"url": pagos_stripe.crear_portal(s, usuario)}


@router.post("/webhook")
async def webhook(request: Request, s: Session = Depends(get_session)) -> dict:
    """Lo llama Stripe, no un usuario: SIN auth, pero con firma verificada.

    El body se lee CRUDO (`await request.body()`): la firma se calcula sobre esos
    bytes exactos, así que no se puede parsear el JSON antes de verificarla.
    Un 400 le dice a Stripe "no reintentes"; cualquier 5xx sí se reintenta.
    """
    if not settings.stripe_webhook_secret:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Webhook no configurado")

    payload = await request.body()
    firma = request.headers.get("stripe-signature", "")
    try:
        evento = stripe.Webhook.construct_event(payload, firma, settings.stripe_webhook_secret)
    except (ValueError, stripe.SignatureVerificationError) as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Firma inválida") from exc

    # Red de última instancia: la firma ya está verificada, o sea que el evento es
    # legítimo. Si igual algo revienta (una forma de payload que no previmos, la DB
    # caída), un 5xx haría que Stripe lo reintente por días — y con el mismo bug,
    # con el mismo resultado. Devolvemos 200 con `ok: False` para que deje de
    # reintentar, y dejamos el error en el log: ESE log es la alarma, y el evento
    # se puede reenviar a mano desde el dashboard de Stripe cuando esté arreglado.
    try:
        resultado = pagos_stripe.procesar_evento(s, evento)
    except Exception as exc:  # noqa: BLE001 — a propósito: nada sale de acá como 5xx
        s.rollback()
        print(
            f"[stripe:error-interno] {type(exc).__name__}: {exc}",
            flush=True,
        )
        return {"ok": False, "resultado": "error-interno"}

    return {"ok": True, "resultado": resultado}
