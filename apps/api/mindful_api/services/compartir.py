"""M5 · Compartir. El link es un REGALO, no un embudo. Token opaco aleatorio (jamás
IDs internos). El link muere si se borra la entrada (salvo la "carta sola", que no
la referencia).

WS25 · el receptor SÍ tiene que loguearse para abrirlo (decisión de Tomás: la
comunidad se entra con nombre). Login simple: Google o enlace por email.

WS25 · el usuario ya no elige qué parte viaja: viaja la ficha ENTERA tal como está
al momento de enviar, y el modo se DERIVA de la Pausa:
- carta_sola → la Pausa no tiene reflexión ni fotos. Sólo la carta (sin datos del
  usuario). Sobrevive al borrado de la entrada.
- ejercicio  → carta + reflexión + fotos. Muere si se borra/revoca la entrada.

El modo queda CONGELADO en la fila: un link "carta sola" enviado antes de escribir
la reflexión sigue mostrando sólo la carta. Lo ya entregado no cambia.
"""

from __future__ import annotations

import secrets

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Carta, Compartido, Entrega, Foto, Usuario
from . import storage
from .entrega import _carta_enriquecida
from .plan import limites


def _modo_de(s: Session, entrega: Entrega) -> str:
    """El modo NO lo elige nadie: lo dice la Pausa. Si tiene algo del usuario
    (reflexión escrita o al menos una foto), viaja entera; si no, viaja la carta sola."""
    if (entrega.reflexion or "").strip():
        return "ejercicio"
    tiene_foto = s.scalar(
        select(Foto.id).where(Foto.entrega_id == entrega.id).limit(1)
    )
    return "ejercicio" if tiene_foto else "carta_sola"


def crear_compartido(s: Session, usuario: Usuario, entrega_id: str, nota=None) -> dict:
    """WS25 · recibe el Usuario (no el id) porque el largo de la nota depende del plan.

    Ya no hay compuerta de premium: compartir la ficha entera es de todos.
    """
    usuario_id = usuario.id
    entrega = s.get(Entrega, entrega_id)
    # Primero el aislamiento: no delatamos la existencia de una entrega ajena ni
    # siquiera con un mensaje distinto.
    if entrega is None or entrega.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")

    lim = limites(usuario)
    if nota is not None and len(nota) > lim.reflexion_max:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Tu nota puede tener hasta {lim.reflexion_max} caracteres "
            f"en el plan {lim.plan} (mandaste {len(nota)})",
        )

    modo = _modo_de(s, entrega)
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
    """Lo que ve el receptor del regalo (WS25 · con login: el router exige identidad).

    El permiso sigue siendo el TOKEN: cualquier persona logueada que lo tenga abre
    el regalo. El login es para entrar a la comunidad con nombre, no un filtro de
    destinatario.
    """
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
            # NUNCA el `storage_path` (lleva el usuario_id adentro y no se puede
            # renderizar): URLs públicas atadas a ESTE token, que mueren con él.
            ids = s.scalars(
                select(Foto.id)
                .where(Foto.entrega_id == entrega.id)
                .order_by(Foto.created_at)
            ).all()
            regalo["fotos"] = [url_foto_publica(comp.token, fid) for fid in ids]
    return regalo


def url_foto_publica(token: str, foto_id: str) -> str:
    """La foto del regalo, servida por el token (jamás por el id del usuario)."""
    return f"/api/c/{token}/fotos/{foto_id}"


def leer_foto_publica(s: Session, token: str, foto_id: str) -> tuple:
    """La imagen de un regalo `ejercicio` vivo. Cualquier otro caso, 404.

    Las condiciones son todas: el compartido existe, está activo, es modo
    `ejercicio`, todavía apunta a una entrega (al borrarla el FK va a NULL) y la
    foto pertenece a ESA entrega. Revocar el link o borrar la entrada apaga las
    fotos en el acto.
    """
    no_esta = HTTPException(status.HTTP_404_NOT_FOUND, "Este regalo ya no está disponible")

    comp = s.scalar(select(Compartido).where(Compartido.token == token))
    if comp is None or not comp.activo:
        raise no_esta
    if comp.modo != "ejercicio" or not comp.entrega_id:
        raise no_esta

    foto = s.get(Foto, foto_id)
    if foto is None or foto.entrega_id != comp.entrega_id:
        raise no_esta

    contenido = storage.leer(foto.storage_path)
    if contenido is None:
        raise no_esta
    return contenido, storage.mime_de(foto.storage_path)


def revocar(s: Session, usuario_id: str, compartido_id: str) -> None:
    comp = s.get(Compartido, compartido_id)
    if comp is None or comp.usuario_id != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Link no encontrado")
    comp.activo = False
    s.commit()
