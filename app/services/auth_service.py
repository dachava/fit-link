# app/services/auth_service.py
# The service handles all the logic, the router just wires HTTP to the service
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException, status
from passlib.context import CryptContext   # bcrypt hashing
from jose import jwt
from datetime import datetime, timedelta, timezone
from app.models.user import User
from app.schemas.auth import RegisterRequest, TokenResponse
from app.config import get_settings

settings = get_settings()
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:

    @staticmethod
    def hash_password(plain: str) -> str:
        return pwd_context.hash(plain)

    @staticmethod
    def verify_password(plain: str, hashed: str) -> bool:
        return pwd_context.verify(plain, hashed)

    @staticmethod
    def create_access_token(user_id: int) -> str:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.access_token_expire_minutes)
        payload = {"sub": str(user_id), "exp": expire}
        return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

    async def register(self, db: AsyncSession, req: RegisterRequest) -> TokenResponse:
        # Check for existing user
        result = await db.execute(select(User).where(User.email == req.email))
        if result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(email=req.email, hashed_password=self.hash_password(req.password))
        db.add(user)
        await db.commit()
        await db.refresh(user)   # loads the auto-generated id back into the object

        return TokenResponse(access_token=self.create_access_token(user.id))

    async def login(self, db: AsyncSession, email: str, password: str) -> TokenResponse:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalar_one_or_none()

        if not user or not self.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials",
            )
        return TokenResponse(access_token=self.create_access_token(user.id))