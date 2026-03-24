# app/routers/workouts.py
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import get_db, get_current_user
from app.models.user import User
from app.schemas.workout import WorkoutCreate, WorkoutUpdate, WorkoutResponse
from app.services.workout_service import WorkoutService

router = APIRouter(prefix="/workouts", tags=["workouts"])
workout_service = WorkoutService()


@router.post("/", response_model=WorkoutResponse, status_code=status.HTTP_201_CREATED)
async def create_workout(
    req: WorkoutCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user), # all workout endpoints are authenticated automatically
):
    return await workout_service.create(db, current_user.id, req)


@router.get("/", response_model=list[WorkoutResponse])
async def list_workouts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await workout_service.list(db, current_user.id)


@router.get("/{workout_id}", response_model=WorkoutResponse)
async def get_workout(
    workout_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await workout_service.get(db, current_user.id, workout_id)


@router.patch("/{workout_id}", response_model=WorkoutResponse)
async def update_workout(
    workout_id: int,
    req: WorkoutUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await workout_service.update(db, current_user.id, workout_id, req)


@router.delete("/{workout_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workout(
    workout_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    await workout_service.delete(db, current_user.id, workout_id)
