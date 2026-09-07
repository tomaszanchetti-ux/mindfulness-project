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
from .db.models import ORIGEN_DWELLIA, Accion, Carta, Categoria

# apps/api/mindful_api/seed.py  →  raíz del repo  →  M0_.../data
DATA = Path(__file__).resolve().parents[3] / "M0_Motor_de_Contenido" / "data"


def _load(name: str) -> list[dict]:
    return json.loads((DATA / name).read_text(encoding="utf-8"))


def seed() -> dict[str, int]:
    """Sincroniza categorías, acciones y cartas con los JSON. Devuelve los conteos.

    WS22: además del upsert, BORRA lo que ya no está en los JSON (cartas retiradas,
    la categoría `calma`, la acción `escribir`). WS27: el borrado respeta las
    cartas de la comunidad (`origen != dwellia`). Si hay datos de usuario apuntando
    a contenido retirado, la migración de limpieza (g7b8c9d0e1f2) corre antes.
    """
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
                concepto=k["concepto"], frase=k["frase"], prompt=k["prompt"],
                origen=ORIGEN_DWELLIA,
            ))

        # Sync: lo que no está en los JSON se va. Hijas primero (FK), con flush
        # explícito entre pasos para fijar el orden de borrado.
        # WS27 · SOLO las cartas de origen `dwellia`: las de la comunidad no
        # viven en los JSON y este job corre en cada deploy — borrarlas sería
        # borrar lo que la gente escribió y Tomás aprobó.
        ids_validos = {k["id"] for k in cartas}
        for carta in s.query(Carta).filter(Carta.origen == ORIGEN_DWELLIA).all():
            if carta.id not in ids_validos:
                s.delete(carta)
        s.flush()
        slugs_acc = {a["slug"] for a in acciones}
        for accion in s.query(Accion).all():
            if accion.slug not in slugs_acc:
                s.delete(accion)
        slugs_cat = {c["slug"] for c in categorias}
        for cat in s.query(Categoria).all():
            if cat.slug not in slugs_cat:
                s.delete(cat)

        s.commit()

    return {"categorias": len(categorias), "acciones": len(acciones), "cartas": len(cartas)}


if __name__ == "__main__":
    result = seed()
    print(
        f"Seed OK · {result['categorias']} categorías · "
        f"{result['acciones']} acciones · {result['cartas']} cartas"
    )
