"""Add id_conductor_unigis to conductores

Revision ID: 0002
Revises: 0001
Create Date: 2026-06-11 00:00:00.000000
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: Union[str, None] = "0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "conductores",
        sa.Column("id_conductor_unigis", sa.Integer(), nullable=True),
    )
    op.create_index(
        "ix_conductores_id_conductor_unigis",
        "conductores",
        ["id_conductor_unigis"],
    )


def downgrade() -> None:
    op.drop_index("ix_conductores_id_conductor_unigis", table_name="conductores")
    op.drop_column("conductores", "id_conductor_unigis")
