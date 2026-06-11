"""add cartas.concepto (huella de deduplicación · WS17)

Cada carta lleva un `concepto`: dos cartas que producen la misma experiencia
emocional comparten etiqueta y M2 no repite concepto dentro de la ventana de
7 días. El valor lo trae el seed (cartas.json es la fuente de verdad).

Revision ID: e5f6a7b8c9d0
Revises: d4c5e6f7a8b9
Create Date: 2026-06-11 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4c5e6f7a8b9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('cartas', sa.Column('concepto', sa.String(length=80), nullable=True))
    op.create_index(op.f('ix_cartas_concepto'), 'cartas', ['concepto'])


def downgrade() -> None:
    op.drop_index(op.f('ix_cartas_concepto'), table_name='cartas')
    op.drop_column('cartas', 'concepto')
