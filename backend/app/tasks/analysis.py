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
            "moca_score": result.get("moca_score"),
            "moca_score_corrected": result.get("moca_score_corrected"),
            "education_correction_applied": result.get("education_correction_applied"),
            "education_correction_points": result.get("education_correction_points"),
            "mmse_subscores": result.get("mmse_subscores"),
            "moca_subscores": result.get("moca_subscores"),
            "clinical_report": result.get("clinical_report"),
            "nc_probability": result.get("nc_probability"),
            "mci_probability": result.get("mci_probability"),
            "ad_probability": result.get("ad_probability"),
            "model_confidence": result.get("model_confidence"),
            "modality_quality": result.get("modality_quality"),
            "modality_contributions": result.get("modality_contributions"),
            "top_factors": result.get("top_factors"),
            "data_quality_flag": result.get("data_quality_flag"),
            "model_name": result.get("model_name"),
            "model_strategy": result.get("model_strategy"),
        }
    except Exception as exc:
        raise self.retry(exc=exc, countdown=5, max_retries=3)
