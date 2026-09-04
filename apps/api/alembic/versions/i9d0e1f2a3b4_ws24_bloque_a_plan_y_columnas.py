"""WS24 · Bloque A (freemium) — el contrato de datos completo, en UNA migración

`usuarios`: plan (free|premium) · plan_hasta (vence el premium) · stripe_customer_id.
`entregas`: comentario_carta (feedback privado debajo de las estrellas) ·
            cambios (cuántas veces premium cambió la carta de hoy, máx. 3) ·
            descartadas (JSON, ids de las cartas que cambió).

Las columnas se crean todas acá para que las cards A1.x corran en paralelo sin
tocar el esquema. Cero filas afectadas: todo tiene default o admite NULL.

Revision ID: i9d0e1f2a3b4
Revises: h8c9d0e1f2a3
Create Date: 2026-09-04 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'i9d0e1f2a3b4'
down_revision: Union[str, None] = 'h8c9d0e1f2a3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('usuarios', sa.Column('plan', sa.String(length=10), nullable=False,
                                        server_default='free'))
    op.add_column('usuarios', sa.Column('plan_hasta', sa.DateTime(timezone=True), nullable=True))
    op.add_column('usuarios', sa.Column('stripe_customer_id', sa.String(length=64), nullable=True))
    op.create_index('ix_usuarios_stripe_customer_id', 'usuarios', ['stripe_customer_id'],
                    unique=True)

    op.add_column('entregas', sa.Column('comentario_carta', sa.Text(), nullable=True))
    op.add_column('entregas', sa.Column('cambios', sa.Integer(), nullable=False,
                                        server_default='0'))
    op.add_column('entregas', sa.Column('descartadas', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('entregas', 'descartadas')
    op.drop_column('entregas', 'cambios')
    op.drop_column('entregas', 'comentario_carta')
    op.drop_index('ix_usuarios_stripe_customer_id', table_name='usuarios')
    op.drop_column('usuarios', 'stripe_customer_id')
    op.drop_column('usuarios', 'plan_hasta')
    op.drop_column('usuarios', 'plan')
