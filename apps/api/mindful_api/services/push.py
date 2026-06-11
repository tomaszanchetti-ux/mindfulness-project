"""Envío de push web (WS21). Estándar Web Push + VAPID, sin FCM ni terceros.

Sin `MINDFUL_VAPID_PRIVATE_KEY` configurada el push está apagado (dev/tests).
La llave pública (derivada de la privada) vive en el front — es pública por diseño.
"""

from __future__ import annotations

import json

from pywebpush import WebPushException, webpush

from ..config import settings
from ..db.models import PushSuscripcion


def enviar_push(sus: PushSuscripcion, titulo: str, cuerpo: str, url: str) -> str:
    """Empuja a UN dispositivo. Devuelve "ok" | "gone" | "error" | "off".

    "gone" = el push service dio de baja la suscripción (404/410): borrar la fila.
    Nunca levanta: un dispositivo caído no debe tumbar el barrido.
    """
    if not settings.vapid_private_key:
        return "off"
    try:
        webpush(
            subscription_info={
                "endpoint": sus.endpoint,
                "keys": {"p256dh": sus.p256dh, "auth": sus.auth},
            },
            data=json.dumps({"titulo": titulo, "cuerpo": cuerpo, "url": url}),
            vapid_private_key=settings.vapid_private_key,
            vapid_claims={"sub": settings.vapid_sub},
            ttl=43200,  # 12h: si el teléfono está apagado, el aviso del día no caduca al toque
        )
        return "ok"
    except WebPushException as exc:
        status = exc.response.status_code if exc.response is not None else 0
        if status in (404, 410):
            return "gone"
        print(f"[push:error] endpoint=…{sus.endpoint[-24:]}: {exc}", flush=True)
        return "error"
    except Exception as exc:  # noqa: BLE001 — el barrido sigue con el resto
        print(f"[push:error] endpoint=…{sus.endpoint[-24:]}: {exc}", flush=True)
        return "error"
