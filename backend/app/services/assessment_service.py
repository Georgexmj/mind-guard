from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.models.assessment import (
    AssessmentSession, AssessmentResponse, AssessmentResult,
    Question, SessionStatus
)
from app.schemas.assessment import AnswerSubmit

PAUSE_RESUME_WINDOW_MINUTES = 30


def get_pause_deadline(session: AssessmentSession) -> Optional[datetime]:
    """
    Reuse completed_at as pause timestamp when status=pending.
    No schema migration required and completed sessions remain distinguishable
    by status=completed.
    """
    if session.status != SessionStatus.pending or session.completed_at is None:
        return None
    return session.completed_at + timedelta(minutes=PAUSE_RESUME_WINDOW_MINUTES)


def is_session_resumable(session: AssessmentSession, now: Optional[datetime] = None) -> bool:
    if session.status != SessionStatus.pending:
        return False
    deadline = get_pause_deadline(session)
    if deadline is None:
        return False
    current = now or datetime.utcnow()
    return current <= deadline


def _attach_pause_metadata(session: AssessmentSession) -> None:
    deadline = get_pause_deadline(session)
    session.pause_deadline = deadline
    session.is_resumable = is_session_resumable(session)


def create_session(db: Session, user_id: int) -> AssessmentSession:
    """
    Create a new assessment session for the given user.
    Sets status to in_progress and records started_at.
    """
    session = AssessmentSession(
        user_id=user_id,
        status=SessionStatus.in_progress,
        started_at=datetime.utcnow(),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return session


def get_next_questions(db: Session, session_id: int, count: int = 5) -> List[Question]:
    """
    Get next unanswered questions for the given session.
    MVP: simple sequential ordering; IRT adaptive selection for production.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status not in (SessionStatus.in_progress, SessionStatus.pending):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not active",
        )

    if session.status == SessionStatus.pending:
        if not is_session_resumable(session):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Paused session expired. Resume is only available within {PAUSE_RESUME_WINDOW_MINUTES} minutes.",
            )
        # Auto-resume when user requests next questions in valid pause window.
        session.status = SessionStatus.in_progress
        session.completed_at = None
        db.commit()
        db.refresh(session)

    # Get IDs of already-answered questions in this session
    answered_ids = (
        db.query(AssessmentResponse.question_id)
        .filter(AssessmentResponse.session_id == session_id)
        .subquery()
    )

    questions = (
        db.query(Question)
        .filter(Question.is_active == True)
        .filter(Question.id.not_in(answered_ids))
        # Randomize selection for each assessment session so users don't always
        # receive the same first N questions from the bank.
        .order_by(func.random())
        .limit(count)
        .all()
    )

    return questions


def submit_answer(db: Session, session_id: int, answer: AnswerSubmit) -> AssessmentResponse:
    """
    Record a user's answer for a question in a session.
    Evaluates correctness for choice questions automatically.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status != SessionStatus.in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Session is not in progress",
        )

    question = db.query(Question).filter(Question.id == answer.question_id).first()
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {answer.question_id} not found",
        )

    # Check for duplicate answer
    existing = (
        db.query(AssessmentResponse)
        .filter(
            AssessmentResponse.session_id == session_id,
            AssessmentResponse.question_id == answer.question_id,
        )
        .first()
    )
    if existing is not None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Question already answered in this session",
        )

    # Evaluate correctness for choice questions
    is_correct: Optional[bool] = None
    score: Optional[float] = None

    if question.q_type.value == "choice" and question.correct_answer is not None:
        answer_text_norm = (answer.answer_text or "").strip().lower()
        correct_norm = question.correct_answer.strip().lower()
        is_correct = answer_text_norm == correct_norm
        score = 1.0 if is_correct else 0.0
    elif question.q_type.value in ("voice", "drawing", "scale"):
        # For non-choice types, scoring is done by AI service later
        # For scale questions, store raw value as score normalized to 0-1
        if question.q_type.value == "scale" and answer.answer_text is not None:
            try:
                raw_val = float(answer.answer_text)
                score = min(max(raw_val / 10.0, 0.0), 1.0)
                is_correct = score >= 0.5
            except ValueError:
                score = 0.0
                is_correct = False

    response = AssessmentResponse(
        session_id=session_id,
        question_id=answer.question_id,
        answer_text=answer.answer_text,
        answer_data=answer.answer_data,
        reaction_time_ms=answer.reaction_time_ms,
        is_correct=is_correct,
        score=score,
    )
    db.add(response)
    db.commit()
    db.refresh(response)
    return response


def complete_session(db: Session, session_id: int) -> Dict[str, Any]:
    """
    Mark session as completed, enqueue Celery analysis task.
    Returns dict with task_id.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status != SessionStatus.in_progress:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Session is not in progress (current status: {session.status.value})",
        )

    # Ensure at least one answer was submitted
    response_count = (
        db.query(AssessmentResponse)
        .filter(AssessmentResponse.session_id == session_id)
        .count()
    )
    if response_count == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot complete session with no answers submitted",
        )

    # Import here to avoid circular imports at module load time
    from app.tasks.analysis import analyze_session_task

    # Enqueue the Celery analysis task
    task = analyze_session_task.delay(session_id)

    # Update session status
    session.status = SessionStatus.completed
    session.completed_at = datetime.utcnow()
    session.task_id = task.id
    db.commit()
    db.refresh(session)

    return {"task_id": task.id, "session_id": session_id, "status": "completed"}


def pause_session(db: Session, session_id: int) -> Dict[str, Any]:
    """
    Pause an in-progress session and allow resume within 30 minutes.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status == SessionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed session cannot be paused",
        )

    if session.status == SessionStatus.pending:
        if not is_session_resumable(session):
            raise HTTPException(
                status_code=status.HTTP_410_GONE,
                detail=f"Paused session expired. Resume is only available within {PAUSE_RESUME_WINDOW_MINUTES} minutes.",
            )
        _attach_pause_metadata(session)
        return {
            "session_id": session.id,
            "status": session.status,
            "message": "Session already paused",
            "pause_deadline": session.pause_deadline,
            "is_resumable": session.is_resumable,
        }

    session.status = SessionStatus.pending
    session.completed_at = datetime.utcnow()
    db.commit()
    db.refresh(session)
    _attach_pause_metadata(session)
    return {
        "session_id": session.id,
        "status": session.status,
        "message": "Session paused successfully",
        "pause_deadline": session.pause_deadline,
        "is_resumable": session.is_resumable,
    }


def resume_session(db: Session, session_id: int) -> Dict[str, Any]:
    """
    Resume a paused session if within the 30-minute window.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status == SessionStatus.in_progress:
        return {
            "session_id": session.id,
            "status": session.status,
            "message": "Session already in progress",
            "pause_deadline": None,
            "is_resumable": True,
        }

    if session.status != SessionStatus.pending:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Only paused sessions can be resumed (current status: {session.status.value})",
        )

    if not is_session_resumable(session):
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail=f"Paused session expired. Resume is only available within {PAUSE_RESUME_WINDOW_MINUTES} minutes.",
        )

    session.status = SessionStatus.in_progress
    session.completed_at = None
    db.commit()
    db.refresh(session)
    return {
        "session_id": session.id,
        "status": session.status,
        "message": "Session resumed successfully",
        "pause_deadline": None,
        "is_resumable": True,
    }


def discard_session(db: Session, session_id: int) -> Dict[str, Any]:
    """
    Discard an unfinished assessment session.

    Intended for "user exited midway" scenario. Completed sessions are retained
    for audit/history and cannot be discarded through this API.
    """
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if session.status == SessionStatus.completed:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Completed session cannot be discarded",
        )

    db.query(AssessmentResult).filter(AssessmentResult.session_id == session_id).delete(synchronize_session=False)
    db.query(AssessmentResponse).filter(AssessmentResponse.session_id == session_id).delete(synchronize_session=False)
    db.delete(session)
    db.commit()

    return {"session_id": session_id, "status": "discarded"}


def get_result(db: Session, session_id: int) -> Optional[AssessmentResult]:
    """Retrieve the AI result for a session, or None if not yet available."""
    result = (
        db.query(AssessmentResult)
        .filter(AssessmentResult.session_id == session_id)
        .first()
    )
    if result is not None and isinstance(result.shap_values, dict):
        explainability = result.shap_values
        # Expose frequently used explainability fields as top-level response attributes.
        result.model_confidence = explainability.get("model_confidence")
        result.modality_quality = explainability.get("modality_quality")
        result.modality_contributions = explainability.get("modality_contributions")
        result.top_factors = explainability.get("top_factors")
        result.data_quality_flag = explainability.get("data_quality_flag")
        result.model_name = explainability.get("model_name")
        result.model_strategy = explainability.get("model_strategy")
        result.engine_info = explainability.get("engine_info")
        result.attention_matrix = explainability.get("attention_matrix")
        result.mmse_subscores = explainability.get("mmse_subscores")
        result.moca_subscores = explainability.get("moca_subscores")
        result.moca_score = explainability.get("moca_score")
        result.moca_score_corrected = explainability.get("moca_score_corrected")
        result.education_correction_applied = explainability.get("education_correction_applied")
        result.education_correction_points = explainability.get("education_correction_points")
        result.clinical_report = explainability.get("clinical_report")
    return result


def get_sessions_by_user(db: Session, user_id: int) -> List[AssessmentSession]:
    """Return all assessment sessions for a user, most recent first."""
    sessions = (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user_id)
        .order_by(AssessmentSession.created_at.desc())
        .all()
    )
    for session in sessions:
        _attach_pause_metadata(session)
    return sessions


def get_session_by_id(db: Session, session_id: int) -> Optional[AssessmentSession]:
    """Retrieve a single session by its ID."""
    session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
    if session is not None:
        _attach_pause_metadata(session)
    return session
