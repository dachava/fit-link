# app/services/exercise_service.py
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.exercise import Exercise
from app.schemas.workout import ExerciseCreate, ExerciseUpdate
from app.services.workout_service import WorkoutService

workout_service = WorkoutService()

# verify the workout belongs to the user then operate on the exercise
class ExerciseService:

    async def create(self, db: AsyncSession, user_id: int, workout_id: int, req: ExerciseCreate) -> Exercise:
        # Ownership check: if the workout doesn't belong to this user, get() raises 404
        await workout_service.get(db, user_id, workout_id)

        exercise = Exercise(workout_id=workout_id, **req.model_dump())
        db.add(exercise)
        await db.commit()
        await db.refresh(exercise)
        return exercise

    async def list(self, db: AsyncSession, user_id: int, workout_id: int) -> list[Exercise]:
        await workout_service.get(db, user_id, workout_id)

        result = await db.execute(
            select(Exercise).where(Exercise.workout_id == workout_id)
        )
        return result.scalars().all()

    async def get(self, db: AsyncSession, user_id: int, workout_id: int, exercise_id: int) -> Exercise:
        await workout_service.get(db, user_id, workout_id)

        result = await db.execute(
            select(Exercise).where(Exercise.id == exercise_id, Exercise.workout_id == workout_id)
        )
        exercise = result.scalar_one_or_none()
        if not exercise:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Exercise not found")
        return exercise

    async def update(self, db: AsyncSession, user_id: int, workout_id: int, exercise_id: int, req: ExerciseUpdate) -> Exercise:
        exercise = await self.get(db, user_id, workout_id, exercise_id)

        for field, value in req.model_dump(exclude_unset=True).items():
            setattr(exercise, field, value)

        await db.commit()
        await db.refresh(exercise)
        return exercise

    async def delete(self, db: AsyncSession, user_id: int, workout_id: int, exercise_id: int) -> None:
        exercise = await self.get(db, user_id, workout_id, exercise_id)
        await db.delete(exercise)
        await db.commit()