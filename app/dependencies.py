# app/dependencies.py
from typing import AsyncGenerator
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from jose import jwt, JWTError    # python-jose for JWT decode
from app.config import get_settings
from app.database import create_engine_from_url, create_session_factory
from app.models.user import User
from sqlalchemy import select

settings = get_settings()
engine = create_engine_from_url(settings.database_url)
SessionFactory = create_session_factory(engine)

# HTTPBearer parses "Authorization: Bearer <token>" for us
bearer_scheme = HTTPBearer()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    # 'async with' ensures the session is closed even if an exception is raised
    async with SessionFactory() as session:
        yield session
        # After the route handler returns, SQLAlchemy commits or rolls back here

# Depends() allow to yield a value and FastAPI calls it auto before handler runs
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials

    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
        user_id: int = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    # Look up the user... if they were deleted after token issue, this fails cleanly
    result = await db.execute(select(User).where(User.id == int(user_id)))
    user = result.scalar_one_or_none()

    if user is None:
        raise credentials_exception

    return user