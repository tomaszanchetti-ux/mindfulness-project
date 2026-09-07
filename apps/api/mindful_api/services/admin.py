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
from datetime import datetime, timedelta, timezone
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
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
    ORIGEN_DWELLIA,
    Accion,
    Carta,
    CartaComunidad,
    Categoria,
    Entrega,
    Usuario,
)
from .avisos import avisar_estado_carta
from .cartas_comunidad import FRASE_MAX, PROMPT_MAX, PROMPT_MIN, _fix_sugerido, _texto
from .entrega import _carta_enriquecida
from .plan import es_premium

# El filtro por defecto de la bandeja: lo que espera decisión de Tomás.
ESTADO_DEFAULT = ESTADO_REVISION_DWELLIA
# Valor especial del filtro: "no filtres nada".
ESTADO_TODAS = "todas"
# Valor especial del filtro: TODO lo que espera una mirada. `revision_dwellia` es
# lo que espera a Tomás y `en_revision` es lo que todavía tiene el juez; las dos
# son "pendiente" desde el escritorio, y una carta clavada en `en_revision` (un
# juez que se cayó) tiene que verse, no esconderse detrás del filtro por defecto.
ESTADO_PENDIENTES = "pendientes"
ESTADOS_PENDIENTES = (ESTADO_EN_REVISION, ESTADO_REVISION_DWELLIA)
ESTADOS_FILTRO = tuple(ESTADOS_CARTA_COMUNIDAD) + (ESTADO_TODAS, ESTADO_PENDIENTES)

# WS27 · B2.1 · el orden del RELOJ de los pilares (el mismo del hexágono de la
# app). El tablero se lee de un vistazo solo si los seis salen siempre igual;
# ordenarlos por nombre o por conteo haría que la columna baile en cada recarga.
ORDEN_PILARES = (
    "amor-propio", "gratitud", "vinculos", "sentido", "perspectiva", "resiliencia",
)

# Ventana del tablero de comentarios: "lo que llegó esta semana".
DIAS_RECIENTES = 7

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

    Q/A B1.3 (BUG-B13-2): en cuanto la propuesta se aprueba y existe la fila
    publicada, la ÚNICA verdad es esa fila. La firma viaja CONGELADA en
    `cartas.firma_publica`, así que recalcularla desde el apodo de hoy haría que
    el panel (y la pantalla del autor) mostraran una firma distinta de la que
    lee la comunidad. Con `carta_id` cargado se sirve la carta de verdad.
    """
    if propuesta.carta_id:
        publicada = s.get(Carta, propuesta.carta_id)
        if publicada is not None:
            return _carta_enriquecida(s, publicada)

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


def _veredicto_resumen(veredicto) -> Optional[dict]:
    """WS27 · B2.1 · la v2 del funnel, masticada para el front.

    El `veredicto` crudo se sigue mandando entero (Tomás tiene derecho a leer
    literalmente lo que dijo el juez), pero para DIBUJAR la columna del medio el
    front necesitaba entrar al JSON, adivinar qué claves existen y decidir qué es
    un `fix` vacío. Eso es lógica de producto viviendo en una pantalla: acá se
    resuelve una vez y viaja ya resuelto.

    Devuelve None cuando no hay nada que mostrar (una propuesta que el juez
    todavía no miró): así el front pregunta por un campo, no por cuatro.
    """
    if not isinstance(veredicto, dict) or not veredicto:
        return None
    resumen = {
        "resultado": _texto(veredicto.get("resultado")),
        "motivo": _texto(veredicto.get("motivo")),
        # El MISMO canon que ve el autor (B1.1): un retoque vacío es None, no un
        # objeto con las dos claves en null que el panel dibujaría en blanco.
        "fix": _fix_sugerido(veredicto.get("fix_sugerido")),
        # `juez` o `dwellia`: quién escribió la sugerencia que se está mirando.
        "fuente": _texto(veredicto.get("fuente")),
        # Cuántas reglas del canon marcó (el detalle está en el veredicto crudo).
        # Q/A B2.1: la columna es JSON y puede venir de un seed o de un fix a mano;
        # un valor que no sea lista no puede tumbar la bandeja entera.
        "hallazgos": (len(veredicto["hallazgos"]) if isinstance(veredicto.get("hallazgos"), list)
                      else (1 if isinstance(veredicto.get("hallazgos"), str)
                            and veredicto["hallazgos"].strip() else 0)),
    }
    if all(v in (None, 0) for v in resumen.values()):
        return None
    return resumen


def _item(s: Session, propuesta: CartaComunidad) -> dict:
    """Una fila de la bandeja. Lleva el `veredicto` CRUDO a propósito: Tomás tiene
    que poder leer literalmente lo que dijo el juez, no un resumen nuestro.

    WS27 · B2.1: y lleva el FUNNEL completo, que es lo que el panel dibuja en tres
    columnas — `historial` (v1: cada redacción del autor, con su versión y su
    fecha) · `veredicto`/`veredicto_resumen` (v2: lo que dijo el juez o Dwellia) ·
    `estado` + `motivo` + `carta_id` (vFinal: la decisión y, si se aprobó, la
    carta que salió al mazo).
    """
    autor = s.get(Usuario, propuesta.usuario_id)
    return {
        "id": propuesta.id,
        "estado": propuesta.estado,
        "firma": propuesta.firma,
        "motivo": propuesta.motivo,
        "concepto": propuesta.concepto,
        "veredicto": propuesta.veredicto,
        "veredicto_resumen": _veredicto_resumen(propuesta.veredicto),
        # v1 del funnel. Lista vacía (no None) si la propuesta es anterior a la
        # migración `l2a3b4c5d6e7`: el front itera, no pregunta si existe.
        "historial": ([v for v in propuesta.historial if isinstance(v, dict)]
                      if isinstance(propuesta.historial, list) else []),
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
    if estado == ESTADO_PENDIENTES:
        q = q.where(CartaComunidad.estado.in_(ESTADOS_PENDIENTES))
    elif estado != ESTADO_TODAS:
        q = q.where(CartaComunidad.estado == estado)
    # `id` como desempate: dos propuestas del mismo instante salen siempre en el
    # mismo orden (una lista que baila entre recargas no se puede revisar).
    q = q.order_by(CartaComunidad.created_at.desc(), CartaComunidad.id.desc())
    return [_item(s, p) for p in s.scalars(q).all()]


# ─────────────────────────────────────────────────────────────────────────────
# WS27 · B2.1 · El TABLERO (`GET /api/admin/resumen`)
#
# Decisión de Tomás (WS27 §6): el adminland NO muestra nada por usuario
# individual. Los números son del SISTEMA — cuántas cartas hay por pilar y de
# dónde vienen, cuántas propuestas esperan, cuánta gente hay y cuánta escribe —
# y sirven para una sola cosa: ver si un pilar quedó desparejo y escribir cartas
# de Dwellia para emparejarlo.
# ─────────────────────────────────────────────────────────────────────────────
def _orden_pilar(slug: str) -> int:
    """Índice en el reloj. Un pilar que no esté en la lista va al final, no revienta."""
    try:
        return ORDEN_PILARES.index(slug)
    except ValueError:
        return len(ORDEN_PILARES)


def _cartas_por_pilar(s: Session) -> list:
    """Los 6 pilares con su conteo, EN EL ORDEN DEL RELOJ y siempre los 6.

    Un pilar sin cartas aparece en cero: el tablero existe justamente para ver
    los huecos, y un pilar que desaparece de la lista es un hueco invisible.
    """
    filas = s.execute(
        select(Carta.categoria_slug, Carta.origen, func.count())
        .group_by(Carta.categoria_slug, Carta.origen)
    ).all()
    conteos: dict = {}
    for slug, origen, cuantas in filas:
        casilla = conteos.setdefault(slug, {ORIGEN_DWELLIA: 0, ORIGEN_COMUNIDAD: 0})
        casilla[origen] = casilla.get(origen, 0) + int(cuantas)

    pilares = s.scalars(select(Categoria)).all()
    salida = []
    for cat in sorted(pilares, key=lambda c: (_orden_pilar(c.slug), c.slug)):
        casilla = conteos.get(cat.slug, {})
        dwellia = int(casilla.get(ORIGEN_DWELLIA, 0))
        comunidad = int(casilla.get(ORIGEN_COMUNIDAD, 0))
        salida.append({
            "slug": cat.slug,
            "nombre": cat.nombre,
            "total": dwellia + comunidad,
            "dwellia": dwellia,
            "comunidad": comunidad,
        })
    return salida


def _resumen_cartas(s: Session) -> dict:
    """El mazo servible: cuántas cartas hay, de dónde vienen y cómo se reparten.

    Los totales se cuentan sobre TODA la tabla `cartas`, no sumando `por_pilar`:
    si mañana una carta apunta a un pilar borrado, el total sigue diciendo la
    verdad y el desajuste se ve, en vez de esconderse en una suma prolija.
    """
    total = int(s.scalar(select(func.count()).select_from(Carta)) or 0)
    dwellia = int(s.scalar(
        select(func.count()).select_from(Carta).where(Carta.origen == ORIGEN_DWELLIA)
    ) or 0)
    comunidad = int(s.scalar(
        select(func.count()).select_from(Carta).where(Carta.origen == ORIGEN_COMUNIDAD)
    ) or 0)
    return {
        "total": total,
        "dwellia": dwellia,
        "comunidad": comunidad,
        "por_pilar": _cartas_por_pilar(s),
    }


def _resumen_propuestas(s: Session) -> dict:
    """Las propuestas por estado. Los SEIS estados salen siempre, aunque sean 0."""
    filas = s.execute(
        select(CartaComunidad.estado, func.count()).group_by(CartaComunidad.estado)
    ).all()
    conteos = {estado: 0 for estado in ESTADOS_CARTA_COMUNIDAD}
    for estado, cuantas in filas:
        conteos[estado] = conteos.get(estado, 0) + int(cuantas)
    # Lo que espera una mirada: el mismo conjunto que el filtro `pendientes`.
    conteos[ESTADO_PENDIENTES] = sum(conteos.get(e, 0) for e in ESTADOS_PENDIENTES)
    return conteos


def _resumen_usuarios(s: Session) -> dict:
    """Cuánta gente hay, cuánta terminó el onboarding, cuánta paga y cuánta escribe.

    Premium se decide con `services/plan.es_premium` (plan == premium Y `plan_hasta`
    en el futuro), no con `plan == 'premium'` a mano: un premium vencido es free
    para la app y tiene que ser free también en el tablero. Por eso se recorren
    las filas en Python en vez de contarlas en SQL — el tablero de una cuenta no
    justifica duplicar la regla del plan en una consulta.
    """
    usuarios = s.scalars(select(Usuario)).all()
    total = len(usuarios)
    con_onboarding = sum(1 for u in usuarios if u.terminos_aceptados_at is not None)
    premium = sum(1 for u in usuarios if es_premium(u))

    autores = {
        uid for (uid,) in s.execute(
            select(CartaComunidad.usuario_id).distinct()
        ).all()
    }
    # Solo los autores que siguen existiendo: borrar la cuenta se lleva sus
    # propuestas en cascada, pero un id fantasma no puede inflar el conteo.
    crearon = sum(1 for u in usuarios if u.id in autores)

    return {
        "total": total,
        "con_onboarding": con_onboarding,
        "premium": premium,
        "free": total - premium,
        "crearon_cartas": crearon,
        "sin_cartas": total - crearon,
    }


def _resumen_comentarios(s: Session) -> dict:
    """El feedback privado de las cartas: cuánto hay y cuánto llegó esta semana."""
    base = select(func.count()).select_from(Entrega).where(
        Entrega.comentario_carta.is_not(None)
    )
    desde = _now() - timedelta(days=DIAS_RECIENTES)
    return {
        "total": int(s.scalar(base) or 0),
        "ultimos_7_dias": int(s.scalar(base.where(Entrega.fecha >= desde)) or 0),
    }


def resumen(s: Session) -> dict:
    """`GET /api/admin/resumen` · el tablero entero, de una sola lectura."""
    return {
        "cartas": _resumen_cartas(s),
        "propuestas": _resumen_propuestas(s),
        "usuarios": _resumen_usuarios(s),
        "comentarios": _resumen_comentarios(s),
    }


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


def _publicable(propuesta: CartaComunidad) -> tuple:
    """Los límites del CONTENIDO, revisados en el punto donde el texto se publica.

    Q/A B1.3 (BUG-B13-1): B1.1 los exige al proponer, pero una fila puede llegar
    a `cartas_comunidad` por otro camino (una migración, el demo-seed, un fix a
    mano en la base) y `aprobar` la copiaba al mazo sin mirarla. Los límites son
    del contenido, no del formulario: se miden acá también, sobre el texto ya
    strippeado, y con las MISMAS constantes de B1.1 (un solo lugar).

    Q/A B1.3 (BUG-B13-8): y la cesión de uso es el permiso legal para publicar lo
    que escribió otra persona. Sin ella no se publica: 409, no 422 — el contenido
    está bien, lo que falta es un paso del recorrido.
    """
    if propuesta.cesion_aceptada_at is None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Falta la cesión del autor: no se puede publicar esta carta.",
        )

    frase = (propuesta.frase or "").strip()
    prompt = (propuesta.prompt or "").strip()
    if not frase or len(frase) > FRASE_MAX:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"La frase de la carta no puede pasar de {FRASE_MAX} caracteres.",
        )
    if len(prompt) < PROMPT_MIN or len(prompt) > PROMPT_MAX:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"El prompt de la carta tiene que medir entre {PROMPT_MIN} y "
            f"{PROMPT_MAX} caracteres.",
        )
    return frase, prompt


def aprobar(
    s: Session, carta_comunidad_id: str, concepto: Optional[str] = None
) -> dict:
    """APROBAR = CARGAR AL MAZO. Publica la carta y avisa al autor."""
    propuesta = _propuesta(s, carta_comunidad_id, DESDE_APROBAR)
    frase, prompt = _publicable(propuesta)
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
        frase=frase,
        prompt=prompt,
        origen=ORIGEN_COMUNIDAD,
        autor_usuario_id=None if autor is None else autor.id,
        firma_publica=_firma_publica(propuesta, autor),
    )
    s.add(carta)
    s.flush()  # la FK `carta_id` necesita la fila ya escrita

    propuesta.estado = ESTADO_APROBADA
    propuesta.carta_id = carta.id
    propuesta.concepto = concepto_final
    # Q/A B1.3 (BUG-B13-9): aprobar CIERRA el recorrido. Si venía de un
    # `a_revisar` o de un rechazo del juez, el motivo viejo no puede quedar
    # pegado: el autor leería "Cargada a la comunidad" junto a un reproche.
    propuesta.motivo = None
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

    Q/A B1.3 (BUG-B13-5): el retoque pasa por `_fix_sugerido`, el mismo canon que
    usa B1.1, así que un `fix` vacío es None (nada) y no un objeto con las dos
    claves en null que el front dibujaría como una caja de sugerencia en blanco.

    Q/A B1.3 (BUG-B13-4): y `fix_sugerido` se escribe SOLO si Tomás mandó uno. Si
    manda nada más su comentario, la sugerencia que ya había redactado el juez se
    conserva — que es justo lo que promete "no borra evidencia".
    """
    propuesta = _propuesta(s, carta_comunidad_id, DESDE_A_REVISAR)
    autor = s.get(Usuario, propuesta.usuario_id)

    fix = _fix_sugerido(fix)

    propuesta.estado = ESTADO_A_REVISAR
    propuesta.motivo = sugerencia
    # Reasignación (no mutación) para que SQLAlchemy vea el cambio en la columna JSON.
    propuesta.veredicto = {
        **(propuesta.veredicto if isinstance(propuesta.veredicto, dict) else {}),
        **({"fix_sugerido": fix} if fix else {}),
        "fuente": "dwellia",
    }
    propuesta.updated_at = _now()
    s.add(propuesta)

    if autor is not None:
        avisar_estado_carta(s, autor, propuesta.id, ESTADO_A_REVISAR)
    s.commit()
    s.refresh(propuesta)
    return _item(s, propuesta)
