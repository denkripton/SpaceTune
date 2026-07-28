"""unique track owner/name constraint

Revision ID: 0003_unique_track_owner_name
Revises: 0002_cascade_delete_track_grades
Create Date: 2026-07-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0003_unique_track_owner_name"
down_revision: Union[str, Sequence[str], None] = "0002_cascade_delete_track_grades"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_unique_constraint(
        "uq_tracks_owner_name",
        "tracks",
        ["owner_id", "name"],
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_constraint(
        "uq_tracks_owner_name",
        "tracks",
        type_="unique",
    )
