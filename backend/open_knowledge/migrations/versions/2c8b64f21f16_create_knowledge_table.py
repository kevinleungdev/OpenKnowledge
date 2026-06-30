"""create knowledge table

Revision ID: 2c8b64f21f16
Revises: 6155d3fbbbca
Create Date: 2026-06-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from open_knowledge.migrations.util import get_existing_tables

# revision identifiers, used by Alembic.
revision: str = '2c8b64f21f16'
down_revision: Union[str, Sequence[str], None] = '6155d3fbbbca'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    existing_tables = get_existing_tables()

    """Upgrade schema."""
    # The `knowledge` table was missing from the initial migration; create it
    # here so SQLite demo mode (which runs no `Base.metadata.create_all` for the
    # main engine) and Postgres both have it. Columns mirror models/knowledge.py.
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
