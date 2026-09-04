"""WS25 · A3 — la visibilidad de cada Pausa (privada | compartida)

`entregas.visibilidad`: si la ficha de esa Pausa la ve la comunidad del usuario
(`compartida`) o solo él (`privada`). Es una decisión POSTERIOR al cierre, que se
cambia desde el Baúl las veces que haga falta — nada que ver con el link de M5,
que es un regalo puntual a una persona.

Aditiva y con `server_default='privada'`: las Pausas que ya existen quedan
privadas, que es el default seguro (nadie publica nada sin pedirlo).

Revision ID: j0e1f2a3b4c5
Revises: i9d0e1f2a3b4
Create Date: 2026-09-04 16:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'j0e1f2a3b4c5'
down_revision: Union[str, None] = 'i9d0e1f2a3b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('entregas', sa.Column('visibilidad', sa.String(length=12), nullable=False,
                                        server_default='privada'))


def downgrade() -> None:
    op.drop_column('entregas', 'visibilidad')
