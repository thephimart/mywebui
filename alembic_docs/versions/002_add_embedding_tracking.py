"""Add embedding model tracking fields

Revision ID: 002_add_embedding_tracking
Revises: 001_initial
Create Date: 2024-01-15 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "002_add_embedding_tracking"
down_revision: str | None = "001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "embeddings",
        sa.Column("embedding_model_id", sa.String(36), nullable=True),
    )
    op.add_column(
        "embeddings",
        sa.Column("dimension", sa.Integer(), nullable=True),
    )
    op.add_column(
        "embeddings",
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_embeddings_model_id", "embeddings", ["embedding_model_id"])


def downgrade() -> None:
    op.drop_index("idx_embeddings_model_id", table_name="embeddings")
    op.drop_column("embeddings", "created_at")
    op.drop_column("embeddings", "dimension")
    op.drop_column("embeddings", "embedding_model_id")
