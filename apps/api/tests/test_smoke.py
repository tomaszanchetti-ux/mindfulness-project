"""Smoke test: health + el contenido global cargó (los dos mundos en pie)."""

from __future__ import annotations

from fastapi.testclient import TestClient

from mindful_api.main import app

client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_seed_y_categorias():
    """Asume DB migrada + seedeada (make api-migrate && make api-seed)."""
    r = client.get("/api/contenido/categorias")
    assert r.status_code == 200
    cats = r.json()
    assert len(cats) == 6
    slugs = {c["slug"] for c in cats}
    assert {"gratitud", "calma", "vinculos"} <= slugs

    r2 = client.get("/api/contenido/resumen")
    assert r2.json()["cartas"] == 69
