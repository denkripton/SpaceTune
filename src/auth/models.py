from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, UUID, DateTime, Date, Text, func, ForeignKey
from src.databases.sql_db import Base
import uuid


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
    )
    username: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    password: Mapped[bytes] = mapped_column(nullable=False)
    email: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)

    created_at: Mapped[DateTime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    profile: Mapped["UserProfile"] = relationship(back_populates="user")


class UserProfile(Base):
    __tablename__ = "users_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), default=uuid.uuid4, primary_key=True
    )

    birth_date: Mapped[Date] = mapped_column(Date, nullable=True)
    bio: Mapped[str] = mapped_column(Text, nullable=True)

    user_id: Mapped[str] = mapped_column(ForeignKey("users.id"), unique=True)

    user: Mapped["User"] = relationship(back_populates="profile")
