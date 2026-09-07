"""WS29 · C0 · el contrato del Bloque C en pie.

Lo que se prueba acá es lo que NINGUNA card del bloque puede reescribir:
la regla de lectura (`services/comunidad.puede_ver`), el perfil privado por
defecto, el vínculo único por par y la ficha extra que no es la carta del día
(su columna: el gancho del motor lo prueba C1.2).
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select
from sqlalchemy.exc import IntegrityError

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    VINCULO_ACEPTADA,
    VINCULO_PENDIENTE,
    Carta,
    Entrega,
    Guardada,
    Reenvio,
    Usuario,
    Vinculo,
)
from mindful_api.main import app
from mindful_api.services.comunidad import (
    entrega_visible,
    puede_ver,
    puede_ver_perfil,
    son_comunidad,
    vinculo_entre,
)
from mindful_api.services.plan import LIMITES_FREE, LIMITES_PREMIUM

client = TestClient(app)
PREFIJO = "c0|"


def _h(sub: str) -> dict:
    return {"X-Debug-Sub": PREFIJO + sub, "X-Debug-Email": f"{sub}@c0.local"}


def _usuario(s, sub: str, **campos) -> Usuario:
    u = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + sub))
    if u is None:
        u = Usuario(firebase_uid=PREFIJO + sub, email=f"{sub}@c0.local", apodo=sub.title())
        s.add(u)
    for k, v in campos.items():
        setattr(u, k, v)
    s.commit()
    s.refresh(u)
    return u


def _pausa(s, duenio: Usuario, visibilidad="compartida", completada=True) -> Entrega:
    carta_id = s.scalar(select(Carta.id).order_by(Carta.id).limit(1))
    e = Entrega(usuario_id=duenio.id, carta_id=carta_id, completada=completada,
                visibilidad=visibilidad, reflexion="c0")
    s.add(e)
    s.commit()
    s.refresh(e)
    return e


@pytest.fixture(autouse=True)
def _limpio():
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()
    yield


# ── Perfil ───────────────────────────────────────────────────────────────────

def test_perfil_privado_por_defecto_y_se_puede_abrir():
    r = client.get("/api/perfil", headers=_h("ana"))
    assert r.status_code == 200
    p = r.json()
    assert p["perfil_publico"] is False
    assert p["usuario_id"]  # el id con el que otros me encuentran
    assert p["limites"]["pausas_extra"] is False  # free

    r = client.put("/api/perfil", headers=_h("ana"), json={"perfil_publico": True})
    assert r.status_code == 200 and r.json()["perfil_publico"] is True
    # Un PUT que no lo nombra, no lo toca.
    r = client.put("/api/perfil", headers=_h("ana"), json={"apodo": "Anita"})
    assert r.json()["perfil_publico"] is True and r.json()["apodo"] == "Anita"


def test_pausas_extra_es_premium():
    assert LIMITES_FREE.pausas_extra is False
    assert LIMITES_PREMIUM.pausas_extra is True


# ── La regla de lectura ──────────────────────────────────────────────────────

def test_puede_ver_en_todos_sus_casos():
    with SessionLocal() as s:
        duenio = _usuario(s, "duenio")
        otro = _usuario(s, "otro")
        compartida = _pausa(s, duenio, "compartida")
        privada = _pausa(s, duenio, "privada")
        sin_vivir = _pausa(s, duenio, "compartida", completada=False)

        # 1. El dueño ve lo suyo, diga lo que diga la visibilidad.
        assert puede_ver(s, duenio, privada) and puede_ver(s, duenio, compartida)
        # 2. Un extraño, con el dueño privado: nada.
        assert not puede_ver(s, otro, compartida)
        assert not puede_ver(s, otro, privada)
        # 3. Dueño público: se ve lo compartido, NUNCA lo privado ni lo no vivido.
        duenio.perfil_publico = True
        s.commit()
        assert puede_ver(s, otro, compartida)
        assert not puede_ver(s, otro, privada)
        assert not puede_ver(s, otro, sin_vivir)
        # 4. Dueño vuelve a privado: se cierra.
        duenio.perfil_publico = False
        s.commit()
        assert not puede_ver(s, otro, compartida)
        # 5. Solicitud pendiente: todavía no.
        v = Vinculo(solicitante_id=otro.id, destinatario_id=duenio.id, estado=VINCULO_PENDIENTE)
        s.add(v)
        s.commit()
        assert not puede_ver(s, otro, compartida)
        assert not son_comunidad(s, otro.id, duenio.id)
        # 6. Aceptada: sí, en cualquier dirección.
        v.estado = VINCULO_ACEPTADA
        s.commit()
        assert son_comunidad(s, duenio.id, otro.id) and son_comunidad(s, otro.id, duenio.id)
        assert puede_ver(s, otro, compartida)
        assert not puede_ver(s, otro, privada)
        assert puede_ver_perfil(s, otro, duenio)
        # 7. El dueño la vuelve privada: el vínculo no alcanza (el dueño manda).
        compartida.visibilidad = "privada"
        s.commit()
        assert not puede_ver(s, otro, compartida)
        compartida.visibilidad = "compartida"
        s.commit()
        # 8. Sin vínculo pero con reenvío: se ve ESA ficha, no el perfil.
        s.delete(v)
        s.commit()
        assert not puede_ver(s, otro, compartida)
        tercero = _usuario(s, "tercero")
        s.add(Reenvio(de_usuario_id=tercero.id, a_usuario_id=otro.id, entrega_id=compartida.id))
        s.commit()
        assert puede_ver(s, otro, compartida)
        assert not puede_ver_perfil(s, otro, duenio)
        # 9. entrega_visible: un solo None para "no existe" y "no puedo".
        assert entrega_visible(s, otro, compartida.id) is not None
        assert entrega_visible(s, otro, privada.id) is None
        assert entrega_visible(s, otro, "no-existe") is None


# ── Lo que la base garantiza sola ────────────────────────────────────────────

def test_vinculo_unico_por_par_sin_direccion_y_nunca_consigo_mismo():
    with SessionLocal() as s:
        a = _usuario(s, "a")
        b = _usuario(s, "b")
        s.add(Vinculo(solicitante_id=a.id, destinatario_id=b.id))
        s.commit()
        assert vinculo_entre(s, b.id, a.id) is not None  # se encuentra al revés
        s.add(Vinculo(solicitante_id=b.id, destinatario_id=a.id))
        with pytest.raises(IntegrityError):
            s.commit()
        s.rollback()
        s.add(Vinculo(solicitante_id=a.id, destinatario_id=a.id))
        with pytest.raises(IntegrityError):
            s.commit()
        s.rollback()


def test_guardada_unica_por_par_y_muere_con_la_entrega():
    with SessionLocal() as s:
        duenio = _usuario(s, "duenio2")
        otro = _usuario(s, "otro2")
        e = _pausa(s, duenio)
        s.add(Guardada(usuario_id=otro.id, entrega_id=e.id))
        s.commit()
        s.add(Guardada(usuario_id=otro.id, entrega_id=e.id))
        with pytest.raises(IntegrityError):
            s.commit()
        s.rollback()
        s.delete(s.get(Entrega, e.id))
        s.commit()
        assert s.scalar(select(Guardada).where(Guardada.entrega_id == e.id)) is None


def test_entrega_extra_nace_como_no_diaria_y_recuerda_de_quien_vino():
    with SessionLocal() as s:
        duenio = _usuario(s, "duenio3")
        yo = _usuario(s, "yo3")
        origen = _pausa(s, duenio)
        e = Entrega(usuario_id=yo.id, carta_id=origen.carta_id, extra=True,
                    de_usuario_id=duenio.id)
        s.add(e)
        s.commit()
        s.refresh(e)
        assert e.extra is True and e.de_usuario_id == duenio.id
        normal = _pausa(s, yo)
        assert normal.extra is False and normal.de_usuario_id is None
