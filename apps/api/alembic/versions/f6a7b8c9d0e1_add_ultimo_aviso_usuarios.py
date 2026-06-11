"""add usuarios.ultimo_aviso_fecha (aviso diario por email · WS20)

Fecha LOCAL (en la TZ del usuario) del último aviso enviado. Garantiza máximo
un email por día aunque el cron corra cada 15 minutos, y se auto-repara si una
corrida se pierde (el siguiente tick del día lo manda igual).

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-06-11 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('ultimo_aviso_fecha', sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column('usuarios', 'ultimo_aviso_fecha')
