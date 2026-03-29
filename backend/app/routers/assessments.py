from typing import List, Optional

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.models.assessment import AssessmentSession, SessionStatus
from app.schemas.assessment import (
    SessionCreate, SessionOut, QuestionOut,
    AnswerSubmit, AnswerOut, ResultOut, TaskStatusOut
)
from app.services import assessment_service
from app.tasks.celery_app import celery_app

router = APIRouter(prefix="/api/v1/assessments", tags=["Assessments"])


@router.post("/sessions", response_model=SessionOut, status_code=status.HTTP_201_CREATED)
def create_session(
    _: SessionCreate = SessionCreate(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new assessment session for the authenticated elder.
    Doctors and admins can also create sessions on behalf of elders.
    """
    if current_user.role == UserRole.family:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Family members cannot start assessment sessions",
        )
    session = assessment_service.create_session(db, current_user.id)
    return session


@router.get("/sessions", response_model=List[SessionOut])
def list_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all assessment sessions for the current user."""
    if current_user.role in (UserRole.admin, UserRole.doctor):
        # Admin and doctor see all sessions
        sessions = db.query(AssessmentSession).order_by(
            AssessmentSession.created_at.desc()
        ).all()
    else:
        sessions = assessment_service.get_sessions_by_user(db, current_user.id)
    return sessions


@router.get("/sessions/{session_id}", response_model=SessionOut)
def get_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific session."""
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    # Authorization: owner or admin/doctor
    if current_user.role not in (UserRole.admin, UserRole.doctor) and session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )
    return session


@router.get("/sessions/{session_id}/questions", response_model=List[QuestionOut])
def get_questions(
    session_id: int,
    count: int = 5,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Fetch the next batch of unanswered questions for a session.
    Returns up to `count` questions (default 5).
    """
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if current_user.role not in (UserRole.admin, UserRole.doctor) and session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )

    questions = assessment_service.get_next_questions(db, session_id, count=count)
    return questions


@router.post("/sessions/{session_id}/answers", response_model=AnswerOut, status_code=status.HTTP_201_CREATED)
def submit_answer(
    session_id: int,
    answer: AnswerSubmit,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an answer to a question within a session."""
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if current_user.role not in (UserRole.admin, UserRole.doctor) and session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )

    response = assessment_service.submit_answer(db, session_id, answer)
    return response


@router.post("/sessions/{session_id}/complete", status_code=status.HTTP_202_ACCEPTED)
def complete_session(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark the session as complete and trigger asynchronous AI analysis.
    Returns 202 Accepted with the Celery task_id for polling.
    """
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if current_user.role not in (UserRole.admin, UserRole.doctor) and session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )

    result = assessment_service.complete_session(db, session_id)
    return result


@router.get("/sessions/{session_id}/result", response_model=Optional[ResultOut])
def get_result(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve the AI analysis result for a session.
    Returns null (204) if the result is not yet available.
    Poll this endpoint after receiving 202 from /complete.
    """
    session = assessment_service.get_session_by_id(db, session_id)
    if session is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Session {session_id} not found",
        )

    if current_user.role not in (UserRole.admin, UserRole.doctor) and session.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to this session",
        )

    result = assessment_service.get_result(db, session_id)
    return result


@router.get("/tasks/{task_id}", response_model=TaskStatusOut)
def get_task_status(
    task_id: str,
    current_user: User = Depends(get_current_user),
):
    """
    Poll the status of a Celery analysis task.
    States: PENDING | STARTED | SUCCESS | FAILURE | RETRY
    """
    task_result = AsyncResult(task_id, app=celery_app)

    result_data = None
    if task_result.ready():
        try:
            result_data = task_result.result
            if not isinstance(result_data, dict):
                result_data = {"raw": str(result_data)}
        except Exception:
            result_data = {"error": "Could not retrieve task result"}

    return TaskStatusOut(
        task_id=task_id,
        status=task_result.status,
        result=result_data,
    )
