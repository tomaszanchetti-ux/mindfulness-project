"""Contratos de entrada/salida (Pydantic). Validan en el borde de la API."""

from __future__ import annotations

import re
from typing import Optional

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")  # HH:MM 24h


class LimitesOut(BaseModel):
    """WS24 · lo que el usuario puede hacer según su plan (espejo de services/plan.Limites).

    El front lee de acá y NUNCA hardcodea límites; el backend los aplica igual."""

    plan: str
    reflexion_max: int
    fotos_max: int
    compartir_ejercicio: bool
    cambios_carta: int
    propone_cartas: bool
    recomendaciones: bool


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
    # WS17/WS22: ni pilares ni acciones se eligen — el perfil ya no lleva elecciones.
    onboarding_completo: bool
    # WS24 · plan y límites vigentes (premium vencido ⇒ free).
    plan: str
    plan_hasta: Optional[datetime] = None
    limites: LimitesOut


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


class CierreRitual(BaseModel):
    """M3 · cierre del ritual. Todo opcional (no bloquea Guardar).

    WS24 · el `max_length` de la reflexión es el TOPE DURO del borde (500 = premium);
    el tope real por plan lo aplica el servicio con `limites(usuario).reflexion_max`.
    """

    estrellas: Optional[int] = Field(default=None, ge=1, le=5)
    reflexion: Optional[str] = Field(default=None, max_length=500)
    # Feedback privado que va debajo de las estrellas ("¿qué te hubiese gustado
    # recibir?"). Nunca se publica ni viaja en un link compartido.
    comentario_carta: Optional[str] = Field(default=None, max_length=150)
    completada: bool = True


class CompartirCreate(BaseModel):
    """M5 · crear un link. carta_sola (sin datos tuyos) o ejercicio (reflexión + fotos).

    `ejercicio` es premium (lo aplica el servicio, no el front). La nota personal va
    junto a la carta; su `max_length` acá es el tope duro del borde (500 = premium) y
    el tope real por plan sale de `limites(usuario).reflexion_max`.
    """

    entrega_id: str
    modo: str = Field(pattern="^(carta_sola|ejercicio)$")
    nota: Optional[str] = Field(default=None, max_length=500)
