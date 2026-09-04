"""WS24 · A0 · el plan y sus límites: un solo lugar, y el perfil los expone."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi.testclient import TestClient
from sqlalchemy import select

from mindful_api.db.base import SessionLocal
from mindful_api.db.models import Usuario
from mindful_api.main import app
from mindful_api.services.plan import (
    LIMITES_FREE,
    LIMITES_PREMIUM,
    activar_premium,
    es_premium,
    limites,
    vencer_premium,
)

client = TestClient(app)


def _headers(sub: str) -> dict:
    return {"X-Debug-Sub": sub, "X-Debug-Email": f"{sub}@mindful.local"}


def hacer_premium(sub: str, dias: int = 365) -> None:
    """Helper para las cards A1.x: vuelve premium al usuario `dev|<sub>` (auto-provisión dev)."""
    with SessionLocal() as s:
        u = s.scalar(select(Usuario).where(Usuario.firebase_uid == sub))
        assert u is not None, "el usuario debe existir (llamar antes a un endpoint con su header)"
        activar_premium(u, datetime.now(timezone.utc) + timedelta(days=dias))
        s.commit()


def test_usuario_fresco_es_free_y_el_perfil_expone_limites():
    h = _headers("test|plan-free")
    p = client.get("/api/perfil", headers=h).json()
    assert p["plan"] == "free"
    assert p["plan_hasta"] is None
    assert p["limites"] == LIMITES_FREE.dict()
    assert p["limites"]["reflexion_max"] == 150
    assert p["limites"]["fotos_max"] == 1
    assert p["limites"]["cambios_carta"] == 0


def test_premium_vigente_expone_limites_premium():
    h = _headers("test|plan-premium")
    client.get("/api/perfil", headers=h)
    hacer_premium("test|plan-premium")
    p = client.get("/api/perfil", headers=h).json()
    assert p["plan"] == "premium"
    assert p["plan_hasta"] is not None
    assert p["limites"] == LIMITES_PREMIUM.dict()
    assert p["limites"]["reflexion_max"] == 500
    assert p["limites"]["fotos_max"] == 3
    assert p["limites"]["cambios_carta"] == 3


def test_premium_vencido_vuelve_a_free_sin_job():
    h = _headers("test|plan-vencido")
    client.get("/api/perfil", headers=h)
    hacer_premium("test|plan-vencido", dias=-1)  # venció ayer
    p = client.get("/api/perfil", headers=h).json()
    assert p["plan"] == "free"
    assert p["plan_hasta"] is None
    assert p["limites"] == LIMITES_FREE.dict()


def test_helpers_puros():
    u = Usuario(firebase_uid="x", email="x@x")
    assert es_premium(u) is False
    activar_premium(u, datetime.now(timezone.utc) + timedelta(days=1))
    assert es_premium(u) is True and limites(u) is LIMITES_PREMIUM
    vencer_premium(u)
    assert es_premium(u) is False and limites(u) is LIMITES_FREE
