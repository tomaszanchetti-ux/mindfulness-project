"""WS29 · Bloque C (Comunidad) — el contrato de datos completo

Se crea todo acá, de una vez, para que las cards C1.x corran en paralelo sin
tocar el esquema. Todo con default o NULL: cero filas afectadas.

Mundo 2 · `usuarios.perfil_publico` (default false: privado) + índices funcionales
   por `lower(email|apodo|nombre|apellido)` para la búsqueda de personas.
   Hallazgo de la Fase 0: `email` NO es único en el esquema → la búsqueda
   devuelve una LISTA, nunca "el" usuario.
Mundo 2 · `usuarios.foto_path`: la foto de perfil (pedido de Tomás, WS29).
Mundo 2 · `entregas.extra` (una Pausa que no es la del día: "Hacer ahora")
   y `entregas.de_usuario_id` (quién me hizo llegar esa carta).
Mundo 2 · `vinculos` (solicitudes y comunidad; único por PAR sin dirección),
   `reenvios` (te enviaron una ficha; da permiso de lectura mientras siga
   compartida), `guardadas` ("Pausa de <apodo>" en mi Baúl; única por par),
   `pausas_programadas` (la cola de "Programar": la próxima carta del día),
   `recomendaciones` (fichas premium del Baúl).

Revision ID: m3b4c5d6e7f8
Revises: l2a3b4c5d6e7
Create Date: 2026-09-07 18:00:00.000000
"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = 'm3b4c5d6e7f8'
down_revision: Union[str, None] = 'l2a3b4c5d6e7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _fecha(nombre: str = 'created_at') -> sa.Column:
    return sa.Column(nombre, sa.DateTime(timezone=True), nullable=False)


def _usuario(nombre: str, ondelete: str = 'CASCADE', nullable: bool = False) -> sa.Column:
    return sa.Column(nombre, sa.String(length=36),
                     sa.ForeignKey('usuarios.id', ondelete=ondelete), nullable=nullable)


def upgrade() -> None:
    # ── usuarios: perfil privado por defecto + búsqueda por texto ───────────
    op.add_column('usuarios', sa.Column('perfil_publico', sa.Boolean(), nullable=False,
                                        server_default=sa.false()))
    for col in ('email', 'apodo', 'nombre', 'apellido'):
        op.execute(f'CREATE INDEX ix_usuarios_{col}_lower ON usuarios (lower({col}))')
    # La foto de perfil vive en Storage (misma regla que las fotos de una Pausa:
    # acá solo la ruta, y la ruta lleva el usuario_id → nunca viaja al cliente).
    op.add_column('usuarios', sa.Column('foto_path', sa.String(length=300), nullable=True))

    # ── entregas: la Pausa extra y de quién vino ────────────────────────────
    op.add_column('entregas', sa.Column('extra', sa.Boolean(), nullable=False,
                                        server_default=sa.false()))
    op.add_column('entregas', _usuario('de_usuario_id', ondelete='SET NULL', nullable=True))

    # ── vinculos ────────────────────────────────────────────────────────────
    op.create_table(
        'vinculos',
        sa.Column('id', sa.String(length=36), primary_key=True),
        _usuario('solicitante_id'),
        _usuario('destinatario_id'),
        sa.Column('estado', sa.String(length=12), nullable=False, server_default='pendiente'),
        _fecha(),
        sa.Column('aceptada_at', sa.DateTime(timezone=True), nullable=True),
        sa.CheckConstraint('solicitante_id <> destinatario_id', name='ck_vinculos_no_consigo'),
    )
    op.create_index('ix_vinculos_solicitante_id', 'vinculos', ['solicitante_id'])
    op.create_index('ix_vinculos_destinatario_id', 'vinculos', ['destinatario_id'])
    # Único por PAR, sin importar quién pidió: (A,B) y (B,A) son el mismo vínculo.
    op.execute(
        'CREATE UNIQUE INDEX ux_vinculos_par ON vinculos '
        '(LEAST(solicitante_id, destinatario_id), GREATEST(solicitante_id, destinatario_id))'
    )

    # ── reenvios ────────────────────────────────────────────────────────────
    op.create_table(
        'reenvios',
        sa.Column('id', sa.String(length=36), primary_key=True),
        _usuario('de_usuario_id'),
        _usuario('a_usuario_id'),
        sa.Column('entrega_id', sa.String(length=36),
                  sa.ForeignKey('entregas.id', ondelete='CASCADE'), nullable=False),
        sa.Column('leido', sa.Boolean(), nullable=False, server_default=sa.false()),
        _fecha(),
        sa.CheckConstraint('de_usuario_id <> a_usuario_id', name='ck_reenvios_no_consigo'),
    )
    op.create_index('ix_reenvios_de_usuario_id', 'reenvios', ['de_usuario_id'])
    op.create_index('ix_reenvios_a_usuario_id', 'reenvios', ['a_usuario_id'])
    op.create_index('ix_reenvios_entrega_id', 'reenvios', ['entrega_id'])

    # ── guardadas ───────────────────────────────────────────────────────────
    op.create_table(
        'guardadas',
        sa.Column('id', sa.String(length=36), primary_key=True),
        _usuario('usuario_id'),
        sa.Column('entrega_id', sa.String(length=36),
                  sa.ForeignKey('entregas.id', ondelete='CASCADE'), nullable=False),
        _fecha(),
        sa.UniqueConstraint('usuario_id', 'entrega_id', name='ux_guardadas_usuario_entrega'),
    )
    op.create_index('ix_guardadas_usuario_id', 'guardadas', ['usuario_id'])
    op.create_index('ix_guardadas_entrega_id', 'guardadas', ['entrega_id'])

    # ── pausas_programadas ──────────────────────────────────────────────────
    op.create_table(
        'pausas_programadas',
        sa.Column('id', sa.String(length=36), primary_key=True),
        _usuario('usuario_id'),
        sa.Column('carta_id', sa.String(length=40), sa.ForeignKey('cartas.id'), nullable=False),
        _usuario('de_usuario_id', ondelete='SET NULL', nullable=True),
        sa.Column('entrega_origen_id', sa.String(length=36),
                  sa.ForeignKey('entregas.id', ondelete='SET NULL'), nullable=True),
        _fecha(),
        sa.Column('servida_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_pausas_programadas_usuario_id', 'pausas_programadas', ['usuario_id'])

    # ── recomendaciones ─────────────────────────────────────────────────────
    op.create_table(
        'recomendaciones',
        sa.Column('id', sa.String(length=36), primary_key=True),
        _usuario('usuario_id'),
        sa.Column('titulo', sa.String(length=80), nullable=False),
        sa.Column('tipo', sa.String(length=12), nullable=False, server_default='otro'),
        sa.Column('texto', sa.Text(), nullable=False),
        sa.Column('url', sa.String(length=500), nullable=True),
        sa.Column('visibilidad', sa.String(length=12), nullable=False, server_default='privada'),
        _fecha(),
        _fecha('updated_at'),
    )
    op.create_index('ix_recomendaciones_usuario_id', 'recomendaciones', ['usuario_id'])


def downgrade() -> None:
    op.drop_index('ix_recomendaciones_usuario_id', table_name='recomendaciones')
    op.drop_table('recomendaciones')
    op.drop_index('ix_pausas_programadas_usuario_id', table_name='pausas_programadas')
    op.drop_table('pausas_programadas')
    op.drop_index('ix_guardadas_entrega_id', table_name='guardadas')
    op.drop_index('ix_guardadas_usuario_id', table_name='guardadas')
    op.drop_table('guardadas')
    op.drop_index('ix_reenvios_entrega_id', table_name='reenvios')
    op.drop_index('ix_reenvios_a_usuario_id', table_name='reenvios')
    op.drop_index('ix_reenvios_de_usuario_id', table_name='reenvios')
    op.drop_table('reenvios')
    op.execute('DROP INDEX ux_vinculos_par')
    op.drop_index('ix_vinculos_destinatario_id', table_name='vinculos')
    op.drop_index('ix_vinculos_solicitante_id', table_name='vinculos')
    op.drop_table('vinculos')
    op.drop_column('entregas', 'de_usuario_id')
    op.drop_column('entregas', 'extra')
    op.drop_column('usuarios', 'foto_path')
    for col in ('email', 'apodo', 'nombre', 'apellido'):
        op.execute(f'DROP INDEX ix_usuarios_{col}_lower')
    op.drop_column('usuarios', 'perfil_publico')
