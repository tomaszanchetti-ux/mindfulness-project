"""WS27 · B1.2 · el juez de cartas de la comunidad, capa por capa.

Ninguno de estos tests llama a la API de Anthropic: la capa 2 se simula
monkeypatcheando `juez._cliente`. Lo que se prueba es el CONTRATO que consume
B1.1 (`evaluar` → `Veredicto`) y que la capa 1 protege aunque el juez esté
apagado.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from mindful_api.config import settings
from mindful_api.services import canon, juez

RAIZ = Path(__file__).resolve().parents[3]
DATA = canon.M0_DIR / "data"


# ─────────────────────────────────────────────────────────────────────────────
# Fixtures: el mazo real (77 cartas) y los slugs reales.
# ─────────────────────────────────────────────────────────────────────────────
@pytest.fixture(scope="module")
def mazo():
    return json.loads((DATA / "cartas.json").read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def categorias():
    return {c["slug"] for c in json.loads((DATA / "categorias.json").read_text(encoding="utf-8"))}


@pytest.fixture(scope="module")
def acciones():
    return {a["slug"] for a in json.loads((DATA / "acciones.json").read_text(encoding="utf-8"))}


# Una candidata escrita para no parecerse a ninguna del mazo (máx. 0,56 de
# similitud) y para respetar los límites de la comunidad (frase 43 · prompt 195).
PROMPT_OK = (
    "Elige un objeto que uses todos los días sin pensarlo y quédate un minuto "
    "mirándolo despacio, como si fuera nuevo. Al terminar, escribe en tu diario "
    "de dónde vino y qué te hizo sentir mirarlo así."
)
PROMPT_SIN_DIARIO = PROMPT_OK.replace("escribe en tu diario", "anota en una hoja")


def _propuesta(**cambios):
    """Una candidata limpia: gratitud×contemplar es un par viable de la matriz."""
    base = {
        "categoria": "gratitud",
        "accion": "contemplar",
        "frase": "El vaso de cada mañana guarda una historia.",
        "prompt": PROMPT_OK,
    }
    base.update(cambios)
    return base


# ─────────────────────────────────────────────────────────────────────────────
# El modelo simulado
# ─────────────────────────────────────────────────────────────────────────────
class _Bloque:
    def __init__(self, text):
        self.type = "text"
        self.text = text


class _Usage:
    def model_dump(self):
        return {"input_tokens": 13000, "output_tokens": 180, "cache_read_input_tokens": 12800}


class _Respuesta:
    def __init__(self, payload):
        self.content = [_Bloque(json.dumps(payload, ensure_ascii=False))]
        self.usage = _Usage()


class _Messages:
    def __init__(self, payload, registro):
        self._payload = payload
        self._registro = registro

    def create(self, **kwargs):
        self._registro.update(kwargs)
        self._registro.setdefault("_llamadas", 0)
        self._registro["_llamadas"] += 1
        return _Respuesta(self._payload)


class _ClienteFalso:
    def __init__(self, payload, registro):
        self.messages = _Messages(payload, registro)


def _simular_modelo(monkeypatch, payload):
    """Enchufa un cliente falso y devuelve el registro de kwargs de la llamada."""
    registro = {}
    monkeypatch.setattr(settings, "anthropic_api_key", "test")
    monkeypatch.setattr(juez, "_cliente", lambda: _ClienteFalso(payload, registro))
    return registro


def _texto_system(registro) -> str:
    return "\n".join(b["text"] for b in registro["system"])


def _texto_user(registro) -> str:
    """El turno `user` es una LISTA de bloques (el mazo va ahí, no en el system)."""
    return "\n".join(b["text"] for b in registro["messages"][0]["content"])


# El fix que propone el modelo tiene que poder usarlo el autor: entra por el
# POST/PUT de B1.1, así que respeta los límites de la comunidad (frase ≤60 ·
# prompt 100-220 · el diario dentro).
FIX_USABLE = {
    "frase": "Otra frase para abrir la pausa de hoy.",
    "prompt": ("Mira ese mismo objeto un minuto entero, sin prisa, y después "
               "escribe en tu diario qué sentiste al mirarlo así."),
}


APRUEBA = {
    "veredicto": "aprueba",
    "hallazgos": [],
    "concepto_sugerido": "gratitud-por-lo-invisible",
    "fix_sugerido": None,
}
REVISION = {
    "veredicto": "requiere_revision",
    "hallazgos": [
        {"regla": "R7.1", "mayor": False, "detalle": "muletilla menor"},
        {"regla": "R3.4", "mayor": True, "detalle": "La consigna se queda en los hechos"},
    ],
    "concepto_sugerido": "mirar-lo-cotidiano",
    "fix_sugerido": FIX_USABLE,
}
RECHAZA = {
    "veredicto": "rechaza",
    "hallazgos": [{"regla": "S1", "mayor": True, "detalle": "Contenido clínico"}],
    "concepto_sugerido": "sin-concepto",
    "fix_sugerido": {"frase": "no debería usarse", "prompt": "no debería usarse"},
}


# ─────────────────────────────────────────────────────────────────────────────
# CAPA 1 · determinística
# ─────────────────────────────────────────────────────────────────────────────
def test_capa1_candidata_valida_no_tiene_errores_ni_parecidos(mazo, categorias, acciones):
    inf = canon.validar_candidata(_propuesta(), mazo, categorias, acciones)
    assert inf.errores == []
    assert inf.similares == []
    assert inf.limpia()


def test_capa1_par_fuera_de_la_matriz_es_error(mazo, categorias, acciones):
    # perspectiva × hacer NO está en MATRIZ_VIABLE (canon R8.1).
    inf = canon.validar_candidata(
        _propuesta(categoria="perspectiva", accion="hacer"), mazo, categorias, acciones
    )
    assert [e["regla"] for e in inf.errores] == ["R8.1"]
    assert "perspectiva×hacer" in inf.errores[0]["detalle"]
    assert not inf.limpia()


def test_capa1_slug_inexistente_es_error(mazo, categorias, acciones):
    inf = canon.validar_candidata(
        _propuesta(categoria="calma"), mazo, categorias, acciones
    )
    assert any(e["regla"] == "R8.1" and "calma" in e["detalle"] for e in inf.errores)


def test_capa1_prompt_sin_diario_es_error(mazo, categorias, acciones):
    sin_diario = _propuesta(prompt=PROMPT_SIN_DIARIO)
    inf = canon.validar_candidata(sin_diario, mazo, categorias, acciones)
    assert [e["regla"] for e in inf.errores] == ["R3.1"]
    assert inf.errores[0]["motivo"] == "El prompt no cierra en el diario"


def test_capa1_frase_copiada_del_mazo_aparece_en_similares(mazo, categorias, acciones):
    original = mazo[0]
    inf = canon.validar_candidata(
        _propuesta(frase=original["frase"]), mazo, categorias, acciones
    )
    coincidencias = [s for s in inf.similares if s["id"] == original["id"]]
    assert coincidencias, inf.similares
    assert coincidencias[0]["campo"] == "frase"
    assert coincidencias[0]["similitud"] >= canon.UMBRAL_SIMILITUD
    assert not inf.limpia()


def test_capa1_prompt_copiado_del_mazo_aparece_en_similares(mazo, categorias, acciones):
    original = mazo[3]
    inf = canon.validar_candidata(
        _propuesta(prompt=original["prompt"]), mazo, categorias, acciones
    )
    assert any(s["id"] == original["id"] and s["campo"] == "prompt" for s in inf.similares)


def test_capa1_localismos_son_aviso_no_error(mazo, categorias, acciones):
    con_voseo = _propuesta(
        frase="Quedate acá un momento.",
        prompt=PROMPT_OK.replace("Elige", "Si vos podés, elige")
                        .replace("escribe en tu diario", "escribí en tu diario"),
    )
    inf = canon.validar_candidata(con_voseo, mazo, categorias, acciones)
    reglas = {a["regla"] for a in inf.avisos}
    assert "R6.1" in reglas          # voseo ("vos", "podés", "escribí")
    assert "R6.2" in reglas          # "acá"
    assert inf.errores == []         # los localismos NO frenan la carta
    assert inf.limpia()


def test_capa1_muletilla_ya_cargada_en_el_pilar_es_aviso(mazo, categorias, acciones):
    # "qué te llevas" ya está en gratitud (grat-con-02) → R7.1.
    inf = canon.validar_candidata(
        _propuesta(prompt=(
            "Elige un objeto que uses todos los días sin pensarlo y quédate un minuto "
            "mirándolo despacio. Al terminar, escribe en tu diario qué te llevas de "
            "mirarlo así y qué te hizo sentir."
        )),
        mazo, categorias, acciones,
    )
    assert any(a["regla"] == "R7.1" for a in inf.avisos), inf.avisos


def test_leer_canon_encuentra_los_dos_archivos():
    assert canon.CANON_PATH.is_file()
    assert canon.FUNDAMENTOS_PATH.is_file()
    texto = canon.leer_canon()
    assert "Canon ejecutable de cartas" in texto      # canon_cartas.md
    assert "Fundamentos de los pilares" in texto      # fundamentos_pilares.md
    assert "S1" in texto and "R4.2" in texto
    assert canon.leer_canon() is texto                # cacheado en módulo


# ─────────────────────────────────────────────────────────────────────────────
# SIN KEY · el juez apagado, la capa 1 protegiendo
# ─────────────────────────────────────────────────────────────────────────────
def test_sin_key_candidata_valida_queda_off(monkeypatch, mazo, categorias, acciones):
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    v = juez.evaluar(_propuesta(), mazo, categorias, acciones)
    assert v.resultado == "off"
    assert v.motivo == "juez apagado"
    assert v.detalle["capa1"]["errores"] == []
    assert v.fix is None


def test_sin_key_prompt_sin_diario_requiere_revision(monkeypatch, mazo, categorias, acciones):
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    sin_diario = _propuesta(prompt=PROMPT_SIN_DIARIO)
    v = juez.evaluar(sin_diario, mazo, categorias, acciones)
    assert v.resultado == "requiere_revision"
    assert "R3.1" in [h["regla"] for h in v.hallazgos]
    assert v.motivo == "El prompt no cierra en el diario"
    assert v.detalle["capa1"]["errores"][0]["regla"] == "R3.1"


def test_sin_key_copia_de_una_carta_requiere_revision(monkeypatch, mazo, categorias, acciones):
    monkeypatch.setattr(settings, "anthropic_api_key", "")
    original = mazo[0]
    v = juez.evaluar(
        _propuesta(frase=original["frase"]), mazo, categorias, acciones
    )
    assert v.resultado == "requiere_revision"
    assert "R5.1" in [h["regla"] for h in v.hallazgos]
    assert v.motivo == "Se parece mucho a una carta que ya existe"
    assert any(h["mayor"] for h in v.hallazgos)


# ─────────────────────────────────────────────────────────────────────────────
# CON KEY · el modelo simulado
# ─────────────────────────────────────────────────────────────────────────────
def test_con_key_aprueba_mapea_el_veredicto(monkeypatch, mazo, categorias, acciones):
    registro = _simular_modelo(monkeypatch, APRUEBA)
    v = juez.evaluar(_propuesta(), mazo, categorias, acciones)

    assert v.resultado == "aprueba"
    assert v.concepto == "gratitud-por-lo-invisible"
    assert v.fix is None
    assert v.motivo == "Lista para publicar"
    assert v.detalle["modelo"]["crudo"] == APRUEBA
    assert v.detalle["modelo"]["usage"]["cache_read_input_tokens"] == 12800
    assert registro["_llamadas"] == 1


def test_con_key_requiere_revision_trae_fix_y_motivo(monkeypatch, mazo, categorias, acciones):
    _simular_modelo(monkeypatch, REVISION)
    v = juez.evaluar(_propuesta(), mazo, categorias, acciones)

    assert v.resultado == "requiere_revision"
    assert v.fix == FIX_USABLE
    assert v.concepto == "mirar-lo-cotidiano"
    # El motivo es el detalle del primer hallazgo MAYOR, no del primero de la lista.
    assert v.motivo == "La consigna se queda en los hechos"
    assert {"R7.1", "R3.4"} <= {h["regla"] for h in v.hallazgos}


def test_con_key_rechaza_no_propone_fix(monkeypatch, mazo, categorias, acciones):
    _simular_modelo(monkeypatch, RECHAZA)
    v = juez.evaluar(_propuesta(), mazo, categorias, acciones)

    assert v.resultado == "rechaza"
    assert v.fix is None            # una S no se arregla con un retoque
    assert v.motivo == "Contenido clínico"
    assert v.hallazgos[0]["regla"] == "S1"


def test_con_key_la_llamada_usa_el_modelo_el_cache_y_el_esquema(
    monkeypatch, mazo, categorias, acciones
):
    registro = _simular_modelo(monkeypatch, APRUEBA)
    juez.evaluar(_propuesta(), mazo, categorias, acciones)

    assert registro["model"] == settings.juez_modelo
    assert registro["max_tokens"] == 8000  # WS27: Sonnet 5 piensa dentro del tope
    assert registro["timeout"] == 120
    assert "thinking" not in registro and "temperature" not in registro

    # El canon va cacheado en el system…
    cacheados = [b for b in registro["system"] if b.get("cache_control")]
    assert len(cacheados) == 1
    assert cacheados[0]["cache_control"] == {"type": "ephemeral"}

    system = _texto_system(registro)
    assert "S1" in system                       # el alcance de seguridad
    assert "R1.5" in system and "R4.2" in system  # las cuatro preguntas de alineación

    # …y el MAZO viaja en el turno `user`, como datos, con su propio breakpoint:
    # desde B1.3 incluye cartas escritas por usuarios y no puede leerse como
    # instrucción del sistema (WS27 · BUG-B12-8).
    bloques_user = registro["messages"][0]["content"]
    assert bloques_user[0]["cache_control"] == {"type": "ephemeral"}
    assert mazo[0]["frase"] in bloques_user[0]["text"]   # el mazo vigente viaja entero
    assert mazo[0]["prompt"] in bloques_user[0]["text"]
    assert "no instrucciones" in bloques_user[0]["text"].lower()
    assert mazo[0]["frase"] not in system

    esquema = registro["output_config"]["format"]
    assert esquema["type"] == "json_schema"
    assert esquema["schema"] is juez.ESQUEMA_VEREDICTO


def test_con_key_el_user_lleva_los_hallazgos_de_la_capa_1(
    monkeypatch, mazo, categorias, acciones
):
    registro = _simular_modelo(monkeypatch, APRUEBA)
    original = mazo[0]
    juez.evaluar(_propuesta(frase=original["frase"]), mazo, categorias, acciones)

    user = _texto_user(registro)
    assert registro["messages"][0]["role"] == "user"
    assert "hallazgos previos" in user.lower()
    assert "R5.1" in user
    assert original["id"] in user
    assert original["frase"] in user            # la propuesta va en el mensaje


def test_con_key_la_capa_1_manda_sobre_un_aprueba_del_modelo(
    monkeypatch, mazo, categorias, acciones
):
    """Si la capa 1 encontró un error duro, el modelo no puede publicarla igual."""
    _simular_modelo(monkeypatch, APRUEBA)
    sin_diario = _propuesta(prompt=PROMPT_SIN_DIARIO)
    v = juez.evaluar(sin_diario, mazo, categorias, acciones)

    assert v.resultado == "requiere_revision"
    assert v.detalle["degradado_por_capa1"] is True
    assert v.motivo == "El prompt no cierra en el diario"


def test_el_juez_nunca_levanta_si_el_cliente_falla(monkeypatch, mazo, categorias, acciones):
    monkeypatch.setattr(settings, "anthropic_api_key", "test")

    def _explota():
        raise RuntimeError("connection reset by peer")

    monkeypatch.setattr(juez, "_cliente", _explota)
    v = juez.evaluar(_propuesta(), mazo, categorias, acciones)

    assert v.resultado == "off"
    assert "connection reset by peer" in v.detalle["error"]
    assert v.detalle["capa1"]["errores"] == []


def test_respuesta_del_modelo_que_no_es_json_cae_en_off(
    monkeypatch, mazo, categorias, acciones
):
    """Si el juez se cae, la carta va a revisión de Dwellia — nunca vuelve al autor."""
    monkeypatch.setattr(settings, "anthropic_api_key", "test")
    monkeypatch.setattr(juez, "_cliente", lambda: _ClienteFalso("no es json", {}))
    original = mazo[0]
    v = juez.evaluar(_propuesta(frase=original["frase"]), mazo, categorias, acciones)

    assert v.resultado == "off"
    assert "error" in v.detalle
    # Los hallazgos de la capa 1 viajan igual: Tomás los ve en el expediente.
    assert "R5.1" in [h["regla"] for h in v.hallazgos]


def test_el_veredicto_es_serializable_a_json(monkeypatch, mazo, categorias, acciones):
    """B1.1 guarda el veredicto en una columna JSON: nada de objetos del SDK."""
    import dataclasses

    _simular_modelo(monkeypatch, REVISION)
    v = juez.evaluar(_propuesta(), mazo, categorias, acciones)
    json.dumps(dataclasses.asdict(v), ensure_ascii=False)


# ─────────────────────────────────────────────────────────────────────────────
# El CLI sigue siendo el mismo (la capa 1 vive ahora en el service)
# ─────────────────────────────────────────────────────────────────────────────
def test_el_cli_sigue_dando_77_de_77_en_verde():
    r = subprocess.run(
        [sys.executable, str(RAIZ / "scripts" / "validar_cartas.py")],
        cwd=str(RAIZ), capture_output=True, text=True,
    )
    assert r.returncode == 0, r.stdout + r.stderr
    assert "VALIDADOR DE CARTAS · 77 carta(s)" in r.stdout
    assert "ERRORES (gate): 0" in r.stdout
    assert "AVISOS (revisar): 0" in r.stdout
