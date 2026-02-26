"""Initial user history schema

Revision ID: 001_initial
Revises:
Create Date: 2024-01-01 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "sessions",
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("session_token", sa.String(36), nullable=False),
        sa.Column("user_id", sa.String(36), nullable=False),
        sa.Column("issued_at", sa.DateTime(), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False, server_default="0"),
        sa.Column("last_activity", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("session_id"),
    )
    op.create_index("idx_sessions_token", "sessions", ["session_token"], unique=True)
    op.create_index("idx_sessions_user", "sessions", ["user_id"])

    op.create_table(
        "messages",
        sa.Column("msg_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("role", sa.String(20), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("timestamp", sa.DateTime(), nullable=False),
        sa.Column("raw_json", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("msg_id"),
    )
    op.create_index("idx_messages_session", "messages", ["session_id"])

    op.create_table(
        "summaries",
        sa.Column("summary_id", sa.String(36), nullable=False),
        sa.Column("session_id", sa.String(36), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("embedding", sa.JSON(), nullable=True),
        sa.ForeignKeyConstraint(["session_id"], ["sessions.session_id"]),
        sa.PrimaryKeyConstraint("summary_id"),
    )
    op.create_index("idx_summaries_session", "summaries", ["session_id"])


def downgrade() -> None:
    op.drop_table("summaries")
    op.drop_table("messages")
    op.drop_table("sessions")
