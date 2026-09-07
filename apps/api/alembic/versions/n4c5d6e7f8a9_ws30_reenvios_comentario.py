"""WS30 · Q/A de Tomás — el reenvío lleva un comentario opcional

`reenvios.comentario` (≤200, NULL): lo que le digo a la persona al mandarle una
Pausa. Le llega con la ficha ("Te enviaron") y se queda con el reenvío.
Columna nullable: cero filas afectadas, ida y vuelta trivial.

Revision ID: n4c5d6e7f8a9
Revises: m3b4c5d6e7f8
Create Date: 2026-09-07 21:30:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'n4c5d6e7f8a9'
down_revision: Union[str, None] = 'm3b4c5d6e7f8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('reenvios', sa.Column('comentario', sa.String(length=200), nullable=True))


def downgrade() -> None:
    op.drop_column('reenvios', 'comentario')
