"""WS27 · B2.1 · Distribución de las cartas de la comunidad + impacto para el autor.

La decisión de Tomás (WS27 §6) es de una línea: **las cartas aprobadas se
reparten como iguales**. En su pilar, con las mismas reglas que las de Dwellia
(rotación 6+1 y las dos ventanas de 7 días), a todo el mundo, sin día especial,
sin tope, **sin interruptor** y **sin exclusiones** — el autor puede recibir la
suya ("reconocimiento propio"; si no la quiere, la cambia).

Eso, en el código, es una NO-feature: el pool de `entrega.py` ya es
`select(Carta)` entero y B1.3 publica la carta aprobada en `cartas`. Justamente
por eso hace falta el candado: nada en el motor dice "las de la comunidad
también", así que nada avisaría si mañana alguien filtrara el pool por `origen`.

**El escenario se CONSTRUYE, no se busca.** Que la carta esté en el pool no
prueba que el motor la sirva: el pool tiene 78 cartas y el sorteo es ponderado.
Se le arma al lector un historial que deja UNA sola salida posible —
(a) las seis últimas entregas cubren los cinco pilares que NO son el de la carta,
    así que la rotación 6+1 tiene que servir ese pilar;
(b) la entrega de hace 7 días carga en `descartadas` TODAS las cartas de Dwellia
    de ese pilar: entran a la ventana de "ya vistas" (7 días) pero quedan fuera
    de la ventana de rotación (6 días), así que no bloquean el pilar y sí bloquean
    las cartas.
Resultado: la única fresca del pilar es la de la comunidad. Si el motor la
excluyera, no habría carta que servir y el test caería con otra.

El impacto (`personas_acompanadas`) es el conteo de `entregas` de la carta
publicada: es lo que el autor ve en Crear, y es 0 mientras no esté aprobada.

Todo lo que este archivo escribe se borra al empezar Y al terminar cada test:
usuarios `b21|…` (que arrastran en cascada entregas y propuestas) y las cartas
publicadas `com-b21…`. El mazo tiene que volver siempre a 77.
"""

from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    ESTADO_APROBADA,
    FIRMA_APODO,
    ORIGEN_COMUNIDAD,
    ORIGEN_DWELLIA,
    Carta,
    CartaComunidad,
    Categoria,
    Entrega,
    Usuario,
)
from mindful_api.main import app

client = TestClient(app)

MARCA = "b21|"
PREFIJO_CARTA = "com-b21-"

AUTOR = MARCA + "autor"
LECTOR = MARCA + "lector"
OTRO = MARCA + "otro"

PILAR = "gratitud"
ACCION = "contemplar"
FRASE = "Lo que sostiene tu día casi nunca hace ruido."
PROMPT = (
    "Escribe en tu diario tres cosas que hoy te sostuvieron sin que las nombraras, "
    "y qué cambiaría si mañana le dieras las gracias en voz alta a una de ellas."
)


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


def _limpiar() -> None:
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(MARCA + "%")))
        s.execute(delete(Carta).where(Carta.id.like(PREFIJO_CARTA + "%")))
        s.commit()


@pytest.fixture(autouse=True)
def limpio():
    _limpiar()
    yield
    _limpiar()


def _usuario(sub: str, apodo=None) -> str:
    """Un usuario ya onboardeado (sin términos, `/api/carta-del-dia` responde 409)."""
    with SessionLocal() as s:
        u = Usuario(
            firebase_uid=sub, email=f"{sub}@mindful.local", apodo=apodo,
            terminos_aceptados_at=datetime.now(timezone.utc),
        )
        s.add(u)
        s.commit()
        return u.id


def _publicar(autor_id, firma_publica=None, concepto=None) -> str:
    """La carta de la comunidad YA en el mazo, como la deja `admin.aprobar`."""
    with SessionLocal() as s:
        carta = Carta(
            id=PREFIJO_CARTA + secrets.token_hex(4),
            categoria_slug=PILAR, accion_slug=ACCION,
            concepto=concepto or ("b21-" + secrets.token_hex(3)),
            frase=FRASE, prompt=PROMPT,
            origen=ORIGEN_COMUNIDAD,
            autor_usuario_id=autor_id,
            firma_publica=firma_publica,
        )
        s.add(carta)
        s.commit()
        return carta.id


def _forzar_el_pilar(usuario_id: str) -> None:
    """Le construye al usuario el ÚNICO historial que deja salir `PILAR` con una
    sola carta fresca: la de la comunidad (ver el docstring del módulo)."""
    with SessionLocal() as s:
        dwellia_del_pilar = [
            c.id for c in s.scalars(
                select(Carta).where(Carta.categoria_slug == PILAR,
                                    Carta.origen == ORIGEN_DWELLIA)
            ).all()
        ]
        otros = sorted({c for c in s.scalars(select(Categoria.slug)).all()} - {PILAR})
        ahora = datetime.now(timezone.utc)
        entregas = []
        for i, dia in enumerate(range(7, 0, -1)):
            cat = otros[i % len(otros)]
            carta_id = s.scalar(
                select(Carta.id).where(Carta.categoria_slug == cat).limit(1)
            )
            e = Entrega(usuario_id=usuario_id, carta_id=carta_id,
                        fecha=ahora - timedelta(days=dia))
            s.add(e)
            entregas.append(e)
        s.flush()
        # La de hace 7 días: dentro de la ventana de cartas vistas, fuera de la
        # ventana de rotación. Bloquea las cartas del pilar, no el pilar.
        entregas[0].descartadas = dwellia_del_pilar
        s.add(entregas[0])
        s.commit()


def _mazo() -> int:
    with SessionLocal() as s:
        return int(s.scalar(select(func.count()).select_from(Carta)) or 0)


# ═════════════════════════════════════════════════════════════════════════════
# 1 · La reparten como iguales
# ═════════════════════════════════════════════════════════════════════════════
def test_el_motor_sirve_la_carta_de_la_comunidad_a_cualquiera():
    """Un lector cualquiera, un día cualquiera: la carta de la comunidad llega.

    Sin interruptor de por medio (la columna `recibe_comunidad` ya no existe) y
    sin día comodín: es la carta del pilar que le tocaba hoy.
    """
    autor = _usuario(AUTOR, apodo="Ana")
    com_id = _publicar(autor, firma_publica="Ana")

    _usuario(LECTOR)
    _forzar_el_pilar(_id_de(LECTOR))

    r = client.get("/api/carta-del-dia", headers=_headers(LECTOR))
    assert r.status_code == 200
    carta = r.json()["carta"]
    assert carta["id"] == com_id, f"sirvió {carta['id']}, no la de la comunidad"
    assert carta["origen"] == ORIGEN_COMUNIDAD
    assert carta["firma_publica"] == "Ana"


def test_el_autor_recibe_su_propia_carta():
    """Sin exclusiones: el "reconocimiento propio" es una decisión, no un descuido.

    El mismo escenario, pero el lector ES el autor. Si el motor tuviera un
    `where autor_usuario_id != usuario` la carta no saldría y este test caería
    con otra distinta.
    """
    autor_id = _usuario(AUTOR, apodo="Ana")
    com_id = _publicar(autor_id, firma_publica="Ana")
    _forzar_el_pilar(autor_id)

    carta = client.get("/api/carta-del-dia", headers=_headers(AUTOR)).json()["carta"]
    assert carta["id"] == com_id, "el autor no recibió su propia carta"
    assert carta["firma_publica"] == "Ana"


def test_una_carta_anonima_llega_sin_firma():
    """Firma `anonima` ⇒ `firma_publica` None: el dorso dirá "alguien de la comunidad"."""
    autor = _usuario(AUTOR, apodo="Ana")
    com_id = _publicar(autor, firma_publica=None)

    _usuario(LECTOR)
    _forzar_el_pilar(_id_de(LECTOR))

    carta = client.get("/api/carta-del-dia", headers=_headers(LECTOR)).json()["carta"]
    assert carta["id"] == com_id
    assert carta["origen"] == ORIGEN_COMUNIDAD
    assert carta["firma_publica"] is None


def test_origen_y_firma_viajan_tambien_al_baul():
    """`_carta_enriquecida` es el ÚNICO punto que arma una carta: lo que ve Hoy lo
    tiene que ver el Baúl. Se vive la Pausa y se la busca en la lista."""
    autor = _usuario(AUTOR, apodo="Ana")
    com_id = _publicar(autor, firma_publica="Ana")

    _usuario(LECTOR)
    _forzar_el_pilar(_id_de(LECTOR))

    hoy = client.get("/api/carta-del-dia", headers=_headers(LECTOR)).json()
    assert hoy["carta"]["id"] == com_id
    cierre = client.put(
        f"/api/entregas/{hoy['entrega']['id']}/cierre",
        headers=_headers(LECTOR),
        json={"estrellas": 5, "reflexion": "Me llegó.", "completada": True},
    )
    assert cierre.status_code == 200
    assert cierre.json()["carta"]["firma_publica"] == "Ana"

    baul = client.get("/api/baul", headers=_headers(LECTOR)).json()
    fichas = [f for f in baul if f["carta"]["id"] == com_id]
    assert len(fichas) == 1, "la Pausa de la carta de la comunidad no está en el Baúl"
    assert fichas[0]["carta"]["origen"] == ORIGEN_COMUNIDAD
    assert fichas[0]["carta"]["firma_publica"] == "Ana"


def test_el_mazo_publico_cuenta_la_carta_de_la_comunidad():
    """El respaldo estructural: publicada ⇒ está en el pool que el motor sortea."""
    autor = _usuario(AUTOR)
    com_id = _publicar(autor)
    assert _mazo() == 78
    with SessionLocal() as s:
        assert com_id in {c.id for c in s.scalars(select(Carta)).all()}
    assert client.get("/api/contenido/resumen").json()["cartas"] == 78


# ═════════════════════════════════════════════════════════════════════════════
# 2 · El impacto que ve el autor
# ═════════════════════════════════════════════════════════════════════════════
def _propuesta_aprobada(autor_id: str, carta_id: str) -> str:
    with SessionLocal() as s:
        p = CartaComunidad(
            usuario_id=autor_id, categoria_slug=PILAR, accion_slug=ACCION,
            frase=FRASE, prompt=PROMPT, firma=FIRMA_APODO,
            estado=ESTADO_APROBADA, carta_id=carta_id,
            cesion_aceptada_at=datetime.now(timezone.utc),
        )
        s.add(p)
        s.commit()
        return p.id


def _entregar(usuario_id: str, carta_id: str, dias: int) -> None:
    with SessionLocal() as s:
        s.add(Entrega(usuario_id=usuario_id, carta_id=carta_id,
                      fecha=datetime.now(timezone.utc) - timedelta(days=dias)))
        s.commit()


def _entregar_con_estrellas(usuario_id: str, carta_id: str, estrellas, dias: int) -> None:
    with SessionLocal() as s:
        s.add(Entrega(usuario_id=usuario_id, carta_id=carta_id, estrellas=estrellas,
                      fecha=datetime.now(timezone.utc) - timedelta(days=dias)))
        s.commit()


def test_estrellas_promedio_de_la_carta_publicada():
    """WS28 · B2.2: dos puntúan (5 y 4), una recibe sin puntuar → 4.5 sobre 2 votos."""
    autor_id = _usuario(AUTOR, apodo="Ana")
    com_id = _publicar(autor_id, firma_publica="Ana")
    _propuesta_aprobada(autor_id, com_id)

    _entregar_con_estrellas(_usuario(LECTOR), com_id, 5, dias=3)
    _entregar_con_estrellas(_usuario(OTRO), com_id, 4, dias=2)
    _entregar(autor_id, com_id, dias=1)                 # sin estrellas: no cuenta

    mia = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR)).json()[0]
    assert mia["estrellas_promedio"] == 4.5
    assert mia["veces_puntuada"] == 2
    assert mia["personas_acompanadas"] == 3


def test_sin_estrellas_el_promedio_es_none_no_cero():
    """Publicada y recibida, pero nadie puntuó: None (el front no dibuja 0,0)."""
    autor_id = _usuario(AUTOR, apodo="Ana")
    com_id = _publicar(autor_id, firma_publica="Ana")
    _propuesta_aprobada(autor_id, com_id)
    _entregar(_usuario(LECTOR), com_id, dias=1)

    mia = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR)).json()[0]
    assert mia["estrellas_promedio"] is None
    assert mia["veces_puntuada"] == 0


def _id_de(sub: str) -> str:
    with SessionLocal() as s:
        return s.scalar(select(Usuario.id).where(Usuario.firebase_uid == sub))


def test_personas_acompanadas_cuenta_las_entregas_de_la_carta():
    """Publicar → que le llegue a dos personas → el autor ve 2."""
    autor_id = _usuario(AUTOR, apodo="Ana")
    com_id = _publicar(autor_id, firma_publica="Ana")
    _propuesta_aprobada(autor_id, com_id)

    lector = _usuario(LECTOR)
    otro = _usuario(OTRO)
    _entregar(lector, com_id, dias=3)
    _entregar(otro, com_id, dias=1)

    mias = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR)).json()
    assert len(mias) == 1
    assert mias[0]["personas_acompanadas"] == 2


def test_una_propuesta_sin_publicar_acompana_a_cero():
    """Mientras no esté aprobada no hay carta publicada: el autor ve un 0 honesto,
    y las entregas de OTRAS cartas no se le suman."""
    autor_id = _usuario(AUTOR)
    with SessionLocal() as s:
        p = CartaComunidad(
            usuario_id=autor_id, categoria_slug=PILAR, accion_slug=ACCION,
            frase=FRASE, prompt=PROMPT,
            cesion_aceptada_at=datetime.now(timezone.utc),
        )
        s.add(p)
        s.commit()

    lector = _usuario(LECTOR)
    with SessionLocal() as s:
        ajena = s.scalar(select(Carta.id).where(Carta.origen == ORIGEN_DWELLIA).limit(1))
    _entregar(lector, ajena, dias=2)

    mias = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR)).json()
    assert mias[0]["carta_id"] is None
    assert mias[0]["personas_acompanadas"] == 0


def test_el_impacto_es_de_esa_carta_y_no_del_mazo():
    """Dos cartas publicadas del mismo autor: cada una cuenta LO SUYO."""
    autor_id = _usuario(AUTOR, apodo="Ana")
    una = _publicar(autor_id, firma_publica="Ana")
    otra = _publicar(autor_id, firma_publica="Ana")
    _propuesta_aprobada(autor_id, una)
    _propuesta_aprobada(autor_id, otra)

    lector = _usuario(LECTOR)
    tercero = _usuario(OTRO)
    _entregar(lector, una, dias=5)
    _entregar(tercero, una, dias=4)
    _entregar(lector, otra, dias=3)

    mias = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR)).json()
    por_carta = {m["carta_id"]: m["personas_acompanadas"] for m in mias}
    assert por_carta == {una: 2, otra: 1}


def test_zz_el_mazo_queda_en_77():
    """Último del módulo: el Q/A no deja cartas colgadas en el Mundo 1."""
    assert _mazo() == 77
