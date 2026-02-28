"""Initial audit events table

Revision ID: 001
Revises:
Create Date: 2026-02-28

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "audit_events",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("timestamp", sa.DateTime, nullable=False),
        sa.Column("user_id", sa.String(36), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("event_type", sa.String(50), nullable=False),
        sa.Column("details", sa.JSON, default={}),
        sa.Column("request_id", sa.String(36), nullable=True),
    )
    op.create_index("idx_audit_timestamp", "audit_events", ["timestamp"])
    op.create_index("idx_audit_user", "audit_events", ["user_id"])
    op.create_index("idx_audit_type", "audit_events", ["event_type"])


def downgrade() -> None:
    op.drop_index("idx_audit_type")
    op.drop_index("idx_audit_user")
    op.drop_index("idx_audit_timestamp")
    op.drop_table("audit_events")
