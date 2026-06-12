"""WS23 · drop de las tablas de elección (cierre del paso 4)

`usuario_categorias` (obsoleta desde WS17: los pilares no se eligen) y
`usuario_acciones` (obsoleta desde WS22: las acciones tampoco) quedaron vacías
en la migración g7b8c9d0e1f2 y vivían solo por compatibilidad con el front
pre-WS22, que llamaba a los endpoints deprecados. El front WS23 ya no los
llama → los endpoints se retiraron del código y las tablas se dropean acá.

Revision ID: h8c9d0e1f2a3
Revises: g7b8c9d0e1f2
Create Date: 2026-06-12 18:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'h8c9d0e1f2a3'
down_revision: Union[str, None] = 'g7b8c9d0e1f2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_table('usuario_acciones')
    op.drop_table('usuario_categorias')


def downgrade() -> None:
    # No hay vuelta atrás: las tablas estaban vacías y nada las leía (WS17/WS22).
    pass
