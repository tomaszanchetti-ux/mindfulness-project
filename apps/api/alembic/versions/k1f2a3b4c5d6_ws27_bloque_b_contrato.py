"""WS27 · Bloque B (Crear: cartas de la comunidad) — el contrato de datos completo

Mundo 1 · `cartas`: origen (dwellia|comunidad) · autor_usuario_id · firma_publica.
   El seed solo sincroniza las de origen `dwellia`: una carta de la comunidad
   publicada en el mazo sobrevive a cada deploy (hallazgo de la Fase 0).
Mundo 2 · `cartas_comunidad`: la propuesta de un usuario premium y su recorrido
   (en_revision → revision_dwellia | a_revisar | rechazada → aprobada = cargada).
Mundo 2 · `avisos`: lo que la app le cuenta al usuario (cambios de estado de su
   carta hoy; reenvíos y solicitudes en el Bloque C).
Mundo 2 · `usuarios.recibe_comunidad`: opt-in para recibir cartas de la
   comunidad el día comodín (default apagado).

Todo con default o NULL: cero filas afectadas. Se crea todo acá para que las
cards B1.x corran en paralelo sin tocar el esquema.

Revision ID: k1f2a3b4c5d6
Revises: j0e1f2a3b4c5
Create Date: 2026-09-07 12:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'k1f2a3b4c5d6'
down_revision: Union[str, None] = 'j0e1f2a3b4c5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Mundo 1 · cartas: de dónde viene cada carta ─────────────────────────
    op.add_column('cartas', sa.Column('origen', sa.String(length=12), nullable=False,
                                      server_default='dwellia'))
    op.add_column('cartas', sa.Column('autor_usuario_id', sa.String(length=36),
                                      sa.ForeignKey('usuarios.id', ondelete='SET NULL'),
                                      nullable=True))
    op.add_column('cartas', sa.Column('firma_publica', sa.String(length=40), nullable=True))
    op.create_index('ix_cartas_origen', 'cartas', ['origen'])

    # ── Mundo 2 · usuarios: opt-in a las cartas de la comunidad ─────────────
    op.add_column('usuarios', sa.Column('recibe_comunidad', sa.Boolean(), nullable=False,
                                        server_default=sa.false()))

    # ── Mundo 2 · cartas_comunidad: la propuesta y su recorrido ─────────────
    op.create_table(
        'cartas_comunidad',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('usuario_id', sa.String(length=36),
                  sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('categoria_slug', sa.String(length=40),
                  sa.ForeignKey('categorias.slug'), nullable=False),
        sa.Column('accion_slug', sa.String(length=40),
                  sa.ForeignKey('acciones.slug'), nullable=False),
        sa.Column('frase', sa.Text(), nullable=False),
        sa.Column('prompt', sa.Text(), nullable=False),
        sa.Column('firma', sa.String(length=10), nullable=False, server_default='anonima'),
        sa.Column('estado', sa.String(length=20), nullable=False, server_default='en_revision'),
        sa.Column('veredicto', sa.JSON(), nullable=True),
        sa.Column('motivo', sa.Text(), nullable=True),
        sa.Column('concepto', sa.String(length=80), nullable=True),
        sa.Column('cesion_aceptada_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('carta_id', sa.String(length=40),
                  sa.ForeignKey('cartas.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_cartas_comunidad_usuario_id', 'cartas_comunidad', ['usuario_id'])
    op.create_index('ix_cartas_comunidad_estado', 'cartas_comunidad', ['estado'])

    # ── Mundo 2 · avisos ────────────────────────────────────────────────────
    op.create_table(
        'avisos',
        sa.Column('id', sa.String(length=36), primary_key=True),
        sa.Column('usuario_id', sa.String(length=36),
                  sa.ForeignKey('usuarios.id', ondelete='CASCADE'), nullable=False),
        sa.Column('tipo', sa.String(length=20), nullable=False),
        sa.Column('referencia_id', sa.String(length=36), nullable=True),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('leido', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_avisos_usuario_id', 'avisos', ['usuario_id'])


def downgrade() -> None:
    op.drop_index('ix_avisos_usuario_id', table_name='avisos')
    op.drop_table('avisos')
    op.drop_index('ix_cartas_comunidad_estado', table_name='cartas_comunidad')
    op.drop_index('ix_cartas_comunidad_usuario_id', table_name='cartas_comunidad')
    op.drop_table('cartas_comunidad')
    op.drop_column('usuarios', 'recibe_comunidad')
    op.drop_index('ix_cartas_origen', table_name='cartas')
    op.drop_column('cartas', 'firma_publica')
    op.drop_column('cartas', 'autor_usuario_id')
    op.drop_column('cartas', 'origen')
