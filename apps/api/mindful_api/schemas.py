"""Contratos de entrada/salida (Pydantic). Validan en el borde de la API."""

from __future__ import annotations

import re
from typing import Optional

from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from .db.models import FIRMA_ANONIMA, FIRMAS
from .services.plan import COMENTARIO_CARTA_MAX

_HORA = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")  # HH:MM 24h


class LimitesOut(BaseModel):
    """WS24 · lo que el usuario puede hacer según su plan (espejo de services/plan.Limites).

    El front lee de acá y NUNCA hardcodea límites; el backend los aplica igual."""

    plan: str
    reflexion_max: int
    fotos_max: int
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
    # WS27 · B2: si esta cuenta puede entrar al adminland (MINDFUL_ADMIN_UIDS).
    es_admin: bool = False


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


def _texto_limpio(v):
    """strip() y blanco puro → None. Se usa en validadores `mode="before"`, o sea
    ANTES de medir el largo.

    Así el borde y el servicio miden lo MISMO (los caracteres útiles): 145 letras
    con 10 espacios delante entran, y "   " se guarda como None, no como texto.
    """
    if isinstance(v, str):
        v = v.strip()
        return v or None
    return v


class CierreRitual(BaseModel):
    """M3 · cierre del ritual. Todo opcional (no bloquea Guardar).

    WS24 · el tope real de la reflexión lo aplica el servicio por plan
    (`limites(usuario).reflexion_max`, con un mensaje que nombra el plan). Acá sólo
    queda un tope duro anti-abuso (5000) para no leer megabytes de JSON: si el borde
    cortara en 500, un free vería un 422 hablando del número de OTRO plan.
    """

    estrellas: Optional[int] = Field(default=None, ge=1, le=5)
    reflexion: Optional[str] = Field(default=None, max_length=5000)
    # Feedback privado que va debajo de las estrellas ("¿qué te hubiese gustado
    # recibir?"). Nunca se publica ni viaja en un link compartido. 150 para todos
    # los planes → sí se aplica en el borde (después del strip, por `mode="before"`).
    comentario_carta: Optional[str] = Field(default=None, max_length=COMENTARIO_CARTA_MAX)
    completada: bool = True

    @field_validator("reflexion", "comentario_carta", mode="before")
    @classmethod
    def _limpia(cls, v):
        return _texto_limpio(v)


class CompartirCreate(BaseModel):
    """M5 · crear un link. Viaja la ficha ENTERA tal como está al momento de enviar.

    WS25 · el usuario ya NO elige qué parte viaja: `modo` se sigue aceptando (los
    clientes viejos lo mandan) pero se IGNORA — el servicio lo deriva de la Pausa
    (`ejercicio` si tiene reflexión o fotos, `carta_sola` si no). Tampoco depende
    del plan: free y premium comparten igual.

    La nota personal va junto a la carta; el tope real por plan sale de
    `limites(usuario).reflexion_max` y lo aplica el servicio (mensaje que nombra el
    plan). Acá, sólo el tope duro anti-abuso (5000).
    """

    entrega_id: str
    modo: Optional[str] = Field(default=None, pattern="^(carta_sola|ejercicio)$")
    nota: Optional[str] = Field(default=None, max_length=5000)

    @field_validator("nota", mode="before")
    @classmethod
    def _limpia(cls, v):
        return _texto_limpio(v)


class VisibilidadUpdate(BaseModel):
    """WS25 · M4 · quién ve la ficha de una Pausa guardada.

    `privada` (solo el dueño) o `compartida` (su comunidad). Las estrellas nunca
    viajan: son del dueño diga lo que diga la visibilidad.
    """

    visibilidad: str = Field(pattern="^(privada|compartida)$")


# ─────────────────────────────────────────────────────────────────────────────
# WS27 · B1.1 · Cartas de la comunidad (Roadmap v2 §4)
#
# Los largos REALES (frase ≤60, prompt 100-220) los aplica
# `services/cartas_comunidad.py`, que es donde viven los límites: acá solo hay un
# tope duro anti-abuso, para no leer megabytes de JSON. Si el borde cortara en 60,
# el autor vería un 422 sin explicación en vez del mensaje que lo ayuda a corregir.
# ─────────────────────────────────────────────────────────────────────────────
_FIRMAS = "^(" + "|".join(FIRMAS) + ")$"
_TOPE_DURO = 5000


class CartaComunidadCreate(BaseModel):
    """Lo que manda el wizard de Crear: la carta + cómo firma + la cesión."""

    categoria: str = Field(max_length=40)
    accion: str = Field(max_length=40)
    frase: str = Field(max_length=_TOPE_DURO)
    prompt: str = Field(max_length=_TOPE_DURO)
    # Anónima por defecto: firmar con el apodo es una decisión explícita.
    firma: str = Field(default=FIRMA_ANONIMA, pattern=_FIRMAS)
    # Sin cesión no hay publicación (el servicio la exige con un 422 legible).
    cesion_aceptada: bool = False

    @field_validator("categoria", "accion", "frase", "prompt", mode="before")
    @classmethod
    def _limpia(cls, v):
        return v.strip() if isinstance(v, str) else v


class CartaComunidadUpdate(BaseModel):
    """El reenvío desde `a_revisar`: cambia el texto (y, si quiere, pilar/acción/firma).

    La cesión NO se vuelve a pedir: se aceptó al proponerla.

    `frase` y `prompt` son OBLIGATORIOS igual (el reenvío manda la carta entera),
    pero acá se declaran opcionales a propósito: así el que falta lo reclama el
    servicio con un mensaje en español ("Falta el prompt de la carta.") y no el
    422 crudo de Pydantic, que le dice "Field required" a un autor que está
    corrigiendo su carta.
    """

    categoria: Optional[str] = Field(default=None, max_length=40)
    accion: Optional[str] = Field(default=None, max_length=40)
    frase: Optional[str] = Field(default=None, max_length=_TOPE_DURO)
    prompt: Optional[str] = Field(default=None, max_length=_TOPE_DURO)
    firma: Optional[str] = Field(default=None, pattern=_FIRMAS)

    @field_validator("categoria", "accion", "frase", "prompt", mode="before")
    @classmethod
    def _limpia(cls, v):
        return v.strip() if isinstance(v, str) else v


class CartaComunidadOut(BaseModel):
    """Una carta propuesta, como la ve su autor en la pestaña Crear.

    `carta` trae la MISMA forma que cualquier carta del mazo (`_carta_enriquecida`),
    para que el front la dibuje con el componente de siempre aunque todavía no esté
    publicada. `sugerencia` es el `fix_sugerido` del juez (frase/prompt reescritos).
    """

    id: str
    estado: str
    firma: str
    motivo: Optional[str] = None
    sugerencia: Optional[dict] = None
    concepto: Optional[str] = None
    carta_id: Optional[str] = None
    # B2.1 lo calcula; hasta entonces, 0.
    personas_acompanadas: int = 0
    created_at: datetime
    updated_at: datetime
    carta: dict
