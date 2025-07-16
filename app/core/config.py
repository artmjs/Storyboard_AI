from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    STATIC_DIR: Path = Path("static")
    FIRST_REFINE_PROMPT: str = (
        "Please clean up and sharpen the existing line work, improve clarity and contrast, "
        "and correct any small drawing inconsistencies—while preserving the original art style, "
        "character designs, and exact object/character positions. "
        "Do not introduce any new filters, color treatments, or stylistic changes." \
        "Make an edit strictly within mask boundaries. If any text is present on the sketch, do not remove it."
    )

    model_config = ConfigDict(env_file=".env")

class EditRequest(BaseSettings):
    image_id: str 
    prompt: str 


settings = Settings()