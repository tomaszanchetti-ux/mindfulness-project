"""Contratos de entrada/salida (Pydantic). Validan en el borde de la API."""

from __future__ import annotations

import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")  # HH:MM 24h


class PerfilOut(BaseModel):
    """El perfil del usuario logueado (lo que ve M1)."""

    email: str
    tz: str
    hora_aviso: str
    aviso_activo: bool
    terminos_aceptados: bool
    categorias: list[str]
    onboarding_completo: bool


class PerfilUpdate(BaseModel):
    """Actualización parcial del perfil (horario / TZ / aviso / términos)."""

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


class CierreRitual(BaseModel):
    """M3 · cierre del ritual. Todo opcional (no bloquea Guardar)."""

    estrellas: Optional[int] = Field(default=None, ge=1, le=5)
    reflexion: Optional[str] = Field(default=None, max_length=250)
    completada: bool = True


class CompartirCreate(BaseModel):
    """M5 · crear un link. carta_sola (sin datos tuyos) o ejercicio (reflexión + fotos)."""

    entrega_id: str
    modo: str = Field(pattern="^(carta_sola|ejercicio)$")
    nota: Optional[str] = Field(default=None, max_length=500)
