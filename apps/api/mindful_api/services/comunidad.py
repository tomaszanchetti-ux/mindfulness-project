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

from datetime import datetime, timezone
from typing import Optional
from uuid import uuid4

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..db.models import (
    AVISO_SOLICITUD,
    VINCULO_ACEPTADA,
    VINCULO_PENDIENTE,
    VISIBILIDAD_COMPARTIDA,
    Entrega,
    Reenvio,
    Usuario,
    Vinculo,
)
from . import avisos, storage
from .fotos import MAX_BYTES

# A dónde lleva el aviso de una solicitud (la pestaña Comunidad, C2).
URL_COMUNIDAD = "/comunidad"


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


# Cómo se ve el vínculo DESDE mí (vocabulario cerrado, espejo de `EstadoVinculo` en types.ts).
ESTADO_NINGUNO = "ninguno"
ESTADO_PENDIENTE_ENVIADA = "pendiente_enviada"     # yo pedí, falta que acepte
ESTADO_PENDIENTE_RECIBIDA = "pendiente_recibida"   # me pidieron, me toca aceptar/rechazar
ESTADO_ACEPTADA = "aceptada"


def estado_vinculo(s: Session, yo_id: str, otro_id: str) -> str:
    v = vinculo_entre(s, yo_id, otro_id)
    if v is None:
        return ESTADO_NINGUNO
    if v.estado == VINCULO_ACEPTADA:
        return ESTADO_ACEPTADA
    if v.estado == VINCULO_PENDIENTE and v.solicitante_id == yo_id:
        return ESTADO_PENDIENTE_ENVIADA
    return ESTADO_PENDIENTE_RECIBIDA


def persona_de(s: Session, yo: Usuario, otro: Usuario) -> dict:
    """`Persona` completa: la mínima + nombre/apellido + el vínculo desde mí.
    Es la forma que devuelven la búsqueda, mi comunidad y `GET /api/fichas/de/{id}`."""
    return {
        **persona_min(otro),
        "nombre": otro.nombre,
        "apellido": otro.apellido,
        "vinculo": ESTADO_ACEPTADA if yo.id == otro.id else estado_vinculo(s, yo.id, otro.id),
    }


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


# ═════════════════════════════════════════════════════════════════════════════
# WS29 · C1.1 · PERSONAS, SOLICITUDES Y FOTO DE PERFIL
# (todo lo de acá abajo se apoya en C0 y no lo reescribe)
# ═════════════════════════════════════════════════════════════════════════════

BUSQUEDA_MINIMO = 2   # con una letra sola no se busca: devolvemos vacío, no todo
BUSQUEDA_MAXIMO = 20  # la búsqueda es para encontrar a alguien, no para pasear el padrón

MSG_YO_MISMO = "No puedes enviarte una solicitud a ti mismo."
MSG_YA_HAY = "Ya hay una solicitud o un vínculo con esta persona."
MSG_NO_EXISTE = "Persona no encontrada"
MSG_SIN_SOLICITUD = "Solicitud no encontrada"
MSG_SIN_VINCULO = "Vínculo no encontrado"
MSG_SIN_FOTO = "Foto no encontrada"


def _orden_por_apodo():
    """El mismo criterio que `como_se_llama`, pero en SQL: así el orden de la
    búsqueda (que se corta en 20 en la base) coincide con el que ve el usuario."""
    return func.lower(func.coalesce(Usuario.apodo, Usuario.nombre, "Alguien"))


def _escapar_like(q: str) -> str:
    """`%`, `_` y `\\` son comodines de LIKE: quien busca "100_%" busca eso."""
    return q.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def buscar_personas(s: Session, yo: Usuario, q: Optional[str]) -> list:
    """Encontrar a alguien para sumarlo a la comunidad: por su email EXACTO (el
    que le pasó por otro lado) o por un pedazo de su apodo/nombre/apellido.

    Nunca devuelve el email de nadie (`persona_de` no lo lleva): el email sirve
    para BUSCAR, no para mostrarse. Tampoco me devuelve a mí."""
    q = (q or "").strip()
    if len(q) < BUSQUEDA_MINIMO:
        return []
    minus = q.lower()
    patron = f"%{_escapar_like(minus)}%"
    filas = s.scalars(
        select(Usuario)
        .where(
            Usuario.id != yo.id,
            or_(
                func.lower(Usuario.email) == minus,
                func.lower(Usuario.apodo).like(patron, escape="\\"),
                func.lower(Usuario.nombre).like(patron, escape="\\"),
                func.lower(Usuario.apellido).like(patron, escape="\\"),
            ),
        )
        .order_by(_orden_por_apodo())
        .limit(BUSQUEDA_MAXIMO)
    ).all()
    return [persona_de(s, yo, u) for u in filas]


def _ordenadas(s: Session, yo: Usuario, usuarios: list) -> list:
    return [
        persona_de(s, yo, u)
        for u in sorted(usuarios, key=lambda u: como_se_llama(u).lower())
    ]


def mi_comunidad(s: Session, yo: Usuario) -> dict:
    """Las tres listas de la pestaña: mi gente, lo que me piden y lo que pedí."""
    vinculos = s.scalars(
        select(Vinculo).where(
            or_(Vinculo.solicitante_id == yo.id, Vinculo.destinatario_id == yo.id)
        )
    ).all()

    gente, recibidas, enviadas = [], [], []
    for v in vinculos:
        otro_id = v.destinatario_id if v.solicitante_id == yo.id else v.solicitante_id
        otro = s.get(Usuario, otro_id)
        if otro is None:  # no debería pasar (FK + cascada), pero no rompemos la lista
            continue
        if v.estado == VINCULO_ACEPTADA:
            gente.append(otro)
        elif v.destinatario_id == yo.id:
            recibidas.append(otro)
        else:
            enviadas.append(otro)

    return {
        "gente": _ordenadas(s, yo, gente),
        "recibidas": _ordenadas(s, yo, recibidas),
        "enviadas": _ordenadas(s, yo, enviadas),
    }


def _otra_persona(s: Session, usuario_id: str) -> Usuario:
    otro = s.get(Usuario, usuario_id)
    if otro is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_NO_EXISTE)
    return otro


def crear_solicitud(s: Session, yo: Usuario, usuario_id: str) -> dict:
    """Pedirle a alguien ser parte de su comunidad. Una sola fila por par: si ya
    hay algo (pendiente en cualquier dirección o aceptada), es 409."""
    if usuario_id == yo.id:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, MSG_YO_MISMO)
    otro = _otra_persona(s, usuario_id)
    if vinculo_entre(s, yo.id, otro.id) is not None:
        raise HTTPException(status.HTTP_409_CONFLICT, MSG_YA_HAY)

    s.add(Vinculo(solicitante_id=yo.id, destinatario_id=otro.id, estado=VINCULO_PENDIENTE))
    avisos.crear_aviso(
        s, otro, AVISO_SOLICITUD,
        f"{como_se_llama(yo)} quiere ser parte de tu comunidad.",
        referencia_id=yo.id, url=URL_COMUNIDAD,
    )
    try:
        s.commit()
    except IntegrityError:
        # Dos pedidos a la vez (o el otro pidiendo al mismo tiempo): el único por
        # par lo frena en la base y contestamos lo mismo que si lo hubiéramos visto.
        s.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, MSG_YA_HAY)
    return persona_de(s, yo, otro)


def aceptar_solicitud(s: Session, yo: Usuario, usuario_id: str) -> dict:
    """Aceptar SOLO lo que me pidieron a mí. Si la solicitud la mandé yo, o no
    existe, o ya está aceptada: 404 (no delatamos de quién es qué)."""
    v = s.scalar(
        select(Vinculo).where(
            Vinculo.solicitante_id == usuario_id,
            Vinculo.destinatario_id == yo.id,
            Vinculo.estado == VINCULO_PENDIENTE,
        )
    )
    if v is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_SIN_SOLICITUD)
    otro = _otra_persona(s, usuario_id)

    v.estado = VINCULO_ACEPTADA
    v.aceptada_at = datetime.now(timezone.utc)
    s.add(v)
    avisos.crear_aviso(
        s, otro, AVISO_SOLICITUD,
        f"{como_se_llama(yo)} aceptó tu solicitud.",
        referencia_id=yo.id, url=URL_COMUNIDAD,
    )
    s.commit()
    return persona_de(s, yo, otro)


def borrar_solicitud(s: Session, yo: Usuario, usuario_id: str) -> None:
    """Rechazar (me la mandaron) o cancelar (la mandé yo): la misma puerta, porque
    en los dos casos el resultado es el mismo — no queda fila. Sin aviso: nadie se
    entera de que lo rechazaron."""
    v = vinculo_entre(s, yo.id, usuario_id)
    if v is None or v.estado != VINCULO_PENDIENTE:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_SIN_SOLICITUD)
    s.delete(v)
    s.commit()


def quitar_de_comunidad(s: Session, yo: Usuario, usuario_id: str) -> None:
    """Sacar a alguien de mi comunidad: se corta para los DOS (el vínculo es uno
    solo) y con él se cierra lo que cada uno veía del otro. Sin aviso."""
    v = vinculo_entre(s, yo.id, usuario_id)
    if v is None or v.estado != VINCULO_ACEPTADA:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_SIN_VINCULO)
    s.delete(v)
    s.commit()


# ── Foto de perfil ───────────────────────────────────────────────────────────
# Mismas reglas que la foto de una pausa (formatos y 8 MB salen de services/fotos:
# un solo número en el repo), pero la ruta es del USUARIO, no de una entrega, y la
# lee cualquier logueado: una cara sin nombre no dice nada, y sin ella la comunidad
# es una lista de textos.

def _ruta_foto_perfil(usuario_id: str, ext: str) -> str:
    return f"perfil/{usuario_id}/{uuid4()}.{ext}"


FORMATOS_AVATAR = ("image/jpeg", "image/jpg", "image/png", "image/webp")


def subir_foto_perfil(
    s: Session, usuario: Usuario, contenido: bytes, content_type: Optional[str]
) -> dict:
    # Q/A C1.1: `storage.extension_para` también admite GIF/HEIC (fotos de una
    # Pausa); el avatar es solo JPG, PNG o WebP, como dice el contrato.
    ext = storage.extension_para(content_type)
    if ext is None or (content_type or "").lower() not in FORMATOS_AVATAR:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            "Formato no soportado: usa una imagen (JPG, PNG o WebP)",
        )
    if len(contenido) == 0:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "La foto llegó vacía")
    if len(contenido) > MAX_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "La foto supera los 8 MB"
        )

    anterior = usuario.foto_path
    ruta = _ruta_foto_perfil(usuario.id, ext)
    # Primero el archivo, después la fila (como en fotos.subir_foto): si la DB
    # falla, limpiamos el archivo huérfano.
    storage.guardar(ruta, contenido, content_type or "application/octet-stream")
    try:
        usuario.foto_path = ruta
        s.add(usuario)
        s.commit()
    except Exception:
        s.rollback()
        storage.borrar([ruta])
        raise
    # La anterior se borra DESPUÉS del commit: si el borrado falla, queda un
    # archivo de más, nunca un perfil apuntando a un archivo que ya no está.
    if anterior and anterior != ruta:
        storage.borrar([anterior])
    return {"foto_url": foto_url_de(usuario)}


def quitar_foto_perfil(s: Session, usuario: Usuario) -> None:
    """Idempotente: quitar la foto que no está también es "quedó sin foto"."""
    anterior = usuario.foto_path
    if anterior is None:
        return
    usuario.foto_path = None
    s.add(usuario)
    s.commit()
    storage.borrar([anterior])


def leer_foto_perfil(s: Session, usuario_id: str) -> tuple:
    """La foto de CUALQUIER usuario (con login). Un solo 404 para "no existe",
    "no tiene foto" y "el archivo se perdió": nada se delata."""
    otro = s.get(Usuario, usuario_id)
    if otro is None or not otro.foto_path:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_SIN_FOTO)
    contenido = storage.leer(otro.foto_path)
    if contenido is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, MSG_SIN_FOTO)
    return contenido, storage.mime_de(otro.foto_path)
