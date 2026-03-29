from datetime import datetime
from typing import List, Optional, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.assessment import (
    AssessmentSession, AssessmentResponse, AssessmentResult,
    Question, SessionStatus
)
from app.schemas.assessment import AnswerSubmit


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
        .order_by(Question.domain, Question.difficulty)
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


def get_result(db: Session, session_id: int) -> Optional[AssessmentResult]:
    """Retrieve the AI result for a session, or None if not yet available."""
    return (
        db.query(AssessmentResult)
        .filter(AssessmentResult.session_id == session_id)
        .first()
    )


def get_sessions_by_user(db: Session, user_id: int) -> List[AssessmentSession]:
    """Return all assessment sessions for a user, most recent first."""
    return (
        db.query(AssessmentSession)
        .filter(AssessmentSession.user_id == user_id)
        .order_by(AssessmentSession.created_at.desc())
        .all()
    )


def get_session_by_id(db: Session, session_id: int) -> Optional[AssessmentSession]:
    """Retrieve a single session by its ID."""
    return db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
