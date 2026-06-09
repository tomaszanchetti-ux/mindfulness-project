"""Seed del MUNDO 1 (contenido global) desde los JSON maestros de M0.

Los 3 JSON de `M0_Motor_de_Contenido/data/` son la ÚNICA fuente de verdad del
contenido. Este script los carga (o re-carga) a las tablas globales. Idempotente:
correrlo dos veces deja lo mismo. Re-seedea si sumamos cartas.

Uso:  python -m mindful_api.seed
"""

from __future__ import annotations

import json
from pathlib import Path

from .db.base import SessionLocal
from .db.models import Accion, Carta, Categoria

# apps/api/mindful_api/seed.py  →  raíz del repo  →  M0_.../data
DATA = Path(__file__).resolve().parents[3] / "M0_Motor_de_Contenido" / "data"


def _load(name: str) -> list[dict]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def seed() -> dict[str, int]:
    """Carga categorías, acciones y cartas. Devuelve los conteos."""
    categorias = _load("categorias.json")
    acciones = _load("acciones.json")
    cartas = _load("cartas.json")

    with SessionLocal() as s:
        # merge = upsert por PK (idempotente). Padres primero.
        for c in categorias:
            s.merge(Categoria(
                slug=c["slug"], nombre=c["nombre"],
                color_accent=c["color_accent"], color_text=c["color_text"], img=c["img"],
            ))
        for a in acciones:
            s.merge(Accion(slug=a["slug"], nombre=a["nombre"], glifo=a["glifo"]))

        # Persistir padres ANTES de las cartas (respeta las FK categoria/accion).
        s.flush()

        for k in cartas:
            s.merge(Carta(
                id=k["id"], categoria_slug=k["categoria"], accion_slug=k["accion"],
                frase=k["frase"], prompt=k["prompt"],
            ))

        s.commit()

    return {"categorias": len(categorias), "acciones": len(acciones), "cartas": len(cartas)}


if __name__ == "__main__":
    result = seed()
    print(
        f"Seed OK · {result['categorias']} categorías · "
        f"{result['acciones']} acciones · {result['cartas']} cartas"
    )
