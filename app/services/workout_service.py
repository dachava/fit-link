# app/services/workout_service.py
# every query filters by both id and user_id. 
# This means a user can never read, edit, or delete another user's workout

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from app.models.workout import Workout
from app.models.exercise import Exercise
from app.schemas.workout import WorkoutCreate, WorkoutUpdate


class WorkoutService:

    async def create(self, db: AsyncSession, user_id: int, req: WorkoutCreate) -> Workout:
        workout = Workout(
            user_id=user_id,
            name=req.name,
            description=req.description,
            scheduled_at=req.scheduled_at,
        )
        db.add(workout)
        await db.flush()   # writes to DB but doesn't commit, gives us workout.id for exercises below

        for ex in req.exercises:
            db.add(Exercise(workout_id=workout.id, **ex.model_dump()))

        await db.commit()
        await db.refresh(workout)
        return workout

    async def list(self, db: AsyncSession, user_id: int) -> list[Workout]:
        result = await db.execute(
            select(Workout).where(Workout.user_id == user_id).order_by(Workout.created_at.desc())
        )
        return result.scalars().all()

    async def get(self, db: AsyncSession, user_id: int, workout_id: int) -> Workout:
        result = await db.execute(
            select(Workout).where(Workout.id == workout_id, Workout.user_id == user_id)
        )
        workout = result.scalar_one_or_none()
        if not workout:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workout not found")
        return workout

    async def update(self, db: AsyncSession, user_id: int, workout_id: int, req: WorkoutUpdate) -> Workout:
        workout = await self.get(db, user_id, workout_id)   # reuse get(), ownership check is free

        # model_dump(exclude_unset=True) only returns fields the caller actually sent
        # so a PATCH with just {"name": "x"} won't wipe out description
        for field, value in req.model_dump(exclude_unset=True).items():
            setattr(workout, field, value)

        await db.commit()
        await db.refresh(workout)
        return workout

    async def delete(self, db: AsyncSession, user_id: int, workout_id: int) -> None:
        workout = await self.get(db, user_id, workout_id)
        await db.delete(workout)
        await db.commit()