# alembic/env.py: key parts
import asyncio
from logging.config import fileConfig
from sqlalchemy.ext.asyncio import create_async_engine
from alembic import context
from app.database import Base
from app.config import get_settings
import app.models  # noqa: importing models registers them with Base.metadata

settings = get_settings()
config = context.config
target_metadata = Base.metadata


def run_migrations_online():
    engine = create_async_engine(
        settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
    )

    async def do_run():
        async with engine.connect() as conn:
            await conn.run_sync(context.configure, connection=conn, target_metadata=target_metadata)
            async with context.begin_transaction():
                await conn.run_sync(context.run_migrations)

    asyncio.run(do_run())
```
```
# requirements.txt
fastapi==0.115.0
uvicorn[standard]==0.30.0
sqlalchemy==2.0.36
alembic==1.13.3
asyncpg==0.29.0
pydantic[email]==2.9.2
pydantic-settings==2.5.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
boto3==1.35.0
httpx==0.27.2        # for async test client