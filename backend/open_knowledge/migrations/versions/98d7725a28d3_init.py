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
    if "chat" not in existing_tables:
        op.create_table(
            "chat",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("chat", sa.JSON(), nullable=True),
            sa.Column("share_id", sa.Text(), nullable=True),
            sa.Column("archived", sa.Boolean(), nullable=True),
            sa.Column("pinned", sa.Boolean(), nullable=True),
            sa.Column("meta", sa.JSON(), nullable=True),
            sa.Column("folder_id", sa.String(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
            sa.UniqueConstraint("share_id"),
        )
    
    if "chatidtag" not in existing_tables:
        op.create_table(
            "chatidtag",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("tag_name", sa.String(), nullable=True),
            sa.Column("chat_id", sa.String(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "document" not in existing_tables:
        op.create_table(
            "document",
            sa.Column("collection_name", sa.String(), nullable=False),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("filename", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("timestamp", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("collection_name"),
            sa.UniqueConstraint("name"),
        )

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

    if "model" not in existing_tables:
        op.create_table(
            "model",
            sa.Column("id", sa.Text(), nullable=False),
            sa.Column("user_id", sa.Text(), nullable=True),
            sa.Column("base_model_id", sa.Text(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("params", JSONField(), nullable=True),
            sa.Column("meta", JSONField(), nullable=True),
            sa.Column("access_control", sa.JSON(), nullable=True),
            sa.Column("is_active", sa.Boolean(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "prompt" not in existing_tables:
        op.create_table(
            "prompt",
            sa.Column("command", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("title", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("access_control", sa.JSON(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("command"),
        )

    if "tag" not in existing_tables:
        op.create_table(
            "tag",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("name", sa.String(), nullable=True),
            sa.Column("meta", JSONField(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )

    if "tool" not in existing_tables:
        op.create_table(
            "tool",
            sa.Column("id", sa.String(), nullable=False),
            sa.Column("user_id", sa.String(), nullable=True),
            sa.Column("name", sa.Text(), nullable=True),
            sa.Column("content", sa.Text(), nullable=True),
            sa.Column("specs", JSONField(), nullable=True),
            sa.Column("meta", JSONField(), nullable=True),
            sa.Column("valves", JSONField(), nullable=True),
            sa.Column("access_control", sa.JSON(), nullable=True),
            sa.Column("updated_at", sa.BigInteger(), nullable=True),
            sa.Column("created_at", sa.BigInteger(), nullable=True),
            sa.PrimaryKeyConstraint("id"),
        )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("tool")
    op.drop_table("tag")
    op.drop_table("prompt")
    op.drop_table("model")
    op.drop_table("file")
    op.drop_table("document")
    op.drop_table("chatidtag")
    op.drop_table("chat")
