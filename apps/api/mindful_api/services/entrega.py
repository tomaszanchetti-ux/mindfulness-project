"""M2/M3 · Servicio de entrega del día + cierre del ritual.

Conecta el motor puro (`seleccion.elegir_carta`) con la DB:
- pool   ← tabla global `cartas` (Mundo 1, completo — WS22: nada se filtra)
- perfil ← `entregas` del usuario (Mundo 2, filtrado por id)

Regla M2: 1 carta por día (TZ del usuario). Si ya hay carta de hoy, se devuelve;
si no, se sortea una nueva y se crea la fila `entregas` (vigencia 24h).
"""

from __future__ import annotations

from datetime import datetime, timezone
from zoneinfo import ZoneInfo

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    Accion,
    Carta,
    Categoria,
    Entrega,
    Usuario,
)
from .plan import COMENTARIO_CARTA_MAX, limites
from .seleccion import Entrega as EntregaMotor
from .seleccion import Perfil, elegir_carta


def _tz(usuario: Usuario) -> ZoneInfo:
    try:
        return ZoneInfo(usuario.tz)
    except Exception:
        return ZoneInfo("Europe/Madrid")


def _fecha_local(fecha: datetime, tz: ZoneInfo):
    # `fecha` viene de Postgres como tz-aware (UTC). La paso a la TZ del usuario.
    if fecha.tzinfo is None:
        fecha = fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(tz).date()


def _carta_enriquecida(s: Session, carta: Carta) -> dict:
    """La carta + lo visual que se joinea al render (categoría + acción)."""
    cat = s.get(Categoria, carta.categoria_slug)
    acc = s.get(Accion, carta.accion_slug)
    return {
        "id": carta.id,
        "frase": carta.frase,
        "prompt": carta.prompt,
        "categoria": {
            "slug": cat.slug, "nombre": cat.nombre,
            "color_accent": cat.color_accent, "color_text": cat.color_text, "img": cat.img,
        },
        "accion": {"slug": acc.slug, "nombre": acc.nombre, "glifo": acc.glifo},
    }


def _salida(s: Session, entrega: Entrega, ya_existia: bool) -> dict:
    carta = s.get(Carta, entrega.carta_id)
    return {
        "entrega": {
            "id": entrega.id,
            "fecha": entrega.fecha,
            "estrellas": entrega.estrellas,
            "completada": entrega.completada,
            "reflexion": entrega.reflexion,
            "comentario_carta": entrega.comentario_carta,
            # WS24 · A1.3: cuántas veces cambió la carta hoy (el front calcula los restantes
            # con `limites.cambios_carta`, así lo sabe también al recargar).
            "cambios": entrega.cambios or 0,
            "ya_existia": ya_existia,
        },
        "carta": _carta_enriquecida(s, carta),
    }


def historial_motor(s: Session, rows, tz: ZoneInfo) -> list:
    """Las entregas del usuario como las ve el motor (una por carta VISTA).

    WS24 · A1.3: las cartas que el usuario descartó al cambiar la de hoy también
    las vio, así que entran a las ventanas de 7 días (carta y concepto) como
    vistas ese mismo día. Van ANTES de la carta servida, para que `historial[-1]`
    siga siendo la carta con la que se quedó (la regla "nunca la de ayer").
    Sin estrellas (no puntuó nada de ellas): no inclinan la afinidad.
    """
    historial = []
    for (e, cat, acc, conc) in rows:
        dia = _fecha_local(e.fecha, tz).toordinal()
        for carta_id in (e.descartadas or []):
            c = s.get(Carta, carta_id)
            if c is None:
                continue
            historial.append(EntregaMotor(
                carta_id=c.id, categoria=c.categoria_slug, accion=c.accion_slug,
                dia=dia, concepto=c.concepto,
            ))
        historial.append(EntregaMotor(
            carta_id=e.carta_id, categoria=cat, accion=acc, dia=dia, concepto=conc,
            estrellas=e.estrellas, completada=e.completada,
        ))
    return historial


def obtener_carta_del_dia(s: Session, usuario: Usuario) -> dict:
    tz = _tz(usuario)
    hoy = datetime.now(tz).date()

    # WS17: las categorías ya no se eligen (rotación completa de los 6 campos).
    # El único requisito de onboarding es haber aceptado los términos.
    if usuario.terminos_aceptados_at is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Onboarding incompleto: acepta los términos antes de recibir cartas.",
        )

    # WS22: las acciones ya no se eligen — el pool es el pilar completo.
    # (`usuario_acciones` quedó obsoleta; nada la lee.)

    # Historial del usuario (con categoría/acción/concepto de cada carta), por fecha.
    rows = s.execute(
        select(Entrega, Carta.categoria_slug, Carta.accion_slug, Carta.concepto)
        .join(Carta, Carta.id == Entrega.carta_id)
        .where(Entrega.usuario_id == usuario.id)
        .order_by(Entrega.fecha)
    ).all()

    # ¿Ya hay carta de hoy? (1/día por TZ del usuario) → devolverla.
    if rows:
        ultima_entrega = rows[-1][0]
        if _fecha_local(ultima_entrega.fecha, tz) == hoy:
            return _salida(s, ultima_entrega, ya_existia=True)

    # Construir el perfil para el motor.
    perfil = Perfil(historial=historial_motor(s, rows, tz))

    # Pool global como dicts con las keys que el motor espera.
    pool = [
        {"id": c.id, "categoria": c.categoria_slug, "accion": c.accion_slug,
         "concepto": c.concepto}
        for c in s.scalars(select(Carta)).all()
    ]

    elegida = elegir_carta(perfil, pool, modo="v1")

    nueva = Entrega(usuario_id=usuario.id, carta_id=elegida["id"])
    s.add(nueva)
    s.commit()
    s.refresh(nueva)
    return _salida(s, nueva, ya_existia=False)


def cerrar_ritual(
    s: Session, usuario: Usuario, entrega_id: str,
    estrellas=None, reflexion=None, completada=True, comentario_carta=None,
) -> dict:
    """M3 · cierre: estrellas + reflexión + comentario + completada (entrega del usuario).

    WS24 · la reflexión se mide contra el plan (`limites`), no contra un número
    hardcodeado: un free que manda 500 caracteres recibe 422 diga lo que diga el front.
    """
    entrega = s.get(Entrega, entrega_id)
    # Aislamiento: 404 si no existe O es de otro usuario (no filtra existencia ajena).
    if entrega is None or entrega.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Entrega no encontrada")

    lim = limites(usuario)

    if estrellas is not None:
        entrega.estrellas = estrellas
    if reflexion is not None:
        # El schema ya la entrega strippeada (y el blanco puro llega como None):
        # medimos los caracteres ÚTILES, nunca el padding.
        reflexion = reflexion.strip()
        if len(reflexion) > lim.reflexion_max:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"Tu reflexión puede tener hasta {lim.reflexion_max} caracteres "
                f"en el plan {lim.plan} (mandaste {len(reflexion)})",
            )
        # Vacío → None: una reflexión en blanco no es una pausa "escrita".
        entrega.reflexion = reflexion or None
    if comentario_carta is not None:
        comentario = comentario_carta.strip()
        if len(comentario) > COMENTARIO_CARTA_MAX:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                f"El comentario sobre la carta puede tener hasta "
                f"{COMENTARIO_CARTA_MAX} caracteres",
            )
        # Vacío → None: no guardamos cadenas en blanco.
        entrega.comentario_carta = comentario or None
    entrega.completada = completada

    s.add(entrega)
    s.commit()
    s.refresh(entrega)
    return _salida(s, entrega, ya_existia=True)
