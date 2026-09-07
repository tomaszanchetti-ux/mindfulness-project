"""Las tablas. Codifican la REGLA DE ORO del aislamiento (Documento Madre §5):

  MUNDO 1 · CONTENIDO (global, compartido)  → NINGUNA columna user_id.
  MUNDO 2 · DATOS DEL USUARIO (privado)     → TODA fila lleva usuario_id.

El filtro por usuario_id vive en el backend, jamás en el cliente. No es "una base
por usuario": es una sola base, filtrada server-side. Escala a +100k.
"""

from __future__ import annotations

import uuid
from datetime import date, datetime, timezone
from typing import Optional

from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── WS27 · Bloque B · vocabulario cerrado (un solo lugar) ────────────────────
ORIGEN_DWELLIA = "dwellia"
ORIGEN_COMUNIDAD = "comunidad"

FIRMA_ANONIMA = "anonima"
FIRMA_APODO = "apodo"
FIRMAS = (FIRMA_ANONIMA, FIRMA_APODO)

# Recorrido de una carta propuesta (Roadmap v2 §4 · B0):
#   en_revision (el juez corriendo) → revision_dwellia (le toca a Tomás)
#                                   → a_revisar (vuelve al autor con sugerencia)
#                                   → rechazada (el juez o Tomás)
#   revision_dwellia → aprobada (= publicada en `cartas`, cargada al mazo) | rechazada
#   a_revisar → en_revision (el autor la reenvía) · cualquiera → retirada (el autor)
ESTADO_EN_REVISION = "en_revision"
ESTADO_REVISION_DWELLIA = "revision_dwellia"
ESTADO_A_REVISAR = "a_revisar"
ESTADO_APROBADA = "aprobada"
ESTADO_RECHAZADA = "rechazada"
ESTADO_RETIRADA = "retirada"
ESTADOS_CARTA_COMUNIDAD = (
    ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA, ESTADO_A_REVISAR,
    ESTADO_APROBADA, ESTADO_RECHAZADA, ESTADO_RETIRADA,
)
# Estados "vivos": mientras hay una en alguno de estos, no se puede proponer otra.
ESTADOS_EN_CURSO = (ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA, ESTADO_A_REVISAR)

AVISO_CARTA_ESTADO = "carta_estado"   # B · cambió el estado de tu carta
AVISO_REENVIO = "reenvio"             # C · te reenviaron una Pausa
AVISO_SOLICITUD = "solicitud"         # C · solicitud de comunidad (recibida o aceptada)

# ── WS29 · Bloque C · vocabulario cerrado ────────────────────────────────────
VISIBILIDAD_PRIVADA = "privada"
VISIBILIDAD_COMPARTIDA = "compartida"
VISIBILIDADES = (VISIBILIDAD_PRIVADA, VISIBILIDAD_COMPARTIDA)

# Un vínculo nace `pendiente` (A le pidió a B) y pasa a `aceptada` (B dijo que sí).
# Rechazar o cancelar BORRA la fila: no hay estado "rechazada" que alguien pueda
# leer para saber que le dijeron que no.
VINCULO_PENDIENTE = "pendiente"
VINCULO_ACEPTADA = "aceptada"
VINCULOS = (VINCULO_PENDIENTE, VINCULO_ACEPTADA)

TIPO_LIBRO = "libro"
TIPO_VIDEO = "video"
TIPO_PODCAST = "podcast"
TIPO_DOCUMENTAL = "documental"
TIPO_OTRO = "otro"
TIPOS_RECOMENDACION = (TIPO_LIBRO, TIPO_VIDEO, TIPO_PODCAST, TIPO_DOCUMENTAL, TIPO_OTRO)
RECOMENDACIONES_MAX = 30
RECOMENDACION_TITULO_MAX = 80
RECOMENDACION_TEXTO_MAX = 500

# Cómo llega una Pausa que no sorteó el motor (`POST /api/pausas/hacer`):
#   `ahora`     → una entrega EXTRA hoy (no toca la diaria)
#   `siguiente` → entra a la cola `pausas_programadas` y el motor la sirve como
#                 la próxima carta del día, en lugar de sortear.
PAUSA_AHORA = "ahora"
PAUSA_SIGUIENTE = "siguiente"
MODOS_PAUSA = (PAUSA_AHORA, PAUSA_SIGUIENTE)


# ─────────────────────────────────────────────────────────────────────────────
# MUNDO 1 · CONTENIDO GLOBAL  (seed = los 3 JSON de M0_Motor_de_Contenido/data/)
# Sin user_id. Iguales para todos. Acá vive M0.
# ─────────────────────────────────────────────────────────────────────────────
class Categoria(Base):
    __tablename__ = "categorias"

    slug: Mapped[str] = mapped_column(String(40), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    color_accent: Mapped[str] = mapped_column(String(9), nullable=False)
    color_text: Mapped[str] = mapped_column(String(9), nullable=False)
    img: Mapped[str] = mapped_column(String(200), nullable=False)


class Accion(Base):
    __tablename__ = "acciones"

    slug: Mapped[str] = mapped_column(String(40), primary_key=True)
    nombre: Mapped[str] = mapped_column(String(80), nullable=False)
    glifo: Mapped[str] = mapped_column(String(200), nullable=False)


class Carta(Base):
    __tablename__ = "cartas"

    id: Mapped[str] = mapped_column(String(40), primary_key=True)
    categoria_slug: Mapped[str] = mapped_column(
        ForeignKey("categorias.slug"), nullable=False, index=True
    )
    accion_slug: Mapped[str] = mapped_column(
        ForeignKey("acciones.slug"), nullable=False, index=True
    )
    # WS17: huella de deduplicación — dos cartas que "se sienten igual" comparten
    # concepto y M2 no repite concepto dentro de la ventana semanal.
    concepto: Mapped[Optional[str]] = mapped_column(String(80), index=True)
    frase: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    # WS27 · Bloque B: de dónde viene la carta. `dwellia` = mazo propio (los JSON de
    # M0, el seed las sincroniza) · `comunidad` = escrita por un usuario premium y
    # aprobada por Tomás (el seed NUNCA las toca). La firma pública es lo que ve
    # el resto en el dorso: el apodo del autor o None (= "alguien de la comunidad").
    origen: Mapped[str] = mapped_column(String(12), nullable=False, default="dwellia", index=True)
    autor_usuario_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    firma_publica: Mapped[Optional[str]] = mapped_column(String(40))


# ─────────────────────────────────────────────────────────────────────────────
# MUNDO 2 · DATOS DEL USUARIO  (privado, TODO con usuario_id)
# ─────────────────────────────────────────────────────────────────────────────
class Usuario(Base):
    __tablename__ = "usuarios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    # El sub de Firebase Auth: donde EMPIEZA el aislamiento.
    firebase_uid: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    # Datos básicos. nombre se pide en el onboarding; apellido es opcional.
    nombre: Mapped[Optional[str]] = mapped_column(String(80))
    apellido: Mapped[Optional[str]] = mapped_column(String(80))
    # Cómo nos referimos al usuario en toda la app (saludo, firma del regalo M5).
    apodo: Mapped[Optional[str]] = mapped_column(String(40))

    # M1 · configuración (TZ autodetectada+editable · aviso 1 toggle).
    tz: Mapped[str] = mapped_column(String(64), nullable=False, default="Europe/Madrid")
    hora_aviso: Mapped[str] = mapped_column(String(5), nullable=False, default="08:00")
    aviso_activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    terminos_aceptados_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    # WS20 · aviso diario: fecha LOCAL del último aviso enviado (1 por día, máximo).
    ultimo_aviso_fecha: Mapped[Optional[date]] = mapped_column(Date)

    # WS24 · plan (Roadmap v2 §0/§1). `plan` es la etiqueta; la VERDAD es
    # `plan_hasta`: premium vigente ⇔ plan == "premium" y plan_hasta > ahora.
    # Nadie lee estas columnas directo: se pasa por `services/plan.py`.
    plan: Mapped[str] = mapped_column(String(10), nullable=False, default="free")
    plan_hasta: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    stripe_customer_id: Mapped[Optional[str]] = mapped_column(String(64), unique=True)
    # WS27 · B2.1: NO hay interruptor de "cartas de la comunidad". Las aprobadas
    # entran al mazo como iguales y el motor las reparte a todos con las mismas
    # reglas que las de Dwellia (decisión de Tomás, WS27 §6): la columna
    # `recibe_comunidad` que había creado B0 se eliminó en `l2a3b4c5d6e7`.

    # WS29 · Bloque C: perfil PRIVADO por defecto (Roadmap v2 §0). Privado = te
    # encuentran en la búsqueda, pero tus fichas compartidas solo las ve quien
    # tiene un vínculo aceptado contigo. Público = las ve cualquier usuario logueado.
    # La regla completa vive en `services/comunidad.puede_ver` y NADIE la reescribe.
    perfil_publico: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    # WS29 · foto de perfil: solo la ruta en Storage (lleva el usuario_id adentro,
    # jamás viaja); se sirve por `GET /api/usuarios/{usuario_id}/foto` con login.
    foto_path: Mapped[Optional[str]] = mapped_column(String(300))

    push_suscripciones: Mapped[list["PushSuscripcion"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )



class Entrega(Base):
    """Una carta entregada un día (el Baúl). M2 la crea; M3 escribe estrellas+reflexión."""

    __tablename__ = "entregas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    carta_id: Mapped[str] = mapped_column(ForeignKey("cartas.id"), nullable=False)

    fecha: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    # M3: opcionales, no bloquean Guardar.
    estrellas: Mapped[Optional[int]] = mapped_column(Integer)  # 1-5
    completada: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    reflexion: Mapped[Optional[str]] = mapped_column(Text)  # ≤150 free · ≤500 premium (WS24)
    # WS24 · feedback privado de la carta (debajo de las estrellas). Nunca se publica.
    comentario_carta: Mapped[Optional[str]] = mapped_column(Text)  # ≤150
    # WS24 · cambiar la carta (premium): cuántas veces hoy (máx. 3) y cuáles descartó.
    cambios: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    descartadas: Mapped[Optional[list]] = mapped_column(JSON)
    # WS25 · quién ve la ficha de esta Pausa: `privada` (solo el dueño) o
    # `compartida` (su comunidad). Default privada: nadie publica sin pedirlo.
    # Es independiente del link de M5, que es un regalo puntual a una persona.
    visibilidad: Mapped[str] = mapped_column(String(12), nullable=False, default="privada")
    # WS29 · Bloque C: una Pausa EXTRA ("Hacer ahora" desde la ficha de otro,
    # premium) no es la carta del día: el motor la ignora al decidir si hoy ya
    # hay carta y al armar el historial de rotación. `de_usuario_id` = quién me la
    # hizo llegar (dueño de la ficha reenviada), para que la ficha pueda decir
    # "te la envió Lu". Vale también para la Pausa programada que el motor sirvió.
    extra: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    de_usuario_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )

    fotos: Mapped[list["Foto"]] = relationship(
        back_populates="entrega", cascade="all, delete-orphan"
    )


class Foto(Base):
    """Hasta 3 por entrega. La imagen vive en Cloud Storage; acá solo la ruta."""

    __tablename__ = "fotos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    entrega_id: Mapped[str] = mapped_column(
        ForeignKey("entregas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_path: Mapped[str] = mapped_column(String(300), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    entrega: Mapped["Entrega"] = relationship(back_populates="fotos")


class Compartido(Base):
    """M5 · link público. token opaco (jamás IDs internos). Muere si se borra la entrega."""

    __tablename__ = "compartidos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    token: Mapped[str] = mapped_column(String(64), unique=True, nullable=False, index=True)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    # entrega_id NULL = modo "carta sola" (sobrevive aunque se borre la entrada).
    entrega_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("entregas.id", ondelete="SET NULL")
    )
    carta_id: Mapped[str] = mapped_column(ForeignKey("cartas.id"), nullable=False)
    modo: Mapped[str] = mapped_column(String(20), nullable=False)  # carta_sola | ejercicio
    nota: Mapped[Optional[str]] = mapped_column(Text)
    activo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class PushSuscripcion(Base):
    """WS21 · suscripción Web Push de UN dispositivo/navegador del usuario.

    El navegador entrega un endpoint único + llaves de cifrado al suscribirse;
    el barrido del aviso diario empuja a TODAS las suscripciones del usuario.
    Si el push service responde 404/410 (dispositivo dado de baja), se borra la fila.
    """

    __tablename__ = "push_suscripciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    endpoint: Mapped[str] = mapped_column(Text, unique=True, nullable=False)
    p256dh: Mapped[str] = mapped_column(String(255), nullable=False)
    auth: Mapped[str] = mapped_column(String(255), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)

    usuario: Mapped["Usuario"] = relationship(back_populates="push_suscripciones")


class CartaComunidad(Base):
    """WS27 · Bloque B · la carta que un usuario premium propone para la comunidad.

    Es Mundo 2 (lleva `usuario_id`): es SU propuesta, con su recorrido. Cuando
    Tomás la aprueba se PUBLICA como una fila nueva en `cartas` (Mundo 1, origen
    `comunidad`) y `carta_id` apunta a ella. Límites del contenido (frase ≤60,
    prompt 100-220) los aplica el servicio, nunca la tabla.
    """

    __tablename__ = "cartas_comunidad"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    categoria_slug: Mapped[str] = mapped_column(ForeignKey("categorias.slug"), nullable=False)
    accion_slug: Mapped[str] = mapped_column(ForeignKey("acciones.slug"), nullable=False)
    frase: Mapped[str] = mapped_column(Text, nullable=False)
    prompt: Mapped[str] = mapped_column(Text, nullable=False)
    firma: Mapped[str] = mapped_column(String(10), nullable=False, default=FIRMA_ANONIMA)
    estado: Mapped[str] = mapped_column(
        String(20), nullable=False, default=ESTADO_EN_REVISION, index=True
    )
    veredicto: Mapped[Optional[dict]] = mapped_column(JSON)   # lo que dijo el juez
    motivo: Mapped[Optional[str]] = mapped_column(Text)        # sugerencia / motivo visible al autor
    # WS27 · B2.1 · las REDACCIONES del autor, una por vuelta: v1 al enviarla y
    # v(n+1) en cada reenvío. Es la primera pata del funnel del adminland
    # (v1 lo que escribió → v2 lo que dijo el juez, en `veredicto` → vFinal la
    # decisión, en `estado`/`motivo`/`carta_id`). Lista de dicts; se REASIGNA
    # entera en cada vuelta (columna JSON: mutarla en su lugar no se guarda).
    historial: Mapped[Optional[list]] = mapped_column(JSON)
    concepto: Mapped[Optional[str]] = mapped_column(String(80))
    cesion_aceptada_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    carta_id: Mapped[Optional[str]] = mapped_column(ForeignKey("cartas.id", ondelete="SET NULL"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)


class Aviso(Base):
    """WS27 · Bloque B · lo que la app le cuenta al usuario (y empuja por push).

    `tipo` = AVISO_* · `referencia_id` = la carta_comunidad (B), el reenvío o la
    solicitud (C). Privado: siempre por `usuario_id`.
    """

    __tablename__ = "avisos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    tipo: Mapped[str] = mapped_column(String(20), nullable=False)
    referencia_id: Mapped[Optional[str]] = mapped_column(String(36))
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    leido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


# ─────────────────────────────────────────────────────────────────────────────
# WS29 · BLOQUE C · COMUNIDAD (todo Mundo 2: cada fila nombra a su(s) usuario(s)
# y cae en cascada si uno se borra; el `conftest` limpia usuarios y se lleva todo)
# ─────────────────────────────────────────────────────────────────────────────
class Vinculo(Base):
    """Una relación entre dos personas. Dirección: `solicitante` le pidió a
    `destinatario`. Único por PAR sin importar la dirección (índice funcional
    LEAST/GREATEST en la migración): nunca hay dos filas entre las mismas dos
    personas. "Mi comunidad" = vínculos `aceptada` en cualquier dirección."""

    __tablename__ = "vinculos"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    solicitante_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    destinatario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    estado: Mapped[str] = mapped_column(String(12), nullable=False, default=VINCULO_PENDIENTE)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    aceptada_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Reenvio(Base):
    """`de` le reenvió a `a` la ficha `entrega` (que puede ser de un tercero).
    El reenvío da PERMISO de lectura a `a` mientras la ficha siga compartida:
    el dueño manda siempre (si la vuelve privada o la borra, el reenvío muere
    con ella por la cascada o por `puede_ver`)."""

    __tablename__ = "reenvios"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    de_usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    a_usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entrega_id: Mapped[str] = mapped_column(
        ForeignKey("entregas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    leido: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class Guardada(Base):
    """La ficha de OTRO que guardé en mi Baúl ("Pausa de <apodo>"). No es una
    copia: se lee en vivo con `puede_ver`, así desaparece si el dueño la vuelve
    privada, la borra o me quita de su comunidad. Única por (usuario, entrega)."""

    __tablename__ = "guardadas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    entrega_id: Mapped[str] = mapped_column(
        ForeignKey("entregas.id", ondelete="CASCADE"), nullable=False, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)


class PausaProgramada(Base):
    """La cola de "Programar": la próxima carta del día de `usuario` es ESTA
    (`carta_id`), en lugar de la que sortearía el motor. FIFO por `created_at`;
    `servida_at` marca cuándo el motor la convirtió en entrega. Una por vez en
    cola (decisión de Tomás: "reemplaza la inmediata siguiente")."""

    __tablename__ = "pausas_programadas"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    carta_id: Mapped[str] = mapped_column(ForeignKey("cartas.id"), nullable=False)
    de_usuario_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("usuarios.id", ondelete="SET NULL")
    )
    entrega_origen_id: Mapped[Optional[str]] = mapped_column(
        ForeignKey("entregas.id", ondelete="SET NULL")
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    servida_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class Recomendacion(Base):
    """Una ficha de recomendación (premium): libro, video, podcast, documental u
    otro. Vive en el Baúl con la misma visibilidad que una Pausa. Los largos los
    aplica el servicio (RECOMENDACION_*), nunca la tabla."""

    __tablename__ = "recomendaciones"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    titulo: Mapped[str] = mapped_column(String(80), nullable=False)
    tipo: Mapped[str] = mapped_column(String(12), nullable=False, default=TIPO_OTRO)
    texto: Mapped[str] = mapped_column(Text, nullable=False)
    url: Mapped[Optional[str]] = mapped_column(String(500))
    visibilidad: Mapped[str] = mapped_column(
        String(12), nullable=False, default=VISIBILIDAD_PRIVADA
    )
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)
