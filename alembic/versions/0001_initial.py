"""Esquema inicial TransitPro con PG_SEDE_LOCAL y emp_id en PG_USUARIO

Revision ID: 0001
Revises:
Create Date: 2026-06-20
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── PG_SEDE ──────────────────────────────────────────────────────────────
    op.create_table(
        "PG_SEDE",
        sa.Column("sede_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nombre",  sa.String(100), nullable=False),
        sa.Column("tipo",    sa.String(1),   nullable=False),
        sa.Column("locales", sa.String(50),  nullable=True),
        sa.Column("activa",  sa.Boolean,     nullable=False, server_default="1"),
    )

    # ── PG_SEDE_LOCAL ─────────────────────────────────────────────────────────
    # Reemplaza el campo locales VARCHAR(50) con comas.
    # Permite filtrar conductores de T_EMPLEADOS con un JOIN limpio.
    op.create_table(
        "PG_SEDE_LOCAL",
        sa.Column("id",       sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("sede_id",  sa.Integer, sa.ForeignKey("PG_SEDE.sede_id"), nullable=False),
        sa.Column("local_id", sa.Integer, nullable=False),
        sa.UniqueConstraint("sede_id", "local_id", name="uq_sede_local"),
    )
    op.create_index("ix_pg_sede_local_sede_id", "PG_SEDE_LOCAL", ["sede_id"])

    # ── PG_CLIENTE ────────────────────────────────────────────────────────────
    op.create_table(
        "PG_CLIENTE",
        sa.Column("cliente_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("nombre",     sa.String(100), nullable=False),
        sa.Column("ruc",        sa.String(20),  nullable=True),
        sa.Column("activo",     sa.Boolean,     nullable=False, server_default="1"),
    )

    # ── PG_VEHICULO ───────────────────────────────────────────────────────────
    op.create_table(
        "PG_VEHICULO",
        sa.Column("vehiculo_id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("placa",       sa.String(10),  nullable=False),
        sa.Column("marca",       sa.String(50),  nullable=True),
        sa.Column("modelo",      sa.String(50),  nullable=True),
        sa.Column("anio",        sa.Integer,     nullable=True),
        sa.Column("tipo",        sa.String(20),  nullable=True),
        sa.Column("categoria",   sa.String(50),  nullable=True),
        sa.Column("color",       sa.String(30),  nullable=True),
        sa.Column("sede_id",     sa.Integer, sa.ForeignKey("PG_SEDE.sede_id"), nullable=True),
        sa.Column("operativo",   sa.Boolean,     nullable=False, server_default="1"),
    )

    # ── PG_PARADERO ───────────────────────────────────────────────────────────
    op.create_table(
        "PG_PARADERO",
        sa.Column("paradero_id", sa.Integer,    primary_key=True, autoincrement=True),
        sa.Column("nombre",      sa.String(150), nullable=False),
        sa.Column("direccion",   sa.String(200), nullable=True),
        sa.Column("sede_id",     sa.Integer, sa.ForeignKey("PG_SEDE.sede_id"), nullable=False),
        sa.Column("activo",      sa.Boolean,     nullable=False, server_default="1"),
    )

    # ── PG_RUTA ───────────────────────────────────────────────────────────────
    op.create_table(
        "PG_RUTA",
        sa.Column("ruta_id",                  sa.Integer,    primary_key=True, autoincrement=True),
        sa.Column("nombre",                   sa.String(100), nullable=False),
        sa.Column("sede_id",                  sa.Integer, sa.ForeignKey("PG_SEDE.sede_id"),      nullable=False),
        sa.Column("cliente_id",               sa.Integer, sa.ForeignKey("PG_CLIENTE.cliente_id"), nullable=False),
        sa.Column("origen_fijo",              sa.Boolean,    nullable=False, server_default="1"),
        sa.Column("origen_texto",             sa.String(200), nullable=True),
        sa.Column("paradero_origen_id",       sa.Integer, sa.ForeignKey("PG_PARADERO.paradero_id"), nullable=True),
        sa.Column("destino_texto",            sa.String(200), nullable=True),
        sa.Column("paradero_destino_id",      sa.Integer, sa.ForeignKey("PG_PARADERO.paradero_id"), nullable=True),
        sa.Column("tiempo_estimado_min",      sa.Integer,    nullable=True),
        sa.Column("calcula_llegada",          sa.Boolean,    nullable=False, server_default="0"),
        sa.Column("requiere_dos_conductores", sa.Boolean,    nullable=False, server_default="0"),
        sa.Column("tipo_servicio",            sa.String(15), nullable=False, server_default="'PERSONAL'"),
        sa.Column("activa",                   sa.Boolean,    nullable=False, server_default="1"),
    )

    # ── PG_RUTA_PARADERO ──────────────────────────────────────────────────────
    op.create_table(
        "PG_RUTA_PARADERO",
        sa.Column("ruta_id",     sa.Integer, sa.ForeignKey("PG_RUTA.ruta_id"),         nullable=False),
        sa.Column("paradero_id", sa.Integer, sa.ForeignKey("PG_PARADERO.paradero_id"), nullable=False),
        sa.Column("orden",       sa.Integer, nullable=False, server_default="1"),
        sa.PrimaryKeyConstraint("ruta_id", "paradero_id"),
    )

    # ── PG_USUARIO ────────────────────────────────────────────────────────────
    # emp_id: vincula usuarios-conductor con T_EMPLEADOS para notificaciones Telegram.
    # roles: administrador | programador | supervisor | conductor
    op.create_table(
        "PG_USUARIO",
        sa.Column("usuario_id",    sa.Integer,    primary_key=True, autoincrement=True),
        sa.Column("nombre",        sa.String(100), nullable=False),
        sa.Column("email",         sa.String(150), nullable=True, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("telegram_id",   sa.BigInteger,  nullable=True),
        sa.Column("emp_id",        sa.Integer,     nullable=True),
        sa.Column("rol",           sa.String(20),  nullable=False),
        sa.Column("sede_id",       sa.Integer, sa.ForeignKey("PG_SEDE.sede_id"), nullable=True),
        sa.Column("activo",        sa.Boolean,     nullable=False, server_default="1"),
    )
    op.create_index("ix_pg_usuario_email",       "PG_USUARIO", ["email"],       unique=True)
    op.create_index("ix_pg_usuario_telegram_id", "PG_USUARIO", ["telegram_id"])
    op.create_index("ix_pg_usuario_emp_id",      "PG_USUARIO", ["emp_id"])

    # ── PG_SERVICIO ───────────────────────────────────────────────────────────
    op.create_table(
        "PG_SERVICIO",
        sa.Column("servicio_id",          sa.Integer,  primary_key=True, autoincrement=True),
        sa.Column("fecha",                sa.Date,     nullable=False, index=True),
        sa.Column("ruta_id",              sa.Integer,  sa.ForeignKey("PG_RUTA.ruta_id"),         nullable=False),
        sa.Column("sede_id",              sa.Integer,  sa.ForeignKey("PG_SEDE.sede_id"),          nullable=False, index=True),
        sa.Column("vehiculo_id",          sa.Integer,  sa.ForeignKey("PG_VEHICULO.vehiculo_id"),  nullable=False),
        sa.Column("conductor_id",         sa.Integer,  nullable=False),
        sa.Column("conductor2_id",        sa.Integer,  nullable=True),
        sa.Column("paradero_origen_id",   sa.Integer,  sa.ForeignKey("PG_PARADERO.paradero_id"), nullable=True),
        sa.Column("hora_inicio",          sa.Time,     nullable=True),
        sa.Column("hora_llegada_est",     sa.Time,     nullable=True),
        sa.Column("hora_llegada_real",    sa.Time,     nullable=True),
        sa.Column("fecha_llegada",        sa.Date,     nullable=True),
        sa.Column("hora_fin_manual",      sa.Time,     nullable=True),
        sa.Column("estado",               sa.String(15), nullable=False, server_default="'PROGRAMADO'"),
        sa.Column("observaciones",        sa.Text,     nullable=True),
        sa.Column("creado_por",           sa.Integer,  sa.ForeignKey("PG_USUARIO.usuario_id"), nullable=True),
        sa.Column("fecha_creacion",       sa.DateTime, nullable=False, server_default=sa.text("GETDATE()")),
        sa.Column("fecha_retorno",        sa.Date,     nullable=True),
        sa.Column("retorno_misma_unidad", sa.Boolean,  nullable=False, server_default="1"),
        sa.Column("retorno_vehiculo_id",  sa.Integer,  sa.ForeignKey("PG_VEHICULO.vehiculo_id"), nullable=True),
        sa.Column("retorno_conductor_id", sa.Integer,  nullable=True),
        sa.Column("retorno_conductor2_id",sa.Integer,  nullable=True),
        sa.Column("hora_salida_planta",   sa.Time,     nullable=True),
        sa.Column("hora_retorno_est",     sa.Time,     nullable=True),
        sa.Column("hora_retorno_real",    sa.Time,     nullable=True),
    )

    # ── PG_CONDUCTOR_DEMO ─────────────────────────────────────────────────────
    # Solo en demo mode. En producción esta tabla no existe / está vacía.
    op.create_table(
        "PG_CONDUCTOR_DEMO",
        sa.Column("emp_id",           sa.Integer,    primary_key=True),
        sa.Column("nombre_completo",  sa.String(150), nullable=False),
        sa.Column("emp_licencia",     sa.String(20),  nullable=True),
        sa.Column("emp_licencia_cat", sa.String(10),  nullable=True),
        sa.Column("emp_telefono",     sa.String(20),  nullable=True),
        sa.Column("sede_id",          sa.Integer, sa.ForeignKey("PG_SEDE.sede_id"), nullable=False),
        sa.Column("activo",           sa.Boolean,     nullable=False, server_default="1"),
    )


def downgrade() -> None:
    op.drop_table("PG_CONDUCTOR_DEMO")
    op.drop_table("PG_SERVICIO")
    op.drop_table("PG_USUARIO")
    op.drop_table("PG_RUTA_PARADERO")
    op.drop_table("PG_RUTA")
    op.drop_table("PG_PARADERO")
    op.drop_table("PG_VEHICULO")
    op.drop_table("PG_CLIENTE")
    op.drop_table("PG_SEDE_LOCAL")
    op.drop_table("PG_SEDE")
