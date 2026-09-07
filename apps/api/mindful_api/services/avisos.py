"""WS27 · B0 · Avisos: lo que la app le cuenta al usuario, y de paso lo empuja por push.

Un aviso es una fila en `avisos` (Mundo 2, privada) + un push a todos los
dispositivos del usuario (reusa `services/push.py`; sin VAPID el push está
apagado y la fila queda igual). Lo escribe el orquestador para que B1.1 (el
juez cambia el estado) y B1.3 (Tomás cambia el estado) usen el MISMO texto y
la misma mecánica. `GET /api/avisos` + marcar leído los construye B2.1.
"""

from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    AVISO_CARTA_ESTADO,
    ESTADO_A_REVISAR,
    ESTADO_APROBADA,
    ESTADO_RECHAZADA,
    ESTADO_REVISION_DWELLIA,
    Aviso,
    PushSuscripcion,
    Usuario,
)
from .push import enviar_push

# El texto que ve el autor cuando su carta cambia de estado (español neutro,
# invita, nunca reprocha). `revision_dwellia` NO avisa: para el autor sigue
# "en proceso de evaluación" (los rótulos visibles viven en el front).
TEXTOS_ESTADO = {
    ESTADO_APROBADA: "Tu carta ya está cargada a la comunidad. Gracias por escribirla.",
    ESTADO_A_REVISAR: "Tu carta necesita un retoque. Entra a Crear para ver la sugerencia.",
    ESTADO_RECHAZADA: "Tu carta no fue aprobada esta vez. En Crear te contamos por qué.",
}
ESTADOS_SIN_AVISO = {ESTADO_REVISION_DWELLIA}

URL_CREAR = "/crear"


def crear_aviso(
    s: Session, usuario: Usuario, tipo: str, texto: str,
    referencia_id: str | None = None, url: str = URL_CREAR, push: bool = True,
) -> Aviso:
    """Guarda el aviso y lo empuja. NO hace commit: el llamador cierra su transacción."""
    aviso = Aviso(usuario_id=usuario.id, tipo=tipo, referencia_id=referencia_id, texto=texto)
    s.add(aviso)
    if push:
        # El push es red: si falla, el aviso queda igual y la transición que lo
        # disparó también (Q/A B1.3: un push que levantaba tumbaba la aprobación).
        try:
            subs = s.scalars(
                select(PushSuscripcion).where(PushSuscripcion.usuario_id == usuario.id)
            ).all()
            for sub in subs:
                if enviar_push(sub, "Dwellia", texto, url) == "gone":
                    s.delete(sub)
        except Exception as exc:  # noqa: BLE001 — el aviso no depende del push
            print(f"[avisos:push] usuario={usuario.id}: {exc}", flush=True)
    return aviso


def avisar_estado_carta(s: Session, usuario: Usuario, carta_comunidad_id: str,
                        estado: str) -> Aviso | None:
    """El aviso canónico de un cambio de estado. Devuelve None si ese estado no avisa."""
    if estado in ESTADOS_SIN_AVISO or estado not in TEXTOS_ESTADO:
        return None
    return crear_aviso(
        s, usuario, AVISO_CARTA_ESTADO, TEXTOS_ESTADO[estado],
        referencia_id=carta_comunidad_id,
    )
