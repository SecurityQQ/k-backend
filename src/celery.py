from celery import Celery
from src.core.config import settings

celery_app = Celery(
    "k-backend",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["src.components.crawl.tasks"],
)

celery_app.conf.update(
    task_track_started=True,
) 