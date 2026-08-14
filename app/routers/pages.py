# app/routers/pages.py
# Read-only reference UI. No auth — this is a single-user lookup tool
# gated by Cloudflare Access at the proxy, not the app's JWT layer.
from itertools import groupby
from pathlib import Path

from fastapi import APIRouter, Depends, Query, Request
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.content.render import render_markdown
from app.dependencies import get_db
from app.models.library import BlockExercise, LibraryExercise, Routine, RoutineBlock

router = APIRouter(tags=["pages"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/manifest.json", include_in_schema=False)
async def manifest():
    return FileResponse(STATIC_DIR / "manifest.json", media_type="application/manifest+json")


@router.get("/sw.js", include_in_schema=False)
async def service_worker():
    # Served at root (not /static/js/) so its default scope covers the whole
    # app — a service worker can only control paths at or below its own URL.
    return FileResponse(
        STATIC_DIR / "js" / "sw.js",
        media_type="text/javascript",
        headers={"Cache-Control": "no-cache"},
    )


@router.get("/offline", response_class=HTMLResponse, include_in_schema=False)
async def offline_page(request: Request):
    return templates.TemplateResponse("offline.html", {"request": request, "active_nav": ""})


@router.get("/", response_class=HTMLResponse)
async def routine_index(request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Routine).order_by(Routine.goal, Routine.name))
    routines = result.scalars().all()
    groups = [(goal, list(items)) for goal, items in groupby(routines, key=lambda r: r.goal)]

    return templates.TemplateResponse(
        "index.html",
        {"request": request, "groups": groups, "active_nav": "routines"},
    )


@router.get("/routines/{slug}", response_class=HTMLResponse)
async def routine_detail(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(Routine)
        .options(
            selectinload(Routine.blocks)
            .selectinload(RoutineBlock.exercises)
            .selectinload(BlockExercise.exercise)
        )
        .where(Routine.slug == slug)
    )
    routine = result.scalar_one_or_none()

    if routine is None:
        return templates.TemplateResponse(
            "not_found.html",
            {"request": request, "message": f"No routine found for '{slug}'.", "active_nav": "routines"},
            status_code=404,
        )

    return templates.TemplateResponse(
        "routine_detail.html",
        {"request": request, "routine": routine, "active_nav": "routines"},
    )


EQUIPMENT_ORDER = ["dumbbell", "bodyweight", "bike", "band", "none"]


def _filter_exercises(
    exercises: list[LibraryExercise], q: str, muscle: str, equipment: list[str]
) -> list[LibraryExercise]:
    q = q.strip().lower()
    filtered = exercises

    if q:
        filtered = [
            e
            for e in filtered
            if q in e.name.lower()
            or q in e.primary_muscle.lower()
            or any(q in alias.lower() for alias in e.aliases)
        ]
    if muscle:
        filtered = [e for e in filtered if e.primary_muscle == muscle]
    if equipment:
        wanted = set(equipment)
        filtered = [e for e in filtered if wanted & set(e.equipment)]

    return filtered


@router.get("/exercises", response_class=HTMLResponse)
async def exercises_page(
    request: Request,
    q: str = "",
    muscle: str = "",
    equipment: list[str] = Query(default=[]),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(LibraryExercise).order_by(LibraryExercise.name))
    all_exercises = result.scalars().all()

    filtered = _filter_exercises(all_exercises, q, muscle, equipment)
    muscles = sorted({e.primary_muscle for e in all_exercises})
    all_equipment = {eq for e in all_exercises for eq in e.equipment}
    equipment_options = [eq for eq in EQUIPMENT_ORDER if eq in all_equipment]

    context = {
        "request": request,
        "exercises": filtered,
        "muscles": muscles,
        "equipment_options": equipment_options,
        "q": q,
        "muscle": muscle,
        "equipment": equipment,
        "active_nav": "exercises",
    }

    template_name = "_exercise_list.html" if request.headers.get("HX-Request") else "exercises.html"
    return templates.TemplateResponse(template_name, context)


@router.get("/exercises/{slug}", response_class=HTMLResponse)
async def exercise_detail(slug: str, request: Request, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(LibraryExercise).where(LibraryExercise.slug == slug))
    exercise = result.scalar_one_or_none()

    if exercise is None:
        return templates.TemplateResponse(
            "not_found.html",
            {"request": request, "message": f"No exercise found for '{slug}'.", "active_nav": "exercises"},
            status_code=404,
        )

    return templates.TemplateResponse(
        "exercise_detail.html",
        {
            "request": request,
            "exercise": exercise,
            "setup_html": render_markdown(exercise.setup),
            "execution_html": render_markdown(exercise.execution),
            "active_nav": "exercises",
        },
    )
