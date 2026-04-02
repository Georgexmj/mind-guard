import csv
import io
from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.deps import require_role
from app.models.user import UserRole
from app.models.assessment import Question, QuestionDomain, QuestionType
from app.schemas.assessment import QuestionOut, QuestionCreate, QuestionUpdate

router = APIRouter(prefix="/api/v1/questions", tags=["Questions"])


@router.get("/", response_model=List[QuestionOut])
def list_questions(
    domain: Optional[QuestionDomain] = Query(None, description="Filter by cognitive domain"),
    q_type: Optional[str] = Query(None, description="Filter by question type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(200, ge=1, le=500),
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


@router.get("/export/csv")
def export_questions_csv(
    domain: Optional[QuestionDomain] = Query(None, description="Filter by cognitive domain"),
    q_type: Optional[str] = Query(None, description="Filter by question type"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    _: object = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    """Export filtered questions as CSV. Admin and doctor access only."""
    query = db.query(Question)

    if domain is not None:
        query = query.filter(Question.domain == domain)
    if q_type is not None:
        query = query.filter(Question.q_type == q_type)
    if is_active is not None:
        query = query.filter(Question.is_active == is_active)

    questions = query.order_by(Question.domain, Question.difficulty).all()

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "id",
            "domain",
            "q_type",
            "content",
            "options",
            "correct_answer",
            "difficulty",
            "irt_a",
            "irt_b",
            "is_active",
        ]
    )

    for item in questions:
        writer.writerow(
            [
                item.id,
                item.domain.value,
                item.q_type.value,
                item.content,
                " | ".join(item.options or []),
                item.correct_answer or "",
                item.difficulty,
                item.irt_a,
                item.irt_b,
                item.is_active,
            ]
        )

    filename = f"mindguard_questions_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
    headers = {"Content-Disposition": f'attachment; filename="{filename}"'}
    csv_bytes = output.getvalue().encode("utf-8-sig")
    output.close()

    return Response(
        content=csv_bytes,
        media_type="text/csv; charset=utf-8",
        headers=headers,
    )


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


@router.put("/{question_id}", response_model=QuestionOut)
def update_question(
    question_id: int,
    data: QuestionUpdate,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(UserRole.admin)),
):
    """Update an assessment question. Admin access only."""
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found",
        )

    update_data = data.model_dump(exclude_unset=True)

    target_q_type = update_data.get("q_type", question.q_type)
    target_options = update_data.get("options", question.options)
    target_correct_answer = update_data.get("correct_answer", question.correct_answer)

    if target_q_type == QuestionType.choice:
        if not target_options or len(target_options) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Choice questions must contain at least 2 options",
            )
        if target_correct_answer and target_correct_answer not in target_options:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="correct_answer must be one of the options",
            )
    else:
        # Non-choice questions should not keep stale choice data.
        update_data["options"] = None
        if "correct_answer" not in update_data:
            update_data["correct_answer"] = None

    for field, value in update_data.items():
        setattr(question, field, value)

    db.commit()
    db.refresh(question)
    return question


@router.delete("/{question_id}", response_model=QuestionOut)
def delete_question(
    question_id: int,
    db: Session = Depends(get_db),
    _: object = Depends(require_role(UserRole.admin)),
):
    """
    Soft delete a question by setting is_active=False.
    Keeps historical assessment data consistent.
    """
    question = db.query(Question).filter(Question.id == question_id).first()
    if question is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question {question_id} not found",
        )

    question.is_active = False
    db.commit()
    db.refresh(question)
    return question
