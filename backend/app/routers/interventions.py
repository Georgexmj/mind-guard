from datetime import date as date_type
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.models.intervention import InterventionPlan, InterventionRecord, PlanStatus
from app.schemas.intervention import (
    InterventionPlanCreate, InterventionPlanUpdate, InterventionPlanOut,
    InterventionRecordCreate, InterventionRecordOut,
)

router = APIRouter(prefix="/api/v1/interventions", tags=["Interventions"])


# ─── Plans ────────────────────────────────────────────────────────────────────

@router.get("/plans", response_model=List[InterventionPlanOut])
def list_plans(
    elder_id: Optional[int] = Query(None),
    plan_status: Optional[PlanStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List intervention plans. Elders see only their own plans."""
    q = db.query(InterventionPlan)

    if current_user.role == UserRole.elder:
        q = q.filter(InterventionPlan.elder_id == current_user.id)
    elif elder_id:
        q = q.filter(InterventionPlan.elder_id == elder_id)

    if plan_status:
        q = q.filter(InterventionPlan.status == plan_status)

    plans = (
        q.order_by(InterventionPlan.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    results = []
    for plan in plans:
        completed = (
            db.query(func.count(InterventionRecord.id))
            .filter(InterventionRecord.plan_id == plan.id, InterventionRecord.completed == True)
            .scalar()
        )
        total = (
            db.query(func.count(InterventionRecord.id))
            .filter(InterventionRecord.plan_id == plan.id)
            .scalar()
        )
        out = InterventionPlanOut.model_validate(plan)
        out.elder_name = plan.elder.name if plan.elder else None
        out.completed_count = completed
        out.total_records = total
        results.append(out)

    return results


@router.post("/plans", response_model=InterventionPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(
    data: InterventionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    """Create a new intervention plan for an elder. Doctor/admin only."""
    plan = InterventionPlan(
        elder_id=data.elder_id,
        created_by=current_user.id,
        title=data.title,
        description=data.description,
        domain_focus=data.domain_focus,
        frequency=data.frequency,
        duration_days=data.duration_days,
        start_date=data.start_date,
        end_date=data.end_date,
        status=PlanStatus.active,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    out = InterventionPlanOut.model_validate(plan)
    out.elder_name = plan.elder.name if plan.elder else None
    out.completed_count = 0
    out.total_records = 0
    return out


@router.get("/plans/{plan_id}", response_model=InterventionPlanOut)
def get_plan(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(InterventionPlan).filter(InterventionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Intervention plan not found")
    if current_user.role == UserRole.elder and plan.elder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    completed = (
        db.query(func.count(InterventionRecord.id))
        .filter(InterventionRecord.plan_id == plan.id, InterventionRecord.completed == True)
        .scalar()
    )
    total = (
        db.query(func.count(InterventionRecord.id))
        .filter(InterventionRecord.plan_id == plan.id)
        .scalar()
    )
    out = InterventionPlanOut.model_validate(plan)
    out.elder_name = plan.elder.name if plan.elder else None
    out.completed_count = completed
    out.total_records = total
    return out


@router.put("/plans/{plan_id}", response_model=InterventionPlanOut)
def update_plan(
    plan_id: int,
    data: InterventionPlanUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    plan = db.query(InterventionPlan).filter(InterventionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Intervention plan not found")

    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(plan, field, value)

    db.commit()
    db.refresh(plan)
    out = InterventionPlanOut.model_validate(plan)
    out.elder_name = plan.elder.name if plan.elder else None
    return out


# ─── Records ──────────────────────────────────────────────────────────────────

@router.get("/plans/{plan_id}/records", response_model=List[InterventionRecordOut])
def list_records(
    plan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(InterventionPlan).filter(InterventionPlan.id == plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if current_user.role == UserRole.elder and plan.elder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    records = (
        db.query(InterventionRecord)
        .filter(InterventionRecord.plan_id == plan_id)
        .order_by(InterventionRecord.record_date.desc())
        .all()
    )
    return records


@router.post("/records", response_model=InterventionRecordOut, status_code=status.HTTP_201_CREATED)
def submit_record(
    data: InterventionRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Submit an intervention execution record. Elder submits for themselves."""
    plan = db.query(InterventionPlan).filter(InterventionPlan.id == data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if current_user.role == UserRole.elder and plan.elder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    elder_id = plan.elder_id
    record = InterventionRecord(
        plan_id=data.plan_id,
        elder_id=elder_id,
        record_date=data.record_date or date_type.today(),
        completed=data.completed,
        duration_min=data.duration_min,
        notes=data.notes,
        mood_score=data.mood_score,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/stats/{elder_id}")
def get_elder_intervention_stats(
    elder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Completion statistics for an elder's intervention plans."""
    if current_user.role == UserRole.elder and current_user.id != elder_id:
        raise HTTPException(status_code=403, detail="Access denied")

    total_plans = db.query(func.count(InterventionPlan.id)).filter(
        InterventionPlan.elder_id == elder_id
    ).scalar()

    active_plans = db.query(func.count(InterventionPlan.id)).filter(
        InterventionPlan.elder_id == elder_id,
        InterventionPlan.status == PlanStatus.active,
    ).scalar()

    total_records = db.query(func.count(InterventionRecord.id)).filter(
        InterventionRecord.elder_id == elder_id
    ).scalar()

    completed_records = db.query(func.count(InterventionRecord.id)).filter(
        InterventionRecord.elder_id == elder_id,
        InterventionRecord.completed == True,
    ).scalar()

    return {
        "elder_id": elder_id,
        "total_plans": total_plans,
        "active_plans": active_plans,
        "total_records": total_records,
        "completed_records": completed_records,
        "completion_rate": round(completed_records / total_records * 100, 1) if total_records else 0,
    }
