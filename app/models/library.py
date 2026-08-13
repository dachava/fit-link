# app/models/library.py
# Reference-library schema: exercises, routines, and the block structure that
# groups exercises into supersets/circuits. Deliberately separate from
# app/models/exercise.py (the workout-logger's per-set log entries) — same
# real-world word "exercise", different entity, different table.
import enum
from sqlalchemy import String, Text, Integer, ForeignKey, Enum, UniqueConstraint
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.database import Base


class BlockKind(str, enum.Enum):
    single = "single"
    superset = "superset"
    circuit = "circuit"


class LibraryExercise(Base):
    __tablename__ = "library_exercises"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    aliases: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    primary_muscle: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    secondary_muscles: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    equipment: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    setup: Mapped[str] = mapped_column(Text, nullable=False)
    execution: Mapped[str] = mapped_column(Text, nullable=False)
    cues: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    common_faults: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)

    video_url: Mapped[str | None] = mapped_column(String(500))
    thumbnail_url: Mapped[str | None] = mapped_column(String(500))

    block_exercises: Mapped[list["BlockExercise"]] = relationship(back_populates="exercise")


class Routine(Base):
    __tablename__ = "routines"

    id: Mapped[int] = mapped_column(primary_key=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)

    goal: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    day_label: Mapped[str | None] = mapped_column(String(100))
    estimated_minutes: Mapped[int | None] = mapped_column(Integer)

    blocks: Mapped[list["RoutineBlock"]] = relationship(
        back_populates="routine",
        cascade="all, delete-orphan",
        order_by="RoutineBlock.order",
    )


class RoutineBlock(Base):
    __tablename__ = "routine_blocks"
    __table_args__ = (UniqueConstraint("routine_id", "order", name="uq_routine_block_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    routine_id: Mapped[int] = mapped_column(
        ForeignKey("routines.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)

    kind: Mapped[BlockKind] = mapped_column(Enum(BlockKind, name="block_kind"), nullable=False)
    rounds: Mapped[int | None] = mapped_column(Integer)
    rest_after_seconds: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    routine: Mapped["Routine"] = relationship(back_populates="blocks")
    exercises: Mapped[list["BlockExercise"]] = relationship(
        back_populates="block",
        cascade="all, delete-orphan",
        order_by="BlockExercise.order",
    )


class BlockExercise(Base):
    __tablename__ = "block_exercises"
    __table_args__ = (UniqueConstraint("block_id", "order", name="uq_block_exercise_order"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    block_id: Mapped[int] = mapped_column(
        ForeignKey("routine_blocks.id", ondelete="CASCADE"), nullable=False, index=True
    )
    order: Mapped[int] = mapped_column(Integer, nullable=False)
    exercise_id: Mapped[int] = mapped_column(ForeignKey("library_exercises.id"), nullable=False, index=True)

    sets: Mapped[int | None] = mapped_column(Integer)
    reps: Mapped[str] = mapped_column(String(50), nullable=False)  # free text: "8-10", "AMRAP", "30s", "400m"
    load_note: Mapped[str | None] = mapped_column(String(255))
    tempo: Mapped[str | None] = mapped_column(String(50))
    rest_seconds: Mapped[int | None] = mapped_column(Integer)
    notes: Mapped[str | None] = mapped_column(Text)

    block: Mapped["RoutineBlock"] = relationship(back_populates="exercises")
    exercise: Mapped["LibraryExercise"] = relationship(back_populates="block_exercises")
