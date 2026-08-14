# app/main.py
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.routers import auth, workouts, exercises, pages
from app.dependencies import engine, settings
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

# Only matters for a browser-based client calling /auth or /workouts from a
# different origin — the reference UI is same-origin and unaffected either
# way. No known external client exists yet, so this is empty by default;
# set CORS_ORIGINS (comma-separated) once one does. allow_credentials is
# False since auth is a Bearer token, not a cookie — nothing here relies on
# credentialed cross-origin requests.
cors_origins = [origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=False,
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