"""init

Revision ID: 98d7725a28d3
Revises:
Create Date: 2025-10-02 16:37:23.596113

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from open_knowledge.internal.db import JSONField
from open_knowledge.migrations.util import get_existing_tables

# revision identifiers, used by Alembic.
revision: str = '98d7725a28d3'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = get_existing_tables()

    """Upgrade schema."""
    # `file` includes the `hash` column (Text, nullable). This was previously
    # added by a follow-up migration (6155d3fbbbca) to backfill older DBs;
    # folded into the initial create here.
    if "file" not in existing_tables:
        op.create_table(
            "file",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("filename", sa.Text(), nullable=True),
            sa.Column("hash", sa.Text(), nullable=True),
            sa.Column("path", sa.Text(), nullable=True),
            sa.Column("data", JSONField(), nullable=True),
            sa.Column("meta", JSONField(), nullable=True),
            sa.Column("access_control", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    # `knowledge` was previously created in a later migration (2c8b64f21f16);
    # merged here so a from-scratch `alembic upgrade head` builds the full
    # schema in one step. Columns mirror models/knowledge.py.
    if "knowledge" not in existing_tables:
        op.create_table(
            "knowledge",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("user_id", sa.Text(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("description", sa.Text(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("data", sa.JSON(), nullable=True),
            sa.Column("access_control", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("id"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("knowledge")
    op.drop_table("file")
