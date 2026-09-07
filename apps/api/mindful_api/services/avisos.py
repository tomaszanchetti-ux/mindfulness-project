"""WS27 · B0 + B2.1 · Avisos: lo que la app le cuenta al usuario, y de paso lo empuja por push.

Un aviso es una fila en `avisos` (Mundo 2, privada) + un push a todos los
dispositivos del usuario (reusa `services/push.py`; sin VAPID el push está
apagado y la fila queda igual). Lo ESCRIBEN B1.1 (el juez cambia el estado) y
B1.3 (Tomás cambia el estado), con el MISMO texto y la misma mecánica.

B2.1 suma la LECTURA (`routers/avisos.py`): la lista, marcar uno como leído,
marcarlos todos y el contador de no leídos que dibuja la campana. El push es un
golpecito que se pierde si el teléfono estaba apagado; la lista es la memoria.
Todo filtrado por `usuario_id`: un aviso ajeno no existe (404, nunca 403 — la
API no delata de quién es una fila que no te pertenece).
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
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


# ─────────────────────────────────────────────────────────────────────────────
# WS27 · B2.1 · LECTURA (lo que sirve `routers/avisos.py`)
# ─────────────────────────────────────────────────────────────────────────────
# Cuántos avisos devuelve la lista si nadie pide otra cosa. La campana no es un
# archivo histórico: se lee lo reciente. El tope duro lo pone el router.
LIMITE_DEFAULT = 50


def item(aviso: Aviso) -> dict:
    """La forma pública de un aviso. `usuario_id` NO viaja: ya sabe quién es."""
    return {
        "id": aviso.id,
        "tipo": aviso.tipo,
        "referencia_id": aviso.referencia_id,
        "texto": aviso.texto,
        "leido": aviso.leido,
        "created_at": aviso.created_at,
    }


def listar_avisos(s: Session, usuario: Usuario, limite: int = LIMITE_DEFAULT) -> list:
    """Los avisos del usuario, el más nuevo primero.

    `id` desempata: dos avisos del mismo instante (una transición que dispara más
    de uno) salen siempre en el mismo orden, y una campana que baila entre
    recargas no se puede leer.
    """
    filas = s.scalars(
        select(Aviso)
        .where(Aviso.usuario_id == usuario.id)
        .order_by(Aviso.created_at.desc(), Aviso.id.desc())
        .limit(limite)
    ).all()
    return [item(a) for a in filas]


def no_leidos(s: Session, usuario: Usuario) -> int:
    """El número de la campana. Cuenta TODOS los no leídos, no solo los listados:
    si hay 60 sin leer y la lista trae 50, el contador dice 60."""
    total = s.scalar(
        select(func.count()).select_from(Aviso)
        .where(Aviso.usuario_id == usuario.id)
        .where(Aviso.leido.is_(False))
    )
    return int(total or 0)


def _mio_o_404(s: Session, usuario: Usuario, aviso_id: str) -> Aviso:
    """404 si no existe O es de otro: el aislamiento no distingue los dos casos."""
    aviso = s.get(Aviso, aviso_id)
    if aviso is None or aviso.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Aviso no encontrado")
    return aviso


def marcar_leido(s: Session, usuario: Usuario, aviso_id: str) -> dict:
    """Marca UN aviso como leído y lo devuelve. Idempotente: marcarlo dos veces
    no es un error, es el mismo aviso ya leído."""
    aviso = _mio_o_404(s, usuario, aviso_id)
    if not aviso.leido:
        aviso.leido = True
        s.add(aviso)
        s.commit()
        s.refresh(aviso)
    return item(aviso)


def marcar_todos_leidos(s: Session, usuario: Usuario) -> int:
    """Vacía la campana de un toque. Devuelve cuántos avisos marcó."""
    filas = s.scalars(
        select(Aviso)
        .where(Aviso.usuario_id == usuario.id)
        .where(Aviso.leido.is_(False))
    ).all()
    for aviso in filas:
        aviso.leido = True
        s.add(aviso)
    if filas:
        s.commit()
    return len(filas)


def bandeja(s: Session, usuario: Usuario, limite: Optional[int] = None) -> dict:
    """Lo que devuelve `GET /api/avisos`: el contador + la lista."""
    return {
        "no_leidos": no_leidos(s, usuario),
        "avisos": listar_avisos(s, usuario, limite or LIMITE_DEFAULT),
    }
