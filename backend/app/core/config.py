from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    PROJECT_NAME: str = "Analytics Platform"
    smtp_host: str
    smtp_port: int
    smtp_user: str
    smtp_pass: str
    class Config:
        env_file = ".env"

settings = Settings()