"""cascade delete track grades

Revision ID: 0002_cascade_delete_track_grades
Revises: 0001_initial_schema
Create Date: 2026-06-25 14:20:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "0002_cascade_delete_track_grades"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.drop_constraint("grades_track_id_fkey", "grades", type_="foreignkey")
    op.create_foreign_key(
        "grades_track_id_fkey",
        "grades",
        "tracks",
        ["track_id"],
        ["id"],
        ondelete="CASCADE",
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint("grades_track_id_fkey", "grades", type_="foreignkey")
    op.create_foreign_key(
        "grades_track_id_fkey",
        "grades",
        "tracks",
        ["track_id"],
        ["id"],
    )
