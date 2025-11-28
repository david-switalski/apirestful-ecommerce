"""Add role and hashed_refresh_token in User model

Revision ID: c70baa783625
Revises: 04ae7ff32cdb
Create Date: 2025-08-05 10:17:23.439259

"""

from typing import Sequence
from typing import Union

import sqlalchemy as sa

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c70baa783625"  # pragma: allowlist secret
down_revision: Union[str, Sequence[str], None] = "04ae7ff32cdb"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""

    op.execute("CREATE TYPE user_role_enum AS ENUM ('admin', 'user');")

    op.add_column(
        "user",
        sa.Column(
            "role", sa.Enum("admin", "user", name="user_role_enum"), nullable=False
        ),
    )
    op.add_column(
        "user", sa.Column("hashed_refresh_token", sa.String(length=512), nullable=True)
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("user", "hashed_refresh_token")
    op.drop_column("user", "role")

    op.execute("DROP TYPE user_role_enum;")
    # ### end Alembic commands ###
