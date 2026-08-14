# app/config.py
from pydantic_settings import BaseSettings # Reads values from env variables
from functools import lru_cache


class Settings(BaseSettings): # These become env variables
    # Database: will come from Kubernetes secret in EKS
    database_url: str

    # JWT: keep this secret, rotate it periodically
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Deploy-only: not read by the app itself. Declared so the single shared .env
    # (also used by docker-compose for the postgres/cloudflared services) doesn't
    # trip extra_forbidden below.
    postgres_user: str = ""
    postgres_password: str = ""
    postgres_db: str = ""
    cloudflare_tunnel_token: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache # Construct Seetings object only once
def get_settings() -> Settings:
    return Settings()