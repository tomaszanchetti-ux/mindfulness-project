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
AVISO_SOLICITUD = "solicitud"         # C · solicitud de comunidad


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
    # WS27 · Bloque B: opt-in a recibir cartas de la comunidad el día comodín.
    recibe_comunidad: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

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
