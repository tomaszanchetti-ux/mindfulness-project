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

from datetime import datetime, timezone
from typing import Callable, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
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


def _ahora() -> datetime:
    return datetime.now(timezone.utc)


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
    categoria = (categoria or "").strip()
    accion = (accion or "").strip()
    frase = (frase or "").strip()
    prompt = (prompt or "").strip()

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

    Se arma una `Carta` en memoria (transitoria: nunca se agrega a la sesión ni se
    flushea) y se la pasa por `_carta_enriquecida`, el único punto que arma una
    carta en todo el backend. Si mañana la carta suma un campo, esto lo hereda.
    """
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


def _salida(s: Session, propuesta: CartaComunidad, usuario: Usuario) -> dict:
    veredicto = propuesta.veredicto or {}
    return {
        "id": propuesta.id,
        "estado": propuesta.estado,
        "firma": propuesta.firma,
        "motivo": propuesta.motivo,
        # La sugerencia concreta del juez (frase/prompt reescritos), si la hubo.
        "sugerencia": veredicto.get("fix_sugerido"),
        "concepto": propuesta.concepto,
        "carta_id": propuesta.carta_id,
        # B2.1 lo calcula (cuánta gente recibió la carta). Hasta entonces, 0.
        "personas_acompanadas": 0,
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
    return (elegido.get("detalle") or elegido.get("regla") or "").strip() or None


def _fix_sugerido(fix) -> Optional[dict]:
    """Forma canónica de la sugerencia: `{"frase","prompt"}` o nada."""
    if not isinstance(fix, dict):
        return None
    frase = (fix.get("frase") or "").strip() or None
    prompt = (fix.get("prompt") or "").strip() or None
    if frase is None and prompt is None:
        return None
    return {"frase": frase, "prompt": prompt}


def _veredicto_json(resultado: str, hallazgos=None, concepto=None,
                    fix_sugerido=None, motivo=None) -> dict:
    """La forma canónica de la columna `veredicto` (la comparte B1.3)."""
    return {
        "resultado": resultado,
        "hallazgos": list(hallazgos or []),
        "concepto": concepto,
        "fix_sugerido": fix_sugerido,
        "motivo": motivo,
        "fuente": FUENTE_JUEZ,
    }


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
    resultado = getattr(veredicto, "resultado", None) or RESULTADO_OFF
    estado = ESTADO_POR_RESULTADO.get(resultado, ESTADO_REVISION_DWELLIA)

    hallazgos = getattr(veredicto, "hallazgos", None) or []
    concepto = (getattr(veredicto, "concepto", None) or "").strip() or None
    fix = _fix_sugerido(getattr(veredicto, "fix", None))

    # El texto que ve el autor. Si el juez no redactó uno, se arma con el primer
    # hallazgo mayor. En los estados sin motivo (revision_dwellia) no se muestra nada.
    motivo = None
    if estado in ESTADOS_CON_MOTIVO:
        motivo = (getattr(veredicto, "motivo", None) or "").strip() or None
        if motivo is None:
            motivo = _linea_de_hallazgos(hallazgos)

    return estado, motivo, concepto, _veredicto_json(
        resultado, hallazgos=hallazgos, concepto=concepto,
        fix_sugerido=fix, motivo=motivo,
    )


def procesar_juez(carta_comunidad_id: str, evaluar: Optional[Callable] = None) -> None:
    """Corre el juez sobre UNA propuesta y guarda su recorrido. NUNCA levanta.

    Abre su propia sesión: corre en `BackgroundTasks`, o sea DESPUÉS de que la
    sesión de la request se cerró. Si la propuesta ya no está `en_revision`
    (el autor la retiró mientras tanto), no toca nada.

    `evaluar` se resuelve en tiempo de llamada contra el módulo `services.juez`
    (no se importa la función): así B1.2 puede llenarlo y los tests pueden
    reemplazarlo sin que este archivo se entere.
    """
    s = SessionLocal()
    try:
        propuesta = s.get(CartaComunidad, carta_comunidad_id)
        if propuesta is None or propuesta.estado != ESTADO_EN_REVISION:
            return

        # Lo que ya había: al reenviar se conserva el veredicto de la vuelta anterior.
        anterior = (propuesta.veredicto or {}).get("anterior")

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
            s.rollback()
            propuesta = s.get(CartaComunidad, carta_comunidad_id)
            if propuesta is None or propuesta.estado != ESTADO_EN_REVISION:
                return
            estado, motivo, concepto = ESTADO_REVISION_DWELLIA, None, None
            veredicto_json = _veredicto_json(RESULTADO_OFF, motivo=MOTIVO_JUEZ_CAIDO)

        if anterior is not None:
            veredicto_json["anterior"] = anterior

        propuesta.estado = estado
        propuesta.motivo = motivo
        if concepto:
            propuesta.concepto = concepto
        propuesta.veredicto = veredicto_json   # columna JSON: siempre un dict NUEVO
        s.add(propuesta)

        usuario = s.get(Usuario, propuesta.usuario_id)
        if usuario is not None:
            # `revision_dwellia` no avisa: para el autor sigue "en evaluación".
            avisar_estado_carta(s, usuario, propuesta.id, estado)
        s.commit()
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
    """
    propuesta = _mia_o_404(s, usuario, carta_comunidad_id)
    if propuesta.estado != ESTADO_A_REVISAR:
        raise HTTPException(
            status.HTTP_409_CONFLICT,
            "Solo puedes reenviar una carta que necesita un retoque.",
        )

    campos = _validar_contenido(
        s, usuario,
        datos.categoria if datos.categoria is not None else propuesta.categoria_slug,
        datos.accion if datos.accion is not None else propuesta.accion_slug,
        datos.frase, datos.prompt,
        datos.firma if datos.firma is not None else propuesta.firma,
    )

    for campo, valor in campos.items():
        setattr(propuesta, campo, valor)
    propuesta.estado = ESTADO_EN_REVISION
    propuesta.motivo = None                       # la sugerencia vieja ya no aplica
    anterior = propuesta.veredicto
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
