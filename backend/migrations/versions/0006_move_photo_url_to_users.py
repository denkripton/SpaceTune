"""move photo_url from profiles to users

Revision ID: 0006_move_photo_url_to_users
Revises: 0005profile_photo_and_visibility
Create Date: 2026-07-19 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0006_move_photo_url_to_users"
down_revision: Union[str, Sequence[str], None] = "0005profile_photo_and_visibility"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # photo_url moves from profiles -> users: a profile photo is a base
    # identity attribute (like username), not an optional profile detail
    # (bio, birth_date, country). Under the old schema, a user without a
    # Profile row (profile creation is optional) could never upload a
    # photo at all — this migration removes that dependency.
    op.add_column(
        "users", sa.Column("photo_url", sa.String(length=100), nullable=True)
    )
    op.create_unique_constraint("uq_users_photo_url", "users", ["photo_url"])

    # Backfill: copy any existing profile photos onto the owning user
    # row before the column is dropped from profiles.
    op.execute(
        sa.text(
            """
            UPDATE users
            SET photo_url = profiles.photo_url
            FROM profiles
            WHERE profiles.user_id = users.id
              AND profiles.photo_url IS NOT NULL
            """
        )
    )

    op.drop_constraint("uq_profiles_photo_url", "profiles", type_="unique")
    op.drop_column("profiles", "photo_url")


def downgrade() -> None:
    """Downgrade schema."""
    op.add_column(
        "profiles", sa.Column("photo_url", sa.String(length=100), nullable=True)
    )
    op.create_unique_constraint(
        "uq_profiles_photo_url", "profiles", ["photo_url"]
    )

    op.execute(
        sa.text(
            """
            UPDATE profiles
            SET photo_url = users.photo_url
            FROM users
            WHERE users.id = profiles.user_id
              AND users.photo_url IS NOT NULL
            """
        )
    )

    op.drop_constraint("uq_users_photo_url", "users", type_="unique")
    op.drop_column("users", "photo_url")
