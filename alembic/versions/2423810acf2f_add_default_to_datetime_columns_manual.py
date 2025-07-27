"""Add default to datetime columns (manual)

Revision ID: 2423810acf2f
Revises: 03001bb4f54a
Create Date: 2025-07-27 03:01:57.856102

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '2423810acf2f'
down_revision: Union[str, Sequence[str], None] = '03001bb4f54a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
