"""WS27 · B2.1 (Distribución + adminland) — el historial de redacciones, y fuera el interruptor

Dos cambios, los dos por decisión de Tomás (WS27 §6):

1. `usuarios.recibe_comunidad` SE VA. B0 la creó pensando en un opt-in para el
   "día comodín"; la decisión final es que **las cartas aprobadas se reparten como
   iguales, a todos, sin interruptor y sin exclusiones** (el autor incluido). Una
   columna que nadie lee es una promesa de producto que nadie cumple: se borra.

2. `cartas_comunidad.historial` (JSON, nullable) GUARDA CADA REDACCIÓN del autor:
   la v1 (lo que escribió al enviarla) y cada v2, v3… (lo que reescribió al
   reenviarla). Es la pata que le faltaba al funnel del adminland: la propuesta ya
   guarda la evaluación (`veredicto`, con su `anterior`) y la decisión final
   (`estado`/`motivo`/`carta_id`), pero el TEXTO viejo se pisaba en cada reenvío y
   Tomás no podía ver de dónde venía la carta que está mirando.

Cero filas afectadas: `historial` admite NULL (una propuesta anterior a esta
migración simplemente no tiene historial) y el DROP no toca datos vivos.

Revision ID: l2a3b4c5d6e7
Revises: k1f2a3b4c5d6
Create Date: 2026-09-07 18:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'l2a3b4c5d6e7'
down_revision: Union[str, None] = 'k1f2a3b4c5d6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Sin interruptor: todos reciben cartas de la comunidad ───────────────
    op.drop_column('usuarios', 'recibe_comunidad')

    # ── El funnel v1 → v2 → vFinal necesita las redacciones ─────────────────
    op.add_column('cartas_comunidad', sa.Column('historial', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('cartas_comunidad', 'historial')
    # Vuelve tal cual la creó `k1f2a3b4c5d6` (default apagado, cero filas rotas).
    op.add_column('usuarios', sa.Column('recibe_comunidad', sa.Boolean(), nullable=False,
                                        server_default=sa.false()))
