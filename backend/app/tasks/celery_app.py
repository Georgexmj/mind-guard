from datetime import timedelta

from celery import Celery
from app.config import settings

celery_app = Celery(
    "cognitive_worker",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.analysis", "app.tasks.reminders"],
)

celery_app.conf.task_serializer = "json"
celery_app.conf.result_serializer = "json"
celery_app.conf.accept_content = ["json"]
celery_app.conf.timezone = "Asia/Shanghai"
celery_app.conf.enable_utc = True

# Task routing (optional, useful when scaling horizontally)
celery_app.conf.task_routes = {
    "analyze_session": {"queue": "ai_analysis"},
    "dispatch_adherence_reminders_periodic": {"queue": "celery"},
    "dispatch_reassessment_reminders_periodic": {"queue": "celery"},
}

if settings.CELERY_BEAT_ENABLED:
    celery_app.conf.beat_schedule = {
        "dispatch-adherence-reminders": {
            "task": "dispatch_adherence_reminders_periodic",
            "schedule": timedelta(minutes=max(settings.CELERY_BEAT_ADHERENCE_INTERVAL_MINUTES, 1)),
        },
        "dispatch-reassessment-reminders": {
            "task": "dispatch_reassessment_reminders_periodic",
            "schedule": timedelta(minutes=max(settings.CELERY_BEAT_REASSESSMENT_INTERVAL_MINUTES, 1)),
        },
    }

# Retry settings
celery_app.conf.task_acks_late = True
celery_app.conf.worker_prefetch_multiplier = 1
