from celery import Celery
from app.config import settings

celery_app = Celery(
    "cognitive_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.analysis"],
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "Asia/Shanghai"
celery_app.conf.enable_utc = True

# Task routing (optional, useful when scaling horizontally)
celery_app.conf.task_routes = {
    "analyze_session": {"queue": "ai_analysis"},
}

# Retry settings
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
