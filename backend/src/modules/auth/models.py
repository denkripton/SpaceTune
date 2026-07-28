import uuid
from typing import List, Optional

from sqlalchemy import UUID, DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from src.databases import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[Optional[bytes]] = mapped_column(nullable=True)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

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

    profile: Mapped["Profile"] = relationship(back_populates="user")
    track: Mapped[List["Track"]] = relationship(back_populates="owner")
    user_grades_conn: Mapped[List["Grade"]] = relationship(back_populates="user_conn")

    google_id: Mapped[Optional[str]] = mapped_column(
        String(100), unique=True, nullable=True
    )
