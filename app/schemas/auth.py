# app/schemas/auth.py
from pydantic import BaseModel, EmailStr


class RegisterRequest(BaseModel):
    email: EmailStr        # Pydantic validates this is a real email format
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


# What we return about the logged-in user... NEVER include the password hash here
class UserResponse(BaseModel):
    id: int
    email: str

    model_config = {"from_attributes": True}  # allows building from ORM objects