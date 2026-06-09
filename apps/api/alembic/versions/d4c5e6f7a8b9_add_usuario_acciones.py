"""add usuario_acciones (actividades elegibles · WS10)

Filtro duro de actividad para M2 (espejo de usuario_categorias). "escribir" es el
piso garantizado del pool; sin filas = sin filtro = todas las actividades.

Revision ID: d4c5e6f7a8b9
Revises: c2b3d4e5f6a7
Create Date: 2026-06-09 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'd4c5e6f7a8b9'
down_revision: Union[str, None] = 'c2b3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'usuario_acciones',
        sa.Column('id', sa.String(length=36), nullable=False),
        sa.Column('usuario_id', sa.String(length=36), nullable=False),
        sa.Column('accion_slug', sa.String(length=40), nullable=False),
        sa.ForeignKeyConstraint(['usuario_id'], ['usuarios.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['accion_slug'], ['acciones.slug']),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('usuario_id', 'accion_slug'),
    )
    op.create_index(
        op.f('ix_usuario_acciones_usuario_id'), 'usuario_acciones', ['usuario_id']
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_usuario_acciones_usuario_id'), table_name='usuario_acciones')
    op.drop_table('usuario_acciones')
