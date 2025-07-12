import redis
from app.core.config import settings

redis_client = redis.from_url(settings.CELERY_BROKER_URL, decode_responses=True)