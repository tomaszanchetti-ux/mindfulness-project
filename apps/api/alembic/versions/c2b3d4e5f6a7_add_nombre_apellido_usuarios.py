"""add nombre y apellido a usuarios

Datos básicos del perfil (nombre se pide en el onboarding; apellido opcional).

Revision ID: c2b3d4e5f6a7
Revises: b1a2c3d4e5f6
Create Date: 2026-06-09 12:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c2b3d4e5f6a7'
down_revision: Union[str, None] = 'b1a2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('nombre', sa.String(length=80), nullable=True))
    op.add_column('usuarios', sa.Column('apellido', sa.String(length=80), nullable=True))


def downgrade() -> None:
    op.drop_column('usuarios', 'apellido')
    op.drop_column('usuarios', 'nombre')
