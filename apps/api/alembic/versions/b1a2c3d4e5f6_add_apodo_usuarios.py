"""add apodo a usuarios

Cómo nos referimos al usuario en toda la app (saludo, firma del regalo M5).

Revision ID: b1a2c3d4e5f6
Revises: ae306810ae14
Create Date: 2026-06-09 12:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b1a2c3d4e5f6'
down_revision: Union[str, None] = 'ae306810ae14'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('apodo', sa.String(length=40), nullable=True))


def downgrade() -> None:
    op.drop_column('usuarios', 'apodo')
