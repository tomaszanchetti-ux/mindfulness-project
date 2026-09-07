"""WS27 · B2.1 · Avisos: la campana de la app (lectura).

El push existe desde WS21, pero un push es un golpecito que se pierde si el
teléfono estaba apagado. La campana es la MEMORIA: la lista de lo que pasó y el
contador de lo que todavía no se miró.

Qué se prueba acá, y por qué:

1. **La forma.** `GET /api/avisos` devuelve `{no_leidos, avisos:[…]}` con los
   seis campos del contrato y el más nuevo primero. Un orden que baila entre
   recargas hace una campana ilegible.
2. **El aislamiento.** Un aviso ajeno NO EXISTE: no aparece en la lista, no se
   puede marcar (404, nunca 403 — un 403 confirmaría que la fila existe) y no
   cuenta en el contador del otro.
3. **El contador cuenta TODO.** Aunque la lista venga recortada por `limite`: si
   hay 60 sin leer y se piden 5, la campana sigue diciendo 60.
4. **Marcar es idempotente.** Marcar dos veces el mismo aviso no es un error.
5. **La punta a punta.** Lo que escribe una transición de carta (B1.1/B1.3, por
   `avisar_estado_carta`) es exactamente lo que el autor lee acá.

Usuarios `b21|…`: se borran al empezar y al terminar cada test, y arrastran sus
avisos en cascada.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    AVISO_CARTA_ESTADO,
    ESTADO_APROBADA,
    ESTADO_REVISION_DWELLIA,
    Aviso,
    Usuario,
)
from mindful_api.main import app
from mindful_api.services.avisos import TEXTOS_ESTADO, avisar_estado_carta

client = TestClient(app)

MARCA = "b21av|"
MIO = MARCA + "mio"
AJENO = MARCA + "ajeno"


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


def _limpiar() -> None:
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(MARCA + "%")))
        s.commit()


@pytest.fixture(autouse=True)
def limpio():
    _limpiar()
    yield
    _limpiar()


def _usuario(sub: str) -> str:
    with SessionLocal() as s:
        u = Usuario(firebase_uid=sub, email=f"{sub}@mindful.local")
        s.add(u)
        s.commit()
        return u.id


def _aviso(usuario_id: str, texto: str, dias: int = 0, leido: bool = False,
           referencia_id=None) -> str:
    with SessionLocal() as s:
        a = Aviso(
            usuario_id=usuario_id, tipo=AVISO_CARTA_ESTADO, texto=texto,
            referencia_id=referencia_id, leido=leido,
            created_at=datetime.now(timezone.utc) - timedelta(days=dias),
        )
        s.add(a)
        s.commit()
        return a.id


# ═════════════════════════════════════════════════════════════════════════════
# 1 · La forma y el orden
# ═════════════════════════════════════════════════════════════════════════════
def test_la_bandeja_vacia_es_una_bandeja():
    """Sin avisos hay respuesta igual: lista vacía y contador en 0, nunca un 404."""
    _usuario(MIO)
    r = client.get("/api/avisos", headers=_headers(MIO))
    assert r.status_code == 200
    assert r.json() == {"no_leidos": 0, "avisos": []}


def test_el_mas_nuevo_primero_y_con_los_campos_del_contrato():
    mio = _usuario(MIO)
    _aviso(mio, "El más viejo", dias=5, leido=True)
    _aviso(mio, "El del medio", dias=2)
    _aviso(mio, "El más nuevo", dias=0, referencia_id="cc-123")

    cuerpo = client.get("/api/avisos", headers=_headers(MIO)).json()
    assert [a["texto"] for a in cuerpo["avisos"]] == [
        "El más nuevo", "El del medio", "El más viejo",
    ]
    assert cuerpo["no_leidos"] == 2

    primero = cuerpo["avisos"][0]
    assert set(primero) == {
        "id", "tipo", "referencia_id", "texto", "leido", "created_at",
    }
    assert primero["tipo"] == AVISO_CARTA_ESTADO
    assert primero["referencia_id"] == "cc-123"
    assert primero["leido"] is False


def test_el_contador_no_lo_recorta_el_limite():
    """La lista se recorta; el número de la campana, no."""
    mio = _usuario(MIO)
    for i in range(8):
        _aviso(mio, f"Aviso {i}", dias=i)

    cuerpo = client.get("/api/avisos?limite=3", headers=_headers(MIO)).json()
    assert len(cuerpo["avisos"]) == 3
    assert cuerpo["no_leidos"] == 8
    # Y lo que recorta es la COLA: quedan los tres más nuevos.
    assert [a["texto"] for a in cuerpo["avisos"]] == ["Aviso 0", "Aviso 1", "Aviso 2"]


# ═════════════════════════════════════════════════════════════════════════════
# 2 · Marcar leído
# ═════════════════════════════════════════════════════════════════════════════
def test_marcar_uno_lo_devuelve_leido_y_baja_el_contador():
    mio = _usuario(MIO)
    aviso_id = _aviso(mio, "Tu carta ya está cargada")
    _aviso(mio, "Otro más")

    r = client.put(f"/api/avisos/{aviso_id}/leido", headers=_headers(MIO))
    assert r.status_code == 200
    assert r.json()["id"] == aviso_id and r.json()["leido"] is True

    cuerpo = client.get("/api/avisos", headers=_headers(MIO)).json()
    assert cuerpo["no_leidos"] == 1


def test_marcar_dos_veces_no_es_un_error():
    """Idempotente: el segundo toque devuelve el mismo aviso, ya leído."""
    mio = _usuario(MIO)
    aviso_id = _aviso(mio, "Tu carta necesita un retoque")
    primero = client.put(f"/api/avisos/{aviso_id}/leido", headers=_headers(MIO))
    segundo = client.put(f"/api/avisos/{aviso_id}/leido", headers=_headers(MIO))
    assert primero.status_code == segundo.status_code == 200
    assert segundo.json()["leido"] is True
    assert client.get("/api/avisos", headers=_headers(MIO)).json()["no_leidos"] == 0


def test_marcar_todos_vacia_la_campana():
    mio = _usuario(MIO)
    for i in range(4):
        _aviso(mio, f"Aviso {i}", dias=i)
    _aviso(mio, "Ya leído", dias=9, leido=True)

    r = client.put("/api/avisos/leidos", headers=_headers(MIO))
    assert r.status_code == 200
    assert r.json() == {"marcados": 4, "no_leidos": 0}

    cuerpo = client.get("/api/avisos", headers=_headers(MIO)).json()
    assert cuerpo["no_leidos"] == 0
    assert all(a["leido"] for a in cuerpo["avisos"])

    # Y otra vez, con la campana ya vacía: 0 marcados, sin error.
    assert client.put("/api/avisos/leidos", headers=_headers(MIO)).json()["marcados"] == 0


def test_un_aviso_inexistente_es_404():
    _usuario(MIO)
    r = client.put("/api/avisos/no-existe/leido", headers=_headers(MIO))
    assert r.status_code == 404
    assert r.json()["detail"] == "Aviso no encontrado"


# ═════════════════════════════════════════════════════════════════════════════
# 3 · El aislamiento
# ═════════════════════════════════════════════════════════════════════════════
def test_los_avisos_ajenos_no_existen():
    """Ni se listan, ni se cuentan, ni se pueden marcar. Y el 404 no delata nada:
    el ajeno responde igual que un id inventado."""
    mio = _usuario(MIO)
    ajeno = _usuario(AJENO)
    _aviso(mio, "Mío")
    del_otro = _aviso(ajeno, "Del otro")

    cuerpo = client.get("/api/avisos", headers=_headers(MIO)).json()
    assert [a["texto"] for a in cuerpo["avisos"]] == ["Mío"]
    assert cuerpo["no_leidos"] == 1

    r = client.put(f"/api/avisos/{del_otro}/leido", headers=_headers(MIO))
    assert r.status_code == 404
    assert r.json()["detail"] == "Aviso no encontrado"

    # Y no lo tocó: el dueño lo sigue teniendo sin leer.
    assert client.get("/api/avisos", headers=_headers(AJENO)).json()["no_leidos"] == 1


def test_marcar_todos_no_toca_los_del_otro():
    mio = _usuario(MIO)
    ajeno = _usuario(AJENO)
    _aviso(mio, "Mío 1")
    _aviso(mio, "Mío 2")
    _aviso(ajeno, "Del otro")

    assert client.put("/api/avisos/leidos", headers=_headers(MIO)).json()["marcados"] == 2
    assert client.get("/api/avisos", headers=_headers(AJENO)).json()["no_leidos"] == 1


# ═════════════════════════════════════════════════════════════════════════════
# 4 · Punta a punta con lo que escribe el recorrido de una carta
# ═════════════════════════════════════════════════════════════════════════════
def test_lo_que_escribe_una_transicion_es_lo_que_se_lee():
    """`avisar_estado_carta` (B1.1/B1.3) escribe · `GET /api/avisos` lee.

    Y `revision_dwellia` no avisa: para el autor sigue "en proceso de evaluación",
    así que ese estado NO tiene que aparecer en la campana.
    """
    mio = _usuario(MIO)
    with SessionLocal() as s:
        usuario = s.get(Usuario, mio)
        assert avisar_estado_carta(s, usuario, "cc-1", ESTADO_REVISION_DWELLIA) is None
        avisar_estado_carta(s, usuario, "cc-1", ESTADO_APROBADA)
        s.commit()

    cuerpo = client.get("/api/avisos", headers=_headers(MIO)).json()
    assert cuerpo["no_leidos"] == 1
    assert len(cuerpo["avisos"]) == 1
    aviso = cuerpo["avisos"][0]
    assert aviso["texto"] == TEXTOS_ESTADO[ESTADO_APROBADA]
    assert aviso["referencia_id"] == "cc-1"
    assert aviso["tipo"] == AVISO_CARTA_ESTADO

    client.put(f"/api/avisos/{aviso['id']}/leido", headers=_headers(MIO))
    with SessionLocal() as s:
        fila = s.scalar(select(Aviso).where(Aviso.usuario_id == mio))
        assert fila.leido is True
