# app/main.py
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import auth, workouts, exercises, pages
from app.dependencies import engine
from app.database import Base

STATIC_DIR = Path(__file__).resolve().parent / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once at startup... good place to verify DB connection
    # In production, Alembic handles schema creation, don't use create_all here
    yield
    # Runs on shutdown... close the connection pool gracefully
    await engine.dispose()


app = FastAPI(
    title="fit-link",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],    # tighten this to your frontend domain in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(exercises.router)
app.include_router(pages.router)


@app.get("/health")
async def health():
    return {"status": "ok"}