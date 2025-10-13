"""update file table hash

Revision ID: 6155d3fbbbca
Revises: 98d7725a28d3
Create Date: 2025-10-13 01:56:26.249446

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '6155d3fbbbca'
down_revision: Union[str, Sequence[str], None] = '98d7725a28d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    columns = inspector.get_columns("file")
    column_dict = {col["name"]: col for col in columns}

    if "hash" not in column_dict:
        op.add_column("file", sa.Column("hash", sa.Text(), nullable=True))
    else:
        pass



def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("file", "hash")
