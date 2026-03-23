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

    # AWS Bedrock
    aws_region: str = "us-east-1"
    bedrock_model_id: str = "anthropic.claude-3-sonnet-20240229-v1:0"

    class Config:
        env_file = ".env"
        case_sensitive = False


@lru_cache # Construct Seetings object only once
def get_settings() -> Settings:
    return Settings()