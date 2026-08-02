from celery import Celery
from server.config import settings

celery_app = Celery("aria", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_routes = {"server.workers.tasks.*": {"queue": "aria"}}
