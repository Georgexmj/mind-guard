from datetime import datetime, date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.training_report import TrainingReport
from app.models.intervention import InterventionPlan, InterventionRecord, PlanStatus
from app.models.user import User
from app.schemas.training_report import TrainingReportCreate, TrainingReportOut
from app.core.security import get_current_user

router = APIRouter(prefix="/api/v1/training", tags=["Training"])


@router.post(
    "/report",
    response_model=TrainingReportOut,
    status_code=status.HTTP_201_CREATED,
)
def submit_training_report(
    data: TrainingReportCreate,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    elder_id = None
    
    print(f"[Training Report] Received data: userId={data.userId}, courseId={data.courseId}, courseName={data.courseName}")
    
    # 优先从认证用户获取ID
    if current_user:
        elder_id = current_user.id
        print(f"[Training Report] Using authenticated user: {elder_id} ({current_user.name})")
    elif data.userId.isdigit():
        elder_id = int(data.userId)
        print(f"[Training Report] userId is digit, elder_id={elder_id}")
    elif data.userId == "unknown":
        # 如果 userId 是 "unknown"，尝试获取第一个老人用户作为默认
        default_elder = db.query(User).filter(User.role == "elder").first()
        if default_elder:
            elder_id = default_elder.id
            print(f"[Training Report] Using default elder: {elder_id} ({default_elder.name})")
        else:
            print("[Training Report] No default elder found")
    else:
        user = db.query(User).filter(User.phone == data.userId).first()
        if user:
            elder_id = user.id
        else:
            user = db.query(User).filter(User.username == data.userId).first()
            if user:
                elder_id = user.id
    
    if elder_id is None:
        raise HTTPException(status_code=404, detail=f"Elder not found for userId: {data.userId}")

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
    
    # 查找匹配的干预计划并创建干预记录
    today = date_type.today()
    course_name = data.courseName
    
    # 尝试找到匹配的活跃干预计划
    matching_plan = (
        db.query(InterventionPlan)
        .filter(
            InterventionPlan.elder_id == elder_id,
            InterventionPlan.status == PlanStatus.active,
            InterventionPlan.title.ilike(f"%{course_name}%"),
        )
        .first()
    )
    
    if matching_plan:
        print(f"[Training Report] Found matching intervention plan: {matching_plan.title} (id={matching_plan.id})")
        
        # 检查今天是否已有该计划的完成记录
        existing_record = (
            db.query(InterventionRecord)
            .filter(
                InterventionRecord.plan_id == matching_plan.id,
                InterventionRecord.elder_id == elder_id,
                InterventionRecord.record_date == today,
                InterventionRecord.completed == True,
            )
            .first()
        )
        
        if not existing_record:
            # 创建干预记录
            record = InterventionRecord(
                plan_id=matching_plan.id,
                elder_id=elder_id,
                record_date=today,
                completed=True,
                duration_min=data.duration_min if hasattr(data, 'duration_min') else None,
            )
            db.add(record)
            print(f"[Training Report] Created intervention record for plan {matching_plan.id}")
        else:
            print(f"[Training Report] Already has completed record for today")
    else:
        print(f"[Training Report] No matching intervention plan found for course: {course_name}")
    
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
