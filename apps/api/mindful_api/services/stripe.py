"""WS24 · A1.2 · Stripe: Checkout anual, Billing Portal y webhook.

Se cobra por WEB (PWA), sin tiendas: una suscripción anual de 8,99 €
("Dwellia premium"). El precio real vive en el Price de Stripe
(`MINDFUL_STRIPE_PRICE_ID`); acá no se hardcodea ningún importe.

Quién manda: el webhook. El front nunca activa premium — solo abre el Checkout.
La verdad del plan sigue siendo `usuarios.plan_hasta` (services/plan.py).

EVENTOS A SUSCRIBIR EN EL DASHBOARD DE STRIPE (son CINCO, no tres):
  1) checkout.session.completed                 → alta (activa si está cobrada)
  2) checkout.session.async_payment_succeeded   → alta de un pago DIFERIDO que
     terminó bien (SEPA débito, boleto…): es el que realmente activa premium en
     esos métodos, porque el `completed` llega con `payment_status="unpaid"`.
  3) checkout.session.async_payment_failed      → el pago diferido falló: no
     activa nada, solo queda en el log.
  4) invoice.paid                               → renovación anual
  5) customer.subscription.deleted              → baja
Si falta el (2), quien paga por SEPA nunca recibe su premium. Si falta el (1),
nadie se activa. Los cinco, o la caja no cierra.

Cuatro reglas que evitan los dolores clásicos de un webhook:
  1) IDEMPOTENCIA — Stripe reintenta y puede repetir un evento. Procesar el mismo
     evento dos veces deja exactamente el mismo estado (por eso la fecha de
     respaldo se ancla en `created` del evento, no en "ahora").
  2) NUNCA 500 — ni por un usuario que no encontramos, ni por un payload con una
     forma rara. Devolvemos "ignorado" y lo registramos. Un 500 haría que Stripe
     reintente para siempre.
  3) NO SE ACTIVA SIN COBRO — `checkout.session.completed` NO significa "pagó":
     significa "terminó el formulario". Quien manda es `payment_status`.
  4) SIN CUSTOMER ANCLADO NO HAY PREMIUM — si no podemos guardar el
     `stripe_customer_id` del usuario, la renovación y la baja de esa suscripción
     no van a encontrar a nadie y el usuario se queda premium para siempre sin
     poder ni abrir el portal. Preferimos no activar y que quede en el log.
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

# `usuarios.stripe_customer_id` es String(64) en la DB. Un id más largo no es un
# customer de Stripe (los reales son `cus_` + ~14 chars): guardarlo daría DataError
# → 500 → Stripe reintentando para siempre.
CUSTOMER_ID_MAX = 64

# Un Checkout puede terminar sin haber cobrado. Solo estos dos estados son plata
# en la mano ("no_payment_required" = cupón del 100 %, prueba gratis).
PAGOS_OK = ("paid", "no_payment_required")


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
def procesar_evento(s: Session, evento) -> str:
    """Aplica UN evento de Stripe. Devuelve la etiqueta de lo que hizo.

    "premium-activado" | "premium-renovado" | "premium-vencido" |
    "pago-pendiente" | "ignorado".

    `evento` viene de `construct_event`, que devuelve lo que haya en el body: si
    el JSON no es un objeto, o `data`/`data.object` no son diccionarios, no nos
    ponemos creativos — "ignorado" y al log.
    """
    if not isinstance(evento, dict):
        return _ignorar("evento-no-dict", type(evento).__name__)

    tipo = evento.get("type") or ""
    data = evento.get("data")
    data = data if isinstance(data, dict) else {}
    objeto = data.get("object")
    objeto = objeto if isinstance(objeto, dict) else {}

    # Ancla de la fecha de respaldo: el momento del EVENTO, no el de la request.
    # Así reprocesar el mismo evento mañana da la misma fecha (idempotencia real).
    # Si `created` del evento viniera roto, el objeto de Stripe también trae el
    # suyo; `_ahora()` es la ÚLTIMA opción (y la única que rompe la idempotencia).
    creado = (
        _desde_epoch(evento.get("created"))
        or _desde_epoch(objeto.get("created"))
        or _ahora()
    )

    if tipo == "checkout.session.completed":
        return _alta(s, objeto, creado)
    if tipo == "checkout.session.async_payment_succeeded":
        # El pago diferido entró. Este evento ES la confirmación del cobro: no
        # hace falta volver a mirar `payment_status` (Stripe puede tardar en
        # ponerlo en "paid" en la copia de la sesión que viaja en el evento).
        return _alta(s, objeto, creado, cobro_confirmado=True)
    if tipo == "checkout.session.async_payment_failed":
        print(
            f"[stripe:pago-diferido-fallido] session={objeto.get('id')} "
            f"ref={objeto.get('client_reference_id')}",
            flush=True,
        )
        return "ignorado"
    if tipo == "invoice.paid":
        return _renovacion(s, objeto, creado)
    if tipo == "customer.subscription.deleted":
        return _baja(s, objeto)
    return "ignorado"


def _alta(s: Session, sesion: dict, creado: datetime, cobro_confirmado: bool = False) -> str:
    """Alta de la suscripción: anclamos su cliente de Stripe y —si pagó— damos premium.

    Tres candados, en orden: que la sesión sea la que esperamos (completa y de
    suscripción), que el customer sea anclable a ESTE usuario, y que esté cobrada.
    """
    usuario = _por_id(s, sesion.get("client_reference_id"))
    if usuario is None:
        usuario = _por_customer(s, _customer_id(sesion.get("customer")))
    if usuario is None:
        return _ignorar("checkout.session.*", sesion.get("client_reference_id"))

    rechazo = _sesion_inesperada(sesion)
    if rechazo is not None:
        print(f"[stripe:sesion-no-activable] {rechazo} usuario={usuario.id}", flush=True)
        return "ignorado"

    customer = _customer_id(sesion.get("customer"))
    if customer is None or not _anclar_customer(s, usuario, customer):
        # Sin customer nuestro no hay renovación ni baja ni portal: activar acá
        # sería regalar premium vitalicio y sin forma de gestionarlo.
        print(
            f"[stripe:customer-no-anclado] usuario={usuario.id} "
            f"customer={sesion.get('customer')!r}",
            flush=True,
        )
        return "ignorado"

    if not (cobro_confirmado or _cobrada(sesion)):
        # Pago diferido (SEPA débito, boleto…): la sesión está "complete" pero
        # todavía no entró la plata. Guardamos el customer para poder engancharlo
        # cuando llegue `async_payment_succeeded`, pero NO activamos premium.
        s.commit()
        print(
            f"[stripe:pago-pendiente] usuario={usuario.id} "
            f"payment_status={sesion.get('payment_status')!r}",
            flush=True,
        )
        return "pago-pendiente"

    hasta = _fin_de_suscripcion(sesion.get("subscription")) or (creado + timedelta(days=DIAS_ANUAL))
    _activar(usuario, hasta)
    s.commit()
    return "premium-activado"


def _renovacion(s: Session, factura: dict, creado: datetime) -> str:
    """Cobró el año siguiente: estiramos la fecha hasta el fin del período pagado."""
    usuario = _por_customer(s, _customer_id(factura.get("customer")))
    if usuario is None:
        return _ignorar("invoice.paid", factura.get("customer"))

    hasta = _fin_de_factura(factura) or (creado + timedelta(days=DIAS_ANUAL))
    _activar(usuario, hasta)
    s.commit()
    return "premium-renovado"


def _baja(s: Session, suscripcion: dict) -> str:
    """La suscripción murió en Stripe: vuelve a free."""
    usuario = _por_customer(s, _customer_id(suscripcion.get("customer")))
    if usuario is None:
        return _ignorar("customer.subscription.deleted", suscripcion.get("customer"))

    vencer_premium(usuario)
    s.commit()
    return "premium-vencido"


# ── Piezas chicas ───────────────────────────────────────────────────────────
def _ahora() -> datetime:
    return datetime.now(timezone.utc)


def _desde_epoch(ts) -> Optional[datetime]:
    # `bool` es subclase de `int`: `True` daría 1970-01-01. No es una fecha.
    if isinstance(ts, bool) or not isinstance(ts, (int, float)):
        return None
    try:
        return datetime.fromtimestamp(ts, tz=timezone.utc)
    except (OverflowError, OSError, ValueError):
        # Un epoch absurdo (1e30) no es motivo para un 500.
        return None


def _customer_id(valor) -> Optional[str]:
    """El `customer` de Stripe puede venir como id (`"cus_…"`) o EXPANDIDO
    (`{"id": "cus_…", "object": "customer"}`). Devuelve siempre el id, o None.

    None también cuando el id no entra en la columna (String(64)): guardarlo daría
    DataError → 500 → reintentos infinitos de Stripe.
    """
    if isinstance(valor, dict):
        valor = valor.get("id")
    if not isinstance(valor, str) or not valor:
        return None
    if len(valor) > CUSTOMER_ID_MAX:
        print(f"[stripe:customer-id-invalido] largo={len(valor)}", flush=True)
        return None
    return valor


def _sesion_inesperada(sesion: dict) -> Optional[str]:
    """Motivo por el que esta sesión NO puede dar de alta nada, o None si está bien.

    Campos ausentes = payload mínimo (tests, eventos recortados): se asumen los
    valores normales de nuestro Checkout (`complete` / `subscription`), porque el
    único campo del que dependemos de verdad para la plata es `payment_status`.
    """
    estado = sesion.get("status")
    if estado is not None and estado != "complete":
        return f"status={estado!r}"
    modo = sesion.get("mode")
    if modo is not None and modo != "subscription":
        # Un pago único no crea suscripción: no hay renovación ni baja que seguir.
        return f"mode={modo!r}"
    return None


def _cobrada(sesion: dict) -> bool:
    """¿Entró la plata? `checkout.session.completed` NO lo garantiza.

    `payment_status` ausente se trata como "paid": los payloads mínimos (tests y
    eventos viejos) no lo traen, y el candado que importa —el de los métodos de
    pago diferidos— siempre manda el campo con "unpaid".
    """
    pago = sesion.get("payment_status")
    if pago is None:
        return True
    return pago in PAGOS_OK


def _por_id(s: Session, usuario_id) -> Optional[Usuario]:
    if not usuario_id:
        return None
    return s.get(Usuario, str(usuario_id))


def _por_customer(s: Session, customer: Optional[str]) -> Optional[Usuario]:
    if not customer or not isinstance(customer, str):
        return None
    return s.scalar(select(Usuario).where(Usuario.stripe_customer_id == customer))


def _ignorar(tipo: str, referencia) -> str:
    """Sin usuario no hay nada que hacer, pero queda dicho en el log (nunca 500)."""
    print(f"[stripe:sin-usuario] evento={tipo} ref={referencia}", flush=True)
    return "ignorado"


def _anclar_customer(s: Session, usuario: Usuario, customer: str) -> bool:
    """Deja el customer pegado al usuario. False si es de OTRO usuario.

    `stripe_customer_id` es único: si otro usuario ya lo tiene, no lo pisamos
    (sería un IntegrityError → 500 → Stripe reintentando para siempre). Y sin
    poder anclarlo, tampoco activamos: toda renovación y baja de ese customer
    caería sobre el otro usuario.
    """
    if usuario.stripe_customer_id == customer:
        return True
    otro = _por_customer(s, customer)
    if otro is not None and otro.id != usuario.id:
        print(f"[stripe:customer-duplicado] customer={customer} usuario={usuario.id}", flush=True)
        return False
    usuario.stripe_customer_id = customer
    return True


def _con_utc(momento: Optional[datetime]) -> Optional[datetime]:
    """Postgres puede devolver la fecha naive (columna sin tz, UPDATE a mano).
    Comparar naive con aware es TypeError: normalizamos SIEMPRE a UTC."""
    if momento is not None and momento.tzinfo is None:
        return momento.replace(tzinfo=timezone.utc)
    return momento


def _activar(usuario: Usuario, hasta: datetime) -> None:
    """Activa premium sin mover NUNCA la fecha hacia atrás.

    Stripe no garantiza el orden de entrega: si la renovación llega antes que el
    alta, el alta no debe recortar el año ya pagado.
    """
    hasta = _con_utc(hasta)
    actual = _con_utc(usuario.plan_hasta)
    if actual is not None and usuario.plan == PLAN_PREMIUM and actual > hasta:
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
    items = suscripcion.get("items")
    datos = items.get("data") if isinstance(items, dict) else None
    for item in datos if isinstance(datos, list) else []:
        if not isinstance(item, dict):
            continue
        fin = _desde_epoch(item.get("current_period_end"))
        if fin is not None:
            return fin
    return None


def _fin_de_factura(factura: dict) -> Optional[datetime]:
    """El `period.end` de la línea de suscripción de la factura."""
    lineas_raw = factura.get("lines")
    datos = lineas_raw.get("data") if isinstance(lineas_raw, dict) else None
    lineas = [linea for linea in datos if isinstance(linea, dict)] if isinstance(datos, list) else []
    de_suscripcion = [
        linea
        for linea in lineas
        if linea.get("subscription")
        or (linea.get("parent") if isinstance(linea.get("parent"), dict) else {}).get(
            "subscription_item_details"
        )
    ]
    fines = []
    for linea in de_suscripcion or lineas:
        periodo = linea.get("period")
        fin = _desde_epoch(periodo.get("end") if isinstance(periodo, dict) else None)
        if fin is not None:
            fines.append(fin)
    return max(fines) if fines else None
