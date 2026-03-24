# app/routers/exercises.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.workout import ExerciseCreate, ExerciseUpdate, ExerciseResponse
from app.services.exercise_service import ExerciseService

# nested under /workouts: makes the ownership hierarchy clear in the URL
router = APIRouter(prefix="/workouts/{workout_id}/exercises", tags=["exercises"])
exercise_service = ExerciseService()


@router.post("/", response_model=ExerciseResponse, status_code=status.HTTP_201_CREATED)
async def create_exercise(
    workout_id: int,
    req: ExerciseCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await exercise_service.create(db, current_user.id, workout_id, req)


@router.get("/", response_model=list[ExerciseResponse])
async def list_exercises(
    workout_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await exercise_service.list(db, current_user.id, workout_id)


@router.get("/{exercise_id}", response_model=ExerciseResponse)
async def get_exercise(
    workout_id: int,
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await exercise_service.get(db, current_user.id, workout_id, exercise_id)


@router.patch("/{exercise_id}", response_model=ExerciseResponse)
async def update_exercise(
    workout_id: int,
    exercise_id: int,
    req: ExerciseUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await exercise_service.update(db, current_user.id, workout_id, exercise_id, req)


@router.delete("/{exercise_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_exercise(
    workout_id: int,
    exercise_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await exercise_service.delete(db, current_user.id, workout_id, exercise_id)