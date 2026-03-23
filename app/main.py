# app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, workouts, exercises, ai
from app.dependencies import engine
from app.database import Base


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

app.include_router(auth.router)
app.include_router(workouts.router)
app.include_router(exercises.router)
app.include_router(ai.router)


@app.get("/health")
async def health():
    return {"status": "ok"}