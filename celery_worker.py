from celery import Celery
from app.core.config import settings

celery = Celery("worker",
                broker=settings.CELERY_BROKER_URL,
                backend=settings.CELERY_RESULT_BACKEND
)

celery.autodiscover_tasks(["app.tasks"])

celery.conf.update(task_serializer="json", result_serializer="json")

import app.tasks.image_tasks