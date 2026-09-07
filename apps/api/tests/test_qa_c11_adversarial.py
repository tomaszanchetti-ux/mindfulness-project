"""WS29 · C1.1 · Q/A adversarial — personas, solicitudes y foto de perfil.

Ataca lo que `test_c11_comunidad.py` no cubre: fuga de email, bordes de la
búsqueda, carreras en las solicitudes, cascada de borrado, y los límites reales
de la foto de perfil (formato, tamaño, un solo archivo vivo por usuario).

Prefijo propio `qa11|` (aislado de `c11|` y `demo|`) con el mismo patrón de
limpieza que la suite hermana.
"""

from __future__ import annotations

import struct
import zlib
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import AVISO_SOLICITUD, Aviso, Carta, Entrega, Vinculo, Usuario
from mindful_api.main import app
from mindful_api.services import avisos as avisos_svc
from mindful_api.services import storage

client = TestClient(app)
PREFIJO = "qa11|"


def _h(sub: str, email: str | None = None) -> dict:
    return {"X-Debug-Sub": PREFIJO + sub, "X-Debug-Email": email or f"{sub}@qa11.local"}


def _usuario(s, sub: str, **campos) -> Usuario:
    uid = PREFIJO + sub
    u = s.scalar(select(Usuario).where(Usuario.firebase_uid == uid))
    if u is None:
        u = Usuario(firebase_uid=uid, email=f"{sub}@qa11.local", apodo=sub.title())
        s.add(u)
    for k, v in campos.items():
        setattr(u, k, v)
    s.commit()
    s.refresh(u)
    return u


def _pausa(s, duenio: Usuario, visibilidad="compartida", completada=True) -> Entrega:
    carta_id = s.scalar(select(Carta.id).order_by(Carta.id).limit(1))
    e = Entrega(usuario_id=duenio.id, carta_id=carta_id, completada=completada,
                visibilidad=visibilidad, reflexion="qa11")
    s.add(e)
    s.commit()
    s.refresh(e)
    return e


def _png(ancho: int = 2, alto: int = 2, rgb: tuple = (10, 120, 90)) -> bytes:
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


def _vinculos_del_par(s, a_id: str, b_id: str) -> list:
    return s.scalars(
        select(Vinculo).where(
            ((Vinculo.solicitante_id == a_id) & (Vinculo.destinatario_id == b_id))
            | ((Vinculo.solicitante_id == b_id) & (Vinculo.destinatario_id == a_id))
        )
    ).all()


@pytest.fixture(autouse=True)
def _limpio():
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()
    yield


# ═════════════════════════════════════════════════════════════════════════════
# 1. Fuga de email
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_ningun_endpoint_de_c11_devuelve_email_ajeno():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id

    # buscar
    encontrada = client.get("/api/comunidad/buscar", params={"q": "beto"},
                            headers=_h("ana")).json()[0]
    assert "email" not in encontrada
    assert "beto@qa11.local" not in str(encontrada)

    # crear solicitud
    r = client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana")).json()
    assert "email" not in r and "beto@qa11.local" not in str(r)

    # mi_comunidad (enviadas/recibidas)
    ca = client.get("/api/comunidad", headers=_h("ana")).json()
    assert "beto@qa11.local" not in str(ca)
    cb = client.get("/api/comunidad", headers=_h("beto")).json()
    assert "ana@qa11.local" not in str(cb)

    # aceptar
    r2 = client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar", headers=_h("beto")).json()
    assert "email" not in r2 and "ana@qa11.local" not in str(r2)

    # y de vuelta mi_comunidad ya con "gente"
    ca2 = client.get("/api/comunidad", headers=_h("ana")).json()
    assert "beto@qa11.local" not in str(ca2)


def test_ok_buscar_por_email_exacto_no_repite_el_email_buscado_en_la_respuesta():
    """El contrato dice que se encuentra por email exacto: eso es intencional.
    Pero la respuesta no debe traer ese email de vuelta (solo el apodo)."""
    with SessionLocal() as s:
        _usuario(s, "ana")
        _usuario(s, "brunilda", email="brunilda.secreta@qa11.local")

    r = client.get("/api/comunidad/buscar",
                   params={"q": "brunilda.secreta@qa11.local"}, headers=_h("ana"))
    assert r.status_code == 200
    assert "brunilda.secreta@qa11.local" not in r.text


# ═════════════════════════════════════════════════════════════════════════════
# 2. Búsqueda: bordes
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_busqueda_con_espacios_alrededor_y_mayusculas():
    with SessionLocal() as s:
        _usuario(s, "ana")
        otro = _usuario(s, "carmen", apodo="Carmencita")
        otro_id = otro.id
    for q in ("  carmen  ", "CARMEN", "  CaRmEn"):
        r = client.get("/api/comunidad/buscar", params={"q": q}, headers=_h("ana"))
        assert r.status_code == 200
        assert otro_id in _ids(r.json()), q


def test_documenta_acentos_no_matchean_sin_normalizar():
    """No es bug (LIKE + lower no pliega acentos): se documenta el comportamiento."""
    with SessionLocal() as s:
        _usuario(s, "ana")
        # Nombre único: la base local también tiene a "Lucía Pérez" (demo-seed).
        _usuario(s, "zulemia", apodo="Zulemía")
    r = client.get("/api/comunidad/buscar", params={"q": "zulemia"}, headers=_h("ana"))
    # "zulemia" (sin tilde) NO encuentra a "Zulemía": comportamiento esperado, se deja registrado.
    assert r.json() == []
    r2 = client.get("/api/comunidad/buscar", params={"q": "zulemía"}, headers=_h("ana"))
    assert len(r2.json()) == 1


def test_ok_porcentaje_guion_bajo_y_backslash_se_tratan_como_literales():
    """`%`, `_`, `\\` deben buscarse literalmente (escapados), nunca como comodín
    que devuelva "todo el mundo"."""
    with SessionLocal() as s:
        _usuario(s, "ana")
        raro = _usuario(s, "raro", apodo="100%_ok\\x")
        otros_ids = [_usuario(s, f"relleno{i}").id for i in range(3)]
        raro_id = raro.id

    for q in ("100%", "%_ok", "\\x"):
        r = client.get("/api/comunidad/buscar", params={"q": q}, headers=_h("ana"))
        assert r.status_code == 200
        encontrados = _ids(r.json())
        assert raro_id in encontrados, q
        # Ninguno de los usuarios "de relleno" (sin ese texto) debería aparecer
        # si el comodín estuviera de verdad activo devolviendo todo.
        assert not (set(otros_ids) & encontrados), q


def test_ok_query_de_mil_caracteres_no_rompe():
    r = client.get("/api/comunidad/buscar", params={"q": "x" * 1000}, headers=_h("ana"))
    assert r.status_code == 200
    assert r.json() == []


def test_ok_usuario_sin_apodo_ni_nombre_aparece_como_alguien():
    with SessionLocal() as s:
        _usuario(s, "ana")
        anon = _usuario(s, "anon", apodo=None, nombre=None, apellido=None,
                        email="buscameporeso@qa11.local")
        anon_id = anon.id
    r = client.get("/api/comunidad/buscar",
                   params={"q": "buscameporeso@qa11.local"}, headers=_h("ana"))
    personas = r.json()
    assert _ids(personas) == {anon_id}
    assert personas[0]["apodo"] == "Alguien"


def test_ok_limite_20_exacto_con_25_coincidencias_y_orden_alfabetico():
    with SessionLocal() as s:
        _usuario(s, "ana")
        apodos = [f"Match{str(i).zfill(2)}" for i in range(25)]
        import random
        barajados = apodos[:]
        random.shuffle(barajados)
        for i, apodo in enumerate(barajados):
            _usuario(s, f"m{i}", apodo=apodo)

    r = client.get("/api/comunidad/buscar", params={"q": "match"}, headers=_h("ana"))
    personas = r.json()
    assert len(personas) == 20
    apodos_devueltos = [p["apodo"] for p in personas]
    assert apodos_devueltos == sorted(apodos_devueltos)
    assert apodos_devueltos == [f"Match{str(i).zfill(2)}" for i in range(20)]


def test_ok_buscarme_por_mi_propio_email_no_me_devuelve():
    with SessionLocal() as s:
        _usuario(s, "ana")
    r = client.get("/api/comunidad/buscar", params={"q": "ana@qa11.local"}, headers=_h("ana"))
    assert r.json() == []


# ═════════════════════════════════════════════════════════════════════════════
# 3. Solicitudes: bordes
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_aceptar_una_que_ya_fue_rechazada_es_404():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id
    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    assert client.delete(f"/api/comunidad/solicitudes/{a_id}", headers=_h("beto")).status_code == 204
    # Ya no hay fila pendiente: aceptar (por cualquiera de los dos) es 404.
    assert client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar",
                       headers=_h("beto")).status_code == 404


def test_ok_delete_solicitudes_sobre_vinculo_aceptado_es_404():
    """Contrato (WS29 §4.3): `DELETE /api/comunidad/solicitudes/{id}` es para
    rechazar/cancelar una PENDIENTE; sobre un vínculo ya ACEPTADO debe ser 404
    (esa puerta es `DELETE /api/comunidad/{id}`, no esta). Candado: pasa —
    `borrar_solicitud` (mindful_api/services/comunidad.py) filtra por
    `v.estado != VINCULO_PENDIENTE` -> 404."""
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id
    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar", headers=_h("beto"))
    r = client.delete(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    assert r.status_code == 404, (
        "DELETE /solicitudes/{id} borró (o tocó) un vínculo ACEPTADO en vez de "
        "devolver 404 — services/comunidad.py::borrar_solicitud dejó pasar un "
        "estado != pendiente."
    )
    with SessionLocal() as s:
        assert _vinculos_del_par(s, a_id, b_id)[0].estado == "aceptada"


def test_ok_delete_comunidad_sobre_vinculo_pendiente_es_404():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id
    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    # Ni el solicitante ni el destinatario pueden "quitar" (esa puerta es solo
    # para vínculos ya aceptados) mientras está pendiente.
    assert client.delete(f"/api/comunidad/{b_id}", headers=_h("ana")).status_code == 404
    assert client.delete(f"/api/comunidad/{a_id}", headers=_h("beto")).status_code == 404


@pytest.mark.parametrize("crudo", ["../etc", "", "x" * 500, "%2e%2e%2f"])
def test_ok_usuario_id_con_formato_raro_nunca_500(crudo):
    """Nunca 500 y nunca delata nada de otro usuario. Un segmento vacío colapsa
    la URL (doble "/") y a veces cae en una ruta sin ese método -> 405; eso es
    ruteo genérico de FastAPI, no una fuga de información, así que se acepta
    junto con 404/422."""
    seg = quote(crudo, safe="")
    for r in (
        client.post(f"/api/comunidad/solicitudes/{seg}", headers=_h("ana")),
        client.post(f"/api/comunidad/solicitudes/{seg}/aceptar", headers=_h("ana")),
        client.delete(f"/api/comunidad/solicitudes/{seg}", headers=_h("ana")),
        client.delete(f"/api/comunidad/{seg}", headers=_h("ana")),
    ):
        assert r.status_code in (404, 422, 405), (seg, r.status_code)


def test_ok_intruso_no_puede_aceptar_ni_borrar_el_vinculo_ajeno():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        _usuario(s, "intruso")
        a_id, b_id = a.id, b.id
    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    assert client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar",
                       headers=_h("intruso")).status_code == 404
    assert client.delete(f"/api/comunidad/solicitudes/{a_id}",
                         headers=_h("intruso")).status_code == 404
    assert client.delete(f"/api/comunidad/solicitudes/{b_id}",
                         headers=_h("intruso")).status_code == 404
    with SessionLocal() as s:
        assert _vinculos_del_par(s, a_id, b_id)[0].estado == "pendiente"


# ═════════════════════════════════════════════════════════════════════════════
# 4. Avisos
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_texto_del_aviso_usa_alguien_cuando_no_hay_apodo_ni_nombre():
    with SessionLocal() as s:
        anon = _usuario(s, "anon", apodo=None, nombre=None, apellido=None)
        b = _usuario(s, "beto")
        anon_id, b_id = anon.id, b.id
    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("anon"))
    with SessionLocal() as s:
        avisos = _avisos_de(s, b_id)
        assert avisos[0].texto == "Alguien quiere ser parte de tu comunidad."
        assert "@qa11.local" not in avisos[0].texto


def test_ok_push_que_falla_no_tumba_la_solicitud(monkeypatch):
    def _explota(*a, **k):
        raise RuntimeError("push caído")
    monkeypatch.setattr(avisos_svc, "enviar_push", _explota)

    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id

    # Sin suscripción push no llega a llamar enviar_push, así que sembramos una.
    from mindful_api.db.models import PushSuscripcion
    with SessionLocal() as s:
        s.add(PushSuscripcion(usuario_id=b_id, endpoint="https://push.example/x",
                              p256dh="k", auth="a"))
        s.commit()

    r = client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    assert r.status_code == 201
    with SessionLocal() as s:
        v = _vinculos_del_par(s, a_id, b_id)
        assert len(v) == 1 and v[0].estado == "pendiente"


# ═════════════════════════════════════════════════════════════════════════════
# 5. Foto de perfil
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_subir_sin_archivo_es_422():
    r = client.post("/api/perfil/foto", headers=_h("ana"))
    assert r.status_code == 422


def test_bug_content_type_gif_no_es_rechazado_con_415():
    """Contrato (WS29 §4.3, tabla C1.1): `POST /api/perfil/foto` acepta
    "JPG/PNG/WebP <=8 MB" — GIF no está en la lista, así que debería ser 415.
    Pero `subir_foto_perfil` (mindful_api/services/comunidad.py) delega el
    formato a `storage.extension_para` (mindful_api/services/storage.py, dict
    `_EXT`), que fue armado para las fotos DE UNA PAUSA (services/fotos.py) y
    ahí sí incluye "image/gif", "image/heic" e "image/heif". La foto de perfil
    reusa ese mapa sin filtrar, así que hoy acepta GIF/HEIC/HEIF de perfil pese
    a que el contrato y el mensaje de error dicen "JPG, PNG o WebP"."""
    r = client.post("/api/perfil/foto", headers=_h("ana"),
                    files={"foto": ("cara.gif", b"GIF89a" + b"\x00" * 20, "image/gif")})
    assert r.status_code == 415, (
        f"esperaba 415 Unsupported Media Type para image/gif, la API contestó "
        f"{r.status_code}: {r.text}"
    )


def test_ok_8mb_mas_1_byte_es_413():
    contenido = _png() + b"\x00" * (8 * 1024 * 1024 + 1 - len(_png()))
    assert len(contenido) == 8 * 1024 * 1024 + 1
    r = client.post("/api/perfil/foto", headers=_h("ana"),
                    files={"foto": ("grande.png", contenido, "image/png")})
    assert r.status_code == 413


def test_ok_reemplazar_dos_veces_deja_un_solo_archivo_en_disco():
    perfil = client.get("/api/perfil", headers=_h("ana")).json()
    mi_id = perfil["usuario_id"]
    carpeta = Path(settings.storage_dir) / "perfil" / mi_id

    for rgb in ((10, 10, 10), (20, 20, 20), (30, 30, 30)):
        r = client.post("/api/perfil/foto", headers=_h("ana"),
                        files={"foto": ("f.png", _png(rgb=rgb), "image/png")})
        assert r.status_code == 200

    if carpeta.exists():
        archivos = [p for p in carpeta.iterdir() if p.is_file()]
        assert len(archivos) == 1, f"quedaron {len(archivos)} archivos: {archivos}"
    with SessionLocal() as s:
        foto_path = s.scalar(select(Usuario.foto_path).where(Usuario.id == mi_id))
    assert foto_path is not None
    assert storage.leer(foto_path) is not None


def test_ok_delete_borra_el_archivo_del_disco():
    client.post("/api/perfil/foto", headers=_h("ana"),
               files={"foto": ("f.png", _png(), "image/png")})
    with SessionLocal() as s:
        mi_id = s.scalar(select(Usuario.id).where(Usuario.firebase_uid == PREFIJO + "ana"))
        ruta = s.scalar(select(Usuario.foto_path).where(Usuario.id == mi_id))
    assert storage.leer(ruta) is not None
    assert client.delete("/api/perfil/foto", headers=_h("ana")).status_code == 204
    assert storage.leer(ruta) is None


def test_ok_get_foto_sin_foto_y_con_id_inexistente_son_404():
    with SessionLocal() as s:
        b = _usuario(s, "beto")
        b_id = b.id
    assert client.get(f"/api/usuarios/{b_id}/foto", headers=_h("ana")).status_code == 404
    assert client.get("/api/usuarios/no-existe-nunca/foto", headers=_h("ana")).status_code == 404


def test_ok_no_existe_endpoint_para_subir_la_foto_de_otro():
    with SessionLocal() as s:
        b = _usuario(s, "beto")
        b_id = b.id
    r = client.post(f"/api/usuarios/{b_id}/foto", headers=_h("ana"),
                    files={"foto": ("f.png", _png(), "image/png")})
    assert r.status_code in (404, 405)


# ═════════════════════════════════════════════════════════════════════════════
# 6. Carrera
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_dos_solicitudes_simultaneas_entre_los_mismos_dos_nunca_dan_500():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id

    def _pedir(quien, destino_id):
        return client.post(f"/api/comunidad/solicitudes/{destino_id}", headers=_h(quien))

    with ThreadPoolExecutor(max_workers=2) as ex:
        f1 = ex.submit(_pedir, "ana", b_id)
        f2 = ex.submit(_pedir, "beto", a_id)
        r1, r2 = f1.result(), f2.result()

    codigos = sorted([r1.status_code, r2.status_code])
    assert 500 not in codigos
    assert codigos == [201, 409], (r1.status_code, r1.text, r2.status_code, r2.text)

    with SessionLocal() as s:
        filas = _vinculos_del_par(s, a_id, b_id)
        assert len(filas) == 1, f"quedaron {len(filas)} filas para el mismo par"


# ═════════════════════════════════════════════════════════════════════════════
# 7. Cascada
# ═════════════════════════════════════════════════════════════════════════════

def test_ok_borrar_al_otro_usuario_se_lleva_el_vinculo_y_no_rompe_get_comunidad():
    with SessionLocal() as s:
        a = _usuario(s, "ana")
        b = _usuario(s, "beto")
        a_id, b_id = a.id, b.id
        pausa_id = _pausa(s, b).id

    client.post(f"/api/comunidad/solicitudes/{b_id}", headers=_h("ana"))
    client.post(f"/api/comunidad/solicitudes/{a_id}/aceptar", headers=_h("beto"))
    assert client.get("/api/comunidad", headers=_h("ana")).json()["gente"] != []

    with SessionLocal() as s:
        s.execute(delete(Entrega).where(Entrega.id == pausa_id))
        s.execute(delete(Usuario).where(Usuario.id == b_id))
        s.commit()

    r = client.get("/api/comunidad", headers=_h("ana"))
    assert r.status_code == 200
    assert _ids(r.json()["gente"]) == set()
    with SessionLocal() as s:
        assert _vinculos_del_par(s, a_id, b_id) == []
