from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import require_role
from app.models.user import UserRole
from app.models.assessment import Question, QuestionDomain
from app.schemas.assessment import QuestionOut, QuestionCreate

router = APIRouter(prefix="/api/v1/questions", tags=["Questions"])


@router.get("/", response_model=List[QuestionOut])
def list_questions(
    domain: Optional[QuestionDomain] = Query(None, description="Filter by cognitive domain"),
    q_type: Optional[str] = Query(None, description="Filter by question type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    _: object = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    """List questions with optional filters. Admin and doctor access only."""
    query = db.query(Question)

    if domain is not None:
        query = query.filter(Question.domain == domain)
    if q_type is not None:
        query = query.filter(Question.q_type == q_type)
    if is_active is not None:
        query = query.filter(Question.is_active == is_active)

    offset = (page - 1) * page_size
    questions = (
        query.order_by(Question.domain, Question.difficulty)
        .offset(offset)
        .limit(page_size)
        .all()
    )
    return questions


@router.post("/", response_model=QuestionOut, status_code=status.HTTP_201_CREATED)
def create_question(
    data: QuestionCreate,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(UserRole.admin)),
):
    """Create a new assessment question. Admin access only."""
    question = Question(
        domain=data.domain,
        q_type=data.q_type,
        content=data.content,
        options=data.options,
        correct_answer=data.correct_answer,
        difficulty=data.difficulty,
        irt_a=data.irt_a,
        irt_b=data.irt_b,
        is_active=True,
    )
    db.add(question)
    db.commit()
    db.refresh(question)
    return question
