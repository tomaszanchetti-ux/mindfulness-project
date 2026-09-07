"""WS29 · C1.1 · personas, solicitudes y foto de perfil.

Lo que se prueba acá es la puerta de entrada a la comunidad: encontrar a alguien
sin que su email salga nunca, pedir/aceptar/cortar un vínculo (uno solo entre dos,
con su aviso), y la foto que la comunidad ve de mí.

Convención de la suite (igual que `test_c0_contrato.py`): usuarios de mentira por
header `X-Debug-Sub` con prefijo propio, y un fixture que los borra antes de cada
test (la cascada se lleva vínculos, avisos y entregas).
"""

from __future__ import annotations

import struct
import zlib

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import AVISO_SOLICITUD, Aviso, Carta, Entrega, Usuario
from mindful_api.main import app
from mindful_api.services.comunidad import puede_ver

client = TestClient(app)
PREFIJO = "c11|"


def _h(sub: str, email: str | None = None) -> dict:
    return {"X-Debug-Sub": PREFIJO + sub, "X-Debug-Email": email or f"{sub}@c11.local"}


def _usuario(s, sub: str, **campos) -> Usuario:
    """Crea (o ajusta) un usuario de prueba. El apodo por defecto es único por sub
    para que la búsqueda no choque con los `demo|` que viven en la misma base."""
    uid = PREFIJO + sub
    u = s.scalar(select(Usuario).where(Usuario.firebase_uid == uid))
    if u is None:
        u = Usuario(firebase_uid=uid, email=f"{sub}@c11.local", apodo=sub.title())
        s.add(u)
    for k, v in campos.items():
        setattr(u, k, v)
    s.commit()
    s.refresh(u)
    return u


def _pausa(s, duenio: Usuario, visibilidad="compartida", completada=True) -> Entrega:
    carta_id = s.scalar(select(Carta.id).order_by(Carta.id).limit(1))
    e = Entrega(usuario_id=duenio.id, carta_id=carta_id, completada=completada,
                visibilidad=visibilidad, reflexion="c11")
    s.add(e)
    s.commit()
    s.refresh(e)
    return e


def _png(ancho: int = 2, alto: int = 2, rgb: tuple = (10, 120, 90)) -> bytes:
    """Un PNG válido mínimo (mismo armado que `demo_seed.png_plano`): firma +
    IHDR + IDAT + IEND. Sin Pillow."""
    crudo = (b"\x00" + bytes(rgb) * ancho) * alto

    def _chunk(tipo: bytes, datos: bytes) -> bytes:
        return (
            struct.pack(">I", len(datos)) + tipo + datos
            + struct.pack(">I", zlib.crc32(tipo + datos) & 0xFFFFFFFF)
        )

    ihdr = struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + _chunk(b"IHDR", ihdr)
        + _chunk(b"IDAT", zlib.compress(crudo, 9))
        + _chunk(b"IEND", b"")
    )


def _avisos_de(s, usuario_id: str) -> list:
    return s.scalars(
        select(Aviso)
        .where(Aviso.usuario_id == usuario_id, Aviso.tipo == AVISO_SOLICITUD)
        .order_by(Aviso.created_at)
    ).all()


def _ids(personas: list) -> set:
    return {p["usuario_id"] for p in personas}


@pytest.fixture(autouse=True)
def _limpio():
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()
    yield


# ── 1. Buscar ────────────────────────────────────────────────────────────────

def test_buscar_por_email_exacto_apodo_nombre_y_apellido():
    with SessionLocal() as s:
        yo = _usuario(s, "ana")
        otro = _usuario(s, "brunilda", email="Brunilda.Zzz@c11.local",
                        apodo="Brunilda", nombre="Filomena", apellido="Zurbarán")
        otro_id, yo_id = otro.id, yo.id

    h = _h("ana")
    # El email, tal cual y en otro case: la misma persona.
    for q in ("Brunilda.Zzz@c11.local", "brunilda.zzz@C11.LOCAL"):
        r = client.get("/api/comunidad/buscar", params={"q": q}, headers=h)
        assert r.status_code == 200
        assert _ids(r.json()) == {otro_id}, q

    # Un pedazo del apodo, del nombre y del apellido (case-insensitive).
    for q in ("runil", "FILOME", "zurbar"):
        r = client.get("/api/comunidad/buscar", params={"q": q}, headers=h)
        assert otro_id in _ids(r.json()), q

    # Un email parecido NO alcanza: el email es exacto o nada.
    r = client.get("/api/comunidad/buscar", params={"q": "runilda.zzz@c11.local"},
                   headers=h)
    assert _ids(r.json()) == set()

    # Nunca me devuelvo a mí.
    r = client.get("/api/comunidad/buscar", params={"q": "ana@c11.local"}, headers=h)
    assert yo_id not in _ids(r.json())


def test_buscar_con_una_letra_devuelve_vacio():
    _ = client.get("/api/perfil", headers=_h("ana"))  # me doy de alta
    with SessionLocal() as s:
        _usuario(s, "brunilda")
    for q in ("b", " b ", ""):
        r = client.get("/api/comunidad/buscar", params={"q": q}, headers=_h("ana"))
        assert r.status_code == 200 and r.json() == [], q
    # Sin `q` tampoco explota.
    assert client.get("/api/comunidad/buscar", headers=_h("ana")).json() == []


def test_buscar_nunca_devuelve_el_email_y_alcanza_a_los_privados():
    with SessionLocal() as s:
        _usuario(s, "ana")
        _usuario(s, "brunilda", perfil_publico=False)

    r = client.get("/api/comunidad/buscar", params={"q": "brunil"}, headers=_h("ana"))
    persona = r.json()[0]
    # Privada y sin vínculo: se la encuentra igual (si no, nadie podría pedirle nada).
    assert persona["perfil_publico"] is False and persona["vinculo"] == "ninguno"
    assert "email" not in persona
    assert set(persona) == {"usuario_id", "apodo", "foto_url", "perfil_publico",
                            "nombre", "apellido", "vinculo"}


# ── 2. Solicitudes ───────────────────────────────────────────────────────────

def test_solicitud_crea_vinculo_y_avisa_al_destinatario():
    with SessionLocal() as s:
        _usuario(s, "ana", apodo="Ana")
        b = _usuario(s, "beto")
        b_id = b.id

    r = client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    assert r.status_code == 201
    assert r.json()["vinculo"] == "pendiente_enviada"

    with SessionLocal() as s:
        avisos = _avisos_de(s, b_id)
        assert len(avisos) == 1
        assert avisos[0].texto == "Ana quiere ser parte de tu comunidad."
        yo_id = s.scalar(select(Usuario.id).where(Usuario.firebase_uid == PREFIJO + "ana"))
        assert avisos[0].referencia_id == yo_id
        # Y al que pide no le llega nada.
        assert _avisos_de(s, yo_id) == []

    # Desde el otro lado se ve como recibida.
    r = client.get("/api/comunidad", headers=_h("beto"))
    assert _ids(r.json()["recibidas"]) == {yo_id}


def test_solicitud_repetida_y_al_reves_chocan_con_409():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id

    assert client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana")).status_code == 201
    r = client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    assert r.status_code == 409
    assert r.json()["detail"] == "Ya hay una solicitud o un vínculo con esta persona."
    # B pidiéndole a A cuando A ya le pidió: el vínculo es uno solo.
    r = client.post(f"/api/comunidad/solicitudes/{a_id}", headers=_h("beto"))
    assert r.status_code == 409


def test_solicitud_a_mi_mismo_y_a_un_inexistente():
    r = client.get("/api/perfil", headers=_h("ana"))
    yo_id = r.json()["usuario_id"]

    r = client.post(f"/api/comunidad/solicitudes/{yo_id}", headers=_h("ana"))
    assert r.status_code == 422
    assert r.json()["detail"] == "No puedes enviarte una solicitud a ti mismo."

    r = client.post("/api/comunidad/solicitudes/no-existe", headers=_h("ana"))
    assert r.status_code == 404


# ── 3. Mi comunidad ──────────────────────────────────────────────────────────

def test_la_pendiente_sale_en_enviadas_para_a_y_en_recibidas_para_b():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id
    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))

    ca = client.get("/api/comunidad", headers=_h("ana")).json()
    assert _ids(ca["enviadas"]) == {b_id} and ca["recibidas"] == [] and ca["gente"] == []
    assert ca["enviadas"][0]["vinculo"] == "pendiente_enviada"

    cb = client.get("/api/comunidad", headers=_h("beto")).json()
    assert _ids(cb["recibidas"]) == {a_id} and cb["enviadas"] == [] and cb["gente"] == []
    assert cb["recibidas"][0]["vinculo"] == "pendiente_recibida"


def test_las_listas_vienen_ordenadas_por_apodo():
    with SessionLocal() as s:
        _usuario(s, "ana")
        ids = [_usuario(s, sub, apodo=apodo).id
               for sub, apodo in (("z1", "Zulema"), ("a1", "Abril"), ("m1", "Malena"))]
    for uid in ids:
        client.post(f"/api/comunidad/solicitudes/{uid}", headers=_h("ana"))
    enviadas = client.get("/api/comunidad", headers=_h("ana")).json()["enviadas"]
    assert [p["apodo"] for p in enviadas] == ["Abril", "Malena", "Zulema"]


# ── 4. Aceptar ───────────────────────────────────────────────────────────────

def test_aceptar_solo_el_destinatario_y_avisa_al_solicitante():
    with SessionLocal() as s:
        a = _usuario(s, "ana", apodo="Ana")
        b = _usuario(s, "beto", apodo="Beto")
        _usuario(s, "intruso")
        a_id, b_id = a.id, b.id
    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))

    # El solicitante no puede aceptarse su propia solicitud, ni un tercero.
    assert client.post(f"/api/comunidad/solicitudes/{b_id}/aceptar",
                       headers=_h("ana")).status_code == 404
    assert client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar",
                       headers=_h("intruso")).status_code == 404

    r = client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar", headers=_h("beto"))
    assert r.status_code == 200
    assert r.json()["vinculo"] == "aceptada" and r.json()["usuario_id"] == a_id

    # Los dos se ven en `gente`, en ninguna cola pendiente.
    ca = client.get("/api/comunidad", headers=_h("ana")).json()
    cb = client.get("/api/comunidad", headers=_h("beto")).json()
    assert _ids(ca["gente"]) == {b_id} and ca["enviadas"] == []
    assert _ids(cb["gente"]) == {a_id} and cb["recibidas"] == []

    with SessionLocal() as s:
        avisos_a = _avisos_de(s, a_id)
        assert [av.texto for av in avisos_a] == ["Beto aceptó tu solicitud."]
        assert avisos_a[0].referencia_id == b_id
        # A B solo le llegó el de la solicitud (aceptar no se avisa a uno mismo).
        assert len(_avisos_de(s, b_id)) == 1

    # Aceptar dos veces ya no encuentra nada pendiente.
    assert client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar",
                       headers=_h("beto")).status_code == 404


# ── 5. Rechazar / cancelar ───────────────────────────────────────────────────

@pytest.mark.parametrize("quien,objetivo", [("beto", "ana"), ("ana", "beto")])
def test_rechazar_o_cancelar_borra_la_pendiente_y_la_segunda_vez_es_404(quien, objetivo):
    with SessionLocal() as s:
        subs = {"ana": _usuario(s, "ana"), "beto": _usuario(s, "beto")}
        _usuario(s, "intruso")
        ids = {k: u.id for k, u in subs.items()}
    client.post(f"/api/comunidad/solicitudes/{ids['beto']}", headers=_h("ana"))

    # Un tercero no puede tocar el vínculo ajeno.
    assert client.delete(f"/api/comunidad/solicitudes/{ids[objetivo]}",
                         headers=_h("intruso")).status_code == 404

    url = f"/api/comunidad/solicitudes/{ids[objetivo]}"
    assert client.delete(url, headers=_h(quien)).status_code == 204
    assert client.get("/api/comunidad", headers=_h("ana")).json()["enviadas"] == []
    assert client.get("/api/comunidad", headers=_h("beto")).json()["recibidas"] == []
    assert client.delete(url, headers=_h(quien)).status_code == 404
    with SessionLocal() as s:  # rechazar/cancelar no avisa a nadie
        assert _avisos_de(s, ids["ana"]) == []


# ── 6. Quitar de mi comunidad ────────────────────────────────────────────────

def test_quitar_de_mi_comunidad_cierra_la_lectura_de_las_pausas():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto", perfil_publico=False)
        _usuario(s, "intruso")
        a_id, b_id = a.id, b.id
        pausa_id = _pausa(s, b).id

    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar", headers=_h("beto"))

    with SessionLocal() as s:
        assert puede_ver(s, s.get(Usuario, a_id), s.get(Entrega, pausa_id)) is True

    # Un tercero no puede desarmar el vínculo de otros.
    assert client.delete(f"/api/comunidad/{b_id}", headers=_h("intruso")).status_code == 404
    # Y una pendiente no se borra por esta puerta (esa es /solicitudes).
    assert client.delete("/api/comunidad/" + a_id, headers=_h("intruso")).status_code == 404

    assert client.delete(f"/api/comunidad/{b_id}", headers=_h("ana")).status_code == 204
    assert client.delete(f"/api/comunidad/{b_id}", headers=_h("ana")).status_code == 404

    with SessionLocal() as s:
        # Se cortó para los dos, y con el vínculo se cerró lo que A veía de B.
        assert client.get("/api/comunidad", headers=_h("beto")).json()["gente"] == []
        assert puede_ver(s, s.get(Usuario, a_id), s.get(Entrega, pausa_id)) is False
        # Quitar no avisa: a B solo le quedó el aviso de la solicitud original,
        # y a A el de la aceptación. Nadie se entera de que lo sacaron.
        assert len(_avisos_de(s, b_id)) == 1
        assert len(_avisos_de(s, a_id)) == 1


# ── 7. Foto de perfil ────────────────────────────────────────────────────────

def test_foto_de_perfil_ciclo_completo():
    with SessionLocal() as s:
        _usuario(s, "ana")
        _usuario(s, "beto")

    # Sin foto: el perfil no la nombra y la lectura es 404.
    perfil = client.get("/api/perfil", headers=_h("ana")).json()
    mi_id = perfil["usuario_id"]
    assert perfil["foto_url"] is None
    assert client.get(f"/api/usuarios/{mi_id}/foto", headers=_h("beto")).status_code == 404

    r = client.post("/api/perfil/foto", headers=_h("ana"),
                    files={"foto": ("cara.png", _png(), "image/png")})
    assert r.status_code == 200
    assert r.json() == {"foto_url": f"/api/usuarios/{mi_id}/foto"}
    assert client.get("/api/perfil", headers=_h("ana")).json()["foto_url"] == \
        f"/api/usuarios/{mi_id}/foto"

    # La ve OTRO usuario logueado (es lo que la comunidad ve de mí).
    r = client.get(f"/api/usuarios/{mi_id}/foto", headers=_h("beto"))
    assert r.status_code == 200
    assert r.headers["content-type"] == "image/png"
    assert r.content.startswith(b"\x89PNG")

    # Y aparece en la búsqueda como URL, nunca como ruta de Storage.
    encontrada = client.get("/api/comunidad/buscar", params={"q": "ana@c11.local"},
                            headers=_h("beto")).json()[0]
    assert encontrada["foto_url"] == f"/api/usuarios/{mi_id}/foto"

    # Reemplazar: queda UNA sola ruta viva (la anterior se borra de Storage).
    with SessionLocal() as s:
        vieja = s.scalar(select(Usuario.foto_path).where(Usuario.id == mi_id))
    client.post("/api/perfil/foto", headers=_h("ana"),
                files={"foto": ("otra.png", _png(rgb=(200, 10, 10)), "image/png")})
    with SessionLocal() as s:
        nueva = s.scalar(select(Usuario.foto_path).where(Usuario.id == mi_id))
    assert nueva and nueva != vieja
    from mindful_api.services import storage
    assert storage.leer(vieja) is None and storage.leer(nueva) is not None
    assert client.get(f"/api/usuarios/{mi_id}/foto", headers=_h("beto")).status_code == 200

    # Quitar: 204, idempotente, y después ya no hay nada que leer.
    assert client.delete("/api/perfil/foto", headers=_h("ana")).status_code == 204
    assert client.delete("/api/perfil/foto", headers=_h("ana")).status_code == 204
    assert client.get(f"/api/usuarios/{mi_id}/foto", headers=_h("beto")).status_code == 404
    assert client.get("/api/perfil", headers=_h("ana")).json()["foto_url"] is None
    assert storage.leer(nueva) is None


def test_foto_de_perfil_rechaza_lo_que_no_es_imagen():
    r = client.post("/api/perfil/foto", headers=_h("ana"),
                    files={"foto": ("nota.txt", b"hola", "text/plain")})
    assert r.status_code == 415
    assert r.json()["detail"] == "Formato no soportado: usa una imagen (JPG, PNG o WebP)"

    r = client.post("/api/perfil/foto", headers=_h("ana"),
                    files={"foto": ("vacia.png", b"", "image/png")})
    assert r.status_code == 400
    assert client.get("/api/perfil", headers=_h("ana")).json()["foto_url"] is None


def test_la_foto_de_alguien_que_no_existe_es_404():
    assert client.get("/api/usuarios/no-existe/foto", headers=_h("ana")).status_code == 404
