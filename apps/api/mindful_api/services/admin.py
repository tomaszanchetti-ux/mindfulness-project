"""WS27 · B1.3 · Administración: el escritorio donde Tomás decide.

Todo lo que llega acá ya pasó por el juez (B1.2) o por su ausencia (sin key, todo
cae en `revision_dwellia`). Acá NO se vuelve a juzgar: se decide.

Las tres decisiones y lo que significan (Roadmap v2 §0 · "Validación"):

  aprobar    → **APROBAR ES CARGAR**. No hay un paso posterior de "publicar": la
               propuesta se copia como una fila nueva de `cartas` (Mundo 1, con
               `origen=comunidad`) y desde ese instante el mazo la puede servir.
               `cartas_comunidad.carta_id` deja el rastro de cuál es.
  rechazar   → no entra, con un motivo que el autor lee en Crear.
  a-revisar  → vuelve al autor con una sugerencia (y, si Tomás lo escribe, un
               `fix_sugerido` con la frase/prompt propuestos). El autor la reenvía.

Cada decisión que el autor tiene que enterarse dispara el aviso canónico
(`services/avisos.avisar_estado_carta`): el MISMO texto y el mismo push que usa
el juez, para que la app no hable con dos voces.

La firma es del AUTOR, no de quien aprueba: si eligió `apodo` (y tiene apodo)
viaja su apodo en `firma_publica`; si eligió `anonima`, viaja None y el dorso
dirá "de alguien de la comunidad".
"""

from __future__ import annotations

import secrets
from datetime import datetime, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    ESTADO_A_REVISAR,
    ESTADO_APROBADA,
    ESTADO_EN_REVISION,
    ESTADO_RECHAZADA,
    ESTADO_REVISION_DWELLIA,
    ESTADOS_CARTA_COMUNIDAD,
    FIRMA_APODO,
    ORIGEN_COMUNIDAD,
    Accion,
    Carta,
    CartaComunidad,
    Categoria,
    Entrega,
    Usuario,
)
from .avisos import avisar_estado_carta

# El filtro por defecto de la bandeja: lo que espera decisión de Tomás.
ESTADO_DEFAULT = ESTADO_REVISION_DWELLIA
# Valor especial del filtro: "no filtres nada".
ESTADO_TODAS = "todas"
ESTADOS_FILTRO = tuple(ESTADOS_CARTA_COMUNIDAD) + (ESTADO_TODAS,)

# Desde dónde se puede tomar cada decisión. Cualquier otro estado ⇒ 409: la
# propuesta ya se decidió (o el autor la retiró) y no se re-decide por encima.
DESDE_APROBAR = (ESTADO_REVISION_DWELLIA, ESTADO_EN_REVISION)
DESDE_RECHAZAR = (ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA, ESTADO_A_REVISAR)
DESDE_A_REVISAR = (ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA)

# Prefijo del id de una carta publicada desde la comunidad. Se ve de un vistazo
# en la DB y JAMÁS colisiona con los ids del mazo de Dwellia (`grat-con-01`…).
PREFIJO_CARTA_COMUNIDAD = "com-"

COMENTARIOS_LIMIT_DEFAULT = 100


def _now() -> datetime:
    return datetime.now(timezone.utc)


# ── Cómo se ve una propuesta desde el escritorio ─────────────────────────────
def _firma_publica(propuesta: CartaComunidad, autor: Optional[Usuario]) -> Optional[str]:
    """Lo que verá el resto en el dorso. None = "alguien de la comunidad"."""
    if propuesta.firma == FIRMA_APODO and autor is not None and autor.apodo:
        return autor.apodo
    return None


def _carta_previa(s: Session, propuesta: CartaComunidad, autor: Optional[Usuario]) -> dict:
    """La propuesta con la MISMA forma que `entrega._carta_enriquecida`.

    Así el front la dibuja con el componente `Card` de siempre, sin un render
    especial para el panel de administración: Tomás ve exactamente la carta que
    vería un usuario si la aprobara. `id` es el de la PROPUESTA (todavía no hay
    carta publicada) y `origen` es `comunidad` por definición.
    """
    cat = s.get(Categoria, propuesta.categoria_slug)
    acc = s.get(Accion, propuesta.accion_slug)
    return {
        "id": propuesta.id,
        "frase": propuesta.frase,
        "prompt": propuesta.prompt,
        "categoria": None if cat is None else {
            "slug": cat.slug, "nombre": cat.nombre,
            "color_accent": cat.color_accent, "color_text": cat.color_text, "img": cat.img,
        },
        "accion": None if acc is None else {
            "slug": acc.slug, "nombre": acc.nombre, "glifo": acc.glifo,
        },
        "origen": ORIGEN_COMUNIDAD,
        "firma_publica": _firma_publica(propuesta, autor),
    }


def _item(s: Session, propuesta: CartaComunidad) -> dict:
    """Una fila de la bandeja. Lleva el `veredicto` CRUDO a propósito: Tomás tiene
    que poder leer literalmente lo que dijo el juez, no un resumen nuestro."""
    autor = s.get(Usuario, propuesta.usuario_id)
    return {
        "id": propuesta.id,
        "estado": propuesta.estado,
        "firma": propuesta.firma,
        "motivo": propuesta.motivo,
        "concepto": propuesta.concepto,
        "veredicto": propuesta.veredicto,
        "carta_id": propuesta.carta_id,
        "created_at": propuesta.created_at,
        "updated_at": propuesta.updated_at,
        "autor": {
            "apodo": None if autor is None else autor.apodo,
            "email": None if autor is None else autor.email,
            "nombre": None if autor is None else autor.nombre,
        },
        "carta": _carta_previa(s, propuesta, autor),
    }


# ── Lectura ──────────────────────────────────────────────────────────────────
def listar_cartas(s: Session, estado: str = ESTADO_DEFAULT) -> list:
    """La bandeja, más nueva primero. `estado='todas'` no filtra."""
    if estado not in ESTADOS_FILTRO:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Estado desconocido: {estado}. Válidos: {', '.join(ESTADOS_FILTRO)}",
        )
    q = select(CartaComunidad)
    if estado != ESTADO_TODAS:
        q = q.where(CartaComunidad.estado == estado)
    # `id` como desempate: dos propuestas del mismo instante salen siempre en el
    # mismo orden (una lista que baila entre recargas no se puede revisar).
    q = q.order_by(CartaComunidad.created_at.desc(), CartaComunidad.id.desc())
    return [_item(s, p) for p in s.scalars(q).all()]


def listar_comentarios(s: Session, limit: int = COMENTARIOS_LIMIT_DEFAULT) -> list:
    """El feedback privado de las cartas (lo que se escribe debajo de las estrellas).

    Es para Dwellia, no es público: por eso NO viaja el email del usuario. Solo el
    apodo, que ya es el nombre con el que la app se dirige a él. Si no tiene
    apodo, viaja None y el comentario queda anónimo — se lee igual.
    """
    rows = s.execute(
        select(Entrega, Carta, Usuario)
        .join(Carta, Carta.id == Entrega.carta_id)
        .join(Usuario, Usuario.id == Entrega.usuario_id)
        .where(Entrega.comentario_carta.is_not(None))
        .order_by(Entrega.fecha.desc(), Entrega.id.desc())
        .limit(limit)
    ).all()
    return [
        {
            "entrega_id": e.id,
            "fecha": e.fecha,
            "estrellas": e.estrellas,
            "comentario": e.comentario_carta,
            "carta_id": c.id,
            "frase": c.frase,
            "categoria": c.categoria_slug,
            "apodo": u.apodo,
        }
        for (e, c, u) in rows
    ]


# ── Decisiones ───────────────────────────────────────────────────────────────
def _propuesta(s: Session, carta_comunidad_id: str, desde: tuple) -> CartaComunidad:
    """Busca la propuesta y verifica que la decisión se pueda tomar AHORA.

    404 si no existe · 409 si su estado no admite esta decisión (ya se decidió,
    el autor la retiró, o el juez todavía la tiene). Se lee CON BLOQUEO: dos
    clics simultáneos en "Aprobar" no publican la carta dos veces — el segundo
    espera al commit del primero y ve el estado ya cambiado.
    """
    propuesta = s.get(CartaComunidad, carta_comunidad_id, with_for_update=True)
    if propuesta is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carta no encontrada")
    if propuesta.estado not in desde:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            f"No se puede decidir sobre una carta en estado '{propuesta.estado}'",
        )
    return propuesta


def _nuevo_id_carta(s: Session) -> str:
    """`com-` + 8 hex. Se reintenta si (contra toda probabilidad) ya existe."""
    for _ in range(10):
        candidato = PREFIJO_CARTA_COMUNIDAD + secrets.token_hex(4)
        if s.get(Carta, candidato) is None:
            return candidato
    raise HTTPException(  # pragma: no cover — 10 colisiones seguidas de 2^32
        status.HTTP_500_INTERNAL_SERVER_ERROR, "No se pudo generar el id de la carta"
    )


def aprobar(
    s: Session, carta_comunidad_id: str, concepto: Optional[str] = None
) -> dict:
    """APROBAR = CARGAR AL MAZO. Publica la carta y avisa al autor."""
    propuesta = _propuesta(s, carta_comunidad_id, DESDE_APROBAR)
    autor = s.get(Usuario, propuesta.usuario_id)

    concepto_final = (concepto or "").strip() or propuesta.concepto
    if not concepto_final:
        # Sin concepto no hay dedupe semanal (M2 no repite concepto en la ventana):
        # antes que dejarlo vacío, se le da uno propio y único a esta carta.
        concepto_final = PREFIJO_CARTA_COMUNIDAD + propuesta.id[:8]

    carta = Carta(
        id=_nuevo_id_carta(s),
        categoria_slug=propuesta.categoria_slug,
        accion_slug=propuesta.accion_slug,
        concepto=concepto_final,
        frase=propuesta.frase,
        prompt=propuesta.prompt,
        origen=ORIGEN_COMUNIDAD,
        autor_usuario_id=None if autor is None else autor.id,
        firma_publica=_firma_publica(propuesta, autor),
    )
    s.add(carta)
    s.flush()  # la FK `carta_id` necesita la fila ya escrita

    propuesta.estado = ESTADO_APROBADA
    propuesta.carta_id = carta.id
    propuesta.concepto = concepto_final
    propuesta.updated_at = _now()
    s.add(propuesta)

    if autor is not None:
        avisar_estado_carta(s, autor, propuesta.id, ESTADO_APROBADA)
    s.commit()
    s.refresh(propuesta)
    return _item(s, propuesta)


def rechazar(s: Session, carta_comunidad_id: str, motivo: str) -> dict:
    """No entra al mazo. El motivo es lo que el autor lee en Crear: se guarda tal cual."""
    propuesta = _propuesta(s, carta_comunidad_id, DESDE_RECHAZAR)
    autor = s.get(Usuario, propuesta.usuario_id)

    propuesta.estado = ESTADO_RECHAZADA
    propuesta.motivo = motivo
    propuesta.updated_at = _now()
    s.add(propuesta)

    if autor is not None:
        avisar_estado_carta(s, autor, propuesta.id, ESTADO_RECHAZADA)
    s.commit()
    s.refresh(propuesta)
    return _item(s, propuesta)


def marcar_a_revisar(
    s: Session, carta_comunidad_id: str, sugerencia: str, fix: Optional[dict] = None
) -> dict:
    """Vuelve al autor con una sugerencia (y opcionalmente una frase/prompt propuestos).

    Convención compartida con B1.1: lo que el autor ve como sugerencia concreta
    vive en `veredicto["fix_sugerido"]`, venga del juez o de Dwellia. Por eso acá
    se ESCRIBE esa misma clave y se marca `fuente: "dwellia"` — el resto del
    veredicto del juez se conserva intacto (Tomás decide, no borra evidencia).
    """
    propuesta = _propuesta(s, carta_comunidad_id, DESDE_A_REVISAR)
    autor = s.get(Usuario, propuesta.usuario_id)

    propuesta.estado = ESTADO_A_REVISAR
    propuesta.motivo = sugerencia
    # Reasignación (no mutación) para que SQLAlchemy vea el cambio en la columna JSON.
    propuesta.veredicto = {
        **(propuesta.veredicto or {}),
        "fix_sugerido": fix,
        "fuente": "dwellia",
    }
    propuesta.updated_at = _now()
    s.add(propuesta)

    if autor is not None:
        avisar_estado_carta(s, autor, propuesta.id, ESTADO_A_REVISAR)
    s.commit()
    s.refresh(propuesta)
    return _item(s, propuesta)
