# app/database.py
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase


# DeclarativeBase is the SQLAlchemy 2.0 way... replaces the old declarative_base() call
class Base(DeclarativeBase):
    pass


def create_engine_from_url(database_url: str):
    # asyncpg is the async PostgreSQL driver... faster than psycopg2
    # The URL format: postgresql+asyncpg://user:password@host/dbname
    async_url = database_url.replace("postgresql://", "postgresql+asyncpg://")

    return create_async_engine(
        async_url,
        pool_size=10,        # keep 10 connections open... good for EKS
        max_overflow=20,     # allow up to 20 extra during spikes
        pool_pre_ping=True,  # test connections before using... handles RDS failovers
        echo=False,          # set True locally to see every SQL statement
    )


# async_sessionmaker is the 2.0 equivalent of sessionmaker
# expire_on_commit=False means objects stay usable after commit (important for async)
def create_session_factory(engine):
    return async_sessionmaker(
        engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )