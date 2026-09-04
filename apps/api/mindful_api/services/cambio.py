"""WS24 · A1.3 · Cambiar la carta del día (premium, hasta 3 veces).

Sigue llegando UNA carta por día: el cambio REEMPLAZA la carta de la entrega de
hoy (misma fila), no crea otra entrega. La nueva es del mismo pilar y cruza el
eje quietud ↔ movimiento — la válvula del "hoy no quiero moverme" (Roadmap v2 §3).

El motor puro decide (`seleccion.cambiar_carta`); acá se resuelve el permiso, se
arma el perfil desde la DB y se actualiza la fila.
"""

from __future__ import annotations

from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import Carta, Entrega, Usuario
from .entrega import Perfil, _fecha_local, _salida, _tz, historial_motor
from .plan import limites
from .seleccion import SinCandidatas, cambiar_carta


def _esta_cerrada(entrega: Entrega) -> bool:
    """La Pausa ya se vivió: hay cierre, estrellas, reflexión o comentario.

    El `comentario_carta` cuenta: el front solo lo muestra DESPUÉS de elegir las
    estrellas, así que si hay comentario la Pausa ya se vivió — y dejarlo cambiar
    dejaría el comentario pegado a la entrega apuntando a OTRA carta.
    """
    return bool(
        entrega.completada
        or entrega.estrellas is not None
        or entrega.reflexion
        or entrega.comentario_carta
    )


def cambiar_carta_del_dia(s: Session, usuario: Usuario, entrega_id: str) -> dict:
    # Cupo atómico: la fila de la entrega se lee CON BLOQUEO (SELECT ... FOR UPDATE).
    # Sin el lock, dos POST simultáneos leen `cambios` antes de que el otro commitee
    # y los dos pasan el tope (leer-y-después-escribir). Con el lock el segundo
    # espera al commit del primero y ve el contador ya actualizado. Se suelta al
    # commit / cierre de la sesión.
    entrega = s.get(Entrega, entrega_id, with_for_update=True)
    # Aislamiento: 404 si no existe O es de otro usuario (no filtra existencia ajena).
    if entrega is None or entrega.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")

    lim = limites(usuario)
    if lim.cambios_carta == 0:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Cambiar la carta es parte de Dwellia premium",
        )

    tz = _tz(usuario)
    hoy = datetime.now(tz).date()
    if _fecha_local(entrega.fecha, tz) != hoy:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Solo puedes cambiar la carta de hoy"
        )

    if _esta_cerrada(entrega):
        raise HTTPException(
            status.HTTP_409_CONFLICT, "La Pausa de hoy ya está cerrada"
        )

    cambios_hechos = entrega.cambios or 0
    if cambios_hechos >= lim.cambios_carta:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"Ya cambiaste la carta {lim.cambios_carta} veces hoy",
        )

    # Historial del usuario SIN la entrega de hoy: sus ventanas no deben bloquear
    # a la carta que estamos cambiando (de eso se ocupan `descartadas` y `actual`).
    rows = s.execute(
        select(Entrega, Carta.categoria_slug, Carta.accion_slug, Carta.concepto)
        .join(Carta, Carta.id == Entrega.carta_id)
        .where(Entrega.usuario_id == usuario.id)
        .order_by(Entrega.fecha)
    ).all()
    # Mismo constructor que la entrega diaria (incluye las descartadas de otros
    # días como vistas); la entrega de HOY se excluye — sus descartadas de hoy
    # viajan aparte en `descartadas` y la carta actual en `actual`.
    perfil = Perfil(historial=historial_motor(
        s, [r for r in rows if r[0].id != entrega.id], tz
    ))

    pool = [
        {"id": c.id, "categoria": c.categoria_slug, "accion": c.accion_slug,
         "concepto": c.concepto}
        for c in s.scalars(select(Carta)).all()
    ]

    vieja = s.get(Carta, entrega.carta_id)
    actual = {
        "id": vieja.id, "categoria": vieja.categoria_slug,
        "accion": vieja.accion_slug, "concepto": vieja.concepto,
    }
    descartadas = list(entrega.descartadas or [])

    try:
        nueva = cambiar_carta(
            perfil, pool, actual, set(descartadas), hoy.toordinal()
        )
    except SinCandidatas:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "No quedan cartas para cambiar hoy"
        )

    # La carta vieja pasa a descartadas (lista nueva: la columna JSON no rastrea
    # mutaciones in-place) y la entrega de HOY cambia de carta en su misma fila.
    entrega.descartadas = descartadas + [actual["id"]]
    entrega.carta_id = nueva["id"]
    entrega.cambios = cambios_hechos + 1

    s.add(entrega)
    s.commit()
    s.refresh(entrega)

    salida = _salida(s, entrega, ya_existia=True)
    salida["cambios"] = entrega.cambios
    salida["cambios_restantes"] = lim.cambios_carta - entrega.cambios
    return salida
