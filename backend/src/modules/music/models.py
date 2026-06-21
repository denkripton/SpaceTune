import uuid
from typing import Optional, List

from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects import postgresql
from sqlalchemy import (
    String,
    UUID,
    DateTime,
    func,
    ForeignKey,
    BigInteger,
)

from src.databases import Base


class Track(Base):
    __tablename__ = "tracks"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
    )

    name: Mapped[str] = mapped_column(String(100), nullable=False)
    duration: Mapped[int] = mapped_column(BigInteger)
    artists: Mapped[List[str]] = mapped_column(postgresql.ARRAY(String()))
    track_url: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    photo_url: Mapped[Optional[str]] = mapped_column(String(100), unique=True)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        server_onupdate=func.now(),
        nullable=False,
    )

    track_grades_conn: Mapped[List["Grade"]] = relationship(back_populates="track_conn")

    owner_id: Mapped[str] = mapped_column(ForeignKey("users.id"))

    owner: Mapped["User"] = relationship(back_populates="track")
