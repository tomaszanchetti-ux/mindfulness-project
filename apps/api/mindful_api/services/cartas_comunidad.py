"""WS27 · B1.1 · Cartas de la comunidad: proponer, ver las mías, reenviar, retirar.

La feature insignia del premium (Roadmap v2 §0/§4). Un usuario premium escribe UNA
carta por vez; el juez la mira apenas se envía (en background, nunca bloquea la
respuesta) y la deja lista para Tomás, o se la devuelve al autor con una sugerencia,
o la rechaza. Publicar la carta aprobada en el mazo es de B1.3 (administración).

Los LÍMITES del contenido viven acá y en ningún otro lado (`FRASE_MAX`,
`PROMPT_MIN`, `PROMPT_MAX`): el borde Pydantic solo pone un tope duro anti-abuso,
porque un 422 que hable de "5000 caracteres" no le sirve a nadie. Se miden sobre
el texto ya strippeado, o sea sobre los caracteres útiles.

Recorrido (el vocabulario cerrado está en `db/models.py`):

    en_revision ──juez── aprueba ──────────→ revision_dwellia  (le toca a Tomás)
                       ├ requiere_revision → a_revisar         (vuelve al autor)
                       ├ rechaza ──────────→ rechazada
                       └ off / error ──────→ revision_dwellia
    a_revisar ──PUT──→ en_revision (y el juez otra vez)
    cualquiera en curso ──DELETE──→ retirada
"""

from __future__ import annotations

import json
import re
import unicodedata
from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ..db.base import SessionLocal
from ..db.models import (
    ESTADO_A_REVISAR,
    ESTADO_EN_REVISION,
    ESTADO_RECHAZADA,
    ESTADO_REVISION_DWELLIA,
    ESTADO_RETIRADA,
    ESTADOS_EN_CURSO,
    FIRMA_APODO,
    ORIGEN_COMUNIDAD,
    Accion,
    Carta,
    CartaComunidad,
    Categoria,
    Entrega,
    Usuario,
)
from . import juez as juez_mod
from .avisos import avisar_estado_carta
from .entrega import _carta_enriquecida
from .plan import limites

# ── Los límites del contenido · UN SOLO LUGAR (Roadmap v2 §0) ────────────────
FRASE_MAX = 60          # la frase del frente
PROMPT_MIN = 100        # el prompt del dorso: ni telegrama…
PROMPT_MAX = 220        # …ni ensayo

# Lo que el juez puede decir (contrato de `services/juez.py`).
RESULTADO_APRUEBA = "aprueba"
RESULTADO_REQUIERE_REVISION = "requiere_revision"
RESULTADO_RECHAZA = "rechaza"
RESULTADO_OFF = "off"

# `resultado` del juez → estado de la propuesta. Todo lo que no sea un veredicto
# conocido (incluido `off` = juez apagado o caído) va a la mesa de Tomás: nunca se
# rechaza una carta por un problema nuestro.
ESTADO_POR_RESULTADO = {
    RESULTADO_APRUEBA: ESTADO_REVISION_DWELLIA,   # Tomás siempre aprueba a mano
    RESULTADO_REQUIERE_REVISION: ESTADO_A_REVISAR,
    RESULTADO_RECHAZA: ESTADO_RECHAZADA,
    RESULTADO_OFF: ESTADO_REVISION_DWELLIA,
}
# Estados que le muestran un texto al autor. En los otros, `motivo` se limpia.
ESTADOS_CON_MOTIVO = (ESTADO_A_REVISAR, ESTADO_RECHAZADA)

FUENTE_JUEZ = "juez"
MOTIVO_JUEZ_CAIDO = "El juez no pudo evaluar la carta."

# La columna `cartas_comunidad.concepto` es `varchar(80)`: lo que no entra, no
# se guarda — y un concepto largo no puede costarle la carta al autor.
CONCEPTO_MAX = 80


# WS27 · B2.1 · quién escribió esa vuelta del historial. Hoy solo hay una fuente
# (el autor); la clave existe porque el funnel del adminland tiene tres columnas y
# mañana Dwellia podría reescribir una carta a mano en la vFinal.
HISTORIAL_AUTOR = "usuario"


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


# ─────────────────────────────────────────────────────────────────────────────
# El historial de redacciones (WS27 · B2.1)
#
# `cartas_comunidad` guardaba la evaluación (`veredicto`, con una sola vuelta
# `anterior`) y la decisión final (`estado`/`motivo`/`carta_id`), pero el TEXTO se
# pisaba en cada reenvío: Tomás abría el panel y no podía saber de dónde venía la
# carta que estaba mirando. `historial` conserva CADA redacción del autor — v1 al
# enviarla, v(n+1) en cada reenvío — y es la primera columna del funnel.
#
# Se REASIGNA la lista entera, nunca se hace `.append()`: `historial` es una
# columna JSON y SQLAlchemy no ve las mutaciones en su lugar (la fila se guardaría
# sin el cambio, en silencio).
# ─────────────────────────────────────────────────────────────────────────────
def _redaccion(propuesta: CartaComunidad, version: int,
               por: str = HISTORIAL_AUTOR) -> dict:
    """La foto de la carta TAL COMO ESTÁ, con su número de vuelta y su fecha UTC."""
    return {
        "version": version,
        "frase": propuesta.frase,
        "prompt": propuesta.prompt,
        "categoria": propuesta.categoria_slug,
        "accion": propuesta.accion_slug,
        "firma": propuesta.firma,
        "fecha": _ahora().isoformat(),
        "por": por,
    }


def _sumar_redaccion(propuesta: CartaComunidad, por: str = HISTORIAL_AUTOR) -> None:
    """Agrega la redacción actual como la vuelta siguiente. NO hace commit.

    El número de vuelta sale del MÁXIMO que ya haya guardado, no del largo de la
    lista: si una fila vieja (o una sembrada a mano) trae el historial incompleto,
    la v2 no vuelve a llamarse v1.
    """
    previas = list(propuesta.historial or [])
    versiones = [
        p.get("version") for p in previas
        if isinstance(p, dict) and isinstance(p.get("version"), int)
    ]
    version = (max(versiones) if versiones else len(previas)) + 1
    propuesta.historial = previas + [_redaccion(propuesta, version, por)]


# ─────────────────────────────────────────────────────────────────────────────
# La limpieza del texto · UN SOLO LUGAR
#
# `strip()` no alcanza. Lo que se guarda tiene que ser exactamente lo que se lee:
#
#   · los caracteres INVISIBLES (categorías Unicode `Cf` = formato y `Cc` =
#     control) pasan cualquier `strip()`. Una frase de veinte espacios de ancho
#     cero se guardaba "llena" y se dibujaba en blanco, y un `\x00` —que Postgres
#     no acepta en un `text`— tumbaba el INSERT con un 500 de cara al usuario;
#   · los saltos de línea, los tabs y los espacios repetidos se colapsan a UN
#     espacio: el frente y el dorso de una carta se renderizan en un componente
#     que no previó saltos, y el largo se mide sobre los caracteres que se ven.
# ─────────────────────────────────────────────────────────────────────────────
_SEPARAN_PALABRAS = "\t\n\r\v\f"     # controles que sí valen como un espacio
_INVISIBLES = ("Cf", "Cc")


def _limpiar_texto(valor) -> str:
    """El texto útil: sin caracteres invisibles y con los espacios colapsados."""
    if not isinstance(valor, str):
        return ""
    visible = "".join(
        ch for ch in valor
        if ch in _SEPARAN_PALABRAS or unicodedata.category(ch) not in _INVISIBLES
    )
    return " ".join(visible.split())


def _texto(valor) -> Optional[str]:
    """Un texto opcional que viene de afuera (el juez, el panel): str o nada.

    El veredicto lo escribe un modelo: `motivo` puede llegar como número, dict o
    None. Se lo lleva a str antes de tocarlo, así un `.strip()` sobre algo que no
    era texto no se lleva puesta la transición."""
    if valor is None:
        return None
    if not isinstance(valor, str):
        valor = str(valor)
    return valor.strip() or None


# ─────────────────────────────────────────────────────────────────────────────
# Validación del contenido (la misma para proponer y para reenviar)
# ─────────────────────────────────────────────────────────────────────────────
def _error(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, mensaje)


def _validar_contenido(
    s: Session, usuario: Usuario, categoria: str, accion: str,
    frase: str, prompt: str, firma: str,
) -> dict:
    """Devuelve los campos ya limpios, o levanta un 422 que el autor entiende."""
    categoria = _limpiar_texto(categoria)
    accion = _limpiar_texto(accion)
    frase = _limpiar_texto(frase)
    prompt = _limpiar_texto(prompt)

    if s.get(Categoria, categoria) is None:
        raise _error("Elige uno de los pilares de Dwellia.")
    if s.get(Accion, accion) is None:
        raise _error("Elige una de las acciones iniciales de Dwellia.")

    if not frase:
        raise _error("La frase no puede quedar vacía.")
    if len(frase) > FRASE_MAX:
        raise _error(f"La frase no puede pasar de {FRASE_MAX} caracteres.")

    if len(prompt) < PROMPT_MIN or len(prompt) > PROMPT_MAX:
        raise _error(
            f"El prompt tiene que medir entre {PROMPT_MIN} y {PROMPT_MAX} caracteres."
        )

    # Firmar con apodo exige tener uno: lo que se publica en el dorso sale de
    # `usuarios.apodo`, no de un texto suelto de la propuesta.
    if firma == FIRMA_APODO and not (usuario.apodo or "").strip():
        raise _error("Para firmar con tu apodo, primero elige uno en tu perfil.")

    return {
        "categoria_slug": categoria, "accion_slug": accion,
        "frase": frase, "prompt": prompt, "firma": firma,
    }


# ─────────────────────────────────────────────────────────────────────────────
# Salida (lo que ve el autor en la pestaña Crear)
# ─────────────────────────────────────────────────────────────────────────────
def _firma_publica(propuesta: CartaComunidad, usuario: Usuario) -> Optional[str]:
    """Lo que vería el resto en el dorso: el apodo, o nada (= alguien de la comunidad)."""
    if propuesta.firma == FIRMA_APODO:
        return (usuario.apodo or "").strip() or None
    return None


def _carta_de_la_propuesta(s: Session, propuesta: CartaComunidad, usuario: Usuario) -> dict:
    """La propuesta con la forma EXACTA de una carta del mazo, para que el front la
    dibuje con el mismo componente sin saber que todavía no está publicada.

    Si la carta YA se publicó (B1.3 la aprobó y `carta_id` apunta al mazo), se
    sirve LA carta publicada: su id es el del mazo y su firma quedó fija el día
    que salió. Si no, se arma una `Carta` en memoria (transitoria: nunca se
    agrega a la sesión ni se flushea) y se la pasa por `_carta_enriquecida`, el
    único punto que arma una carta en todo el backend. Si mañana la carta suma un
    campo, esto lo hereda.
    """
    if propuesta.carta_id:
        publicada = s.get(Carta, propuesta.carta_id)
        if publicada is not None:
            return _carta_enriquecida(s, publicada)

    carta = Carta(
        id=propuesta.id,   # la propuesta todavía no tiene id de carta: se usa el suyo
        categoria_slug=propuesta.categoria_slug,
        accion_slug=propuesta.accion_slug,
        concepto=propuesta.concepto,
        frase=propuesta.frase,
        prompt=propuesta.prompt,
        origen=ORIGEN_COMUNIDAD,
        autor_usuario_id=usuario.id,
        firma_publica=_firma_publica(propuesta, usuario),
    )
    return _carta_enriquecida(s, carta)


def personas_acompanadas(s: Session, propuesta: CartaComunidad) -> int:
    """WS27 · B2.1 · el IMPACTO: a cuánta gente le llegó esta carta.

    Es el conteo de `entregas` de la carta PUBLICADA — o sea, cuántas veces el
    motor la eligió como carta del día de alguien. Mientras la propuesta no esté
    aprobada no hay carta publicada y el impacto es 0, no "todavía no se sabe":
    el autor ve un cero honesto.

    Se cuentan PERSONAS distintas (Q/A B2.1): la ventana del motor dura 7 días,
    así que la misma persona puede volver a recibir la carta más adelante, y el
    rótulo del front dice "N personas la recibieron", no "N veces".
    """
    if not propuesta.carta_id:
        return 0
    total = s.scalar(
        select(func.count(func.distinct(Entrega.usuario_id)))
        .where(Entrega.carta_id == propuesta.carta_id)
    )
    return int(total or 0)


def _salida(s: Session, propuesta: CartaComunidad, usuario: Usuario) -> dict:
    veredicto = propuesta.veredicto or {}
    return {
        "id": propuesta.id,
        "estado": propuesta.estado,
        "firma": propuesta.firma,
        "motivo": propuesta.motivo,
        # La sugerencia concreta (frase/prompt reescritos), si la hubo. Pasa por
        # `_fix_sugerido` SIEMPRE: el panel de B1.3 puede guardar un retoque vacío
        # (`{}` → `{"frase": None, "prompt": None}`) y el autor no tiene por qué
        # ver un cuadro de sugerencia dibujado en blanco.
        "sugerencia": _fix_sugerido(veredicto.get("fix_sugerido")),
        "concepto": propuesta.concepto,
        "carta_id": propuesta.carta_id,
        # B2.1 · cuánta gente recibió la carta (0 mientras no esté publicada).
        "personas_acompanadas": personas_acompanadas(s, propuesta),
        "created_at": propuesta.created_at,
        "updated_at": propuesta.updated_at,
        "carta": _carta_de_la_propuesta(s, propuesta, usuario),
    }


# ─────────────────────────────────────────────────────────────────────────────
# El juez, en background (nunca bloquea la respuesta, nunca levanta)
# ─────────────────────────────────────────────────────────────────────────────
def _linea_de_hallazgos(hallazgos) -> Optional[str]:
    """Una línea legible para el autor: el primer hallazgo mayor, o el primero."""
    if not hallazgos:
        return None
    mayores = [h for h in hallazgos if isinstance(h, dict) and h.get("mayor")]
    elegido = (mayores or [h for h in hallazgos if isinstance(h, dict)] or [None])[0]
    if not elegido:
        return None
    return _texto(elegido.get("detalle")) or _texto(elegido.get("regla"))


def _fix_sugerido(fix) -> Optional[dict]:
    """Forma canónica de la sugerencia: `{"frase","prompt"}` o nada."""
    if not isinstance(fix, dict):
        return None
    frase = _texto(fix.get("frase"))
    prompt = _texto(fix.get("prompt"))
    if frase is None and prompt is None:
        return None
    return {"frase": frase, "prompt": prompt}


# ── Blindaje de lo que escribe el juez ───────────────────────────────────────
_NO_KEBAB = re.compile(r"[^a-z0-9-]+")
_GUIONES = re.compile(r"-{2,}")


def _concepto_canonico(valor) -> Optional[str]:
    """El `concepto` en kebab-case y del largo que entra en la columna.

    El juez es un modelo: puede devolver "Aire de la mañana", 240 caracteres o
    nada. `concepto` es una ETIQUETA (la usa el dedupe semanal de M2), no un
    texto, y la columna mide 80: un concepto largo reventaba el commit entero y
    dejaba la carta clavada en `en_revision`, sin aviso y ocupando el único lugar
    del autor. Acá se normaliza y se recorta; la evidencia cruda de lo que dijo
    el juez queda igual en `veredicto`.
    """
    texto = _limpiar_texto(valor).lower()
    # "mañana" → "manana": se descompone el acento y se tira la marca.
    texto = "".join(
        ch for ch in unicodedata.normalize("NFKD", texto)
        if unicodedata.category(ch) != "Mn"
    )
    texto = _GUIONES.sub("-", _NO_KEBAB.sub("-", texto)).strip("-")
    return texto[:CONCEPTO_MAX].strip("-") or None


def _json_seguro(valor):
    """Lo mismo, pero garantizado guardable en una columna JSON.

    Si el juez devuelve algo que `json` no sabe serializar, antes reventaba el
    commit y la propuesta se quedaba en `en_revision` para siempre. `default=str`
    lo baja a su representación: preferimos un hallazgo feo a una carta clavada.
    """
    try:
        return json.loads(json.dumps(valor, default=str))
    except Exception:  # noqa: BLE001 — ni así: se guarda su repr y se sigue
        return json.loads(json.dumps(repr(valor)))


def _veredicto_json(resultado: str, hallazgos=None, concepto=None,
                    fix_sugerido=None, motivo=None, detalle=None) -> dict:
    """La forma canónica de la columna `veredicto` (la comparte B1.3)."""
    veredicto = {
        "resultado": resultado,
        "hallazgos": _json_seguro(list(hallazgos or [])),
        "concepto": concepto,
        "fix_sugerido": fix_sugerido,
        "motivo": motivo,
        "fuente": FUENTE_JUEZ,
    }
    # La evidencia cruda del juez: el informe de la capa 1, la respuesta del
    # modelo y el consumo de tokens. B1.3 le promete a Tomás "literalmente lo que
    # dijo el juez", así que se guarda. Solo se escribe la clave si hay algo (un
    # veredicto sin detalle no estrena una clave vacía).
    if detalle:
        veredicto["detalle"] = _json_seguro(detalle)
    return veredicto


def _contexto_del_mazo(s: Session) -> tuple:
    """Lo que el juez necesita saber del mundo: el mazo vigente y el vocabulario."""
    mazo = [
        {"id": c.id, "categoria": c.categoria_slug, "accion": c.accion_slug,
         "concepto": c.concepto, "frase": c.frase, "prompt": c.prompt}
        for c in s.scalars(select(Carta)).all()
    ]
    categorias = {c.slug for c in s.scalars(select(Categoria)).all()}
    acciones = {a.slug for a in s.scalars(select(Accion)).all()}
    return mazo, categorias, acciones


def _leer_veredicto(veredicto) -> tuple:
    """`Veredicto` (dataclass de `services/juez.py`) → (estado, motivo, concepto, json)."""
    resultado = _texto(getattr(veredicto, "resultado", None)) or RESULTADO_OFF
    estado = ESTADO_POR_RESULTADO.get(resultado, ESTADO_REVISION_DWELLIA)

    hallazgos = getattr(veredicto, "hallazgos", None) or []
    if not isinstance(hallazgos, list):
        hallazgos = [hallazgos]
    hallazgos = _json_seguro(hallazgos)     # antes de leerlos: ya guardables
    concepto = _concepto_canonico(getattr(veredicto, "concepto", None))
    fix = _fix_sugerido(getattr(veredicto, "fix", None))

    # El texto que ve el autor. Si el juez no redactó uno, se arma con el primer
    # hallazgo mayor. En los estados sin motivo (revision_dwellia) no se muestra nada.
    motivo = None
    if estado in ESTADOS_CON_MOTIVO:
        motivo = _texto(getattr(veredicto, "motivo", None))
        if motivo is None:
            motivo = _linea_de_hallazgos(hallazgos)

    return estado, motivo, concepto, _veredicto_json(
        resultado, hallazgos=hallazgos, concepto=concepto,
        fix_sugerido=fix, motivo=motivo,
        detalle=getattr(veredicto, "detalle", None),
    )


def _releer_en_revision(s: Session, carta_comunidad_id: str) -> Optional[CartaComunidad]:
    """La fila de AHORA, bloqueada, y solo si sigue esperando al juez.

    Entre que el modelo empieza a pensar y termina pasan segundos, y en esos
    segundos la carta puede haberse decidido: Tomás la aprobó desde el panel (y
    ya está publicada en el mazo), o el autor la retiró y escribió otra. El
    estado que se leyó al arrancar quedó VIEJO, así que antes de escribir una
    sola letra se vuelve a mirar la fila con `FOR UPDATE`. Si ya no está
    `en_revision`, el juez llegó tarde y no opina: ni estado, ni motivo, ni aviso.
    """
    # Cierra la transacción de lectura (la del contexto del mazo): lo que sigue
    # tiene que ver el mundo de ahora, no el de hace un rato.
    s.rollback()
    return s.scalars(
        select(CartaComunidad)
        .where(CartaComunidad.id == carta_comunidad_id)
        .where(CartaComunidad.estado == ESTADO_EN_REVISION)
        .with_for_update()
        .execution_options(populate_existing=True)
    ).first()


def _avisar_al_autor(s: Session, usuario_id: str, carta_comunidad_id: str,
                     estado: str) -> None:
    """El aviso al autor, DESPUÉS de la transición y con su propia red de contención.

    `revision_dwellia` no avisa (para el autor sigue "en evaluación"). Y si el
    canal de notificación falla, falla solo: el recorrido de una carta no se
    revierte porque un push devolvió basura.
    """
    try:
        usuario = s.get(Usuario, usuario_id)
        if usuario is not None:
            avisar_estado_carta(s, usuario, carta_comunidad_id, estado)
            s.commit()
    except Exception as exc:  # noqa: BLE001 — el aviso nunca se lleva la transición
        print(f"[juez:aviso] carta_comunidad={carta_comunidad_id}: {exc!r}", flush=True)
        try:
            s.rollback()
        except Exception:  # noqa: BLE001
            pass


def procesar_juez(carta_comunidad_id: str, evaluar: Optional[Callable] = None) -> None:
    """Corre el juez sobre UNA propuesta y guarda su recorrido. NUNCA levanta.

    Abre su propia sesión: corre en `BackgroundTasks`, o sea DESPUÉS de que la
    sesión de la request se cerró. Si la propuesta ya no está `en_revision`
    (el autor la retiró, o Tomás la decidió mientras el modelo pensaba), no toca
    nada: el estado se relee con `FOR UPDATE` justo antes de escribir.

    `evaluar` se resuelve en tiempo de llamada contra el módulo `services.juez`
    (no se importa la función): así B1.2 puede llenarlo y los tests pueden
    reemplazarlo sin que este archivo se entere.
    """
    s = SessionLocal()
    try:
        propuesta = s.get(CartaComunidad, carta_comunidad_id)
        if propuesta is None or propuesta.estado != ESTADO_EN_REVISION:
            return

        try:
            propuesta_dict = {
                "categoria": propuesta.categoria_slug,
                "accion": propuesta.accion_slug,
                "frase": propuesta.frase,
                "prompt": propuesta.prompt,
            }
            mazo, categorias, acciones = _contexto_del_mazo(s)
            fn = evaluar if evaluar is not None else juez_mod.evaluar
            veredicto = fn(propuesta_dict, mazo, categorias, acciones)
            estado, motivo, concepto, veredicto_json = _leer_veredicto(veredicto)
        except Exception as exc:  # noqa: BLE001 — un juez caído no bloquea a nadie
            print(f"[juez:error] carta_comunidad={carta_comunidad_id}: {exc!r}", flush=True)
            estado, motivo, concepto = ESTADO_REVISION_DWELLIA, None, None
            veredicto_json = _veredicto_json(RESULTADO_OFF, motivo=MOTIVO_JUEZ_CAIDO)

        # La decisión se escribe sobre la fila de AHORA, no sobre la que se leyó
        # antes de pensar.
        propuesta = _releer_en_revision(s, carta_comunidad_id)
        if propuesta is None:
            s.commit()          # suelta la transacción sin escribir nada
            return

        # Al reenviar se conserva el veredicto de la vuelta anterior (uno solo).
        anterior = (propuesta.veredicto or {}).get("anterior")
        if anterior is not None:
            veredicto_json["anterior"] = anterior

        usuario_id = propuesta.usuario_id
        propuesta.estado = estado
        propuesta.motivo = motivo
        if concepto:
            propuesta.concepto = concepto
        propuesta.veredicto = veredicto_json   # columna JSON: siempre un dict NUEVO
        s.add(propuesta)
        s.commit()              # la transición ya está guardada, pase lo que pase

        _avisar_al_autor(s, usuario_id, carta_comunidad_id, estado)
    except Exception as exc:  # noqa: BLE001 — el background NUNCA levanta
        print(f"[juez:fatal] carta_comunidad={carta_comunidad_id}: {exc!r}", flush=True)
        try:
            s.rollback()
        except Exception:  # noqa: BLE001
            pass
    finally:
        s.close()


# ─────────────────────────────────────────────────────────────────────────────
# Los cuatro movimientos del autor
# ─────────────────────────────────────────────────────────────────────────────
def _en_curso(s: Session, usuario: Usuario) -> Optional[CartaComunidad]:
    return s.scalars(
        select(CartaComunidad)
        .where(CartaComunidad.usuario_id == usuario.id)
        .where(CartaComunidad.estado.in_(ESTADOS_EN_CURSO))
        .limit(1)
    ).first()


def _mia_o_404(s: Session, usuario: Usuario, carta_comunidad_id: str) -> CartaComunidad:
    """404 si no existe O es de otro: la API no revela la existencia de lo ajeno."""
    propuesta = s.get(CartaComunidad, carta_comunidad_id)
    if propuesta is None or propuesta.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Carta no encontrada")
    return propuesta


def crear_propuesta(s: Session, usuario: Usuario, datos, tareas=None) -> dict:
    """`POST /api/cartas-comunidad` · premium, una por vez, cesión obligatoria."""
    if not limites(usuario).propone_cartas:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Escribir cartas para la comunidad es parte de Dwellia premium",
        )

    if not datos.cesion_aceptada:
        raise _error(
            "Para publicar tu carta en Dwellia hace falta aceptar la cesión de uso."
        )

    campos = _validar_contenido(
        s, usuario, datos.categoria, datos.accion,
        datos.frase, datos.prompt, datos.firma,
    )

    # Una carta en curso a la vez. La fila del usuario se lee CON BLOQUEO: sin el
    # lock, dos POST simultáneos leen "no hay ninguna" antes de que el otro
    # commitee y las dos entran. Se suelta al commit.
    s.get(Usuario, usuario.id, with_for_update=True)
    if _en_curso(s, usuario) is not None:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Ya tienes una carta en curso. Puedes retirarla para escribir otra.",
        )

    propuesta = CartaComunidad(
        usuario_id=usuario.id,
        estado=ESTADO_EN_REVISION,
        cesion_aceptada_at=_ahora(),
        **campos,
    )
    # La v1 del funnel: lo que el autor escribió, guardado antes de que nadie
    # (el juez, Dwellia) lo toque.
    _sumar_redaccion(propuesta)
    s.add(propuesta)
    s.commit()
    s.refresh(propuesta)

    # El juez corre DESPUÉS de responder: el autor no espera a la API de Anthropic.
    if tareas is not None:
        tareas.add_task(procesar_juez, propuesta.id)
    return _salida(s, propuesta, usuario)


def listar_mias(s: Session, usuario: Usuario) -> list:
    """`GET /api/cartas-comunidad/mias` · las mías, la más nueva primero."""
    filas = s.scalars(
        select(CartaComunidad)
        .where(CartaComunidad.usuario_id == usuario.id)
        .order_by(CartaComunidad.created_at.desc(), CartaComunidad.id.desc())
    ).all()
    return [_salida(s, p, usuario) for p in filas]


def reenviar_propuesta(s: Session, usuario: Usuario, carta_comunidad_id: str,
                       datos, tareas=None) -> dict:
    """`PUT /api/cartas-comunidad/{id}` · el autor corrige y la manda de nuevo.

    Solo desde `a_revisar`: es la única vuelta que el recorrido le da al autor.
    La cesión no se vuelve a pedir (ya la aceptó al proponerla).

    Pide plan igual que proponer: cada reenvío es OTRA corrida del juez, o sea
    otra llamada paga, y `a_revisar → PUT → a_revisar` no tiene techo. Retirar,
    en cambio, sigue abierto sin plan: nadie queda atrapado en su propia carta.
    """
    if not limites(usuario).propone_cartas:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN,
            "Escribir cartas para la comunidad es parte de Dwellia premium",
        )

    propuesta = _mia_o_404(s, usuario, carta_comunidad_id)
    if propuesta.estado != ESTADO_A_REVISAR:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo puedes reenviar una carta que necesita un retoque.",
        )

    # El reenvío manda la carta ENTERA: lo que no llega no se conserva, se pide.
    # (Pilar, acción y firma sí son opcionales: lo que no se manda, no se toca.)
    if datos.frase is None:
        raise _error("Falta la frase de la carta.")
    if datos.prompt is None:
        raise _error("Falta el prompt de la carta.")

    campos = _validar_contenido(
        s, usuario,
        datos.categoria if datos.categoria is not None else propuesta.categoria_slug,
        datos.accion if datos.accion is not None else propuesta.accion_slug,
        datos.frase, datos.prompt,
        datos.firma if datos.firma is not None else propuesta.firma,
    )

    for campo, valor in campos.items():
        setattr(propuesta, campo, valor)
    # La vuelta siguiente del funnel (v2, v3…): el texto nuevo se suma DESPUÉS de
    # escribirlo en la fila, así la foto es la carta tal como se reenvía. La
    # redacción anterior queda guardada, ya no se pisa.
    _sumar_redaccion(propuesta)
    propuesta.estado = ESTADO_EN_REVISION
    propuesta.motivo = None                       # la sugerencia vieja ya no aplica
    # Se guarda SOLO la vuelta inmediatamente anterior, podada de su propio
    # `anterior`: si no, cada reenvío anida el histórico entero adentro de la
    # columna JSON y nadie lo poda nunca. Lo que hace falta leer es "qué decía
    # antes de este retoque", no las N vueltas.
    anterior = propuesta.veredicto or None
    if anterior:
        anterior = {k: v for k, v in anterior.items() if k != "anterior"}
    propuesta.veredicto = {"anterior": anterior} if anterior else None

    s.add(propuesta)
    s.commit()
    s.refresh(propuesta)

    if tareas is not None:
        tareas.add_task(procesar_juez, propuesta.id)
    return _salida(s, propuesta, usuario)


def retirar_propuesta(s: Session, usuario: Usuario, carta_comunidad_id: str) -> None:
    """`DELETE /api/cartas-comunidad/{id}` · el autor la baja y queda libre para otra.

    No se borra la fila: queda `retirada` en su historial (y la carta ya publicada
    de una aprobada no se toca desde acá).
    """
    propuesta = _mia_o_404(s, usuario, carta_comunidad_id)
    if propuesta.estado not in ESTADOS_EN_CURSO:
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Esta carta ya no se puede retirar."
        )
    propuesta.estado = ESTADO_RETIRADA
    propuesta.motivo = None
    s.add(propuesta)
    s.commit()
