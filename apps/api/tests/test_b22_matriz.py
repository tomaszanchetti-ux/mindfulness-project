"""WS28 · B2.2 · `GET /api/contenido/matriz`: la matriz pilar × acción del canon.

El wizard de Crear filtra con esto el paso 2, así que tiene que ser LA MISMA
matriz que aplica la capa 1 del juez (R8.1): si divergieran, el usuario elegiría
una acción que después "no combina".
"""

from fastapi.testclient import TestClient

from mindful_api.main import app
from mindful_api.services.canon import MATRIZ_VIABLE

client = TestClient(app)


def test_la_matriz_es_publica_y_es_la_del_canon():
    r = client.get("/api/contenido/matriz")
    assert r.status_code == 200
    data = r.json()
    assert set(data) == set(MATRIZ_VIABLE)
    for pilar, acciones in MATRIZ_VIABLE.items():
        assert set(data[pilar]) == set(acciones)
        assert len(data[pilar]) == len(set(data[pilar]))      # sin repetidos


def test_las_acciones_salen_en_el_orden_de_la_app():
    """contemplar → respirar → caminar → hacer, como en /api/contenido/acciones."""
    orden = ["contemplar", "respirar", "caminar", "hacer"]
    for acciones in client.get("/api/contenido/matriz").json().values():
        posiciones = [orden.index(a) for a in acciones]
        assert posiciones == sorted(posiciones)
