"""Contratos de entrada/salida (Pydantic). Validan en el borde de la API."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")  # HH:MM 24h


class PerfilOut(BaseModel):
    """El perfil del usuario logueado (lo que ve M1)."""

    email: str
    nombre: Optional[str] = None
    apellido: Optional[str] = None
    apodo: Optional[str] = None
    tz: str
    hora_aviso: str
    aviso_activo: bool
    terminos_aceptados: bool
    categorias: list[str]
    acciones: list[str]  # WS10: actividades elegidas ("escribir" siempre incluida)
    onboarding_completo: bool


class PerfilUpdate(BaseModel):
    """Actualización parcial del perfil (apodo / horario / TZ / aviso / términos)."""

    nombre: Optional[str] = Field(default=None, max_length=80)
    apellido: Optional[str] = Field(default=None, max_length=80)
    apodo: Optional[str] = Field(default=None, max_length=40)
    tz: Optional[str] = None
    hora_aviso: Optional[str] = None
    aviso_activo: Optional[bool] = None
    aceptar_terminos: Optional[bool] = None

    @field_validator("hora_aviso")
    @classmethod
    def _valida_hora(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not _HORA.match(v):
            raise ValueError("hora_aviso debe ser HH:MM (24h), ej. 08:00")
        return v


class CategoriasUpdate(BaseModel):
    """Las 2-6 categorías elegidas (filtro duro de M2)."""

    categorias: list[str] = Field(min_length=2, max_length=6)

    @field_validator("categorias")
    @classmethod
    def _sin_duplicados(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError("hay categorías repetidas")
        return v


class AccionesUpdate(BaseModel):
    """WS10 · las actividades elegidas (filtro duro de M2).

    0 a 5 slugs. "escribir" es el piso garantizado: el backend la agrega siempre,
    venga o no en la lista (en la UI se muestra incluida y bloqueada).
    """

    acciones: list[str] = Field(max_length=5)

    @field_validator("acciones")
    @classmethod
    def _sin_duplicados(cls, v: list[str]) -> list[str]:
        if len(set(v)) != len(v):
            raise ValueError("hay actividades repetidas")
        return v


class CierreRitual(BaseModel):
    """M3 · cierre del ritual. Todo opcional (no bloquea Guardar)."""

    estrellas: Optional[int] = Field(default=None, ge=1, le=5)
    reflexion: Optional[str] = Field(default=None, max_length=250)
    completada: bool = True


class CompartirCreate(BaseModel):
    """M5 · crear un link. carta_sola (sin datos tuyos) o ejercicio (reflexión + fotos).

    En v1 free el front sólo ofrece `carta_sola`; `ejercicio` queda soportado en el
    backend para reactivarlo en premium. La nota personal va junto a la carta (≤250).
    """

    entrega_id: str
    modo: str = Field(pattern="^(carta_sola|ejercicio)$")
    nota: Optional[str] = Field(default=None, max_length=250)
