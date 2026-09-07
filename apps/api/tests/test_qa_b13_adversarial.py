"""Q/A ADVERSARIAL de la card B1.3 (WS27) · Administración: aprobar cartas de la comunidad.

No valida la card: intenta ROMPERLA. Lo que ya cubre `tests/test_b13_admin.py`
(la puerta básica, la forma del ítem, el recorrido feliz, los 409 más obvios, los
comentarios sin email) no se repite: acá se ataca lo que queda afuera.

Nombres de los tests, y qué significan:

  `test_ok_*`   → candado que aguanta. Queda como regresión.
  `test_bug_*`  → BUG real, con `@pytest.mark.xfail(strict=True)`: el test afirma
                  el comportamiento CORRECTO y hoy falla. Cuando alguien lo
                  arregle, el xfail estricto pasa a XPASS y rompe la suite: eso
                  obliga a sacarle el marcador y dejarlo como candado.
  `test_nota_*` → comportamiento documentado, defendible hoy, que hay que mirar
                  (o que espera a otra card).

Los nueve bugs numerados están en el informe de la sesión (BUG-B13-1 … BUG-B13-9).

ESTADO (WS27 · corrección): los NUEVE están corregidos, así que ya no queda
ningún `xfail`. Los `test_bug_*` conservan el nombre a propósito — es la única
manera de seguir leyendo el informe contra la suite —, pero hoy son candados de
regresión que pasan. Dos `test_nota_*` que documentaban el daño (los límites del
contenido al aprobar, y el prompt del `fix` fuera de rango) se convirtieron en
`test_ok_*` parametrizados por borde: ahora afirman el comportamiento corregido.

Todo lo que este archivo escribe se borra al empezar Y al terminar cada test:
usuarios `qa13|…` (que arrastran en cascada entregas, avisos y propuestas) y
cartas publicadas `com-…`. El mazo tiene que volver siempre a 77.

Correr:
    cd apps/api && MINDFUL_DATABASE_URL=… \\
        .venv/bin/pytest -q -p no:warnings tests/test_qa_b13_adversarial.py
"""

from __future__ import annotations

import json
import threading
from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, func, select, text

from mindful_api import seed as seed_mod
from mindful_api.config import settings
from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    AVISO_CARTA_ESTADO,
    ESTADO_A_REVISAR,
    ESTADO_APROBADA,
    ESTADO_EN_REVISION,
    ESTADO_RECHAZADA,
    ESTADO_RETIRADA,
    ESTADO_REVISION_DWELLIA,
    FIRMA_ANONIMA,
    FIRMA_APODO,
    ORIGEN_COMUNIDAD,
    ORIGEN_DWELLIA,
    Aviso,
    Carta,
    CartaComunidad,
    Categoria,
    Entrega,
    PushSuscripcion,
    Usuario,
)
from mindful_api.main import app
from mindful_api.services import avisos as avisos_mod
from mindful_api.services.admin import PREFIJO_CARTA_COMUNIDAD
from mindful_api.services.cartas_comunidad import FRASE_MAX, PROMPT_MAX, PROMPT_MIN

client = TestClient(app)
# Para los 500: sin esto TestClient re-levanta la excepción y no se ve el status.
client_500 = TestClient(app, raise_server_exceptions=False)

MARCA = "qa13|"
ADMIN_SUB = MARCA + "admin"
AUTOR_SUB = MARCA + "autor"
LECTOR_SUB = MARCA + "lector"

PROMPT_OK = (
    "Escribe en tu diario tres cosas que hoy sostuvieron tu día sin que las "
    "nombraras, y qué cambiaría si les dieras las gracias en voz alta."
)
FRASE_OK = "Hoy alcanza con lo que ya está."


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


# Identidades que los ataques a la puerta provocan de rebote: la auto-provisión
# de `get_current_user` crea la fila igual. Se limpian para no dejar rastro.
UIDS_DE_REBOTE = ("dev|user", " ")


# ── Limpieza: el mazo vuelve a 77 y no queda ningún `qa13|` ──────────────────
def _limpiar() -> None:
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(MARCA + "%")))
        s.execute(delete(Usuario).where(Usuario.firebase_uid.in_(UIDS_DE_REBOTE)))
        s.execute(delete(Carta).where(Carta.id.like(PREFIJO_CARTA_COMUNIDAD + "%")))
        s.commit()


@pytest.fixture(autouse=True)
def limpio():
    _limpiar()
    yield
    _limpiar()


@pytest.fixture
def admin(monkeypatch) -> dict:
    monkeypatch.setattr(settings, "admin_uids", ADMIN_SUB)
    return _headers(ADMIN_SUB)


# ── Siembra (sin pasar por B1.1: esta card no depende de aquella) ────────────
def _usuario(sub: str, apodo=None, nombre=None) -> str:
    with SessionLocal() as s:
        u = Usuario(
            firebase_uid=sub, email=f"{sub}@mindful.local", apodo=apodo, nombre=nombre,
            terminos_aceptados_at=datetime.now(timezone.utc),
        )
        s.add(u)
        s.commit()
        return u.id


def _sembrar(
    usuario_id: str,
    estado: str = ESTADO_REVISION_DWELLIA,
    firma: str = FIRMA_ANONIMA,
    frase: str = FRASE_OK,
    prompt: str = PROMPT_OK,
    categoria: str = "gratitud",
    accion: str = "contemplar",
    veredicto=None,
    motivo=None,
    cesion: bool = True,
) -> str:
    with SessionLocal() as s:
        p = CartaComunidad(
            usuario_id=usuario_id, categoria_slug=categoria, accion_slug=accion,
            frase=frase, prompt=prompt, firma=firma, estado=estado,
            veredicto=veredicto, motivo=motivo,
            cesion_aceptada_at=datetime.now(timezone.utc) if cesion else None,
        )
        s.add(p)
        s.commit()
        return p.id


def _carta_publicada() -> Carta:
    with SessionLocal() as s:
        return s.scalar(
            select(Carta).where(Carta.id.like(PREFIJO_CARTA_COMUNIDAD + "%"))
        )


def _cuantas_publicadas() -> int:
    with SessionLocal() as s:
        return s.scalar(
            select(func.count()).select_from(Carta)
            .where(Carta.id.like(PREFIJO_CARTA_COMUNIDAD + "%"))
        )


def _avisos(usuario_id: str) -> list:
    with SessionLocal() as s:
        return list(s.scalars(
            select(Aviso).where(Aviso.usuario_id == usuario_id)
            .order_by(Aviso.created_at, Aviso.id)
        ).all())


# ═════════════════════════════════════════════════════════════════════════════
# 1 · LA PUERTA (`get_admin`)
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_la_lista_de_admins_tolera_espacios_y_comas_vacias(monkeypatch):
    """`" qa13|admin , , otro ,"` tiene que resolver a dos uids, no a cinco basuras.

    Es exactamente lo que va a pasar cuando alguien pegue la variable a mano en
    Cloud Run: sobra un espacio, sobra una coma final.
    """
    monkeypatch.setattr(settings, "admin_uids", f" {ADMIN_SUB} , , otro ,")
    assert settings.admin_uids_list == [ADMIN_SUB, "otro"]
    assert client.get("/api/admin/cartas", headers=_headers(ADMIN_SUB)).status_code == 200


def test_ok_la_puerta_distingue_mayusculas(monkeypatch):
    """El uid declarado en mayúsculas NO abre la puerta al uid real.

    Es el default seguro: los `firebase_uid` son case-sensitive y "casi igual"
    nunca puede alcanzar. Un uid mal tipeado deja el panel cerrado, no abierto.
    """
    monkeypatch.setattr(settings, "admin_uids", ADMIN_SUB.upper())
    assert client.get("/api/admin/cartas", headers=_headers(ADMIN_SUB)).status_code == 403


@pytest.mark.parametrize("lista", ["", ",", " , , ", "   "])
def test_ok_una_lista_sin_uids_utiles_no_deja_entrar_a_nadie(monkeypatch, lista):
    """Comas sueltas y blancos NO son uids: `admin_uids_list` los descarta.

    Importa porque un uid en blanco que sobreviviera al parseo empataría con el
    `firebase_uid` de cualquier request rara y abriría el panel.
    """
    monkeypatch.setattr(settings, "admin_uids", lista)
    assert settings.admin_uids_list == []
    assert client.get("/api/admin/cartas", headers=_headers(ADMIN_SUB)).status_code == 403
    # …y tampoco entra alguien cuyo uid sea, literalmente, un espacio.
    assert client.get("/api/admin/cartas", headers={"X-Debug-Sub": " "}).status_code == 403


def test_ok_en_modo_firebase_sin_token_es_401_y_no_403(monkeypatch):
    """Primero "¿quién sos?", después "¿podés?".

    Un 403 sin token le diría al cliente "existís pero no te alcanza" cuando en
    realidad ni se identificó. El orden correcto es 401.
    """
    monkeypatch.setattr(settings, "admin_uids", ADMIN_SUB)
    monkeypatch.setattr(settings, "auth_mode", "firebase")
    r = client.get("/api/admin/cartas", headers=_headers(ADMIN_SUB))
    assert r.status_code == 401
    assert "token" in r.json()["detail"].lower()
    # También en los POST, y antes de mirar el body.
    assert client.post(
        "/api/admin/cartas/lo-que-sea/rechazar", headers=_headers(ADMIN_SUB), json={}
    ).status_code == 401


def test_ok_la_puerta_gana_al_404_y_al_422(monkeypatch):
    """Sin ser admin NO se puede distinguir un id que existe de uno que no.

    Si el 404 llegara antes que el 403, `/api/admin` sería un oráculo de ids de
    propuestas ajenas. Y el 422 del body tampoco puede adelantarse.
    """
    monkeypatch.setattr(settings, "admin_uids", "")
    h = _headers(ADMIN_SUB)
    assert client.post("/api/admin/cartas/no-existe/rechazar", headers=h,
                       json={"motivo": "x"}).status_code == 403
    assert client.post("/api/admin/cartas/no-existe/rechazar", headers=h,
                       json={}).status_code == 403


def test_nota_en_modo_dev_un_header_vacio_cae_a_dev_user(monkeypatch):
    """DOCUMENTADO (riesgo de configuración, no bug de la card).

    `auth._identidad_dev` hace `x_debug_sub or DEV_SUB`: un `X-Debug-Sub` vacío
    (o ausente) resuelve `dev|user`. O sea que si algún día `dev|user` entrara a
    `MINDFUL_ADMIN_UIDS`, CUALQUIERA sin header sería administración.

    Hoy no es explotable en producción (allá `auth_mode=firebase`), pero es la
    razón por la que `dev|user` no puede aparecer nunca en esa variable.
    """
    monkeypatch.setattr(settings, "admin_uids", "dev|user")
    assert client.get("/api/admin/cartas", headers={"X-Debug-Sub": ""}).status_code == 200
    assert client.get("/api/admin/cartas").status_code == 200


# ═════════════════════════════════════════════════════════════════════════════
# 2 · APROBAR = CARGAR (lo que se publica, y lo que no debería publicarse)
# ═════════════════════════════════════════════════════════════════════════════
def test_bug_aprobar_publica_frase_y_prompt_fuera_de_los_limites(admin):
    """Los límites son del CONTENIDO, no del formulario del autor.

    Cualquier fila que llegue a `cartas_comunidad` por otro camino (una
    migración, el demo-seed, un fix a mano en la base) se publica sin control:
    `aprobar` copia frase y prompt sin mirarlos. Esperado: 422 y mazo intacto.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor, frase="X" * 200, prompt="corto")

    r = client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})

    assert r.status_code == 422, (
        f"esperado 422 (contenido fuera de contrato), obtenido {r.status_code}"
    )
    assert _cuantas_publicadas() == 0


@pytest.mark.parametrize("frase,prompt,esperado", [
    ("F" * FRASE_MAX, "p" * PROMPT_MIN, 200),        # los dos bordes de adentro
    ("F" * FRASE_MAX, "p" * PROMPT_MAX, 200),
    ("F" * (FRASE_MAX + 1), "p" * PROMPT_MIN, 422),  # …y los tres de afuera
    ("F" * FRASE_MAX, "p" * (PROMPT_MIN - 1), 422),
    ("F" * FRASE_MAX, "p" * (PROMPT_MAX + 1), 422),
])
def test_ok_los_limites_del_contrato_se_miran_al_aprobar(admin, frase, prompt, esperado):
    """El otro lado de BUG-B13-1, ya corregido: los cuatro bordes, uno por uno.

    Antes esto era un `test_nota_` que documentaba el daño (200 y una carta con
    frase de 200 caracteres publicada en el mazo). Ahora es el candado: los
    límites se miden donde el texto SE PUBLICA, no solo en el formulario del
    autor, y de a un borde por vez.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor, frase=frase, prompt=prompt)

    r = client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})

    assert r.status_code == esperado
    assert _cuantas_publicadas() == (1 if esperado == 200 else 0)


def test_bug_el_concepto_del_body_no_se_normaliza_a_kebab_case(admin):
    """El concepto es la huella de deduplicación semanal, no un título libre.

    Tomás escribe en un input; el CLI que valida el mazo exige `[a-z0-9-]+`.
    Esperado: normalizar (`gratitud-por-el-dia`) o rechazar con 422.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)

    r = client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin,
                    json={"concepto": "  Gratitud POR el Día!!  "})

    assert r.status_code == 200
    concepto = _carta_publicada().concepto
    assert concepto == concepto.lower(), f"concepto guardado tal cual: {concepto!r}"
    assert " " not in concepto


def test_bug_se_publica_una_propuesta_sin_cesion_aceptada(admin):
    """La cesión es el permiso legal para publicar lo que escribió otra persona.

    B1.1 la exige al proponer, pero el punto donde el texto SE PUBLICA no la
    mira. Esperado: 409 si `cesion_aceptada_at is None`.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor, cesion=False)

    r = client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})

    assert r.status_code == 409, f"se publicó sin cesión (status {r.status_code})"


def test_bug_aprobar_no_limpia_el_motivo_viejo(admin):
    """Aprobar cierra el recorrido: no puede quedar un reproche pegado.

    `rechazar` y `marcar_a_revisar` escriben `motivo`; `aprobar` es el único que
    no lo toca. Esperado: `motivo is None` después de aprobar.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor, motivo="La frase no cumple el canon.")

    r = client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})
    assert r.status_code == 200
    assert r.json()["estado"] == ESTADO_APROBADA

    mias = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR_SUB)).json()
    assert mias[0]["motivo"] is None, f"el autor ve: {mias[0]['motivo']!r}"


def test_ok_el_concepto_vacio_cae_al_respaldo_y_el_de_81_es_422(admin):
    """Nunca se publica una carta sin concepto, y el borde de 80 muerde.

    Sin concepto no hay dedupe semanal: el respaldo `com-<8 hex del id>` es
    correcto. 81 caracteres tiene que ser 422 (la columna es String(80)): un
    500 de Postgres acá sería un bug.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)

    assert client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin,
                       json={"concepto": "c" * 81}).status_code == 422
    assert _cuantas_publicadas() == 0

    assert client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin,
                       json={"concepto": "   "}).status_code == 200
    carta = _carta_publicada()
    assert carta.concepto and carta.concepto.startswith(PREFIJO_CARTA_COMUNIDAD)
    assert len(carta.id) == len(PREFIJO_CARTA_COMUNIDAD) + 8


def test_ok_aprobar_sin_body_funciona(admin):
    """El front puede no mandar body (`AprobarBody` es opcional): no puede ser 422."""
    autor = _usuario(AUTOR_SUB, apodo="Ana")
    pid = _sembrar(autor, firma=FIRMA_APODO)

    r = client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin)

    assert r.status_code == 200
    assert _carta_publicada().firma_publica == "Ana"


def test_ok_dos_aprobaciones_en_paralelo_publican_una_sola_carta(admin):
    """El `with_for_update` de `_propuesta` tiene que morder de verdad.

    Dos hilos golpean `aprobar` sobre la MISMA propuesta. Si el bloqueo no
    existiera, las dos leerían `revision_dwellia` y el mazo terminaría con la
    misma carta dos veces (y dos avisos al autor).
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    codigos = []

    def golpear():
        try:
            c = TestClient(app)
            codigos.append(
                c.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={}).status_code
            )
        except Exception as exc:  # noqa: BLE001 — que el hilo cuente qué le pasó
            codigos.append(repr(exc)[:300])

    hilos = [threading.Thread(target=golpear) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join(timeout=30)

    assert all(isinstance(c, int) for c in codigos), f"un hilo reventó: {codigos}"
    assert sorted(codigos) == [200, 409], f"códigos: {codigos}"
    assert _cuantas_publicadas() == 1
    assert len(_avisos(autor)) == 1


def test_ok_aprobar_de_nuevo_despues_de_aprobada_es_409(admin):
    """Secuencial, por si el paralelo se serializa solo: la segunda es 409."""
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    assert client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin,
                       json={}).status_code == 200
    r = client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})
    assert r.status_code == 409
    assert ESTADO_APROBADA in r.json()["detail"]
    assert _cuantas_publicadas() == 1


def test_ok_si_el_autor_borro_su_cuenta_la_propuesta_ya_no_existe(admin):
    """Borrar el usuario arrastra su propuesta (CASCADE) → decidir es 404, no 500.

    Es el caso "el autor se dio de baja mientras Tomás miraba la bandeja": el
    panel tiene una fila en pantalla que ya no está en la base.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.id == autor))
        s.commit()
        assert s.get(CartaComunidad, pid) is None

    for ruta, body in (("aprobar", {}), ("rechazar", {"motivo": "x"}),
                       ("a-revisar", {"sugerencia": "x"})):
        r = client.post(f"/api/admin/cartas/{pid}/{ruta}", headers=admin, json=body)
        assert r.status_code == 404, f"{ruta} → {r.status_code}"


def test_ok_la_carta_publicada_sobrevive_a_la_baja_del_autor(admin):
    """La carta es del mazo, la propuesta es del usuario.

    Si el autor se da de baja después de la aprobación: `cartas.autor_usuario_id`
    va a NULL (FK SET NULL) pero la carta sigue viva y `firma_publica` queda
    CONGELADA — la comunidad sigue leyendo "de Ana".
    """
    autor = _usuario(AUTOR_SUB, apodo="Ana")
    pid = _sembrar(autor, firma=FIRMA_APODO)
    client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})

    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.id == autor))
        s.commit()
        assert s.get(CartaComunidad, pid) is None

    carta = _carta_publicada()
    assert carta is not None
    assert carta.autor_usuario_id is None
    assert carta.firma_publica == "Ana"
    assert carta.origen == ORIGEN_COMUNIDAD


def test_ok_borrar_la_propuesta_aprobada_no_mata_la_carta(admin):
    """`cartas_comunidad.carta_id` es SET NULL, no CASCADE: la carta queda."""
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})

    with SessionLocal() as s:
        s.execute(delete(CartaComunidad).where(CartaComunidad.id == pid))
        s.commit()

    assert _cuantas_publicadas() == 1


def test_nota_no_se_puede_borrar_a_mano_una_carta_ya_entregada(admin):
    """DOCUMENTADO: `entregas.carta_id` es FK **sin** ondelete.

    Si Tomás quisiera bajar del mazo una carta de la comunidad que alguien ya
    recibió, el DELETE explota con ForeignKeyViolation. No hay hoy ningún camino
    para retirar una carta publicada: es deuda para B2.1/C (un `activa=false`, o
    `ondelete=SET NULL` en `entregas.carta_id` con el Baúl preparado).
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})
    carta_id = _carta_publicada().id

    with SessionLocal() as s:
        s.add(Entrega(usuario_id=autor, carta_id=carta_id))
        s.commit()
        with pytest.raises(Exception) as exc:
            s.execute(delete(Carta).where(Carta.id == carta_id))
            s.commit()
        s.rollback()
    assert "entregas_carta_id_fkey" in str(exc.value)


def test_nota_la_categoria_inexistente_la_frena_la_base(admin):
    """DOCUMENTADO: el escenario "la propuesta apunta a un pilar que ya no existe"
    NO se puede construir.

    `cartas_comunidad.categoria_slug` tiene FK a `categorias` sin ondelete, así
    que ni se puede insertar una propuesta con slug inválido ni se puede borrar
    la categoría mientras haya propuestas. El `None` defensivo de
    `admin._carta_previa` (categoría/acción nulas) es, por eso, inalcanzable.
    """
    autor = _usuario(AUTOR_SUB)
    with SessionLocal() as s:
        with pytest.raises(Exception) as exc:
            s.execute(
                text(
                    "insert into cartas_comunidad "
                    "(id,usuario_id,categoria_slug,accion_slug,frase,prompt,firma,"
                    " estado,created_at,updated_at) values "
                    "('qa13-bad',:u,'no-existe','contemplar',:f,:p,'anonima',"
                    " 'revision_dwellia',now(),now())"
                ),
                {"u": autor, "f": FRASE_OK, "p": PROMPT_OK},
            )
            s.commit()
        s.rollback()
    assert "cartas_comunidad_categoria_slug_fkey" in str(exc.value)


# ═════════════════════════════════════════════════════════════════════════════
# 3 · LA FIRMA (congelada al publicar vs. viva en la pantalla del autor)
# ═════════════════════════════════════════════════════════════════════════════
def test_bug_la_firma_que_ve_el_autor_no_es_la_que_lee_la_comunidad(admin):
    """La carta publicada lleva el apodo DE ENTONCES: la app tiene que decir lo mismo.

    `cartas_comunidad._firma_publica` y `admin._firma_publica` arman la carta de
    la propuesta desde el apodo actual; `aprobar` copió el apodo del momento a
    `cartas.firma_publica`. Una vez que existe `propuesta.carta_id`, la única
    verdad es la fila publicada.
    """
    autor = _usuario(AUTOR_SUB, apodo="Tomi")
    pid = _sembrar(autor, firma=FIRMA_APODO)
    client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})

    with SessionLocal() as s:
        u = s.get(Usuario, autor)
        u.apodo = "OtroApodo"
        s.add(u)
        s.commit()

    publicada = _carta_publicada().firma_publica
    assert publicada == "Tomi"          # congelada: esto está bien

    mias = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR_SUB)).json()
    panel = client.get("/api/admin/cartas?estado=todas", headers=admin).json()

    assert mias[0]["carta"]["firma_publica"] == publicada, (
        f"el autor ve {mias[0]['carta']['firma_publica']!r}, la comunidad {publicada!r}"
    )
    assert panel[0]["carta"]["firma_publica"] == publicada


def test_ok_un_apodo_de_40_entra_entero_en_la_firma(admin):
    """`usuarios.apodo` y `cartas.firma_publica` son String(40): el borde encaja.

    Y 41 no es construible: Postgres lo corta de raíz en `usuarios.apodo`, así
    que `firma_publica` nunca puede desbordar por ese camino.
    """
    apodo = "A" * 40
    autor = _usuario(AUTOR_SUB, apodo=apodo)
    pid = _sembrar(autor, firma=FIRMA_APODO)

    assert client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin,
                       json={}).status_code == 200
    assert _carta_publicada().firma_publica == apodo

    with SessionLocal() as s:
        with pytest.raises(Exception) as exc:
            s.execute(text("update usuarios set apodo=:a where id=:i"),
                      {"a": "B" * 41, "i": autor})
            s.commit()
        s.rollback()
    assert "character varying(40)" in str(exc.value)


# ═════════════════════════════════════════════════════════════════════════════
# 4 · RECHAZAR / A-REVISAR (los bordes del formulario y la evidencia del juez)
# ═════════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("largo,esperado", [(300, 200), (301, 422)])
def test_ok_el_motivo_mide_300_ya_strippeado(admin, largo, esperado):
    """El borde se mide sobre los caracteres útiles, no sobre los espacios."""
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    r = client.post(f"/api/admin/cartas/{pid}/rechazar", headers=admin,
                    json={"motivo": "   " + "m" * largo + "   "})
    assert r.status_code == esperado


@pytest.mark.parametrize("largo,esperado", [(500, 200), (501, 422)])
def test_ok_la_sugerencia_mide_500_ya_strippeada(admin, largo, esperado):
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "  " + "s" * largo + "  "})
    assert r.status_code == esperado


def test_ok_un_fix_que_no_es_objeto_es_422_no_500(admin):
    """`fix: "texto"` tiene que rebotar en el borde Pydantic."""
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "retoca", "fix": "texto suelto"})
    assert r.status_code == 422


def test_ok_las_claves_de_mas_en_el_fix_se_ignoran(admin):
    """`fix` con una clave inventada no rompe ni se filtra al veredicto.

    (La frase y el prompt del `fix` tienen que estar DENTRO del contrato: desde
    que BUG-B13-6 está corregido, una sugerencia inaplicable es 422. Acá se usan
    valores válidos porque lo que se prueba es la clave de más, no el largo.)
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "retoca",
                          "fix": {"frase": FRASE_OK, "prompt": PROMPT_OK,
                                  "inventada": 1}})
    assert r.status_code == 200
    assert r.json()["veredicto"]["fix_sugerido"] == {
        "frase": FRASE_OK, "prompt": PROMPT_OK,
    }


def test_bug_un_fix_vacio_no_se_normaliza_a_nada(admin):
    """Un fix sin frase ni prompt es "no hay sugerencia concreta", no un objeto.

    `routers/admin.py:a_revisar` hace `body.fix.model_dump()` a secas; el mismo
    dato pasado por el juez sale como `None`. Dos caminos, dos formas.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "retoca", "fix": {}})
    assert r.status_code == 200

    mias = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR_SUB)).json()
    assert mias[0]["sugerencia"] is None, (
        f"el autor recibe {json.dumps(mias[0]['sugerencia'])}"
    )


def test_bug_el_fix_admite_una_frase_que_el_autor_no_puede_reenviar(admin):
    """La sugerencia tiene que ser aplicable: si no, es una trampa para el autor.

    Camino completo del daño: a-revisar con `fix.frase` de FRASE_MAX+1 → el autor
    lo lee en Crear, lo copia, lo reenvía → 422 "La frase no puede pasar de
    FRASE_MAX caracteres".
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "acorta", "fix": {"frase": "F" * (FRASE_MAX + 1)}})
    assert r.status_code == 422, f"aceptó una frase de {FRASE_MAX + 1} ({r.status_code})"


@pytest.mark.parametrize("largo,esperado", [
    (PROMPT_MIN - 1, 422), (PROMPT_MIN, 200), (PROMPT_MAX, 200), (PROMPT_MAX + 1, 422),
])
def test_ok_el_fix_mide_el_prompt_con_el_rango_del_contrato(admin, largo, esperado):
    """La MISMA raíz que BUG-B13-6, del otro lado: el prompt sugerido.

    Antes era un `test_nota_` que documentaba el daño (un prompt de 10 pasaba con
    200 y el autor recibía como "sugerencia" algo más corto que el mínimo que su
    propio reenvío exige). Ahora es candado, y con los cuatro bordes.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "reescribe", "fix": {"prompt": "x" * largo}})
    assert r.status_code == esperado
    if esperado == 200:
        assert len(r.json()["veredicto"]["fix_sugerido"]["prompt"]) == largo


def test_bug_a_revisar_sin_fix_borra_la_sugerencia_del_juez(admin):
    """"Tomás decide, no borra evidencia" (docstring de `marcar_a_revisar`).

    El juez ya había redactado una frase/prompt de recambio; Tomás agrega su
    comentario y esa sugerencia desaparece de la pantalla del autor.
    """
    autor = _usuario(AUTOR_SUB)
    del_juez = {"frase": "la que propuso el juez", "prompt": "el prompt del juez"}
    pid = _sembrar(autor, veredicto={
        "resultado": "requiere_revision",
        "hallazgos": [{"regla": "R5", "mayor": True, "detalle": "muy parecida"}],
        "concepto": "gratitud-simple", "fix_sugerido": del_juez,
        "motivo": "se parece a otra", "fuente": "juez",
    })

    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "acorta la frase"})
    assert r.status_code == 200

    mias = client.get("/api/cartas-comunidad/mias", headers=_headers(AUTOR_SUB)).json()
    assert mias[0]["sugerencia"] == del_juez, (
        f"la sugerencia del juez quedó en {mias[0]['sugerencia']!r}"
    )


def test_ok_a_revisar_conserva_hallazgos_y_resultado_del_juez(admin):
    """Lo que SÍ se conserva: `resultado` y `hallazgos` crudos (y `fuente` pasa a dwellia)."""
    autor = _usuario(AUTOR_SUB)
    hallazgos = [{"regla": "R7", "mayor": False, "detalle": "muletilla"}]
    pid = _sembrar(autor, veredicto={"resultado": "requiere_revision",
                                     "hallazgos": hallazgos, "fuente": "juez"})
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "retoca"})
    ver = r.json()["veredicto"]
    assert ver["resultado"] == "requiere_revision"
    assert ver["hallazgos"] == hallazgos
    assert ver["fuente"] == "dwellia"


@pytest.mark.parametrize("estado", [ESTADO_A_REVISAR, ESTADO_APROBADA,
                                    ESTADO_RECHAZADA, ESTADO_RETIRADA])
def test_ok_a_revisar_desde_un_estado_cerrado_es_409(admin, estado):
    """Incluye el caso que faltaba: a-revisar sobre una que YA está `a_revisar`."""
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor, estado=estado)
    r = client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                    json={"sugerencia": "x"})
    assert r.status_code == 409
    assert estado in r.json()["detail"]


@pytest.mark.parametrize("estado", [ESTADO_APROBADA, ESTADO_RECHAZADA, ESTADO_RETIRADA])
def test_ok_rechazar_desde_un_estado_cerrado_es_409(admin, estado):
    """Una aprobada (ya en el mazo) o una retirada por el autor no se rechazan."""
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor, estado=estado)
    r = client.post(f"/api/admin/cartas/{pid}/rechazar", headers=admin,
                    json={"motivo": "no"})
    assert r.status_code == 409


@pytest.mark.parametrize("estado", [ESTADO_A_REVISAR, ESTADO_RETIRADA, ESTADO_RECHAZADA])
def test_ok_aprobar_desde_un_estado_no_habilitado_es_409_y_no_publica(admin, estado):
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor, estado=estado)
    assert client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin,
                       json={}).status_code == 409
    assert _cuantas_publicadas() == 0


# ═════════════════════════════════════════════════════════════════════════════
# 5 · AVISOS (uno por transición, y qué pasa si el push se cae)
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_cada_transicion_deja_exactamente_un_aviso_a_la_propuesta(admin):
    """Un aviso por decisión, ni cero ni dos, y siempre apuntando a la propuesta."""
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)

    client.post(f"/api/admin/cartas/{pid}/a-revisar", headers=admin,
                json={"sugerencia": "retoca"})
    assert len(_avisos(autor)) == 1

    client.post(f"/api/admin/cartas/{pid}/rechazar", headers=admin, json={"motivo": "no"})
    avisos = _avisos(autor)
    assert len(avisos) == 2
    assert {a.tipo for a in avisos} == {AVISO_CARTA_ESTADO}
    assert {a.referencia_id for a in avisos} == {pid}
    assert all(not a.leido for a in avisos)


def test_ok_aprobar_avisa_una_sola_vez(admin):
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})
    avisos = _avisos(autor)
    assert len(avisos) == 1
    assert avisos[0].referencia_id == pid
    assert "cargada" in avisos[0].texto.lower()


def test_bug_un_push_que_levanta_tumba_la_aprobacion(admin, monkeypatch):
    """La buena noticia: es atómico (no queda media carta publicada).

    La mala: el resultado es un 500 y una aprobación perdida. `push.enviar_push`
    hoy no levanta nunca, pero `crear_aviso` confía en eso sin red — y encima
    hace I/O de red con el `FOR UPDATE` de la propuesta tomado.
    Esperado: 200, carta publicada, aviso guardado; el push es best-effort.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    with SessionLocal() as s:
        s.add(PushSuscripcion(usuario_id=autor, endpoint="https://push.qa13/x",
                              p256dh="k", auth="a"))
        s.commit()

    def _revienta(*_a, **_k):
        raise RuntimeError("push service caído")

    monkeypatch.setattr(avisos_mod, "enviar_push", _revienta)
    r = client_500.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})

    assert r.status_code == 200, f"obtenido {r.status_code}"
    assert _cuantas_publicadas() == 1
    assert len(_avisos(autor)) == 1   # el aviso queda: lo best-effort es el push


def test_ok_si_el_aviso_explota_no_queda_la_carta_a_medio_publicar(admin, monkeypatch):
    """El otro lado de BUG-B13-7, que SÍ está bien y NO se rompió al arreglarlo: todo o nada.

    El push pasó a ser best-effort (ya no tumba la aprobación), pero el AVISO
    sigue siendo parte de la transacción: si escribirlo falla de verdad, la
    sesión se cierra sin commit y no queda ni la carta en `cartas`, ni el estado
    `aprobada`, ni el aviso. Media aprobación no existe.

    Por eso acá se revienta `crear_aviso` (la escritura), no `enviar_push` (la
    red): el escenario se CONSTRUYE sobre lo que sigue siendo crítico.
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)

    def _revienta(*_a, **_k):
        raise RuntimeError("la tabla avisos no responde")

    monkeypatch.setattr(avisos_mod, "crear_aviso", _revienta)
    client_500.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})

    with SessionLocal() as s:
        assert s.get(CartaComunidad, pid).estado == ESTADO_REVISION_DWELLIA
    assert _cuantas_publicadas() == 0
    assert _avisos(autor) == []


# ═════════════════════════════════════════════════════════════════════════════
# 6 · LISTADO Y COMENTARIOS
# ═════════════════════════════════════════════════════════════════════════════
@pytest.mark.parametrize("valor,esperado", [
    ("", 422), ("APROBADA", 422), ("Aprobada", 422), ("todas", 200),
    ("aprobada", 200), ("en_revision", 200),
])
def test_ok_el_filtro_de_estado_es_una_lista_positiva_cerrada(admin, valor, esperado):
    """El vocabulario es cerrado y en minúscula: nada de "casi" un estado.

    `estado=` vacío y `estado=APROBADA` son 422 con el listado de válidos en el
    detalle, no un listado silencioso de todo.
    """
    r = client.get(f"/api/admin/cartas?estado={valor}", headers=admin)
    assert r.status_code == esperado
    if esperado == 422:
        assert "Estado desconocido" in r.json()["detail"]


def _de_este_qa(items: list) -> list:
    """Los ítems de la bandeja que son de ESTE módulo (autores `qa13|…`).

    WS27 · B2.1: la base es compartida y el `make demo-seed` del Q/A visual deja
    las propuestas de los usuarios `demo|` (el `conftest` los preserva a
    propósito). Contar la bandeja entera dejó de probar lo que este test quiere
    probar; contar lo propio, sí.
    """
    return [i for i in items if (i["autor"]["email"] or "").startswith(MARCA)]


def test_ok_un_autor_sin_apodo_ni_nombre_no_rompe_la_bandeja(admin):
    """Y el ítem NO lleva el `usuario_id` del autor (solo apodo/email/nombre).

    El email sí viaja: es el panel de administración y Tomás necesita saber a
    quién le está por publicar una carta.
    """
    autor = _usuario(AUTOR_SUB)
    _sembrar(autor)
    items = _de_este_qa(client.get("/api/admin/cartas", headers=admin).json())
    assert len(items) == 1
    assert items[0]["autor"] == {
        "apodo": None, "email": f"{AUTOR_SUB}@mindful.local", "nombre": None,
    }
    assert autor not in json.dumps(items, default=str)


def test_ok_el_admin_no_es_superusuario_en_las_cartas_del_autor(admin):
    """`/api/cartas-comunidad/mias` es de B1.1 y filtra por usuario, siempre.

    Ser administración habilita `/api/admin`, no ver el Mundo 2 ajeno.
    """
    otro = _usuario(MARCA + "otro")
    _sembrar(otro)
    _usuario(ADMIN_SUB)

    assert client.get("/api/cartas-comunidad/mias", headers=admin).json() == []
    assert len(_de_este_qa(client.get("/api/admin/cartas", headers=admin).json())) == 1


@pytest.mark.parametrize("valor", ["abc", "0", "-1", "501", "1.5", ""])
def test_ok_un_limit_invalido_en_comentarios_es_422(admin, valor):
    assert client.get(f"/api/admin/comentarios?limit={valor}",
                      headers=admin).status_code == 422


def test_ok_un_comentario_de_150_emojis_y_sin_estrellas_se_lee_entero(admin):
    """El feedback puede ser 150 emojis y sin puntuar: no puede romper el panel.

    Y la lista sigue sin exponer `usuario_id` ni el email de quien comentó.
    """
    lector = _usuario(LECTOR_SUB, apodo="Pipo")
    with SessionLocal() as s:
        carta_id = s.scalar(select(Carta.id).where(Carta.origen == ORIGEN_DWELLIA).limit(1))
        s.add(Entrega(usuario_id=lector, carta_id=carta_id,
                      comentario_carta="🙂" * 150, estrellas=None))
        s.commit()

    filas = client.get("/api/admin/comentarios", headers=admin).json()
    mio = [f for f in filas if f["comentario"].startswith("🙂")]
    assert len(mio) == 1
    assert len(mio[0]["comentario"]) == 150
    assert mio[0]["estrellas"] is None
    assert mio[0]["apodo"] == "Pipo"
    crudo = json.dumps(filas, default=str)
    assert lector not in crudo and "@mindful.local" not in crudo


# ═════════════════════════════════════════════════════════════════════════════
# 7 · APROBAR ES CARGAR DE VERDAD: el seed no la borra y el motor la sirve
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_el_seed_no_pisa_la_carta_publicada(admin):
    """`seed()` corre en CADA deploy: la carta de la comunidad tiene que sobrevivir
    intacta, con su origen, su autor y su firma.

    Se corre el seed de verdad (el mismo que ejecuta el job `dwellia-migrate`).
    """
    autor = _usuario(AUTOR_SUB, apodo="Ana")
    pid = _sembrar(autor, firma=FIRMA_APODO)
    client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin,
                json={"concepto": "qa13-concepto-unico"})

    antes = _carta_publicada()
    huella = (antes.id, antes.origen, antes.autor_usuario_id,
              antes.firma_publica, antes.concepto, antes.frase, antes.prompt)

    seed_mod.seed()

    with SessionLocal() as s:
        d = s.get(Carta, huella[0])
        assert d is not None, "el seed borró la carta de la comunidad"
        assert (d.id, d.origen, d.autor_usuario_id, d.firma_publica,
                d.concepto, d.frase, d.prompt) == huella
        assert s.scalar(select(func.count()).select_from(Carta)) == 78


def test_ok_la_carta_aprobada_la_sirve_de_verdad_carta_del_dia(admin):
    """APROBAR = CARGAR: la prueba no es el estado, es que el motor la entregue.

    El escenario se CONSTRUYE (no se busca): un lector con siete entregas, las
    seis últimas cubriendo los cinco pilares que no son el de la carta (así el
    pilar del día es forzosamente ese), y la entrega de hace 7 días cargando en
    `descartadas` TODAS las cartas de Dwellia de ese pilar (entran a la ventana
    de 7 días de "ya vistas" pero quedan fuera de la ventana de rotación de 6).
    Resultado: la única fresca del pilar es la carta de la comunidad.

    De paso queda documentado que la recibe un lector cualquiera, en un día que
    NO es comodín. Cuando se escribió este test eso era "lo esperado hasta B2.1";
    B2.1 lo volvió LA regla: las aprobadas se reparten como iguales, sin
    interruptor y sin exclusiones (WS27 §6), y la columna `usuarios.recibe_comunidad`
    dejó de existir.
    """
    autor = _usuario(AUTOR_SUB, apodo="Ana")
    pid = _sembrar(autor, firma=FIRMA_APODO, categoria="gratitud", accion="contemplar")
    client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin,
                json={"concepto": "qa13-concepto-unico"})
    com_id = _carta_publicada().id

    lector = _usuario(LECTOR_SUB)
    with SessionLocal() as s:
        dwellia_del_pilar = [
            c.id for c in s.scalars(
                select(Carta).where(Carta.categoria_slug == "gratitud",
                                    Carta.origen == ORIGEN_DWELLIA)
            ).all()
        ]
        otros = sorted({c for c in s.scalars(select(Categoria.slug)).all()} - {"gratitud"})
        ahora = datetime.now(timezone.utc)
        entregas = []
        for i, dia in enumerate(range(7, 0, -1)):
            cat = otros[i % len(otros)]
            cid = s.scalar(select(Carta.id).where(Carta.categoria_slug == cat).limit(1))
            e = Entrega(usuario_id=lector, carta_id=cid,
                        fecha=ahora - timedelta(days=dia))
            s.add(e)
            entregas.append(e)
        s.flush()
        entregas[0].descartadas = dwellia_del_pilar   # la de hace 7 días
        s.add(entregas[0])
        s.commit()

    r = client.get("/api/carta-del-dia", headers=_headers(LECTOR_SUB))
    assert r.status_code == 200
    carta = r.json()["carta"]
    assert carta["id"] == com_id, f"sirvió {carta['id']}, no la de la comunidad"
    assert carta["origen"] == ORIGEN_COMUNIDAD
    assert carta["firma_publica"] == "Ana"


def test_ok_la_carta_publicada_entra_al_pool_que_arma_el_motor(admin):
    """El respaldo estructural del test de arriba: el pool es `select(Carta)` entero.

    Si mañana alguien filtra el pool por `origen` sin tocar B2.1, este candado
    avisa antes de que "aprobar" deje de significar "cargado".
    """
    autor = _usuario(AUTOR_SUB)
    pid = _sembrar(autor)
    client.post(f"/api/admin/cartas/{pid}/aprobar", headers=admin, json={})
    com_id = _carta_publicada().id

    with SessionLocal() as s:
        pool = {c.id for c in s.scalars(select(Carta)).all()}
    assert com_id in pool
    assert len(pool) == 78

    resumen = client.get("/api/contenido/resumen").json()
    assert resumen["cartas"] == 78


# ═════════════════════════════════════════════════════════════════════════════
# 8 · CIERRE: la base queda como estaba
# ═════════════════════════════════════════════════════════════════════════════
def test_ok_zz_la_base_queda_en_77_y_sin_usuarios_qa13():
    """Último test del módulo: el Q/A no deja rastro.

    (Se ejecuta al final por el `zz` del nombre; pytest respeta el orden del
    archivo, pero el nombre lo deja explícito para quien lo lea.)
    """
    with SessionLocal() as s:
        assert s.scalar(select(func.count()).select_from(Carta)) == 77
        assert s.scalar(
            select(func.count()).select_from(Carta).where(Carta.origen != ORIGEN_DWELLIA)
        ) == 0
        assert s.scalar(
            select(func.count()).select_from(Usuario)
            .where(Usuario.firebase_uid.like(MARCA + "%"))
        ) == 0
        assert s.scalar(
            select(func.count()).select_from(Usuario)
            .where(Usuario.firebase_uid.in_(UIDS_DE_REBOTE))
        ) == 0
        # Las propuestas de ESTE módulo. (Antes se contaba la tabla entera; desde
        # B2.1 el `make demo-seed` deja las de los `demo|`, que el conftest
        # preserva: lo que este test tiene que probar es que el Q/A no dejó
        # rastro, no que nadie más escribió nunca una carta.)
        assert s.scalar(
            select(func.count()).select_from(CartaComunidad)
            .join(Usuario, Usuario.id == CartaComunidad.usuario_id)
            .where(Usuario.firebase_uid.like(MARCA + "%"))
        ) == 0
