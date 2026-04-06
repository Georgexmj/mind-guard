from __future__ import annotations

from typing import Any, Dict

from app.config import settings
from app.database import SessionLocal
from app.services.reminder_service import (
    dispatch_adherence_reminders,
    dispatch_reassessment_reminders,
    resolve_dispatch_user,
)
from app.tasks.celery_app import celery_app


@celery_app.task(name="dispatch_adherence_reminders_periodic")
def dispatch_adherence_reminders_periodic() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        dispatcher = resolve_dispatch_user(db)
        if dispatcher is None:
            return {"ok": False, "reason": "dispatcher_not_found"}
        result = dispatch_adherence_reminders(
            db,
            dispatcher=dispatcher,
            due_only=settings.CELERY_BEAT_ADHERENCE_DUE_ONLY,
        )
        result["ok"] = True
        result["trigger"] = "celery_beat"
        return result
    except Exception as exc:
        db.rollback()
        return {"ok": False, "reason": "exception", "error": str(exc)}
    finally:
        db.close()


@celery_app.task(name="dispatch_reassessment_reminders_periodic")
def dispatch_reassessment_reminders_periodic() -> Dict[str, Any]:
    db = SessionLocal()
    try:
        dispatcher = resolve_dispatch_user(db)
        if dispatcher is None:
            return {"ok": False, "reason": "dispatcher_not_found"}
        result = dispatch_reassessment_reminders(
            db,
            dispatcher=dispatcher,
            within_days=settings.CELERY_BEAT_REASSESSMENT_WITHIN_DAYS,
        )
        result["ok"] = True
        result["trigger"] = "celery_beat"
        return result
    except Exception as exc:
        db.rollback()
        return {"ok": False, "reason": "exception", "error": str(exc)}
    finally:
        db.close()
