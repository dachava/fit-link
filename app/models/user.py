# app/models/user.py
from datetime import datetime
from sqlalchemy import String, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class User(Base):
    __tablename__ = "users"

    # mapped_column with Mapped[type]: SQLAlchemy infers the column type from the Python type
    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)

    # server_default means Postgres sets this, not Python: more reliable for distributed apps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # One user has many workouts: back_populates wires up the reverse side
    workouts: Mapped[list["Workout"]] = relationship(back_populates="user", cascade="all, delete-orphan")