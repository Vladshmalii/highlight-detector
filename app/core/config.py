from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:pass@localhost:5432/highlights"
    REDIS_URL: str = "redis://localhost:6379/0"
    VIDEO_UPLOAD_DIR: str = "/app/videos"
    MAX_UPLOAD_MB: int = 2048

    class Config:
        env_file = ".env"


settings = Settings()