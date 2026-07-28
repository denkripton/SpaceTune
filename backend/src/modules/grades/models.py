import uuid

from sqlalchemy import (
    UUID,
    DateTime,
    ForeignKey,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.databases import Base


class Grade(Base):
    __tablename__ = "grades"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
    )
    grade: Mapped[int] = mapped_column()

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"))
    track_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("tracks.id", ondelete="CASCADE")
    )

    __table_args__ = (
        UniqueConstraint("user_id", "track_id", name="uq_grades_user_track"),
    )

    track_conn: Mapped["Track"] = relationship(back_populates="track_grades_conn")
    user_conn: Mapped["User"] = relationship(back_populates="user_grades_conn")
