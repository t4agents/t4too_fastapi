"""grant too_inv schema usage to authenticated

Revision ID: c91f2b6e4d10
Revises: 89a0f5767289
Create Date: 2026-04-19 11:05:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c91f2b6e4d10"
down_revision: Union[str, None] = "89a0f5767289"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("GRANT USAGE ON SCHEMA too_inv TO authenticated")
    op.execute(
        "GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA too_inv TO authenticated"
    )
    op.execute("GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA too_inv TO authenticated")
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA too_inv GRANT SELECT, INSERT, UPDATE, DELETE ON TABLES TO authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA too_inv GRANT USAGE, SELECT ON SEQUENCES TO authenticated"
    )


def downgrade() -> None:
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA too_inv REVOKE USAGE, SELECT ON SEQUENCES FROM authenticated"
    )
    op.execute(
        "ALTER DEFAULT PRIVILEGES IN SCHEMA too_inv REVOKE SELECT, INSERT, UPDATE, DELETE ON TABLES FROM authenticated"
    )
    op.execute(
        "REVOKE SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA too_inv FROM authenticated"
    )
    op.execute("REVOKE USAGE, SELECT ON ALL SEQUENCES IN SCHEMA too_inv FROM authenticated")
    op.execute("REVOKE USAGE ON SCHEMA too_inv FROM authenticated")
