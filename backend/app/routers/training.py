from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.training_report import TrainingReport
from app.models.user import User
from app.schemas.training_report import TrainingReportCreate, TrainingReportOut

router = APIRouter(prefix="/api/v1/training", tags=["Training"])


@router.post(
    "/report",
    response_model=TrainingReportOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_training_report(
    data: TrainingReportCreate,
    db: Session = Depends(get_db),
):
    elder_id = None
    
    if data.userId.isdigit():
        elder_id = int(data.userId)
    else:
        user = db.query(User).filter(User.phone == data.userId).first()
        if user:
            elder_id = user.id
        else:
            user = db.query(User).filter(User.username == data.userId).first()
            if user:
                elder_id = user.id
    
    if elder_id is None:
        raise HTTPException(status_code=404, detail="Elder not found")

    report = TrainingReport(
        elder_id=elder_id,
        course_id=data.courseId,
        course_name=data.courseName,
        correct_count=data.correctCount,
        total_questions=data.totalQuestions,
        accuracy=data.accuracy,
        completed_at=data.completedAt,
        answers=[answer.dict() for answer in data.answers],
    )

    db.add(report)
    db.commit()
    db.refresh(report)

    return report


@router.get("/reports", response_model=List[TrainingReportOut])
def get_training_reports(
    elder_id: Optional[int] = None,
    course_id: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    q = db.query(TrainingReport)

    if elder_id is not None:
        q = q.filter(TrainingReport.elder_id == elder_id)

    if course_id is not None:
        q = q.filter(TrainingReport.course_id == course_id)

    reports = (
        q.order_by(TrainingReport.completed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    return reports


@router.get("/reports/{report_id}", response_model=TrainingReportOut)
def get_training_report(
    report_id: int,
    db: Session = Depends(get_db),
):
    report = db.query(TrainingReport).filter(TrainingReport.id == report_id).first()
    if not report:
        raise HTTPException(status_code=404, detail="Training report not found")
    return report


@router.get("/reports/stats/{elder_id}")
def get_elder_training_stats(
    elder_id: int,
    db: Session = Depends(get_db),
):
    total_reports = (
        db.query(func.count(TrainingReport.id))
        .filter(TrainingReport.elder_id == elder_id)
        .scalar()
    ) or 0

    avg_accuracy = (
        db.query(func.avg(TrainingReport.accuracy))
        .filter(TrainingReport.elder_id == elder_id)
        .scalar()
    ) or 0.0

    total_questions = (
        db.query(func.sum(TrainingReport.total_questions))
        .filter(TrainingReport.elder_id == elder_id)
        .scalar()
    ) or 0

    total_correct = (
        db.query(func.sum(TrainingReport.correct_count))
        .filter(TrainingReport.elder_id == elder_id)
        .scalar()
    ) or 0

    latest_report = (
        db.query(TrainingReport)
        .filter(TrainingReport.elder_id == elder_id)
        .order_by(TrainingReport.completed_at.desc())
        .first()
    )

    return {
        "elder_id": elder_id,
        "total_reports": int(total_reports),
        "avg_accuracy": round(avg_accuracy, 2),
        "total_questions": int(total_questions),
        "total_correct": int(total_correct),
        "overall_accuracy": round(total_correct / total_questions * 100, 2) if total_questions else 0.0,
        "latest_report_at": latest_report.completed_at if latest_report else None,
    }
