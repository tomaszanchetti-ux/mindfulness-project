"""Las tablas. Codifican la REGLA DE ORO del aislamiento (Documento Madre §5):

  MUNDO 1 · CONTENIDO (global, compartido)  → NINGUNA columna user_id.
  MUNDO 2 · DATOS DEL USUARIO (privado)     → TODA fila lleva usuario_id.

El filtro por usuario_id vive en el backend, jamás en el cliente. No es "una base
por usuario": es una sola base, filtrada server-side. Escala a +100k.
"""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


def _uuid() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


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

    categorias: Mapped[list["UsuarioCategoria"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )
    acciones: Mapped[list["UsuarioAccion"]] = relationship(
        back_populates="usuario", cascade="all, delete-orphan"
    )


class UsuarioCategoria(Base):
    """Las 2-6 categorías elegidas en el onboarding (filtro duro de M2)."""

    __tablename__ = "usuario_categorias"
    __table_args__ = (UniqueConstraint("usuario_id", "categoria_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    categoria_slug: Mapped[str] = mapped_column(ForeignKey("categorias.slug"), nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="categorias")


class UsuarioAccion(Base):
    """Las actividades elegidas en el onboarding (filtro duro de M2, WS10).

    "escribir" siempre cuenta como piso garantizado del pool, esté o no en esta tabla.
    Sin filas (usuario nuevo o nunca elegido) = sin filtro de actividad = todas.
    """

    __tablename__ = "usuario_acciones"
    __table_args__ = (UniqueConstraint("usuario_id", "accion_slug"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    usuario_id: Mapped[str] = mapped_column(
        ForeignKey("usuarios.id", ondelete="CASCADE"), nullable=False, index=True
    )
    accion_slug: Mapped[str] = mapped_column(ForeignKey("acciones.slug"), nullable=False)

    usuario: Mapped["Usuario"] = relationship(back_populates="acciones")


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
    reflexion: Mapped[Optional[str]] = mapped_column(Text)  # ≤150

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
