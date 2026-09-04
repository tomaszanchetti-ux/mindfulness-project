"""WS24 · A1.2 · Stripe: Checkout anual, Billing Portal y webhook.

Se cobra por WEB (PWA), sin tiendas: una suscripción anual de 8,99 €
("Dwellia premium"). El precio real vive en el Price de Stripe
(`MINDFUL_STRIPE_PRICE_ID`); acá no se hardcodea ningún importe.

Quién manda: el webhook. El front nunca activa premium — solo abre el Checkout.
La verdad del plan sigue siendo `usuarios.plan_hasta` (services/plan.py).

Dos reglas que evitan los dolores clásicos de un webhook:
  1) IDEMPOTENCIA — Stripe reintenta y puede repetir un evento. Procesar el mismo
     evento dos veces deja exactamente el mismo estado (por eso la fecha de
     respaldo se ancla en `created` del evento, no en "ahora").
  2) NUNCA 500 por un usuario que no encontramos — devolvemos "ignorado" y lo
     registramos. Un 500 haría que Stripe reintente para siempre.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional

import stripe
from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..config import settings
from ..db.models import Usuario
from .plan import PLAN_PREMIUM, activar_premium, vencer_premium

# La suscripción es anual. 366 días = un año con margen para el bisiesto; es solo
# el respaldo para cuando el evento no trae el fin de período real de Stripe.
DIAS_ANUAL = 366


def esta_configurado() -> bool:
    """Sin clave secreta los pagos están apagados (dev/tests y prod hasta que Tomás
    cree la cuenta). El front lo consulta para no mostrar el botón de premium."""
    return bool(settings.stripe_secret_key)


def _preparar() -> None:
    """Exige pagos encendidos y deja la clave lista para el SDK."""
    if not esta_configurado():
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Pagos no configurados")
    stripe.api_key = settings.stripe_secret_key


# ── Cara al usuario: abrir Checkout y el portal de facturación ───────────────
def crear_checkout(s: Session, usuario: Usuario) -> str:
    """Devuelve la URL del Checkout de Stripe (el front redirige ahí).

    `client_reference_id` es nuestro puente: el webhook usa ese id para saber a
    quién activarle premium (Stripe nos lo devuelve tal cual en el evento).
    """
    _preparar()
    if not settings.stripe_price_id:
        # Clave puesta pero sin Price: no hay nada que vender todavía.
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "Pagos no configurados")
    params = {
        "mode": "subscription",
        "line_items": [{"price": settings.stripe_price_id, "quantity": 1}],
        "client_reference_id": usuario.id,
        "success_url": f"{settings.app_url}/premium/gracias?session_id={{CHECKOUT_SESSION_ID}}",
        "cancel_url": f"{settings.app_url}/premium",
        "allow_promotion_codes": True,
    }
    # Si ya compró alguna vez, reusamos su cliente para no duplicarlo en Stripe.
    if usuario.stripe_customer_id:
        params["customer"] = usuario.stripe_customer_id
    else:
        params["customer_email"] = usuario.email

    sesion = stripe.checkout.Session.create(**params)
    return sesion.url


def crear_portal(s: Session, usuario: Usuario) -> str:
    """Portal de facturación: cambiar tarjeta, ver facturas, cancelar. Lo gestiona Stripe."""
    _preparar()
    if not usuario.stripe_customer_id:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Todavía no hay una suscripción para gestionar"
        )
    sesion = stripe.billing_portal.Session.create(
        customer=usuario.stripe_customer_id,
        return_url=f"{settings.app_url}/premium",
    )
    return sesion.url


# ── El webhook ──────────────────────────────────────────────────────────────
def procesar_evento(s: Session, evento: dict) -> str:
    """Aplica UN evento de Stripe. Devuelve la etiqueta de lo que hizo.

    "premium-activado" | "premium-renovado" | "premium-vencido" | "ignorado".
    """
    tipo = evento.get("type") or ""
    objeto = (evento.get("data") or {}).get("object") or {}
    # Ancla de la fecha de respaldo: el momento del EVENTO, no el de la request.
    # Así reprocesar el mismo evento mañana da la misma fecha (idempotencia real).
    creado = _desde_epoch(evento.get("created")) or _ahora()

    if tipo == "checkout.session.completed":
        return _alta(s, objeto, creado)
    if tipo == "invoice.paid":
        return _renovacion(s, objeto, creado)
    if tipo == "customer.subscription.deleted":
        return _baja(s, objeto)
    return "ignorado"


def _alta(s: Session, sesion: dict, creado: datetime) -> str:
    """Pagó por primera vez: guardamos su cliente de Stripe y le damos premium."""
    usuario = _por_id(s, sesion.get("client_reference_id"))
    if usuario is None:
        usuario = _por_customer(s, sesion.get("customer"))
    if usuario is None:
        return _ignorar("checkout.session.completed", sesion.get("client_reference_id"))

    _guardar_customer(s, usuario, sesion.get("customer"))
    hasta = _fin_de_suscripcion(sesion.get("subscription")) or (creado + timedelta(days=DIAS_ANUAL))
    _activar(usuario, hasta)
    s.commit()
    return "premium-activado"


def _renovacion(s: Session, factura: dict, creado: datetime) -> str:
    """Cobró el año siguiente: estiramos la fecha hasta el fin del período pagado."""
    usuario = _por_customer(s, factura.get("customer"))
    if usuario is None:
        return _ignorar("invoice.paid", factura.get("customer"))

    hasta = _fin_de_factura(factura) or (creado + timedelta(days=DIAS_ANUAL))
    _activar(usuario, hasta)
    s.commit()
    return "premium-renovado"


def _baja(s: Session, suscripcion: dict) -> str:
    """La suscripción murió en Stripe: vuelve a free."""
    usuario = _por_customer(s, suscripcion.get("customer"))
    if usuario is None:
        return _ignorar("customer.subscription.deleted", suscripcion.get("customer"))

    vencer_premium(usuario)
    s.commit()
    return "premium-vencido"


# ── Piezas chicas ───────────────────────────────────────────────────────────
def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _desde_epoch(ts) -> Optional[datetime]:
    if not isinstance(ts, (int, float)):
        return None
    return datetime.fromtimestamp(ts, tz=timezone.utc)


def _por_id(s: Session, usuario_id) -> Optional[Usuario]:
    if not usuario_id:
        return None
    return s.get(Usuario, str(usuario_id))


def _por_customer(s: Session, customer) -> Optional[Usuario]:
    if not customer or not isinstance(customer, str):
        return None
    return s.scalar(select(Usuario).where(Usuario.stripe_customer_id == customer))


def _ignorar(tipo: str, referencia) -> str:
    """Sin usuario no hay nada que hacer, pero queda dicho en el log (nunca 500)."""
    print(f"[stripe:sin-usuario] evento={tipo} ref={referencia}", flush=True)
    return "ignorado"


def _guardar_customer(s: Session, usuario: Usuario, customer) -> None:
    if not customer or not isinstance(customer, str) or usuario.stripe_customer_id == customer:
        return
    # `stripe_customer_id` es único: si otro usuario ya lo tiene, no lo pisamos
    # (sería un IntegrityError → 500 → Stripe reintentando para siempre).
    otro = _por_customer(s, customer)
    if otro is not None and otro.id != usuario.id:
        print(f"[stripe:customer-duplicado] customer={customer} usuario={usuario.id}", flush=True)
        return
    usuario.stripe_customer_id = customer


def _activar(usuario: Usuario, hasta: datetime) -> None:
    """Activa premium sin mover NUNCA la fecha hacia atrás.

    Stripe no garantiza el orden de entrega: si la renovación llega antes que el
    alta, el alta no debe recortar el año ya pagado.
    """
    actual = usuario.plan_hasta
    if actual is not None:
        if actual.tzinfo is None:
            actual = actual.replace(tzinfo=timezone.utc)
        if usuario.plan == PLAN_PREMIUM and actual > hasta:
            hasta = actual
    activar_premium(usuario, hasta)


def _fin_de_suscripcion(suscripcion) -> Optional[datetime]:
    """Fin del período, si el evento trae la suscripción expandida (no siempre)."""
    if not isinstance(suscripcion, dict):
        return None
    fin = _desde_epoch(suscripcion.get("current_period_end"))
    if fin is not None:
        return fin
    # En las versiones nuevas de la API el período vive en cada item.
    for item in (suscripcion.get("items") or {}).get("data") or []:
        fin = _desde_epoch(item.get("current_period_end"))
        if fin is not None:
            return fin
    return None


def _fin_de_factura(factura: dict) -> Optional[datetime]:
    """El `period.end` de la línea de suscripción de la factura."""
    lineas = (factura.get("lines") or {}).get("data") or []
    de_suscripcion = [
        linea
        for linea in lineas
        if linea.get("subscription")
        or (linea.get("parent") or {}).get("subscription_item_details")
    ]
    fines = []
    for linea in de_suscripcion or lineas:
        fin = _desde_epoch((linea.get("period") or {}).get("end"))
        if fin is not None:
            fines.append(fin)
    return max(fines) if fines else None
