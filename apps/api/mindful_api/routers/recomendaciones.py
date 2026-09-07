"""WS29 · C1.3 · Recomendaciones: las mías, crear, editar, borrar y publicar.

Router fino: resuelve sesión y usuario y delega TODO en
`services/recomendaciones.py` (plan, largos, tipos y el tope de 30).

Los bodies viven acá (no en `schemas.py`) y solo ponen el TOPE DURO: cortan lo
absurdo antes de que llegue a la base. El largo real y su mensaje en español los
decide el servicio, para que el usuario lea "El título no puede tener más de 80
caracteres." y no un error de validación armado por Pydantic.
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..auth import get_current_user
from ..db.base import get_session
from ..db.models import Usuario
from ..services.recomendaciones import (
    borrar,
    cambiar_visibilidad,
    crear,
    editar,
    listar,
)

router = APIRouter(prefix="/api/recomendaciones", tags=["recomendaciones"])

# Mismo tope duro que el resto de la API (`schemas._TOPE_DURO`): nadie sube un
# libro entero en el título para tirar abajo la validación.
TOPE_DURO = 5000


class RecomendacionCreate(BaseModel):
    """Lo que manda el formulario. `visibilidad` ausente = privada (el default
    seguro: se publica cuando el usuario lo decide, no por omisión)."""

    titulo: str = Field(max_length=TOPE_DURO)
    tipo: str = Field(max_length=TOPE_DURO)
    texto: str = Field(max_length=TOPE_DURO)
    url: Optional[str] = Field(default=None, max_length=TOPE_DURO)
    visibilidad: Optional[str] = Field(default=None, max_length=TOPE_DURO)


class RecomendacionUpdate(BaseModel):
    """Edición parcial: lo que no viene, no se toca. `url: ""` borra el enlace."""

    titulo: Optional[str] = Field(default=None, max_length=TOPE_DURO)
    tipo: Optional[str] = Field(default=None, max_length=TOPE_DURO)
    texto: Optional[str] = Field(default=None, max_length=TOPE_DURO)
    url: Optional[str] = Field(default=None, max_length=TOPE_DURO)
    visibilidad: Optional[str] = Field(default=None, max_length=TOPE_DURO)


class VisibilidadRecomendacionUpdate(BaseModel):
    visibilidad: str = Field(max_length=TOPE_DURO)


@router.get("")
def mis_recomendaciones(
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> list:
    """Las recomendaciones que subí, de la más nueva a la más vieja."""
    return listar(s, usuario)


@router.post("", status_code=status.HTTP_201_CREATED)
def nueva(
    body: RecomendacionCreate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Sube una recomendación al Baúl (30 como máximo)."""
    return crear(
        s,
        usuario,
        titulo=body.titulo,
        tipo=body.tipo,
        texto=body.texto,
        url=body.url,
        visibilidad=body.visibilidad,
    )


@router.put("/{recomendacion_id}")
def actualizar(
    recomendacion_id: str,
    body: RecomendacionUpdate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """Corrige una recomendación mía. Ajena o inexistente: 404, el mismo."""
    return editar(
        s,
        usuario,
        recomendacion_id,
        titulo=body.titulo,
        tipo=body.tipo,
        texto=body.texto,
        url=body.url,
        visibilidad=body.visibilidad,
    )


@router.delete("/{recomendacion_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar(
    recomendacion_id: str,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> Response:
    """La saca del Baúl para siempre (y libera un lugar de los 30)."""
    borrar(s, usuario, recomendacion_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.put("/{recomendacion_id}/visibilidad")
def poner_visibilidad(
    recomendacion_id: str,
    body: VisibilidadRecomendacionUpdate,
    s: Session = Depends(get_session),
    usuario: Usuario = Depends(get_current_user),
) -> dict:
    """La publica con la comunidad o la repliega. Devuelve el ítem ya actualizado."""
    return cambiar_visibilidad(s, usuario, recomendacion_id, body.visibilidad)
