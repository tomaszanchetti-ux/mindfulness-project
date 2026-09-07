"""WS29 · Bloque C · Comunidad — LA regla de lectura y los vínculos.

Este archivo nace en C0 con lo que TODAS las cards del bloque necesitan y ninguna
puede reescribir: `puede_ver`. Quien quiera mostrar la ficha de otro (su Baúl, una
foto, un reenvío, una guardada) pasa por acá. Si esta función dice que no, es 404:
nunca un 403 que delate que la ficha existe.

La regla (Roadmap v2 §0 "Perfil y comunidad" + WS29 §0.3):

  visible ⇔ la ficha está `compartida`
            y ( soy el dueño
                o el dueño tiene perfil público
                o tenemos un vínculo aceptado
                o alguien me la reenvió )

El dueño manda siempre: si vuelve la ficha privada, deja de verse para todos,
incluidos los que la guardaron y los que la recibieron por reenvío. Las
estrellas NUNCA salen de la cuenta del dueño, pero eso no lo decide esta
función: lo decide la forma de salida (`services/baul.item_ajeno`, C1.2).

C1.1 (personas y solicitudes) agrega DEBAJO sus funciones; C1.2 y C1.3 solo
importan de acá.
"""

from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..db.models import (
    VINCULO_ACEPTADA,
    VISIBILIDAD_COMPARTIDA,
    Entrega,
    Reenvio,
    Usuario,
    Vinculo,
)


def foto_url_de(usuario: Usuario) -> Optional[str]:
    """La URL pública-con-login de la foto de perfil (o None). Nunca el path."""
    return f"/api/usuarios/{usuario.id}/foto" if usuario.foto_path else None


def como_se_llama(usuario: Usuario) -> str:
    """Cómo se muestra una persona a los demás: apodo, si no nombre, si no
    "Alguien". El email NUNCA sale de acá."""
    return usuario.apodo or usuario.nombre or "Alguien"


def persona_min(usuario: Usuario) -> dict:
    """La forma MÍNIMA de una persona (la que llevan las fichas ajenas, los
    reenvíos y las guardadas). C1.1 la extiende con el estado del vínculo en
    `persona_de`; nadie inventa otra forma."""
    return {
        "usuario_id": usuario.id,
        "apodo": como_se_llama(usuario),
        "foto_url": foto_url_de(usuario),
        "perfil_publico": usuario.perfil_publico,
    }


def vinculo_entre(s: Session, a_id: str, b_id: str) -> Optional[Vinculo]:
    """La fila del vínculo entre dos personas, en cualquier dirección (o None)."""
    if a_id == b_id:
        return None
    return s.scalar(
        select(Vinculo).where(
            or_(
                (Vinculo.solicitante_id == a_id) & (Vinculo.destinatario_id == b_id),
                (Vinculo.solicitante_id == b_id) & (Vinculo.destinatario_id == a_id),
            )
        )
    )


def son_comunidad(s: Session, a_id: str, b_id: str) -> bool:
    """¿Hay un vínculo ACEPTADO entre los dos? (la dirección no importa)."""
    v = vinculo_entre(s, a_id, b_id)
    return v is not None and v.estado == VINCULO_ACEPTADA


def me_la_reenviaron(s: Session, quien_id: str, entrega_id: str) -> bool:
    return s.scalar(
        select(Reenvio.id).where(
            Reenvio.a_usuario_id == quien_id, Reenvio.entrega_id == entrega_id
        ).limit(1)
    ) is not None


def puede_ver(s: Session, quien: Usuario, entrega: Entrega) -> bool:
    """¿`quien` puede leer la ficha de `entrega`? Ver la regla arriba.

    Recibe objetos ya cargados (no ids) para que el llamador haya hecho su propio
    `s.get` y decida qué hacer con un None. Devuelve bool; el 404 lo pone el que
    llama (`exigir_visible`)."""
    if entrega.usuario_id == quien.id:
        # El dueño ve lo suyo, compartido o no. (El Baúl propio no pasa por acá,
        # pero si una ruta "ajena" recibe al dueño, no lo dejamos afuera.)
        return True
    if entrega.visibilidad != VISIBILIDAD_COMPARTIDA:
        return False
    if not entrega.completada:
        # Solo se publica lo VIVIDO (misma regla que `cambiar_visibilidad`).
        return False
    duenio = s.get(Usuario, entrega.usuario_id)
    if duenio is None:
        return False
    if duenio.perfil_publico:
        return True
    if son_comunidad(s, quien.id, duenio.id):
        return True
    return me_la_reenviaron(s, quien.id, entrega.id)


def entrega_visible(s: Session, quien: Usuario, entrega_id: str) -> Optional[Entrega]:
    """La entrega si `quien` puede verla; None en cualquier otro caso (inexistente,
    privada, sin vínculo…). Un solo None para todos: nada se delata."""
    entrega = s.get(Entrega, entrega_id)
    if entrega is None or not puede_ver(s, quien, entrega):
        return None
    return entrega


def puede_ver_perfil(s: Session, quien: Usuario, duenio: Usuario) -> bool:
    """¿`quien` puede ver el Baúl compartido de `duenio` (Pausas y recomendaciones)?
    Es la misma regla sin la pata del reenvío (un reenvío abre UNA ficha, no un
    perfil)."""
    if quien.id == duenio.id or duenio.perfil_publico:
        return True
    return son_comunidad(s, quien.id, duenio.id)
