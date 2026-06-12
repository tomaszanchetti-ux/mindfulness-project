"""WS22 · limpieza para el contenido nuevo (refundación de las cartas)

El canon WS22 refundó el mazo: la categoría `calma` deja su lugar a `sentido`,
la acción `escribir` sale del enum (es el cierre universal) y el mazo pasa de
69 a 77 cartas con ids nuevos. Antes de que el seed sincronice el Mundo 1, hay
que soltar todo lo del Mundo 2 que apunta al contenido viejo:

- `fotos`, `compartidos`, `entregas`: referencian cartas retiradas → se vacían
  (reset de contenido; mismo criterio que el wipe de WS19).
- `usuario_acciones` y `usuario_categorias`: OBSOLETAS (WS22/WS17, nada las
  lee) → se vacían. Las tablas se dropean recién en el paso 4, cuando el front
  deje de llamar a los endpoints deprecados.

Se CONSERVAN: `usuarios` (cuentas/perfil) y `push_suscripciones` (aviso diario).

Revision ID: g7b8c9d0e1f2
Revises: a8b9c0d1e2f3
Create Date: 2026-06-12 13:00:00.000000
"""
from typing import Sequence, Union

from alembic import op


revision: str = 'g7b8c9d0e1f2'
down_revision: Union[str, None] = 'a8b9c0d1e2f3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Hijas primero (FK): fotos → compartidos → entregas; después las obsoletas.
    op.execute("DELETE FROM fotos")
    op.execute("DELETE FROM compartidos")
    op.execute("DELETE FROM entregas")
    op.execute("DELETE FROM usuario_acciones")
    op.execute("DELETE FROM usuario_categorias")


def downgrade() -> None:
    # Migración de datos: no hay vuelta atrás (el contenido viejo ya no existe).
    pass
