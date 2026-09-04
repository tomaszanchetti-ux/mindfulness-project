"""M4 Baúl + M5 Compartir: lectura, visibilidad, borrado real, regalo y muerte del link."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mindful_api.main import app

client = TestClient(app)


def _onboard(sub: str) -> dict:
    h = {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}
    client.put("/api/perfil", headers=h, json={"aceptar_terminos": True})
    return h


def _entrega_de_hoy(h: dict) -> str:
    return client.get("/api/carta-del-dia", headers=h).json()["entrega"]["id"]


def test_baul_lista_y_ordenes():
    h = _onboard("baul|lectura")
    eid = _entrega_de_hoy(h)
    client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"estrellas": 4})

    r = client.get("/api/baul", headers=h)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["estrellas"] == 4
    assert "carta" in items[0] and "fotos" in items[0]

    # Los dos modos de orden responden 200.
    assert client.get("/api/baul?orden=reciente", headers=h).status_code == 200
    assert client.get("/api/baul?orden=valoradas", headers=h).status_code == 200
    # Orden inválido → 422.
    assert client.get("/api/baul?orden=loquesea", headers=h).status_code == 422


def test_baul_no_lista_entrega_sin_vivir():
    # La carta del día entregada pero aún no completada NO aparece en el Baúl.
    h = _onboard("baul|sinvivir")
    _entrega_de_hoy(h)
    assert client.get("/api/baul", headers=h).json() == []


def test_borrado_real():
    h = _onboard("baul|borrado")
    eid = _entrega_de_hoy(h)
    # El Baúl solo lista pausas vividas: hay que cerrar el ritual antes de verla.
    client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"completada": True})
    assert len(client.get("/api/baul", headers=h).json()) == 1

    r = client.delete(f"/api/baul/{eid}", headers=h)
    assert r.status_code == 204
    assert client.get("/api/baul", headers=h).json() == []  # para siempre, sin papelera


def test_compartir_la_ficha_entera_y_el_receptor_la_abre_con_su_sesion():
    """WS25 · viaja la ficha ENTERA (no la elige nadie) y el receptor entra logueado."""
    h = _onboard("share|ok")
    eid = _entrega_de_hoy(h)
    client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"reflexion": "Respiré hondo."})

    # Free, sin pedir modo: la Pausa tiene reflexión ⇒ viaja entera.
    r = client.post("/api/compartir", headers=h,
                    json={"entrega_id": eid, "nota": "Para vos."})
    assert r.status_code == 201
    token = r.json()["token"]
    assert r.json()["modo"] == "ejercicio"

    # Lo abre OTRA persona, con su propia sesión (el permiso es el token).
    hr = _onboard("share|receptor")
    pub = client.get(f"/api/c/{token}", headers=hr)
    assert pub.status_code == 200
    regalo = pub.json()
    assert regalo["modo"] == "ejercicio"
    assert regalo["nota"] == "Para vos."
    assert regalo["reflexion"] == "Respiré hondo."
    assert "frase" in regalo["carta"]
    # Las estrellas son privadas: nunca salen en la ficha compartida (WS25 §1.1).
    assert "estrellas" not in regalo


def test_link_carta_sola_creado_antes_de_la_reflexion_sigue_mostrando_solo_la_carta():
    """WS25 §1.2 · lo ya enviado no cambia: el modo queda congelado en el link."""
    h = _onboard("share|congelado")
    hr = _onboard("share|congelado-receptor")
    eid = _entrega_de_hoy(h)

    # Se envía la Pausa en blanco → carta sola.
    t_sola = client.post("/api/compartir", headers=h, json={"entrega_id": eid}).json()
    assert t_sola["modo"] == "carta_sola"

    # Después escribe la reflexión y la guarda.
    client.put(f"/api/entregas/{eid}/cierre", headers=h,
               json={"reflexion": "Escrita DESPUÉS de enviar.", "completada": True})

    # El link viejo sigue mostrando sólo la carta.
    regalo = client.get(f"/api/c/{t_sola['token']}", headers=hr).json()
    assert regalo["modo"] == "carta_sola"
    assert "reflexion" not in regalo
    assert "DESPUÉS" not in client.get(f"/api/c/{t_sola['token']}", headers=hr).text

    # Y un link nuevo sí la lleva.
    t_ej = client.post("/api/compartir", headers=h, json={"entrega_id": eid}).json()
    assert t_ej["modo"] == "ejercicio"
    assert client.get(f"/api/c/{t_ej['token']}", headers=hr).json()["reflexion"] \
        == "Escrita DESPUÉS de enviar."


def test_link_ejercicio_muere_al_borrar_pero_carta_sola_sobrevive():
    h = _onboard("share|muerte")
    hr = _onboard("share|muerte-receptor")
    eid = _entrega_de_hoy(h)

    # Primero el link de la Pausa en blanco (carta sola), después el de la escrita.
    t_sola = client.post("/api/compartir", headers=h,
                         json={"entrega_id": eid}).json()["token"]
    client.put(f"/api/entregas/{eid}/cierre", headers=h,
               json={"reflexion": "Una tarde tranquila.", "completada": True})
    t_ej = client.post("/api/compartir", headers=h,
                       json={"entrega_id": eid}).json()["token"]

    # Borro la entrada del Baúl.
    client.delete(f"/api/baul/{eid}", headers=h)

    # El link "ejercicio" murió; la "carta sola" sigue viva.
    assert client.get(f"/api/c/{t_ej}", headers=hr).status_code == 404
    assert client.get(f"/api/c/{t_sola}", headers=hr).status_code == 200


def test_el_regalo_exige_sesion():
    """WS25 §1.3 · en modo firebase, sin identidad no se abre el regalo: 401."""
    from mindful_api.config import settings

    h = _onboard("share|con-login")
    eid = _entrega_de_hoy(h)
    tok = client.post("/api/compartir", headers=h, json={"entrega_id": eid}).json()["token"]

    antes = settings.auth_mode
    settings.auth_mode = "firebase"
    try:
        sin_sesion = TestClient(app)
        assert sin_sesion.get(f"/api/c/{tok}").status_code == 401
        assert sin_sesion.get(f"/api/c/{tok}/fotos/no-importa").status_code == 401
    finally:
        settings.auth_mode = antes


def test_compartir_aislamiento():
    ha = _onboard("share|dueno")
    hb = _onboard("share|otro")
    eid_a = _entrega_de_hoy(ha)
    # B no puede compartir una entrega de A: 404, no delatamos que existe.
    r = client.post("/api/compartir", headers=hb, json={"entrega_id": eid_a})
    assert r.status_code == 404


# ── WS25 · visibilidad de la ficha (privada | compartida con tu comunidad) ───


def test_visibilidad_nace_privada_y_se_alterna():
    h = _onboard("baul|visibilidad")
    eid = _entrega_de_hoy(h)
    client.put(f"/api/entregas/{eid}/cierre", headers=h, json={"completada": True})

    item = client.get("/api/baul", headers=h).json()[0]
    assert item["visibilidad"] == "privada"   # default seguro: nadie publica sin pedirlo

    r = client.put(f"/api/baul/{eid}/visibilidad", headers=h,
                   json={"visibilidad": "compartida"})
    assert r.status_code == 200
    assert r.json()["id"] == eid and r.json()["visibilidad"] == "compartida"
    assert client.get("/api/baul", headers=h).json()[0]["visibilidad"] == "compartida"

    # Y se puede volver atrás.
    assert client.put(f"/api/baul/{eid}/visibilidad", headers=h,
                      json={"visibilidad": "privada"}).json()["visibilidad"] == "privada"

    # Un valor inventado no entra (lo corta el borde).
    assert client.put(f"/api/baul/{eid}/visibilidad", headers=h,
                      json={"visibilidad": "publica"}).status_code == 422


def test_visibilidad_de_una_pausa_sin_vivir_da_409():
    """Solo se publica lo vivido: una Pausa sin cerrar no tiene ficha que mostrar."""
    h = _onboard("baul|visibilidad-sin-vivir")
    eid = _entrega_de_hoy(h)
    r = client.put(f"/api/baul/{eid}/visibilidad", headers=h,
                   json={"visibilidad": "compartida"})
    assert r.status_code == 409


def test_visibilidad_aislamiento_entrega_ajena_404():
    """La regla de oro: el Baúl de cada uno nunca se cruza con el de otro."""
    ha = _onboard("baul|vis-dueno")
    hb = _onboard("baul|vis-intruso")
    eid = _entrega_de_hoy(ha)
    client.put(f"/api/entregas/{eid}/cierre", headers=ha, json={"completada": True})

    # Ajena → 404 (nunca 409 ni 403: eso delataría que existe).
    assert client.put(f"/api/baul/{eid}/visibilidad", headers=hb,
                      json={"visibilidad": "compartida"}).status_code == 404
    # Inexistente → 404 igual.
    assert client.put("/api/baul/no-existe/visibilidad", headers=hb,
                      json={"visibilidad": "compartida"}).status_code == 404
    # Y la de A no se movió.
    assert client.get("/api/baul", headers=ha).json()[0]["visibilidad"] == "privada"
