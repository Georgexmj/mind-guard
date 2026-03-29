from app.tasks.celery_app import celery_app
from app.services.ai_service import analyze_session
from app.config import settings


@celery_app.task(bind=True, name="analyze_session", max_retries=3)
def analyze_session_task(self, session_id: int):
    """
    Celery task: run AI analysis for a completed assessment session.

    Args:
        session_id: ID of the AssessmentSession to analyze

    Returns:
        dict with status and session_id on success

    Raises:
        Retries up to 3 times with 5-second back-off on any exception.
    """
    try:
        result = analyze_session(session_id, settings.DATABASE_URL)
        return {
            "status": "completed",
            "session_id": session_id,
            "risk_level": result.get("risk_level"),
            "mmse_score": result.get("mmse_score"),
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5, max_retries=3)
