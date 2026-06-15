"""initial inspections table

Revision ID: 0001
Revises:
Create Date: 2026-06-15
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "inspections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=32), nullable=False),
        sa.Column("image_name", sa.String(length=255), nullable=True),
        sa.Column("label", sa.String(length=64), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("is_defect", sa.Boolean(), nullable=False),
        sa.Column("report", sa.Text(), nullable=True),
        sa.Column("model_backend", sa.String(length=32), nullable=False),
        sa.Column("latency_ms", sa.Float(), nullable=False),
    )
    op.create_index("ix_inspections_created_at", "inspections", ["created_at"])
    op.create_index("ix_inspections_label", "inspections", ["label"])


def downgrade() -> None:
    op.drop_index("ix_inspections_label", table_name="inspections")
    op.drop_index("ix_inspections_created_at", table_name="inspections")
    op.drop_table("inspections")
