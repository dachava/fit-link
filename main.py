from datetime import date
from typing import Optional
from uuid import UUID, uuid4

from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel

app = FastAPI(title="Workout Tracker")

db: dict[UUID, dict] = {}


class WorkoutIn(BaseModel):
    name: str
    exercises: list[str]
    date: date
    notes: Optional[str] = None


class WorkoutOut(WorkoutIn):
    id: UUID


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/workouts", response_model=list[WorkoutOut])
def list_workouts():
    return list(db.values())


@app.post("/workouts", response_model=WorkoutOut, status_code=status.HTTP_201_CREATED)
def create_workout(payload: WorkoutIn):
    workout_id = uuid4()
    workout = {"id": workout_id, **payload.model_dump()}
    db[workout_id] = workout
    return workout


@app.get("/workouts/{id}", response_model=WorkoutOut)
def get_workout(id: UUID):
    workout = db.get(id)
    if not workout:
        raise HTTPException(status_code=404, detail="Workout not found")
    return workout


@app.delete("/workouts/{id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_workout(id: UUID):
    if id not in db:
        raise HTTPException(status_code=404, detail="Workout not found")
    del db[id]
