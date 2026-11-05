import uuid

from sqlalchemy import (
    UUID,
    BigInteger,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects import postgresql
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.databases import Base


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[int] = mapped_column(BigInteger)
    artists: Mapped[list[str]] = mapped_column(postgresql.ARRAY(String()))
    track_url: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    photo_url: Mapped[str | None] = mapped_column(String(100), unique=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    __table_args__ = (
        UniqueConstraint("owner_id", "name", name="uq_tracks_owner_name"),
    )

    track_grades_conn: Mapped[list["Grade"]] = relationship(
        back_populates="track_conn",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    owner_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id"))

    owner: Mapped["User"] = relationship(back_populates="track")
