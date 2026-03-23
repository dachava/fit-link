# app/routers/ai.py
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from app.services.ai_service import AIService
from app.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/ai", tags=["ai"])
ai_service = AIService()


class WorkoutPlanRequest(BaseModel):
    fitness_level: str          # e.g. "beginner", "intermediate", "advanced"
    goals: list[str]            # e.g. ["weight loss", "build muscle"]


class WorkoutPlanResponse(BaseModel):
    plan: str


@router.post("/workout-plan", response_model=WorkoutPlanResponse)
async def generate_workout_plan(
    req: WorkoutPlanRequest,
    current_user: User = Depends(get_current_user),   # auth required
):
    plan = await ai_service.generate_workout_plan(req.fitness_level, req.goals)
    return WorkoutPlanResponse(plan=plan)