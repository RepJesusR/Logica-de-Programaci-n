"""Initial schema — Zuvra Compliance v1

Revision ID: 0001
Revises:
Create Date: 2024-01-01 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── tenants ────────────────────────────────────────────────────────
    op.create_table(
        "tenants",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nombre", sa.String(120), nullable=False),
        sa.Column("slug", sa.String(60), nullable=False),
        sa.Column("unigis_wsdl_url", sa.String(500), nullable=False),
        sa.Column("unigis_api_key", sa.String(200), nullable=False),
        sa.Column("unigis_login", sa.String(100), nullable=False),
        sa.Column("unigis_password", sa.String(200), nullable=False),
        sa.Column("dias_preaviso_default", sa.Integer(), nullable=False, server_default="15"),
        sa.Column("notificar_whatsapp", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("notificar_email", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("admin_email", sa.String(200), nullable=True),
        sa.Column("admin_whatsapp", sa.String(30), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_tenants_id", "tenants", ["id"])
    op.create_index("ix_tenants_slug", "tenants", ["slug"], unique=True)

    # ── conductores ───────────────────────────────────────────────────
    op.create_table(
        "conductores",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("tenant_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("nro_documento", sa.String(30), nullable=False),
        sa.Column("login", sa.String(100), nullable=True),
        sa.Column("nombre", sa.String(200), nullable=True),
        sa.Column("apellido", sa.String(200), nullable=True),
        sa.Column("email", sa.String(200), nullable=True),
        sa.Column("telefono", sa.String(30), nullable=True),
        sa.Column("ultimo_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["tenant_id"], ["tenants.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("tenant_id", "nro_documento", name="uq_tenant_nro_documento"),
    )
    op.create_index("ix_conductores_id", "conductores", ["id"])
    op.create_index("ix_conductores_tenant_id", "conductores", ["tenant_id"])
    op.create_index("ix_conductores_nro_documento", "conductores", ["nro_documento"])

    # ── documentos ────────────────────────────────────────────────────
    op.create_table(
        "documentos",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("conductor_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("documento_id_unigis", sa.Integer(), nullable=True),
        sa.Column("tipo_documento_id_unigis", sa.Integer(), nullable=False),
        sa.Column("tipo_documento_nombre", sa.String(200), nullable=False),
        sa.Column("fecha_vencimiento", sa.Date(), nullable=True),
        sa.Column("dias_preaviso", sa.Integer(), nullable=False, server_default="15"),
        sa.Column(
            "estado",
            sa.Enum("VIGENTE", "POR_VENCER", "VENCIDO", "SIN_DOCUMENTO", name="estadodocumento"),
            nullable=False,
            server_default="SIN_DOCUMENTO",
        ),
        sa.Column("dias_para_vencer", sa.Integer(), nullable=True),
        sa.Column("ultimo_sync", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["conductor_id"], ["conductores.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("conductor_id", "tipo_documento_id_unigis", name="uq_conductor_tipo_doc"),
    )
    op.create_index("ix_documentos_id", "documentos", ["id"])
    op.create_index("ix_documentos_conductor_id", "documentos", ["conductor_id"])

    # ── notificaciones ────────────────────────────────────────────────
    op.create_table(
        "notificaciones",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("documento_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            "canal",
            sa.Enum("WHATSAPP", "EMAIL", name="canalnotificacion"),
            nullable=False,
        ),
        sa.Column("destinatario", sa.String(200), nullable=False),
        sa.Column("asunto", sa.String(300), nullable=True),
        sa.Column("cuerpo", sa.Text(), nullable=False),
        sa.Column("external_id", sa.String(200), nullable=True),
        sa.Column("enviado_ok", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("error_detalle", sa.Text(), nullable=True),
        sa.Column("fecha_envio", sa.DateTime(timezone=True), server_default=sa.text("now()")),
        sa.ForeignKeyConstraint(["documento_id"], ["documentos.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notificaciones_id", "notificaciones", ["id"])
    op.create_index("ix_notificaciones_documento_id", "notificaciones", ["documento_id"])
    op.create_index("ix_notificaciones_fecha_envio", "notificaciones", ["fecha_envio"])


def downgrade() -> None:
    op.drop_table("notificaciones")
    op.drop_table("documentos")
    op.drop_table("conductores")
    op.drop_table("tenants")
    op.execute("DROP TYPE IF EXISTS estadodocumento")
    op.execute("DROP TYPE IF EXISTS canalnotificacion")
