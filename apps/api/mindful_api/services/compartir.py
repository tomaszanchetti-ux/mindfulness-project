"""M5 · Compartir. El link es un REGALO, no un embudo: el receptor abre y ve sin
instalar ni loguear. Token opaco aleatorio (jamás IDs internos). El link muere si se
borra la entrada (salvo la "carta sola", que no la referencia).

Dos modos:
- carta_sola → sólo la carta (sin datos del usuario). Sobrevive al borrado de la entrada.
- ejercicio  → carta + reflexión + fotos. Muere si se borra/revoca la entrada.
"""

from __future__ import annotations

import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Carta, Compartido, Entrega, Foto, Usuario
from .entrega import _carta_enriquecida
from .plan import limites


def crear_compartido(s: Session, usuario: Usuario, entrega_id: str, modo: str,
                     nota=None) -> dict:
    """WS24 · recibe el Usuario (no el id): el modo `ejercicio` y el largo de la nota
    dependen del plan, y el backend es quien los aplica."""
    usuario_id = usuario.id
    entrega = s.get(Entrega, entrega_id)
    # Primero el aislamiento (404 antes que cualquier compuerta de plan): no delatamos
    # la existencia de una entrega ajena ni siquiera con un 403.
    if entrega is None or entrega.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")

    lim = limites(usuario)
    if modo == "ejercicio" and not lim.compartir_ejercicio:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Compartir el ejercicio completo es parte de Dwellia premium",
        )
    if nota is not None and len(nota) > lim.reflexion_max:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Tu nota puede tener hasta {lim.reflexion_max} caracteres "
            f"en el plan {lim.plan} (mandaste {len(nota)})",
        )

    token = secrets.token_urlsafe(16)  # opaco, ~22 chars
    comp = Compartido(
        token=token,
        usuario_id=usuario_id,
        # carta_sola NO referencia la entrega → sobrevive al borrado.
        entrega_id=entrega_id if modo == "ejercicio" else None,
        carta_id=entrega.carta_id,
        modo=modo,
        nota=nota,
        activo=True,
    )
    s.add(comp)
    s.commit()
    s.refresh(comp)
    return {"token": token, "url": f"/c/{token}", "modo": modo}


def leer_publico(s: Session, token: str) -> dict:
    """Sin login. Lo que ve el receptor del regalo."""
    comp = s.scalar(select(Compartido).where(Compartido.token == token))
    if comp is None or not comp.activo:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Este regalo ya no está disponible")

    carta = s.get(Carta, comp.carta_id)
    remitente = s.get(Usuario, comp.usuario_id)
    regalo = {
        "modo": comp.modo,
        "nota": comp.nota,
        # Cómo firmamos el regalo: el apodo del remitente (o None → "Alguien" en el front).
        "de": remitente.apodo if remitente else None,
        "carta": _carta_enriquecida(s, carta),
    }

    # Modo ejercicio: sumar reflexión + fotos, sólo si la entrega sigue viva.
    if comp.modo == "ejercicio" and comp.entrega_id:
        entrega = s.get(Entrega, comp.entrega_id)
        if entrega is not None:
            regalo["reflexion"] = entrega.reflexion
            regalo["fotos"] = list(s.scalars(
                select(Foto.storage_path).where(Foto.entrega_id == entrega.id)
            ).all())
    return regalo


def revocar(s: Session, usuario_id: str, compartido_id: str) -> None:
    comp = s.get(Compartido, compartido_id)
    if comp is None or comp.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link no encontrado")
    comp.activo = False
    s.commit()
