import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.database import Base
from app.config import get_settings
import app.models.user
import app.models.workout
import app.models.exercise
import app.models.library

settings = get_settings()
config = context.config
target_metadata = Base.metadata


def do_migrations(connection):
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online():
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    )

    async def do_run():
        async with engine.connect() as conn:
            await conn.run_sync(do_migrations)

    asyncio.run(do_run())


run_migrations_online()