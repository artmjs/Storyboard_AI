from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    STATIC_DIR: Path = Path("static")

    model_config = ConfigDict(env_file=".env")

settings = Settings()