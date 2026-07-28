"""unique grade user/track constraint

Revision ID: 0004_unique_grade_user_track
Revises: 0003_unique_track_owner_name
Create Date: 2026-07-14 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0004_unique_grade_user_track"
down_revision: Union[str, Sequence[str], None] = "0003_unique_track_owner_name"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_grades_user_track",
        "grades",
        ["user_id", "track_id"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_grades_user_track",
        "grades",
        type_="unique",
    )
