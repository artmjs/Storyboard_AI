from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from pathlib import Path

class Settings(BaseSettings):
    OPENAI_API_KEY: str
    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str
    STATIC_DIR: Path = Path("static")
    FRONTEND_DIR: str = "frontend"
    FIRST_REFINE_PROMPT: str = (
        "MAKE EDIT STRICTLY WITHIN MASK BOUNDARIES. If any text is present on the sketch, do not remove it." \
        "Please clean up and sharpen the existing line work, improve clarity and contrast, " \
        "and correct any small drawing inconsistencies—while preserving the original art style, " \
        "character designs, and exact object/character positions. " \
        "Do not introduce any new filters, color treatments, or stylistic changes." 
        
    )

    model_config = ConfigDict(env_file=".env")

class EditRequest(BaseSettings):
    image_id: str 
    prompt: str 


settings = Settings()