"""WS29 · C1.3 · Recomendaciones (premium).

Una recomendación es una ficha corta que alguien deja en su Baúl: un libro, un
video, un podcast, un documental u otra cosa que le hizo bien. Vive al lado de
las Pausas y con la MISMA visibilidad (`privada` o `compartida`), así que
aparece mezclada por fecha en el Baúl propio y, si está compartida, en la
vitrina que ven los demás.

Dos reglas que no se negocian:

1. **Escribir es premium, leer no.** Crear, editar, borrar y cambiar la
   visibilidad exigen premium vigente. Pero quien tuvo premium y se le venció
   sigue viendo lo suyo en el Baúl: nada de lo que alguien escribió desaparece
   porque dejó de pagar. Por eso `mias()` y `compartidas_de()` no miran el plan;
   el candado está en los endpoints, no en la lectura.

2. **Nunca más de `RECOMENDACIONES_MAX`.** El tope se cuenta con la fila del
   usuario bloqueada (`FOR UPDATE`), no con un `COUNT` suelto: dos pedidos a la
   vez no pueden dejar 31.

La forma de salida (`ItemRecomendacion`) la define `item_recomendacion` y la
usan las tres puertas: este router, `services/baul` y `services/fichas`.
"""

from __future__ import annotations

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db.models import (
    RECOMENDACION_TEXTO_MAX,
    RECOMENDACION_TITULO_MAX,
    RECOMENDACIONES_MAX,
    TIPOS_RECOMENDACION,
    VISIBILIDAD_COMPARTIDA,
    VISIBILIDAD_PRIVADA,
    VISIBILIDADES,
    Recomendacion,
    Usuario,
)
from .plan import limites

# La URL es `String(500)` en la tabla: el largo lo aplica el servicio, con mensaje.
URL_MAX = 500
URL_PREFIJO = "https://"

# ── Los mensajes, todos en español y todos acá ───────────────────────────────
SOLO_PREMIUM = "Las recomendaciones son de quienes son parte."
NO_ENCONTRADA = "No encontramos esta recomendación."
MSG_TOPE = f"Ya tienes {RECOMENDACIONES_MAX} recomendaciones, el máximo."
MSG_TITULO_FALTA = "Falta el título."
MSG_TITULO_LARGO = (
    f"El título no puede tener más de {RECOMENDACION_TITULO_MAX} caracteres."
)
MSG_TEXTO_FALTA = "Falta el texto."
MSG_TEXTO_LARGO = (
    f"El texto no puede tener más de {RECOMENDACION_TEXTO_MAX} caracteres."
)
MSG_TIPO = "El tipo tiene que ser uno de: " + ", ".join(TIPOS_RECOMENDACION) + "."
MSG_URL = f"El enlace debe empezar con {URL_PREFIJO}"
MSG_URL_LARGO = f"El enlace no puede tener más de {URL_MAX} caracteres."
MSG_VISIBILIDAD = "La visibilidad tiene que ser " + " o ".join(VISIBILIDADES) + "."


def _422(mensaje: str) -> HTTPException:
    return HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, mensaje)


# ═════════════════════════════════════════════════════════════════════════════
# LA FORMA DE SALIDA
# ═════════════════════════════════════════════════════════════════════════════

def item_recomendacion(rec: Recomendacion, de: Optional[dict] = None) -> dict:
    """`ItemRecomendacion` (contrato C0 §4.3).

    `de` es `persona_min(dueño)` cuando la recomendación es de otro (vitrina) y
    `None` cuando es mía (Baúl): la misma convención que `ItemBaul`.
    """
    return {
        "tipo": "recomendacion",
        "id": rec.id,
        "fecha": rec.created_at,
        "titulo": rec.titulo,
        "tipo_recomendacion": rec.tipo,
        "texto": rec.texto,
        "url": rec.url,
        "visibilidad": rec.visibilidad,
        "de": de,
    }


# ═════════════════════════════════════════════════════════════════════════════
# LECTURA (sin candado de plan: leer lo propio no es premium)
# ═════════════════════════════════════════════════════════════════════════════

def mias(s: Session, usuario_id: str) -> list:
    """Todas mis recomendaciones, de la más nueva a la más vieja."""
    return list(
        s.scalars(
            select(Recomendacion)
            .where(Recomendacion.usuario_id == usuario_id)
            .order_by(Recomendacion.created_at.desc())
        ).all()
    )


def compartidas_de(s: Session, usuario_id: str) -> list:
    """Las recomendaciones que alguien PUBLICÓ. Es lo único que sale a la vitrina,
    incluso cuando el que mira es el dueño (esa pantalla es "como me ven")."""
    return list(
        s.scalars(
            select(Recomendacion)
            .where(
                Recomendacion.usuario_id == usuario_id,
                Recomendacion.visibilidad == VISIBILIDAD_COMPARTIDA,
            )
            .order_by(Recomendacion.created_at.desc())
        ).all()
    )


# ═════════════════════════════════════════════════════════════════════════════
# VALIDACIÓN (el router pone el tope duro; la regla fina vive acá)
# ═════════════════════════════════════════════════════════════════════════════

def exigir_premium(usuario: Usuario) -> None:
    """El candado de escritura. Un premium vencido cae acá, pero sigue leyendo."""
    if not limites(usuario).recomendaciones:
        raise HTTPException(status.HTTP_403_FORBIDDEN, SOLO_PREMIUM)


def _obligatorio(valor, maximo: int, falta: str, largo: str) -> str:
    limpio = (valor or "").strip()
    if not limpio:
        raise _422(falta)
    if len(limpio) > maximo:
        raise _422(largo)
    return limpio


def limpiar_titulo(valor) -> str:
    return _obligatorio(valor, RECOMENDACION_TITULO_MAX, MSG_TITULO_FALTA, MSG_TITULO_LARGO)


def limpiar_texto(valor) -> str:
    return _obligatorio(valor, RECOMENDACION_TEXTO_MAX, MSG_TEXTO_FALTA, MSG_TEXTO_LARGO)


def limpiar_tipo(valor) -> str:
    tipo = (valor or "").strip()
    if tipo not in TIPOS_RECOMENDACION:
        raise _422(MSG_TIPO)
    return tipo


def limpiar_url(valor) -> Optional[str]:
    """Opcional: vacío (o solo espacios) es None. Si viene, tiene que ser https:
    un enlace que alguien abre desde la app no viaja en claro."""
    url = (valor or "").strip()
    if not url:
        return None
    # Q/A C1.3: el esquema no distingue mayúsculas (RFC 3986): "HTTPS://" vale.
    if not url.lower().startswith(URL_PREFIJO):
        raise _422(MSG_URL)
    if len(url) > URL_MAX:
        raise _422(MSG_URL_LARGO)
    return url


def limpiar_visibilidad(valor) -> str:
    vis = (valor or "").strip()
    if vis not in VISIBILIDADES:
        raise _422(MSG_VISIBILIDAD)
    return vis


# ═════════════════════════════════════════════════════════════════════════════
# ESCRITURA (todo premium)
# ═════════════════════════════════════════════════════════════════════════════

def _mia_o_404(s: Session, usuario: Usuario, recomendacion_id: str) -> Recomendacion:
    """La recomendación si es mía; si no, 404 — ajena e inexistente dan lo MISMO,
    igual que en el Baúl: un 403 delataría que existe."""
    rec = s.get(Recomendacion, recomendacion_id)
    if rec is None or rec.usuario_id != usuario.id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, NO_ENCONTRADA)
    return rec


def listar(s: Session, usuario: Usuario) -> list:
    """`GET /api/recomendaciones` — las mías, de la más nueva a la más vieja."""
    exigir_premium(usuario)
    return [item_recomendacion(r) for r in mias(s, usuario.id)]


def crear(
    s: Session,
    usuario: Usuario,
    titulo,
    tipo,
    texto,
    url=None,
    visibilidad=None,
) -> dict:
    exigir_premium(usuario)
    titulo = limpiar_titulo(titulo)
    tipo = limpiar_tipo(tipo)
    texto = limpiar_texto(texto)
    url = limpiar_url(url)
    visibilidad = (
        VISIBILIDAD_PRIVADA if visibilidad is None else limpiar_visibilidad(visibilidad)
    )

    # El tope se cuenta con MI fila bloqueada: dos POST simultáneos se ponen en
    # fila y el segundo cuenta lo que dejó el primero (un COUNT suelto dejaría 31).
    s.execute(select(Usuario.id).where(Usuario.id == usuario.id).with_for_update())
    cuantas = len(
        s.scalars(
            select(Recomendacion.id).where(Recomendacion.usuario_id == usuario.id)
        ).all()
    )
    if cuantas >= RECOMENDACIONES_MAX:
        s.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, MSG_TOPE)

    rec = Recomendacion(
        usuario_id=usuario.id,
        titulo=titulo,
        tipo=tipo,
        texto=texto,
        url=url,
        visibilidad=visibilidad,
    )
    s.add(rec)
    s.commit()
    s.refresh(rec)
    return item_recomendacion(rec)


def editar(
    s: Session,
    usuario: Usuario,
    recomendacion_id: str,
    titulo=None,
    tipo=None,
    texto=None,
    url=None,
    visibilidad=None,
) -> dict:
    """Edición PARCIAL: lo que no viene, no se toca.

    `url` es el único campo con dos "vacíos": `None` = no lo nombraste, `""` =
    quiero borrarlo. Así se puede sacar un enlace sin borrar la recomendación.
    """
    exigir_premium(usuario)
    rec = _mia_o_404(s, usuario, recomendacion_id)

    if titulo is not None:
        rec.titulo = limpiar_titulo(titulo)
    if tipo is not None:
        rec.tipo = limpiar_tipo(tipo)
    if texto is not None:
        rec.texto = limpiar_texto(texto)
    if url is not None:
        rec.url = limpiar_url(url)
    if visibilidad is not None:
        rec.visibilidad = limpiar_visibilidad(visibilidad)

    s.add(rec)
    s.commit()
    s.refresh(rec)
    return item_recomendacion(rec)


def borrar(s: Session, usuario: Usuario, recomendacion_id: str) -> None:
    exigir_premium(usuario)
    rec = _mia_o_404(s, usuario, recomendacion_id)
    s.delete(rec)
    s.commit()


def cambiar_visibilidad(
    s: Session, usuario: Usuario, recomendacion_id: str, visibilidad
) -> dict:
    """Publica la recomendación con la comunidad o la repliega. El dueño manda:
    al volverla privada desaparece de su vitrina para todos, al instante."""
    exigir_premium(usuario)
    vis = limpiar_visibilidad(visibilidad)
    rec = _mia_o_404(s, usuario, recomendacion_id)
    rec.visibilidad = vis
    s.add(rec)
    s.commit()
    s.refresh(rec)
    return item_recomendacion(rec)
