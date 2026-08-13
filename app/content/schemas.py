# app/content/schemas.py
# Pydantic validation for content/exercises/*.md frontmatter and
# content/routines/*.yaml — kept separate from app/models/library.py
# because these describe the on-disk content format, not the DB schema.
from pydantic import BaseModel, Field, field_validator

VALID_CATEGORIES = {"compound", "isolation", "conditioning", "plyometric"}
VALID_EQUIPMENT = {"dumbbell", "bodyweight", "bike", "band", "none"}
VALID_BLOCK_KINDS = {"single", "superset", "circuit"}


class ExerciseFrontmatter(BaseModel):
    slug: str
    name: str
    aliases: list[str] = Field(default_factory=list)
    primary_muscle: str
    secondary_muscles: list[str] = Field(default_factory=list)
    equipment: list[str]
    category: str
    cues: list[str] = Field(default_factory=list)
    common_faults: list[str] = Field(default_factory=list)
    video_url: str | None = None
    thumbnail_url: str | None = None

    @field_validator("category")
    @classmethod
    def check_category(cls, v: str) -> str:
        if v not in VALID_CATEGORIES:
            raise ValueError(f"category must be one of {sorted(VALID_CATEGORIES)}, got {v!r}")
        return v

    @field_validator("equipment")
    @classmethod
    def check_equipment(cls, v: list[str]) -> list[str]:
        bad = set(v) - VALID_EQUIPMENT
        if bad:
            raise ValueError(f"unknown equipment {sorted(bad)}, must be subset of {sorted(VALID_EQUIPMENT)}")
        return v


class RoutineExerciseItem(BaseModel):
    exercise: str  # slug reference, cross-checked against loaded exercises
    sets: int | None = None
    reps: str
    load_note: str | None = None
    tempo: str | None = None
    rest_seconds: int | None = None
    notes: str | None = None


class RoutineBlockItem(BaseModel):
    kind: str
    rounds: int | None = None
    rest_after_seconds: int | None = None
    notes: str | None = None
    exercises: list[RoutineExerciseItem]

    @field_validator("kind")
    @classmethod
    def check_kind(cls, v: str) -> str:
        if v not in VALID_BLOCK_KINDS:
            raise ValueError(f"kind must be one of {sorted(VALID_BLOCK_KINDS)}, got {v!r}")
        return v


class RoutineFile(BaseModel):
    slug: str
    name: str
    description: str | None = None
    goal: str
    day_label: str | None = None
    estimated_minutes: int | None = None
    blocks: list[RoutineBlockItem]
