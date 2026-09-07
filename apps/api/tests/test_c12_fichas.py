"""WS29 · C1.2 · Las fichas ajenas: descubrir, mirar, reenviar, guardar, vivir.

Lo que se prueba acá es la SUPERFICIE de la comunidad: qué ve cada uno, qué no
ve nunca, y qué pasa cuando el dueño cambia de idea. La regla de lectura ya la
probó C0; acá se prueba que ninguna puerta la esquiva —incluida la de las fotos,
que es la que más fácil se olvida— y que la Pausa de otro no le rompe el motor
al que la vive.

Los vínculos se escriben directo en la base (el modelo es del contrato C0): así
esta card no depende de los endpoints de C1.1, que se construyen en paralelo.
"""

from __future__ import annotations

import struct
import zlib
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    AVISO_REENVIO,
    VINCULO_ACEPTADA,
    VINCULO_PENDIENTE,
    Aviso,
    Carta,
    Entrega,
    Guardada,
    PausaProgramada,
    PushSuscripcion,
    Reenvio,
    Usuario,
    Vinculo,
)
from mindful_api.main import app
from mindful_api.services import aviso as aviso_srv
from mindful_api.services import avisos as avisos_srv

client = TestClient(app)
PREFIJO = "c12|"


# ── Herramientas ─────────────────────────────────────────────────────────────

def png_plano(ancho: int = 4, alto: int = 4, rgb: tuple = (180, 200, 190)) -> bytes:
    """Un PNG válido mínimo (copiado de `demo_seed.png_plano`): firma + IHDR +
    IDAT + IEND. Sirve para subir una foto REAL sin sumar dependencias."""
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
    return {"X-Debug-Sub": PREFIJO + sub, "X-Debug-Email": f"{sub}@c12.local"}


def _usuario(s, sub: str, premium: bool = False, **campos) -> Usuario:
    u = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + sub))
    if u is None:
        u = Usuario(firebase_uid=PREFIJO + sub, email=f"{sub}@c12.local", apodo=sub.title())
        s.add(u)
    # Sin términos aceptados no hay carta del día (M2) ni aviso diario (WS20).
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


# ── 1 · Descubrir ────────────────────────────────────────────────────────────

def test_descubrir_muestra_publicas_y_de_mi_comunidad_y_nada_mas():
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        publico = _usuario(s, "publico", perfil_publico=True)
        amigo = _usuario(s, "amigo")
        extranio = _usuario(s, "extranio")
        _vinculo(s, yo, amigo)
        _vinculo(s, yo, extranio, estado=VINCULO_PENDIENTE)  # pendiente no alcanza

        del_publico = _pausa(s, publico).id
        del_amigo = _pausa(s, amigo).id
        del_extranio = _pausa(s, extranio).id
        privada = _pausa(s, publico, visibilidad="privada").id
        sin_vivir = _pausa(s, publico, completada=False).id
        extra = _pausa(s, publico, extra=True).id
        mia = _pausa(s, yo).id

    r = client.get("/api/fichas/descubrir", headers=_h("yo"))
    assert r.status_code == 200
    ids = [f["id"] for f in r.json()]
    assert del_publico in ids and del_amigo in ids
    assert extra in ids  # WS29: una extra vivida y compartida es una Pausa más
    for oculta in (del_extranio, privada, sin_vivir, mia):
        assert oculta not in ids

    # La forma: lo del dueño y nada de lo que es solo suyo.
    ficha = next(f for f in r.json() if f["id"] == del_publico)
    assert ficha["tipo"] == "pausa"
    assert ficha["de"]["usuario_id"] and ficha["de"]["apodo"] == "Publico"
    assert ficha["guardada"] is False
    assert "estrellas" not in ficha
    assert "visibilidad" not in ficha
    assert "comentario_carta" not in ficha
    assert "email" not in ficha["de"]


def test_descubrir_pone_las_de_foto_primero_y_corta_en_30():
    with SessionLocal() as s:
        _usuario(s, "yo")
        publico = _usuario(s, "publico", perfil_publico=True)
        # La con foto se crea ANTES (más vieja): si igual sale primero, el orden
        # por foto le ganó a la fecha, que es lo que se quiere probar.
        con_foto = _pausa(s, publico, fecha=datetime.now(timezone.utc) - timedelta(days=3))
        sin_foto = _pausa(s, publico, fecha=datetime.now(timezone.utc))
        con_foto_id, sin_foto_id = con_foto.id, sin_foto.id
    _subir_foto("publico", con_foto_id)

    ids = [f["id"] for f in client.get("/api/fichas/descubrir", headers=_h("yo")).json()]
    assert ids.index(con_foto_id) < ids.index(sin_foto_id)

    # 31 candidatas → 30 y ni una más.
    with SessionLocal() as s:
        publico = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + "publico"))
        for _ in range(29):
            _pausa(s, publico)
    r = client.get("/api/fichas/descubrir", headers=_h("yo"))
    assert len(r.json()) == 30


# ── 2 · La vitrina de una persona ────────────────────────────────────────────

def test_vitrina_publica_privada_y_con_vinculo():
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        publico = _usuario(s, "publico", perfil_publico=True, nombre="Ana", apellido="Ruiz")
        cerrado = _usuario(s, "cerrado")
        _pausa(s, publico)
        _pausa(s, publico, visibilidad="privada")
        _pausa(s, publico, extra=True)
        _pausa(s, cerrado)
        publico_id, cerrado_id, yo_id = publico.id, cerrado.id, yo.id

    r = client.get(f"/api/fichas/de/{publico_id}", headers=_h("yo"))
    assert r.status_code == 200
    cuerpo = r.json()
    assert cuerpo["persona"]["nombre"] == "Ana" and cuerpo["persona"]["vinculo"] == "ninguno"
    assert "email" not in cuerpo["persona"]
    # Solo lo compartido y vivido (la extra compartida cuenta): la privada no.
    assert len(cuerpo["fichas"]) == 2
    assert all("estrellas" not in f for f in cuerpo["fichas"])

    # Privado sin vínculo: la persona sí (para poder pedirle vínculo), las fichas no.
    r = client.get(f"/api/fichas/de/{cerrado_id}", headers=_h("yo"))
    assert r.status_code == 200
    assert r.json()["fichas"] is None
    assert r.json()["persona"]["apodo"] == "Cerrado"

    # Con el vínculo aceptado se abre.
    with SessionLocal() as s:
        _vinculo(s, s.get(Usuario, yo_id), s.get(Usuario, cerrado_id))
    r = client.get(f"/api/fichas/de/{cerrado_id}", headers=_h("yo"))
    assert len(r.json()["fichas"]) == 1
    assert r.json()["persona"]["vinculo"] == "aceptada"

    # La mía también vale (misma vista) y una persona que no existe es 404.
    r = client.get(f"/api/fichas/de/{yo_id}", headers=_h("yo"))
    assert r.status_code == 200 and r.json()["fichas"] == []
    assert client.get("/api/fichas/de/no-existe", headers=_h("yo")).status_code == 404


# ── 3 · La ficha y su foto ───────────────────────────────────────────────────

def test_ficha_y_foto_ajena_solo_por_la_regla():
    with SessionLocal() as s:
        _usuario(s, "yo")
        publico = _usuario(s, "publico", perfil_publico=True)
        _usuario(s, "intruso")
        cerrado = _usuario(s, "cerrado")
        visible = _pausa(s, publico)
        otra = _pausa(s, publico)
        escondida = _pausa(s, cerrado)
        visible_id, otra_id, escondida_id = visible.id, otra.id, escondida.id

    foto_id = _subir_foto("publico", visible_id)
    otra_foto = _subir_foto("publico", otra_id)

    # La ficha: cualquiera la ve si el dueño es público…
    r = client.get(f"/api/fichas/{visible_id}", headers=_h("yo"))
    assert r.status_code == 200
    assert r.json()["fotos"] == [f"/api/fichas/{visible_id}/fotos/{foto_id}"]
    # …y nadie la ve si el dueño es privado (404, nunca 403).
    r = client.get(f"/api/fichas/{escondida_id}", headers=_h("yo"))
    assert r.status_code == 404 and r.json()["detail"] == "No encontramos esta Pausa."
    assert client.get("/api/fichas/no-existe", headers=_h("yo")).status_code == 404

    # La foto por la puerta de la comunidad: 200 con la regla, 404 sin ella.
    r = client.get(f"/api/fichas/{visible_id}/fotos/{foto_id}", headers=_h("yo"))
    assert r.status_code == 200 and r.headers["content-type"].startswith("image/png")
    assert r.headers["cache-control"] == "private, max-age=86400"
    assert r.content[:8] == b"\x89PNG\r\n\x1a\n"

    with SessionLocal() as s:
        publico = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + "publico"))
        publico.perfil_publico = False
        s.commit()
    assert client.get(f"/api/fichas/{visible_id}/fotos/{foto_id}",
                      headers=_h("intruso")).status_code == 404
    assert client.get(f"/api/fichas/{visible_id}", headers=_h("intruso")).status_code == 404

    # La puerta VIEJA (solo del dueño) sigue cerrada para un tercero.
    assert client.get(f"/api/fotos/{foto_id}", headers=_h("intruso")).status_code == 404
    assert client.get(f"/api/fotos/{foto_id}", headers=_h("publico")).status_code == 200

    # Una foto de OTRA entrega bajo un entrega_id visible: 404 (no se cruzan).
    with SessionLocal() as s:
        publico = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + "publico"))
        publico.perfil_publico = True
        s.commit()
    r = client.get(f"/api/fichas/{visible_id}/fotos/{otra_foto}", headers=_h("yo"))
    assert r.status_code == 404
    r = client.get(f"/api/fichas/{visible_id}/fotos/no-existe", headers=_h("yo"))
    assert r.status_code == 404


# ── 4 · Reenviar ─────────────────────────────────────────────────────────────

def test_reenviar_abre_una_ficha_y_no_un_perfil(monkeypatch):
    # El push del reenvío lleva la url IN-APP de la ficha (el aviso guardado no
    # tiene columna `url`: la url viaja en el push, y es lo que se verifica).
    empujados = []
    monkeypatch.setattr(
        avisos_srv, "enviar_push",
        lambda sus, titulo, cuerpo, url: empujados.append((cuerpo, url)) or "ok",
    )

    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio")
        receptor = _usuario(s, "receptor")
        afuera = _usuario(s, "afuera")
        _vinculo(s, yo, duenio)
        _vinculo(s, yo, receptor)
        ficha = _pausa(s, duenio)
        s.add(PushSuscripcion(usuario_id=receptor.id, endpoint="https://push.test/c12-r",
                              p256dh="k" * 20, auth="a" * 10))
        s.commit()
        ficha_id, duenio_id, receptor_id, afuera_id, yo_id = (
            ficha.id, duenio.id, receptor.id, afuera.id, yo.id
        )

    r = client.post("/api/reenvios", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "a_usuario_id": receptor_id})
    assert r.status_code == 201 and r.json()["id"]

    # El aviso le llegó al receptor, con la url in-app de la ficha.
    with SessionLocal() as s:
        aviso = s.scalar(select(Aviso).where(Aviso.usuario_id == receptor_id))
        assert aviso is not None and aviso.tipo == AVISO_REENVIO
        assert aviso.texto == "Yo te envió una Pausa."
        assert aviso.referencia_id == ficha_id
    assert empujados == [("Yo te envió una Pausa.", f"/comunidad/ficha/{ficha_id}")]
    bandeja = client.get("/api/avisos", headers=_h("receptor")).json()
    assert bandeja["no_leidos"] == 1
    assert bandeja["avisos"][0]["referencia_id"] == ficha_id

    # El receptor ve ESA ficha aunque no tenga vínculo con el dueño…
    assert client.get(f"/api/fichas/{ficha_id}", headers=_h("receptor")).status_code == 200
    # …pero no el perfil del dueño.
    r = client.get(f"/api/fichas/de/{duenio_id}", headers=_h("receptor"))
    assert r.status_code == 200 and r.json()["fichas"] is None

    # A alguien fuera de mi comunidad: 404 con el mensaje de comunidad.
    r = client.post("/api/reenvios", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "a_usuario_id": afuera_id})
    assert r.status_code == 404 and r.json()["detail"] == "Esa persona no está en tu comunidad."
    # A mí mismo: 422.
    r = client.post("/api/reenvios", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "a_usuario_id": yo_id})
    assert r.status_code == 422
    # De nuevo lo mismo a la misma persona: 409.
    r = client.post("/api/reenvios", headers=_h("yo"),
                    json={"entrega_id": ficha_id, "a_usuario_id": receptor_id})
    assert r.status_code == 409
    # Un intruso no puede reenviar lo que no ve.
    r = client.post("/api/reenvios", headers=_h("afuera"),
                    json={"entrega_id": ficha_id, "a_usuario_id": receptor_id})
    assert r.status_code == 404

    # Recibidos: uno, sin leer, con la ficha adentro.
    r = client.get("/api/reenvios/recibidos", headers=_h("receptor"))
    cuerpo = r.json()
    assert cuerpo["no_leidos"] == 1 and len(cuerpo["reenvios"]) == 1
    recibido = cuerpo["reenvios"][0]
    assert recibido["de"]["apodo"] == "Yo" and recibido["ficha"]["id"] == ficha_id
    assert recibido["leido"] is False

    assert client.put(f"/api/reenvios/{recibido['id']}/leido",
                      headers=_h("receptor")).json() == {"leido": True}
    assert client.get("/api/reenvios/recibidos", headers=_h("receptor")).json()["no_leidos"] == 0
    # Marcar el envío de otro: 404.
    assert client.put(f"/api/reenvios/{recibido['id']}/leido",
                      headers=_h("afuera")).status_code == 404

    # El dueño la repliega: se cae de recibidos y la ficha deja de existir.
    with SessionLocal() as s:
        s.get(Entrega, ficha_id).visibilidad = "privada"
        s.commit()
    assert client.get("/api/reenvios/recibidos", headers=_h("receptor")).json()["reenvios"] == []
    assert client.get(f"/api/fichas/{ficha_id}", headers=_h("receptor")).status_code == 404


# ── 5 · Guardar ──────────────────────────────────────────────────────────────

def test_guardar_una_ficha_ajena_vive_en_mi_baul_mientras_el_dueno_quiera():
    with SessionLocal() as s:
        yo = _usuario(s, "yo")
        duenio = _usuario(s, "duenio", perfil_publico=True)
        _usuario(s, "intruso")
        ajena = _pausa(s, duenio, reflexion="lo que escribió el otro")
        ajena.estrellas = 5
        s.commit()
        mia = _pausa(s, yo, reflexion="lo mío")
        ajena_id, mia_id = ajena.id, mia.id

    r = client.post(f"/api/guardadas/{ajena_id}", headers=_h("yo"))
    assert r.status_code == 201 and r.json() == {"guardada": True}

    baul = client.get("/api/baul", headers=_h("yo")).json()
    item = next(i for i in baul if i["id"] == ajena_id)
    assert item["guardada"] is True
    assert item["estrellas"] is None          # las estrellas son del dueño, jamás viajan
    assert item["completada"] is True and item["visibilidad"] == "compartida"
    assert item["de"]["apodo"] == "Duenio"
    assert next(i for i in baul if i["id"] == mia_id)["de"] is None

    # Repetida → 409 · la mía → 422 · la que no veo → 404.
    assert client.post(f"/api/guardadas/{ajena_id}", headers=_h("yo")).status_code == 409
    r = client.post(f"/api/guardadas/{mia_id}", headers=_h("yo"))
    assert r.status_code == 422 and r.json()["detail"] == "Esta Pausa ya es tuya."
    assert client.post(f"/api/guardadas/{mia_id}", headers=_h("intruso")).status_code == 404

    # El dueño la repliega: desaparece de mi Baúl. La vuelve a compartir: vuelve.
    with SessionLocal() as s:
        s.get(Entrega, ajena_id).visibilidad = "privada"
        s.commit()
    assert ajena_id not in [i["id"] for i in client.get("/api/baul", headers=_h("yo")).json()]
    with SessionLocal() as s:
        s.get(Entrega, ajena_id).visibilidad = "compartida"
        s.commit()
    assert ajena_id in [i["id"] for i in client.get("/api/baul", headers=_h("yo")).json()]

    # La ficha ya se sabe guardada, y quitarla la saca (dos veces, no).
    assert client.get(f"/api/fichas/{ajena_id}", headers=_h("yo")).json()["guardada"] is True
    assert client.delete(f"/api/guardadas/{ajena_id}", headers=_h("yo")).status_code == 204
    assert client.delete(f"/api/guardadas/{ajena_id}", headers=_h("yo")).status_code == 404
    assert ajena_id not in [i["id"] for i in client.get("/api/baul", headers=_h("yo")).json()]

    # Un intruso no puede borrar lo que guardó otro (ni ve nada de esto).
    client.post(f"/api/guardadas/{ajena_id}", headers=_h("yo"))
    assert client.delete(f"/api/guardadas/{ajena_id}", headers=_h("intruso")).status_code == 404
    with SessionLocal() as s:
        assert s.scalar(select(Guardada).where(Guardada.entrega_id == ajena_id)) is not None


# ── 6 · Hacer la Pausa de otra persona ───────────────────────────────────────

def test_hacer_la_pausa_ahora_es_extra_y_no_pisa_la_carta_del_dia():
    with SessionLocal() as s:
        _usuario(s, "free")
        _usuario(s, "yo", premium=True)
        duenio = _usuario(s, "duenio", perfil_publico=True)
        cartas = _cartas(s, 3)
        ajena = _pausa(s, duenio, carta_id=cartas[0])
        ajena_id, duenio_id = ajena.id, duenio.id

    # Free: no. Y el mensaje es el del contrato.
    r = client.post("/api/pausas/hacer", headers=_h("free"),
                    json={"entrega_id": ajena_id, "modo": "ahora"})
    assert r.status_code == 403
    assert r.json()["detail"] == "Hacer la Pausa de otra persona es de quienes son parte."
    # Un modo inventado: 422 (el vocabulario es cerrado).
    r = client.post("/api/pausas/hacer", headers=_h("yo"),
                    json={"entrega_id": ajena_id, "modo": "cuando-sea"})
    assert r.status_code == 422

    r = client.post("/api/pausas/hacer", headers=_h("yo"),
                    json={"entrega_id": ajena_id, "modo": "ahora"})
    assert r.status_code == 201
    salida = r.json()
    extra_id = salida["entrega"]["id"]
    assert salida["entrega"]["extra"] is True
    assert salida["entrega"]["de"]["usuario_id"] == duenio_id
    assert salida["entrega"]["ya_existia"] is False

    # La carta del día NO es la extra: la extra no ocupa el día.
    hoy = client.get("/api/carta-del-dia", headers=_h("yo")).json()
    assert hoy["entrega"]["id"] != extra_id
    assert hoy["entrega"]["extra"] is False and hoy["entrega"]["de"] is None
    # …y pedirla de nuevo sigue devolviendo la del día (la extra no confunde al motor).
    otra_vez = client.get("/api/carta-del-dia", headers=_h("yo")).json()
    assert otra_vez["entrega"]["id"] == hoy["entrega"]["id"]

    # La extra se vive como cualquier otra y cae en el Baúl.
    assert client.get(f"/api/entregas/{extra_id}", headers=_h("yo")).status_code == 200
    assert client.get(f"/api/entregas/{extra_id}", headers=_h("duenio")).status_code == 404
    r = client.put(f"/api/entregas/{extra_id}/cierre", headers=_h("yo"),
                   json={"estrellas": 4, "reflexion": "la viví", "completada": True})
    assert r.status_code == 200 and r.json()["entrega"]["completada"] is True
    assert r.json()["entrega"]["extra"] is True
    baul = client.get("/api/baul", headers=_h("yo")).json()
    item = next(i for i in baul if i["id"] == extra_id)
    assert item["de"]["usuario_id"] == duenio_id and item["estrellas"] == 4

    # Un intruso no puede hacer la Pausa que no ve.
    with SessionLocal() as s:
        s.get(Usuario, duenio_id).perfil_publico = False
        s.commit()
    r = client.post("/api/pausas/hacer", headers=_h("yo"),
                    json={"entrega_id": ajena_id, "modo": "ahora"})
    assert r.status_code == 404


def test_pausa_programada_es_la_carta_del_dia_siguiente():
    with SessionLocal() as s:
        yo = _usuario(s, "yo", premium=True)
        duenio = _usuario(s, "duenio", perfil_publico=True)
        cartas = _cartas(s, 2)
        ajena = _pausa(s, duenio, carta_id=cartas[0])
        otra = _pausa(s, duenio, carta_id=cartas[1])
        ajena_id, otra_id, duenio_id, yo_id = ajena.id, otra.id, duenio.id, yo.id

    r = client.post("/api/pausas/hacer", headers=_h("yo"),
                    json={"entrega_id": ajena_id, "modo": "siguiente"})
    assert r.status_code == 201
    assert r.json()["programada"] is True and r.json()["carta"]["id"] == cartas[0]

    # Programar de nuevo REEMPLAZA: la cola es de una.
    r = client.post("/api/pausas/hacer", headers=_h("yo"),
                    json={"entrega_id": otra_id, "modo": "siguiente"})
    assert r.status_code == 201
    with SessionLocal() as s:
        pendientes = s.scalars(
            select(PausaProgramada).where(
                PausaProgramada.usuario_id == yo_id,
                PausaProgramada.servida_at.is_(None),
            )
        ).all()
        assert len(pendientes) == 1 and pendientes[0].carta_id == cartas[1]

    # Sin carta hoy: la del día ES la programada, con `de` y con `servida_at`.
    r = client.get("/api/carta-del-dia", headers=_h("yo"))
    assert r.status_code == 200
    servida = r.json()
    assert servida["carta"]["id"] == cartas[1]
    assert servida["entrega"]["de"]["usuario_id"] == duenio_id
    assert servida["entrega"]["extra"] is False    # es la carta del día, no una extra
    assert servida["entrega"]["ya_existia"] is False
    with SessionLocal() as s:
        prog = s.scalar(select(PausaProgramada).where(PausaProgramada.usuario_id == yo_id))
        assert prog.servida_at is not None

    # Pedirla de nuevo: la misma (no se sirve dos veces).
    de_nuevo = client.get("/api/carta-del-dia", headers=_h("yo")).json()
    assert de_nuevo["entrega"]["id"] == servida["entrega"]["id"]
    assert de_nuevo["entrega"]["ya_existia"] is True


def test_la_programada_espera_a_manana_si_hoy_ya_hubo_carta():
    with SessionLocal() as s:
        yo = _usuario(s, "yo", premium=True)
        duenio = _usuario(s, "duenio", perfil_publico=True)
        ajena_id = _pausa(s, duenio, carta_id=_cartas(s, 2)[1]).id
        yo_id = yo.id

    hoy_id = client.get("/api/carta-del-dia", headers=_h("yo")).json()["entrega"]["id"]
    client.post("/api/pausas/hacer", headers=_h("yo"),
                json={"entrega_id": ajena_id, "modo": "siguiente"})

    # Hoy ya hay carta: la programada no se toca.
    assert client.get("/api/carta-del-dia", headers=_h("yo")).json()["entrega"]["id"] == hoy_id
    with SessionLocal() as s:
        assert s.scalar(
            select(PausaProgramada).where(PausaProgramada.usuario_id == yo_id)
        ).servida_at is None
        # Mañana (la de hoy pasa a ser la de ayer)…
        s.get(Entrega, hoy_id).fecha = datetime.now(timezone.utc) - timedelta(days=1)
        s.commit()

    manana = client.get("/api/carta-del-dia", headers=_h("yo")).json()
    assert manana["entrega"]["id"] != hoy_id
    assert manana["entrega"]["de"] is not None
    with SessionLocal() as s:
        assert s.scalar(
            select(PausaProgramada).where(PausaProgramada.usuario_id == yo_id)
        ).servida_at is not None


# ── 7 · El aviso diario nombra la Pausa que me espera ────────────────────────

def test_aviso_diario_nombra_a_quien_me_envio_la_pausa(monkeypatch):
    cuerpos = []

    def _fake(sus, titulo, cuerpo, url):  # noqa: ANN001 — firma del real
        cuerpos.append(cuerpo)
        return "ok"

    monkeypatch.setattr(aviso_srv, "enviar_push", _fake)

    with SessionLocal() as s:
        yo = _usuario(s, "yo", premium=True, hora_aviso="08:00", tz="Europe/Madrid")
        duenio = _usuario(s, "duenio", perfil_publico=True, apodo="Lu")
        ajena_id = _pausa(s, duenio).id
        s.add(PushSuscripcion(usuario_id=yo.id, endpoint="https://push.test/c12",
                              p256dh="k" * 20, auth="a" * 10))
        s.commit()

    ahora = datetime(2026, 6, 11, 12, 0, tzinfo=timezone.utc)  # 14:00 en Madrid
    with SessionLocal() as s:
        aviso_srv.enviar_avisos(s, ahora)
    assert cuerpos and cuerpos[-1] == aviso_srv.CUERPO   # sin programada, el de siempre

    cuerpos.clear()
    client.post("/api/pausas/hacer", headers=_h("yo"),
                json={"entrega_id": ajena_id, "modo": "siguiente"})
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + "yo"))
        u.ultimo_aviso_fecha = None   # que le vuelva a tocar hoy
        s.commit()

    with SessionLocal() as s:
        aviso_srv.enviar_avisos(s, ahora)
    assert cuerpos and cuerpos[-1] == "Hoy te espera la Pausa que te envió Lu."


# ── Aislamiento transversal ──────────────────────────────────────────────────

def test_un_intruso_no_toca_nada_de_lo_ajeno():
    with SessionLocal() as s:
        duenio = _usuario(s, "duenio")
        amigo = _usuario(s, "amigo")
        _usuario(s, "intruso", premium=True)
        _vinculo(s, duenio, amigo)
        ficha_id = _pausa(s, duenio).id
        amigo_id, duenio_id = amigo.id, duenio.id

    h = _h("intruso")
    assert client.get(f"/api/fichas/{ficha_id}", headers=h).status_code == 404
    assert client.get(f"/api/fichas/de/{duenio_id}", headers=h).json()["fichas"] is None
    assert ficha_id not in [f["id"] for f in client.get("/api/fichas/descubrir", headers=h).json()]
    assert client.post("/api/reenvios", headers=h,
                       json={"entrega_id": ficha_id, "a_usuario_id": amigo_id}).status_code == 404
    assert client.post(f"/api/guardadas/{ficha_id}", headers=h).status_code == 404
    assert client.post("/api/pausas/hacer", headers=h,
                       json={"entrega_id": ficha_id, "modo": "ahora"}).status_code == 404
    assert client.get(f"/api/entregas/{ficha_id}", headers=h).status_code == 404
    with SessionLocal() as s:
        assert s.scalar(select(Reenvio).where(Reenvio.entrega_id == ficha_id)) is None
        assert s.scalar(select(Guardada).where(Guardada.entrega_id == ficha_id)) is None
