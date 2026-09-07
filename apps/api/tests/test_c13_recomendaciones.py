"""WS29 · C1.3 · Recomendaciones (premium) y su lugar en el Baúl y la vitrina.

Tres cosas se prueban acá:

1. **El candado del plan.** Escribir una recomendación es de quienes son parte;
   LEER lo propio no. Un premium vencido sigue viendo lo suyo en el Baúl y
   recibe 403 recién cuando quiere tocarlo.
2. **Los límites que muerden de verdad.** Título, tipo, texto, enlace,
   visibilidad y el tope de 30 — con los bordes exactos (80 y 500 pasan; 81 y
   501 no) y el mensaje en español.
3. **La mezcla.** El Baúl deja de ser solo Pausas y la vitrina ajena muestra
   solo lo COMPARTIDO, con `de` y sin una sola letra del email de nadie.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import delete, select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import (
    RECOMENDACION_TEXTO_MAX,
    RECOMENDACION_TITULO_MAX,
    RECOMENDACIONES_MAX,
    Carta,
    Entrega,
    Recomendacion,
    Usuario,
)
from mindful_api.main import app

client = TestClient(app)
PREFIJO = "c13|"


# ── Herramientas ─────────────────────────────────────────────────────────────

def _h(sub: str) -> dict:
    return {"X-Debug-Sub": PREFIJO + sub, "X-Debug-Email": f"{sub}@c13.local"}


def _usuario(s, sub: str, premium: bool = True, vencido: bool = False, **campos) -> Usuario:
    """Premium por defecto: casi todo lo de esta card lo es. `vencido` deja el
    plan en "premium" con la fecha en el pasado (el caso que más importa)."""
    u = s.scalar(select(Usuario).where(Usuario.firebase_uid == PREFIJO + sub))
    if u is None:
        u = Usuario(firebase_uid=PREFIJO + sub, email=f"{sub}@c13.local", apodo=sub.title())
        s.add(u)
    u.terminos_aceptados_at = datetime.now(timezone.utc)
    if vencido:
        u.plan = "premium"
        u.plan_hasta = datetime.now(timezone.utc) - timedelta(days=1)
    elif premium:
        u.plan = "premium"
        u.plan_hasta = datetime.now(timezone.utc) + timedelta(days=30)
    else:
        u.plan = "free"
        u.plan_hasta = None
    for k, v in campos.items():
        setattr(u, k, v)
    s.commit()
    s.refresh(u)
    return u


def _pausa(s, duenio, visibilidad="compartida", fecha=None, estrellas=None) -> Entrega:
    carta_id = s.scalar(select(Carta.id).order_by(Carta.id).limit(1))
    e = Entrega(
        usuario_id=duenio.id, carta_id=carta_id, completada=True,
        visibilidad=visibilidad, reflexion="c13", estrellas=estrellas,
    )
    if fecha is not None:
        e.fecha = fecha
    s.add(e)
    s.commit()
    s.refresh(e)
    return e


def _crear(sub: str, **campos) -> "tuple[int, dict]":
    cuerpo = {"titulo": "Un libro", "tipo": "libro", "texto": "Me hizo bien."}
    cuerpo.update(campos)
    r = client.post("/api/recomendaciones", headers=_h(sub), json=cuerpo)
    return r.status_code, (r.json() if r.content else {})


def _fechar(rec_id: str, cuando: datetime) -> None:
    """Mueve la fecha de una recomendación ya creada: así el orden del Baúl se
    prueba con distancias de días y no con milisegundos."""
    with SessionLocal() as s:
        rec = s.get(Recomendacion, rec_id)
        rec.created_at = cuando
        s.commit()


@pytest.fixture(autouse=True)
def _limpio():
    with SessionLocal() as s:
        s.execute(delete(Usuario).where(Usuario.firebase_uid.like(PREFIJO + "%")))
        s.commit()
    yield


# ── 1 · El candado del plan ──────────────────────────────────────────────────

def test_free_no_puede_ni_leer_ni_escribir_recomendaciones():
    with SessionLocal() as s:
        _usuario(s, "free", premium=False)

    esperado = "Las recomendaciones son de quienes son parte."
    r = client.get("/api/recomendaciones", headers=_h("free"))
    assert r.status_code == 403 and r.json()["detail"] == esperado

    codigo, cuerpo = _crear("free")
    assert codigo == 403 and cuerpo["detail"] == esperado

    r = client.put("/api/recomendaciones/lo-que-sea", headers=_h("free"),
                   json={"texto": "otra cosa"})
    assert r.status_code == 403
    r = client.delete("/api/recomendaciones/lo-que-sea", headers=_h("free"))
    assert r.status_code == 403
    r = client.put("/api/recomendaciones/lo-que-sea/visibilidad", headers=_h("free"),
                   json={"visibilidad": "compartida"})
    assert r.status_code == 403


def test_premium_crea_y_lista_lo_suyo():
    with SessionLocal() as s:
        _usuario(s, "ana")

    codigo, item = _crear("ana", titulo="  Meditar a diario  ", tipo="podcast",
                          texto="  Veinte minutos.  ", url=" https://ejemplo.org/x ")
    assert codigo == 201, item
    # La forma del contrato C0 §4.3, completa y sin nada de más.
    assert item["tipo"] == "recomendacion"
    assert item["titulo"] == "Meditar a diario"      # strip
    assert item["tipo_recomendacion"] == "podcast"
    assert item["texto"] == "Veinte minutos."
    assert item["url"] == "https://ejemplo.org/x"
    assert item["visibilidad"] == "privada"          # default seguro
    assert item["de"] is None                         # es mía
    assert item["id"] and item["fecha"]

    r = client.get("/api/recomendaciones", headers=_h("ana"))
    assert r.status_code == 200
    lista = r.json()
    assert [i["id"] for i in lista] == [item["id"]]

    # Orden: la más nueva primero.
    _, segunda = _crear("ana", titulo="Otra")
    lista = client.get("/api/recomendaciones", headers=_h("ana")).json()
    assert [i["id"] for i in lista] == [segunda["id"], item["id"]]


# ── 2 · Los límites ──────────────────────────────────────────────────────────

def test_validaciones_con_mensaje_en_espaniol():
    with SessionLocal() as s:
        _usuario(s, "val")

    codigo, cuerpo = _crear("val", titulo="   ")
    assert codigo == 422 and cuerpo["detail"] == "Falta el título."

    codigo, cuerpo = _crear("val", titulo="x" * (RECOMENDACION_TITULO_MAX + 1))
    assert codigo == 422
    assert cuerpo["detail"] == "El título no puede tener más de 80 caracteres."

    codigo, cuerpo = _crear("val", tipo="pelicula")
    assert codigo == 422 and "libro" in cuerpo["detail"]

    codigo, cuerpo = _crear("val", texto="")
    assert codigo == 422 and cuerpo["detail"] == "Falta el texto."

    codigo, cuerpo = _crear("val", texto="x" * (RECOMENDACION_TEXTO_MAX + 1))
    assert codigo == 422
    assert cuerpo["detail"] == "El texto no puede tener más de 500 caracteres."

    codigo, cuerpo = _crear("val", url="http://inseguro.example")
    assert codigo == 422 and cuerpo["detail"] == "El enlace debe empezar con https://"

    codigo, cuerpo = _crear("val", visibilidad="secreta")
    assert codigo == 422 and "privada" in cuerpo["detail"]

    # El enlace es opcional: vacío (o solo espacios) es None, no un error.
    codigo, item = _crear("val", url="   ")
    assert codigo == 201 and item["url"] is None
    codigo, item = _crear("val", url=None)
    assert codigo == 201 and item["url"] is None


def test_los_bordes_exactos_pasan():
    with SessionLocal() as s:
        _usuario(s, "borde")

    codigo, item = _crear(
        "borde",
        titulo="t" * RECOMENDACION_TITULO_MAX,
        texto="x" * RECOMENDACION_TEXTO_MAX,
        tipo="documental",
        visibilidad="compartida",
    )
    assert codigo == 201, item
    assert len(item["titulo"]) == 80 and len(item["texto"]) == 500
    assert item["visibilidad"] == "compartida"


def test_el_tope_son_treinta_y_se_libera_al_borrar():
    with SessionLocal() as s:
        _usuario(s, "tope")

    ids = []
    for n in range(RECOMENDACIONES_MAX):
        codigo, item = _crear("tope", titulo=f"Numero {n}")
        assert codigo == 201, item
        ids.append(item["id"])

    codigo, cuerpo = _crear("tope", titulo="La treinta y uno")
    assert codigo == 409
    assert cuerpo["detail"] == "Ya tienes 30 recomendaciones, el máximo."
    assert len(client.get("/api/recomendaciones", headers=_h("tope")).json()) == 30

    # Se libera un lugar y entra otra: el tope cuenta lo que HAY, no lo que hubo.
    assert client.delete(f"/api/recomendaciones/{ids[0]}", headers=_h("tope")).status_code == 204
    codigo, _ = _crear("tope", titulo="Ahora si")
    assert codigo == 201
    assert len(client.get("/api/recomendaciones", headers=_h("tope")).json()) == 30


# ── 3 · Editar ───────────────────────────────────────────────────────────────

def test_put_parcial_conserva_el_resto_y_valida_igual():
    with SessionLocal() as s:
        _usuario(s, "edito")

    _, item = _crear("edito", titulo="Original", tipo="video",
                     texto="Antes", url="https://uno.example", visibilidad="compartida")

    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("edito"),
                   json={"texto": "Después"})
    assert r.status_code == 200
    puesto = r.json()
    assert puesto["texto"] == "Después"
    # Lo que no viene, no se toca.
    assert puesto["titulo"] == "Original"
    assert puesto["tipo_recomendacion"] == "video"
    assert puesto["url"] == "https://uno.example"
    assert puesto["visibilidad"] == "compartida"

    # Las mismas validaciones que al crear.
    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("edito"),
                   json={"titulo": "x" * 81})
    assert r.status_code == 422
    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("edito"),
                   json={"url": "ftp://viejo.example"})
    assert r.status_code == 422
    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("edito"),
                   json={"tipo": "cancion"})
    assert r.status_code == 422
    # El enlace se puede sacar sin borrar la recomendación.
    r = client.put(f"/api/recomendaciones/{item['id']}", headers=_h("edito"),
                   json={"url": ""})
    assert r.status_code == 200 and r.json()["url"] is None


def test_la_visibilidad_tiene_su_propia_puerta():
    with SessionLocal() as s:
        _usuario(s, "visi")

    _, item = _crear("visi")
    assert item["visibilidad"] == "privada"

    r = client.put(f"/api/recomendaciones/{item['id']}/visibilidad", headers=_h("visi"),
                   json={"visibilidad": "compartida"})
    assert r.status_code == 200
    assert r.json()["visibilidad"] == "compartida" and r.json()["tipo"] == "recomendacion"

    r = client.put(f"/api/recomendaciones/{item['id']}/visibilidad", headers=_h("visi"),
                   json={"visibilidad": "publica"})
    assert r.status_code == 422


# ── 4 · Aislamiento ──────────────────────────────────────────────────────────

def test_la_recomendacion_de_otro_no_existe_para_mi():
    with SessionLocal() as s:
        _usuario(s, "mia")
        _usuario(s, "ajena")

    _, item = _crear("mia", titulo="Solo mia")

    # Ajena e inexistente dan lo MISMO: 404 y el mismo mensaje.
    for pedido in (
        lambda i: client.put(f"/api/recomendaciones/{i}", headers=_h("ajena"),
                             json={"texto": "te la edito"}),
        lambda i: client.delete(f"/api/recomendaciones/{i}", headers=_h("ajena")),
        lambda i: client.put(f"/api/recomendaciones/{i}/visibilidad", headers=_h("ajena"),
                             json={"visibilidad": "compartida"}),
    ):
        r = pedido(item["id"])
        assert r.status_code == 404
        assert r.json()["detail"] == "No encontramos esta recomendación."
        assert pedido("no-existe").status_code == 404

    # Y no aparece en su lista ni en su Baúl.
    assert client.get("/api/recomendaciones", headers=_h("ajena")).json() == []
    assert "Solo mia" not in client.get("/api/baul", headers=_h("ajena")).text
    # La mía sigue intacta.
    assert client.get("/api/recomendaciones", headers=_h("mia")).json()[0]["titulo"] == "Solo mia"


# ── 5 · El Baúl ──────────────────────────────────────────────────────────────

def test_el_baul_mezcla_pausas_y_recomendaciones_por_fecha():
    ahora = datetime.now(timezone.utc)
    with SessionLocal() as s:
        yo = _usuario(s, "baul")
        _pausa(s, yo, fecha=ahora - timedelta(days=3))   # la más vieja
        _pausa(s, yo, fecha=ahora - timedelta(days=1))

    _, vieja = _crear("baul", titulo="Reco vieja")
    _fechar(vieja["id"], ahora - timedelta(days=2))
    _, nueva = _crear("baul", titulo="Reco nueva")
    _fechar(nueva["id"], ahora)

    baul = client.get("/api/baul", headers=_h("baul")).json()
    assert len(baul) == 4
    # Todo ítem se sabe nombrar, y el orden es puramente cronológico.
    assert [i["tipo"] for i in baul] == ["recomendacion", "pausa", "recomendacion", "pausa"]
    assert baul[0]["id"] == nueva["id"] and baul[2]["id"] == vieja["id"]
    # La recomendación llega entera y sin dueño (es mía).
    assert baul[0]["titulo"] == "Reco nueva" and baul[0]["de"] is None


def test_con_orden_valoradas_las_recomendaciones_van_al_fondo():
    ahora = datetime.now(timezone.utc)
    with SessionLocal() as s:
        yo = _usuario(s, "estrellas")
        # Pausa vieja PERO valorada: manda la estrella, no la fecha.
        _pausa(s, yo, fecha=ahora - timedelta(days=9), estrellas=5)
        _pausa(s, yo, fecha=ahora - timedelta(days=8), estrellas=2)

    _, reco = _crear("estrellas", titulo="Reco de hoy")
    _fechar(reco["id"], ahora)

    baul = client.get("/api/baul?orden=valoradas", headers=_h("estrellas")).json()
    assert [i["tipo"] for i in baul] == ["pausa", "pausa", "recomendacion"]
    assert [i["estrellas"] for i in baul[:2]] == [5, 2]
    assert baul[-1]["id"] == reco["id"]


def test_premium_vencido_sigue_viendo_lo_suyo_pero_no_puede_escribir():
    with SessionLocal() as s:
        _usuario(s, "vencido")

    _, item = _crear("vencido", titulo="La escribi cuando era premium")
    assert item["id"]

    with SessionLocal() as s:
        _usuario(s, "vencido", vencido=True)

    # Leer lo propio no es premium: el Baúl la sigue mostrando.
    baul = client.get("/api/baul", headers=_h("vencido")).json()
    assert [i["id"] for i in baul] == [item["id"]]
    assert baul[0]["titulo"] == "La escribi cuando era premium"

    # Escribir sí lo es.
    codigo, cuerpo = _crear("vencido", titulo="Otra mas")
    assert codigo == 403
    assert cuerpo["detail"] == "Las recomendaciones son de quienes son parte."
    assert client.delete(f"/api/recomendaciones/{item['id']}",
                         headers=_h("vencido")).status_code == 403
    # Y el listado propio también está detrás del candado.
    assert client.get("/api/recomendaciones", headers=_h("vencido")).status_code == 403


# ── 6 · La vitrina ───────────────────────────────────────────────────────────

def test_la_vitrina_ajena_muestra_solo_las_compartidas_y_con_de():
    ahora = datetime.now(timezone.utc)
    with SessionLocal() as s:
        duenio = _usuario(s, "publico", perfil_publico=True)
        _usuario(s, "curiosa", premium=False)
        _pausa(s, duenio, fecha=ahora - timedelta(days=1))
        duenio_id = duenio.id

    _, publicada = _crear("publico", titulo="Esto lo comparto", visibilidad="compartida")
    _fechar(publicada["id"], ahora)
    _, guardada = _crear("publico", titulo="Esto me lo guardo", visibilidad="privada")

    r = client.get(f"/api/fichas/de/{duenio_id}", headers=_h("curiosa"))
    assert r.status_code == 200
    fichas = r.json()["fichas"]
    assert [f["tipo"] for f in fichas] == ["recomendacion", "pausa"]   # mezcla por fecha
    assert fichas[0]["id"] == publicada["id"]
    # Lleva `de` (quién la recomendó), nunca el email de nadie.
    assert fichas[0]["de"]["usuario_id"] == duenio_id
    assert fichas[0]["de"]["apodo"] == "Publico"
    assert "email" not in fichas[0]["de"] and "@c13.local" not in r.text
    # La privada no sale ni por asomo.
    assert guardada["id"] not in [f["id"] for f in fichas]
    assert "Esto me lo guardo" not in r.text

    # Mi propia vitrina es "como me ven": tampoco muestra las privadas.
    mia = client.get(f"/api/fichas/de/{duenio_id}", headers=_h("publico")).json()
    assert [f["id"] for f in mia["fichas"] if f["tipo"] == "recomendacion"] == [publicada["id"]]


def test_un_perfil_privado_sin_vinculo_no_muestra_ni_una_recomendacion():
    with SessionLocal() as s:
        duenio = _usuario(s, "reservado")   # perfil_publico = False por defecto
        _usuario(s, "extranio", premium=False)
        duenio_id = duenio.id

    _, publicada = _crear("reservado", titulo="Compartida igual", visibilidad="compartida")

    r = client.get(f"/api/fichas/de/{duenio_id}", headers=_h("extranio"))
    assert r.status_code == 200
    assert r.json()["fichas"] is None          # cerrado, no vacío
    assert publicada["titulo"] not in r.text
    assert "@c13.local" not in r.text
