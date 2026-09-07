"""Q/A ADVERSARIAL de la card C1.2 (WS29) · Fichas ajenas, descubrir, reenviar,
guardar y hacer la Pausa.

No repite lo que ya prueba `tests/test_c12_fichas.py` (fotos por la regla, la
forma de la ficha, descubrir/vitrina básicos, guardar/quitar, la extra y la
programada). Acá se ataca: cambios en caliente (vínculo removido), fotos
cruzadas entre entregas del mismo dueño, la cadena de reenvíos, el 500 cuando
el dueño borra, las operaciones de dueño sobre una guardada, y el costo en
queries de "descubrir".

  `test_ok_*`   → candado que aguanta. Documenta el comportamiento correcto.
  `test_bug_*`  → falla de verdad (sin xfail): el test afirma el contrato y hoy
                  el código no lo cumple. Docstring: contrato · qué hace el
                  código · archivo:línea.

Prefijo de aislamiento: `qa12c|` (el `qa12|` ya lo usa otro bloque de Q/A).
"""

from __future__ import annotations

import struct
import zlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, event, select

from mindful_api.db.base import SessionLocal, engine
from mindful_api.db.models import (
    Carta,
    Entrega,
    Guardada,
    Reenvio,
    Usuario,
    Vinculo,
    VINCULO_ACEPTADA,
    VINCULO_PENDIENTE,
)
from mindful_api.main import app

client = TestClient(app)
PREFIJO = "qa12c|"


# ── Herramientas (copiadas de test_c12_fichas.py, no importadas) ────────────

def png_plano(ancho: int = 4, alto: int = 4, rgb: tuple = (180, 200, 190)) -> bytes:
    fila = b"\x00" + bytes(rgb) * ancho
    crudo = fila * alto

    def _chunk(tipo: bytes, datos: bytes) -> bytes:
        return (
            struct.pack(">I", len(datos))
            + tipo
            + datos
            + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(crudo, 9))
        + _chunk(b"IEND", b"")
    )


def _h(sub: str) -> dict:
    return {"X-Debug-Sub": PREFIJO + sub, "X-Debug-Email": f"{sub}@qa12c.local"}


def _usuario(s, sub: str, premium: bool = False, **campos) -> Usuario:
    u = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + sub))
    if u is None:
        u = Usuario(firebase_uid=PREFIJO + sub, email=f"{sub}@qa12c.local", apodo=sub.title())
        s.add(u)
    u.terminos_aceptados_at = datetime.now(timezone.utc)
    if premium:
        u.plan = "premium"
        u.plan_hasta = datetime.now(timezone.utc) + timedelta(days=30)
    for k, v in campos.items():
        setattr(u, k, v)
    s.commit()
    s.refresh(u)
    return u


def _cartas(s, cuantas: int = 1) -> list:
    return list(s.scalars(select(Carta.id).order_by(Carta.id).limit(cuantas)).all())


def _pausa(s, duenio, visibilidad="compartida", completada=True, extra=False,
           fecha=None, reflexion="una pausa", carta_id=None) -> Entrega:
    e = Entrega(
        usuario_id=duenio.id,
        carta_id=carta_id or _cartas(s)[0],
        completada=completada,
        visibilidad=visibilidad,
        extra=extra,
        reflexion=reflexion,
    )
    if fecha is not None:
        e.fecha = fecha
    s.add(e)
    s.commit()
    s.refresh(e)
    return e


def _vinculo(s, a, b, estado=VINCULO_ACEPTADA) -> Vinculo:
    v = Vinculo(solicitante_id=a.id, destinatario_id=b.id, estado=estado)
    s.add(v)
    s.commit()
    return v


def _subir_foto(sub: str, entrega_id: str) -> str:
    r = client.post(
        f"/api/entregas/{entrega_id}/fotos",
        headers=_h(sub),
        files={"foto": ("p.png", png_plano(), "image/png")},
    )
    assert r.status_code == 201, r.text
    return r.json()["id"]


@pytest.fixture(autouse=True)
def _limpio():
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()
    yield


# ── 1 · Nada privado viaja, en ninguna puerta ────────────────────────────────

def test_ok_ninguna_puerta_ajena_lleva_campos_privados():
    """Barrido con json.dumps sobre TODAS las respuestas de lectura ajena:
    ni estrellas, ni comentario_carta, ni descartadas, ni cambios, ni
    storage_path, ni el email del dueño."""
    import json

    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        amigo = _usuario(s, "amigo")
        _vinculo(s, yo, amigo)
        ficha = _pausa(s, duenio, reflexion="privado?")
        ficha.estrellas = 5
        ficha.comentario_carta = "comentario secreto"
        ficha.cambios = 2
        ficha.descartadas = ["algo"]
        s.commit()
        ficha_amigo = _pausa(s, amigo)
        ficha_id, ficha_amigo_id, duenio_id, amigo_id = (
            ficha.id, ficha_amigo.id, duenio.id, amigo.id
        )

    _subir_foto("duenio", ficha_id)
    client.post(f"/api/guardadas/{ficha_id}", headers=_h("yo"))

    # Claves que NO pueden aparecer del todo en una FichaAjena (descubrir, de/id,
    # la ficha directa): ni la clave existe.
    claves_prohibidas = ("estrellas", "visibilidad", "comentario_carta", "cambios", "descartadas")
    # Valores que jamás pueden viajar en ninguna respuesta (aparezca la clave o
    # no): el contenido real de lo privado.
    valores_prohibidos = ("comentario secreto", "storage_path", "duenio@qa12c.local")

    fichas_ajenas = [
        client.get("/api/fichas/descubrir", headers=_h("yo")),
        client.get(f"/api/fichas/de/{duenio_id}", headers=_h("yo")),
        client.get(f"/api/fichas/{ficha_id}", headers=_h("yo")),
        client.get(f"/api/fichas/de/{amigo_id}", headers=_h("yo")),
    ]
    for r in fichas_ajenas:
        assert r.status_code == 200, r.text
        crudo = json.dumps(r.json())
        for clave in claves_prohibidas:
            assert clave not in crudo, f"{clave!r} viajó en {r.request.url}"

    # `/api/baul` SÍ trae la clave `estrellas` (siempre, para toda la lista
    # homogénea), pero para una ficha guardada tiene que ser SIEMPRE null.
    baul = client.get("/api/baul", headers=_h("yo")).json()
    guardada = next(i for i in baul if i["id"] == ficha_id)
    assert guardada["estrellas"] is None
    assert "comentario_carta" not in guardada and "cambios" not in guardada

    for r in fichas_ajenas + [client.get("/api/baul", headers=_h("yo"))]:
        crudo = json.dumps(r.json())
        for valor in valores_prohibidos:
            assert valor not in crudo, f"{valor!r} viajó en {r.request.url}"


# ── 2 · Cambios en caliente ───────────────────────────────────────────────────

def test_ok_quitar_el_vinculo_saca_la_guardada_del_baul():
    """Guardé una ficha PRIVADA de alguien con quien tengo vínculo aceptado. El
    dueño me quita de su comunidad (borra el vínculo, sin tocar la visibilidad):
    la ficha deja de ser `puede_ver` y tiene que desaparecer de mi Baúl, sin 500."""
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio")  # privado (default), solo por vínculo
        _vinculo(s, yo, duenio)
        ficha = _pausa(s, duenio)
        ficha_id, yo_id, duenio_id = ficha.id, yo.id, duenio.id

    r = client.post(f"/api/guardadas/{ficha_id}", headers=_h("yo"))
    assert r.status_code == 201
    assert ficha_id in [i["id"] for i in client.get("/api/baul", headers=_h("yo")).json()]

    with SessionLocal() as s:
        s.execute(
            delete(Vinculo).where(
                Vinculo.solicitante_id == yo_id, Vinculo.destinatario_id == duenio_id
            )
        )
        s.commit()

    r = client.get("/api/baul", headers=_h("yo"))
    assert r.status_code == 200
    assert ficha_id not in [i["id"] for i in r.json()]
    # Y la ficha directa también se cierra.
    assert client.get(f"/api/fichas/{ficha_id}", headers=_h("yo")).status_code == 404


def test_ok_guardar_ficha_y_que_el_dueno_la_borre_no_rompe_el_baul():
    """El dueño borra la entrega REAL (`DELETE /api/baul/{id}`, no solo la
    repliega). Mi guardada apunta a una fila que ya no existe: el Baúl tiene que
    seguir dando 200 sin ella, nunca 500."""
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        ficha = _pausa(s, duenio)
        ficha_id = ficha.id

    assert client.post(f"/api/guardadas/{ficha_id}", headers=_h("yo")).status_code == 201
    assert ficha_id in [i["id"] for i in client.get("/api/baul", headers=_h("yo")).json()]

    assert client.delete(f"/api/baul/{ficha_id}", headers=_h("duenio")).status_code == 204

    r = client.get("/api/baul", headers=_h("yo"))
    assert r.status_code == 200
    assert ficha_id not in [i["id"] for i in r.json()]
    with SessionLocal() as s:
        # La cascada tiene que haberse llevado la fila `guardadas` (o al menos
        # no debe quedar huérfana rompiendo nada): lo que importa es el 200 de
        # arriba, esto es diagnóstico extra.
        restante = s.scalar(select(Guardada.id).where(Guardada.entrega_id == ficha_id))
        assert restante is None, "la cascade no limpió `guardadas`: la FK debería tener ondelete=CASCADE"


# ── 3 · Una guardada no es mía para operarla ─────────────────────────────────

def test_ok_una_guardada_no_se_opera_como_propia():
    """Guardar una ficha ajena da lectura, nunca escritura: cerrar, cambiar
    visibilidad, borrar, subir foto o compartir esa entrega tienen que dar 404
    para quien la guardó (no es su dueño)."""
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        ficha = _pausa(s, duenio)
        ficha_id = ficha.id

    assert client.post(f"/api/guardadas/{ficha_id}", headers=_h("yo")).status_code == 201

    h = _h("yo")
    assert client.put(f"/api/entregas/{ficha_id}/cierre", headers=h,
                      json={"estrellas": 5}).status_code == 404
    assert client.put(f"/api/baul/{ficha_id}/visibilidad", headers=h,
                      json={"visibilidad": "privada"}).status_code == 404
    assert client.post(f"/api/entregas/{ficha_id}/fotos", headers=h,
                       files={"foto": ("p.png", png_plano(), "image/png")}).status_code == 404
    assert client.post("/api/compartir", headers=h,
                       json={"entrega_id": ficha_id, "modo": "ejercicio"}).status_code == 404
    assert client.delete(f"/api/baul/{ficha_id}", headers=h).status_code == 404

    # Y la ficha del dueño sigue intacta.
    r = client.get(f"/api/fichas/{ficha_id}", headers=_h("yo"))
    assert r.status_code == 200 and r.json()["reflexion"] == "una pausa"


def test_ok_orden_valoradas_manda_las_guardadas_al_fondo():
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        mia_baja = _pausa(s, yo, reflexion="mia baja")
        mia_baja.estrellas = 1
        mia_alta = _pausa(s, yo, reflexion="mia alta")
        mia_alta.estrellas = 5
        ajena = _pausa(s, duenio, reflexion="ajena")
        s.commit()
        ids = (mia_baja.id, mia_alta.id, ajena.id)

    client.post(f"/api/guardadas/{ids[2]}", headers=_h("yo"))
    r = client.get("/api/baul?orden=valoradas", headers=_h("yo"))
    assert r.status_code == 200
    orden = [i["id"] for i in r.json()]
    # Las dos mías, con estrellas, van antes que la guardada (estrellas=None).
    assert orden.index(ids[0]) < orden.index(ids[2])
    assert orden.index(ids[1]) < orden.index(ids[2])
    # Y entre las mías, la de más estrellas primero.
    assert orden.index(ids[1]) < orden.index(ids[0])


# ── 4 · Fotos cruzadas ────────────────────────────────────────────────────────

def test_ok_foto_de_entrega_privada_del_mismo_dueno_bajo_entrega_compartida_404():
    """El dueño tiene dos entregas: una compartida (visible para mí) y una
    privada. La foto de la privada, pedida bajo el entrega_id de la compartida,
    tiene que dar 404 (las fotos no se cruzan entre entregas del mismo dueño)."""
    with SessionLocal() as s:
        _usuario(s, "yo")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        compartida = _pausa(s, duenio, visibilidad="compartida")
        privada = _pausa(s, duenio, visibilidad="privada")
        compartida_id, privada_id = compartida.id, privada.id

    foto_privada = _subir_foto("duenio", privada_id)
    r = client.get(f"/api/fichas/{compartida_id}/fotos/{foto_privada}", headers=_h("yo"))
    assert r.status_code == 404


def test_ok_foto_de_otro_dueno_bajo_entrega_id_visible_404():
    """Dos dueños distintos, ambos públicos. La foto del dueño B pedida con el
    entrega_id del dueño A (visible) tiene que dar 404: `foto.entrega_id` no
    coincide con la entrega del path."""
    with SessionLocal() as s:
        _usuario(s, "yo")
        a = _usuario(s, "duenio_a", perfil_publico=True)
        b = _usuario(s, "duenio_b", perfil_publico=True)
        ficha_a = _pausa(s, a)
        ficha_b = _pausa(s, b)
        ficha_a_id, ficha_b_id = ficha_a.id, ficha_b.id

    foto_b = _subir_foto("duenio_b", ficha_b_id)
    r = client.get(f"/api/fichas/{ficha_a_id}/fotos/{foto_b}", headers=_h("yo"))
    assert r.status_code == 404


def test_ok_la_foto_de_un_reenvio_sirve_al_receptor_y_no_a_tercero():
    with SessionLocal() as s:
        duenio = _usuario(s, "duenio")  # privado: solo se ve por reenvío
        yo = _usuario(s, "yo")
        receptor = _usuario(s, "receptor")
        _usuario(s, "tercero")
        _vinculo(s, duenio, yo)
        _vinculo(s, yo, receptor)
        ficha = _pausa(s, duenio)
        ficha_id, receptor_id = ficha.id, receptor.id

    foto_id = _subir_foto("duenio", ficha_id)
    r = client.post("/api/reenvios", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "a_usuario_id": receptor_id})
    assert r.status_code == 201

    r = client.get(f"/api/fichas/{ficha_id}/fotos/{foto_id}", headers=_h("receptor"))
    assert r.status_code == 200

    r = client.get(f"/api/fichas/{ficha_id}/fotos/{foto_id}", headers=_h("tercero"))
    assert r.status_code == 404


# ── 5 · Reenvíos ──────────────────────────────────────────────────────────────

def test_ok_reenviar_una_ficha_vista_solo_por_reenvio_esta_permitido():
    """Contrato: `puede_ver` incluye `me_la_reenviaron`, y `reenviar` usa
    `entrega_visible` (la misma regla). B recibió la ficha de A por reenvío
    (sin vínculo con A, ficha privada): B tiene que poder re-reenviarla a C, que
    está en la comunidad de B."""
    with SessionLocal() as s:
        a = _usuario(s, "a")  # privado, dueño
        b = _usuario(s, "b")
        c = _usuario(s, "c")
        intermediario = _usuario(s, "intermediario")
        _vinculo(s, a, intermediario)
        _vinculo(s, intermediario, b)
        _vinculo(s, b, c)
        ficha = _pausa(s, a)
        ficha_id, a_id, b_id, c_id = ficha.id, a.id, b.id, c.id

    # intermediario ve la ficha de A (vínculo) y se la reenvía a B.
    r = client.post("/api/reenvios", headers=_h("intermediario"),
                    json={"entrega_id": ficha_id, "a_usuario_id": b_id})
    assert r.status_code == 201
    # B no tiene vínculo con A: solo la ve por el reenvío.
    assert client.get(f"/api/fichas/de/{a_id}", headers=_h("b")).json()["fichas"] is None
    assert client.get(f"/api/fichas/{ficha_id}", headers=_h("b")).status_code == 200

    # B se la reenvía a C (que sí está en la comunidad de B).
    r = client.post("/api/reenvios", headers=_h("b"),
                    json={"entrega_id": ficha_id, "a_usuario_id": c_id})
    assert r.status_code == 201
    assert client.get(f"/api/fichas/{ficha_id}", headers=_h("c")).status_code == 200


def test_ok_reenviar_a_alguien_con_solicitud_pendiente_da_404():
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        pendiente = _usuario(s, "pendiente")
        _vinculo(s, yo, pendiente, estado=VINCULO_PENDIENTE)
        ficha_id = _pausa(s, duenio).id
        pendiente_id = pendiente.id

    r = client.post("/api/reenvios", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "a_usuario_id": pendiente_id})
    assert r.status_code == 404


def test_ok_el_receptor_sigue_viendo_la_ficha_aunque_deje_de_ser_mi_comunidad():
    """El reenvío es un permiso propio (tabla `reenvios`), no un derivado del
    vínculo entre quien envía y quien recibe. Si YO dejo de tener vínculo con el
    receptor DESPUÉS de reenviarle algo, la ficha le tiene que seguir sirviendo."""
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        receptor = _usuario(s, "receptor")
        v = _vinculo(s, yo, receptor)
        ficha_id = _pausa(s, duenio).id
        receptor_id, yo_id, v_id = receptor.id, yo.id, v.id

    r = client.post("/api/reenvios", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "a_usuario_id": receptor_id})
    assert r.status_code == 201

    with SessionLocal() as s:
        s.execute(delete(Vinculo).where(Vinculo.id == v_id))
        s.commit()

    r = client.get(f"/api/fichas/{ficha_id}", headers=_h("receptor"))
    assert r.status_code == 200  # el dueño es público igual, pero probamos el reenvío:
    r = client.get("/api/reenvios/recibidos", headers=_h("receptor"))
    assert ficha_id in [x["ficha"]["id"] for x in r.json()["reenvios"]]


def test_ok_recibidos_no_rompe_cuando_el_dueno_borra_la_entrega_y_no_lista_muertos():
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio")
        receptor = _usuario(s, "receptor")
        _vinculo(s, yo, duenio)
        _vinculo(s, yo, receptor)
        ficha = _pausa(s, duenio)
        ficha_id, receptor_id = ficha.id, receptor.id

    r = client.post("/api/reenvios", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "a_usuario_id": receptor_id})
    assert r.status_code == 201
    assert len(client.get("/api/reenvios/recibidos", headers=_h("receptor")).json()["reenvios"]) == 1

    assert client.delete(f"/api/baul/{ficha_id}", headers=_h("duenio")).status_code == 204

    r = client.get("/api/reenvios/recibidos", headers=_h("receptor"))
    assert r.status_code == 200, r.text
    assert r.json()["reenvios"] == []
    assert r.json()["no_leidos"] == 0


def test_ok_no_leidos_cuenta_solo_los_que_siguen_visibles():
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio1 = _usuario(s, "duenio1")
        duenio2 = _usuario(s, "duenio2", perfil_publico=True)
        receptor = _usuario(s, "receptor")
        _vinculo(s, yo, duenio1)
        _vinculo(s, yo, receptor)
        f1 = _pausa(s, duenio1).id
        f2 = _pausa(s, duenio2).id
        f1id, f2id, receptor_id = f1, f2, receptor.id

    client.post("/api/reenvios", headers=_h("yo"), json={"entrega_id": f1id, "a_usuario_id": receptor_id})
    client.post("/api/reenvios", headers=_h("yo"), json={"entrega_id": f2id, "a_usuario_id": receptor_id})
    assert client.get("/api/reenvios/recibidos", headers=_h("receptor")).json()["no_leidos"] == 2

    # El dueño 1 repliega su ficha: el reenvío 1 deja de ser visible.
    with SessionLocal() as s:
        s.get(Entrega, f1id).visibilidad = "privada"
        s.commit()

    r = client.get("/api/reenvios/recibidos", headers=_h("receptor"))
    assert r.json()["no_leidos"] == 1
    assert len(r.json()["reenvios"]) == 1
    assert r.json()["reenvios"][0]["ficha"]["id"] == f2id


# ── 6 · Hacer la Pausa: el motor ─────────────────────────────────────────────

def test_ok_free_403_no_crea_nada():
    with SessionLocal() as s:
        _usuario(s, "free")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        ficha_id = _pausa(s, duenio).id

    with SessionLocal() as s:
        antes = s.scalar(select(Entrega.id).where(Entrega.usuario_id ==
                          s.scalar(select(Usuario.id).where(Usuario.firebase_uid == PREFIJO + "free"))))
        assert antes is None

    r = client.post("/api/pausas/hacer", headers=_h("free"),
                    json={"entrega_id": ficha_id, "modo": "ahora"})
    assert r.status_code == 403

    with SessionLocal() as s:
        free_id = s.scalar(select(Usuario.id).where(Usuario.firebase_uid == PREFIJO + "free"))
        assert s.scalar(select(Entrega.id).where(Entrega.usuario_id == free_id)) is None


def test_ok_hacer_ahora_dos_veces_da_dos_extras_y_no_toca_la_carta_del_dia():
    with SessionLocal() as s:
        yo = _usuario(s, "yo", premium=True)
        duenio = _usuario(s, "duenio", perfil_publico=True)
        cartas = _cartas(s, 2)
        f1 = _pausa(s, duenio, carta_id=cartas[0]).id
        f2 = _pausa(s, duenio, carta_id=cartas[1]).id

    hoy = client.get("/api/carta-del-dia", headers=_h("yo")).json()
    hoy_id = hoy["entrega"]["id"]

    r1 = client.post("/api/pausas/hacer", headers=_h("yo"), json={"entrega_id": f1, "modo": "ahora"})
    r2 = client.post("/api/pausas/hacer", headers=_h("yo"), json={"entrega_id": f2, "modo": "ahora"})
    assert r1.status_code == 201 and r2.status_code == 201
    extra1, extra2 = r1.json()["entrega"]["id"], r2.json()["entrega"]["id"]
    assert extra1 != extra2 and extra1 != hoy_id and extra2 != hoy_id

    otra_vez = client.get("/api/carta-del-dia", headers=_h("yo")).json()
    assert otra_vez["entrega"]["id"] == hoy_id
    assert otra_vez["entrega"]["extra"] is False


def test_ok_ahora_sin_carta_hoy_luego_carta_del_dia_sortea_una_nueva():
    """Hacer 'ahora' antes de haber pedido la carta del día no debe hacerse
    pasar por ella: el próximo `GET /api/carta-del-dia` sortea/crea una NUEVA
    entrega de rotación, distinta de la extra."""
    with SessionLocal() as s:
        yo = _usuario(s, "yo", premium=True)
        duenio = _usuario(s, "duenio", perfil_publico=True)
        ficha_id = _pausa(s, duenio).id

    r = client.post("/api/pausas/hacer", headers=_h("yo"), json={"entrega_id": ficha_id, "modo": "ahora"})
    assert r.status_code == 201
    extra_id = r.json()["entrega"]["id"]

    hoy = client.get("/api/carta-del-dia", headers=_h("yo")).json()
    assert hoy["entrega"]["id"] != extra_id
    assert hoy["entrega"]["extra"] is False
    assert hoy["entrega"]["ya_existia"] is False  # se sorteó de cero, no reusó la extra


def test_ok_la_extra_aparece_en_el_baul_solo_tras_cerrarla():
    with SessionLocal() as s:
        yo = _usuario(s, "yo", premium=True)
        duenio = _usuario(s, "duenio", perfil_publico=True)
        ficha_id = _pausa(s, duenio).id
        duenio_id = duenio.id

    r = client.post("/api/pausas/hacer", headers=_h("yo"), json={"entrega_id": ficha_id, "modo": "ahora"})
    extra_id = r.json()["entrega"]["id"]

    assert extra_id not in [i["id"] for i in client.get("/api/baul", headers=_h("yo")).json()]

    r = client.put(f"/api/entregas/{extra_id}/cierre", headers=_h("yo"),
                   json={"reflexion": "la hice", "completada": True})
    assert r.status_code == 200

    baul = client.get("/api/baul", headers=_h("yo")).json()
    item = next(i for i in baul if i["id"] == extra_id)
    assert item["de"]["usuario_id"] == duenio_id


def test_ok_la_programada_se_sirve_aunque_el_dueno_repliegue_la_ficha_despues():
    """Documenta el contrato explícito: 'la carta ya es del mazo, debería
    servirse'. Se programa mientras la ficha es visible; el dueño la repliega
    ANTES de que el motor la sirva; igual tiene que servirse (no vuelve a
    chequear `puede_ver` al momento de servir)."""
    with SessionLocal() as s:
        yo = _usuario(s, "yo", premium=True)
        duenio = _usuario(s, "duenio", perfil_publico=True)
        carta_id = _cartas(s, 1)[0]
        ficha = _pausa(s, duenio, carta_id=carta_id)
        ficha_id = ficha.id

    r = client.post("/api/pausas/hacer", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "modo": "siguiente"})
    assert r.status_code == 201

    with SessionLocal() as s:
        s.get(Entrega, ficha_id).visibilidad = "privada"
        s.commit()
    # Ya no la puedo ver directamente.
    assert client.get(f"/api/fichas/{ficha_id}", headers=_h("yo")).status_code == 404

    servida = client.get("/api/carta-del-dia", headers=_h("yo")).json()
    assert servida["carta"]["id"] == carta_id
    assert servida["entrega"]["de"] is not None


# ── 7 · Descubrir: costo en queries ──────────────────────────────────────────

def test_ok_descubrir_cuenta_las_queries_para_30_fichas():
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        publico = _usuario(s, "publico", perfil_publico=True)
        for _ in range(30):
            _pausa(s, publico)

    sentencias: list[str] = []

    def _espia(conn, cursor, statement, parameters, context, executemany):
        sentencias.append(statement)

    event.listen(engine, "before_cursor_execute", _espia)
    try:
        r = client.get("/api/fichas/descubrir", headers=_h("yo"))
    finally:
        event.remove(engine, "before_cursor_execute", _espia)

    assert r.status_code == 200 and len(r.json()) == 30
    # No es un bug: es el dato pedido. `ficha_ajena` hace 1 query de fotos +
    # 1 de dueño + 1 de carta + 2 (categoría/acción) + 1 de `guardada` por
    # ficha, arriba de las 2 de la lista/comunidad → posible N+1.
    print(f"\n[QA C1.2] descubrir con 30 fichas ejecutó {len(sentencias)} queries")
    assert len(sentencias) >= 30  # como mínimo, 1 por ficha — confirma que hay N+1


# ── 8 · La extra compartida: la puerta directa NO respeta "no repetir ecos" ─

def test_ok_extra_compartida_es_una_ficha_mas_en_todas_las_puertas():
    """DECISIÓN WS29 (Tomás/orquestador, tras este hallazgo): una Pausa extra
    vivida y compartida se ve, se guarda y se reenvía como cualquier otra, y
    aparece en descubrir. La regla es una sola en todas las puertas.

    Hallazgo original que motivó la decisión — contrato implícito (`services/fichas.py:86-95`, `_publicables()`): una
    Pausa EXTRA ("Hacer ahora" de la ficha de otro) NO se re-publica —
    "la reflexión es mía, pero la vitrina se llenaría de ecos". `descubrir()` y
    `vitrina_de()` filtran `Entrega.extra.is_(False)` para cumplirlo.

    Pero `puede_ver()` (`mindful_api/services/comunidad.py:133-155`), que es LA
    puerta que usan `GET /api/fichas/{entrega_id}`, `guardar()` y `reenviar()`,
    NO chequea `extra` en ningún punto. Si yo marco mi extra `compartida`
    (`PUT /api/baul/{id}/visibilidad`, que tampoco filtra `extra`), cualquiera
    de mi comunidad que conozca (o adivine, o reciba por otro canal) el
    `entrega_id` la ve, la guarda y la reenvía como si fuera una ficha mía
    original — el "eco" que el comentario de `_publicables` dice que no debería
    existir. La regla de lectura no es la misma en todas las puertas."""
    with SessionLocal() as s:
        yo = _usuario(s, "yo", premium=True)
        duenio = _usuario(s, "duenio", perfil_publico=True)
        amigo = _usuario(s, "amigo")
        _vinculo(s, yo, amigo)
        ficha_id = _pausa(s, duenio).id

    r = client.post("/api/pausas/hacer", headers=_h("yo"), json={"entrega_id": ficha_id, "modo": "ahora"})
    extra_id = r.json()["entrega"]["id"]
    client.put(f"/api/entregas/{extra_id}/cierre", headers=_h("yo"),
               json={"reflexion": "eco", "completada": True})
    client.put(f"/api/baul/{extra_id}/visibilidad", headers=_h("yo"),
               json={"visibilidad": "compartida"})

    # Regla única: la puerta directa y la vitrina dicen lo mismo (sí).
    assert client.get(f"/api/fichas/{extra_id}", headers=_h("amigo")).status_code == 200
    assert extra_id in [
        f["id"] for f in client.get("/api/fichas/descubrir", headers=_h("amigo")).json()
    ]
