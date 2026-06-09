"""App FastAPI. Espejo de Arc One. Por ahora: health + lectura del contenido global.

Los endpoints privados (M1 perfil, M3 ritual, M4 Baúl) se suman en sus pasos del
build; todos filtrarán por el usuario logueado (Firebase) en el backend.
"""

from __future__ import annotations

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from .config import settings
from .db.base import get_session
from .db.models import Carta, Categoria
from .routers import perfil

app = FastAPI(title="Mindful API", version="0.0.1")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(perfil.router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "env": settings.env}


@app.get("/api/contenido/categorias")
def listar_categorias(s: Session = Depends(get_session)) -> list[dict]:
    """Las 6 categorías globales (contenido compartido · Mundo 1)."""
    rows = s.scalars(select(Categoria).order_by(Categoria.nombre)).all()
    return [
        {
            "slug": c.slug,
            "nombre": c.nombre,
            "color_accent": c.color_accent,
            "color_text": c.color_text,
            "img": c.img,
        }
        for c in rows
    ]


@app.get("/api/contenido/resumen")
def resumen_contenido(s: Session = Depends(get_session)) -> dict:
    """Conteo del contenido cargado (sirve para verificar el seed de un vistazo)."""
    total_cartas = s.scalar(select(func.count()).select_from(Carta))
    return {"cartas": total_cartas}
