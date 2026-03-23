# app/schemas/workout.py
from datetime import datetime
from pydantic import BaseModel


class ExerciseBase(BaseModel):
    name: str
    sets: int | None = None
    reps: int | None = None
    weight_kg: float | None = None
    duration_seconds: int | None = None
    notes: str | None = None


class ExerciseCreate(ExerciseBase):
    pass   # same fields: having a separate class lets you add workout_id later


class ExerciseResponse(ExerciseBase):
    id: int
    workout_id: int
    model_config = {"from_attributes": True}


class WorkoutBase(BaseModel):
    name: str
    description: str | None = None
    scheduled_at: datetime | None = None


class WorkoutCreate(WorkoutBase):
    exercises: list[ExerciseCreate] = []   # create exercises inline with a workout


class WorkoutUpdate(BaseModel):
    # All fields optional, you only send what you want to change (PATCH semantics)
    name: str | None = None
    description: str | None = None
    scheduled_at: datetime | None = None


class WorkoutResponse(WorkoutBase):
    id: int
    user_id: int
    exercises: list[ExerciseResponse] = []
    created_at: datetime
    model_config = {"from_attributes": True}