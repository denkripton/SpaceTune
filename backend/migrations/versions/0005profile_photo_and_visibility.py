"""add profile photo_url and per-field visibility

Revision ID: 0005_profile_photo_and_visibility
Revises: 0004_unique_grade_user_track
Create Date: 2026-07-16 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "0005profile_photo_and_visibility"
down_revision: Union[str, Sequence[str], None] = "0004_unique_grade_user_track"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DEFAULT_VISIBLE_FIELDS = {
    "email": False,
    "phone_number": False,
    "birth_date": False,
    "bio": True,
    "country": True,
}


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "profiles", sa.Column("photo_url", sa.String(length=100), nullable=True)
    )
    op.create_unique_constraint(
        "uq_profiles_photo_url", "profiles", ["photo_url"]
    )

    # nullable=True first so the ALTER doesn't require a value for existing
    # rows, then backfill, then flip to NOT NULL — the standard three-step
    # pattern for adding a required column to a populated table.
    op.add_column(
        "profiles",
        sa.Column("visible_fields", postgresql.JSONB(), nullable=True),
    )
    op.execute(
        sa.text("UPDATE profiles SET visible_fields = :defaults").bindparams(
            sa.bindparam("defaults", value=DEFAULT_VISIBLE_FIELDS, type_=postgresql.JSONB)
        )
    )
    op.alter_column("profiles", "visible_fields", nullable=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("profiles", "visible_fields")
    op.drop_constraint("uq_profiles_photo_url", "profiles", type_="unique")
    op.drop_column("profiles", "photo_url")
