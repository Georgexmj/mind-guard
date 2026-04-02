from datetime import date as date_type, datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.database import get_db
from app.core.security import get_current_user
from app.core.deps import require_role
from app.models.assessment import AssessmentResult, AssessmentSession
from app.models.user import User, UserRole
from app.models.intervention import InterventionPlan, InterventionRecord, PlanStatus
from app.schemas.intervention import (
    InterventionPlanCreate, InterventionPlanUpdate, InterventionPlanOut,
    InterventionRecordCreate, InterventionRecordOut,
    InterventionRecommendationItemOut, InterventionTop5Out,
)

router = APIRouter(prefix="/api/v1/interventions", tags=["Interventions"])

DOMAIN_LABELS = {
    "memory": "记忆力",
    "orientation": "定向力",
    "language": "语言能力",
    "attention": "注意力",
    "visuospatial": "视空间能力",
    "executive": "执行功能",
}

INTERVENTION_CATALOG: List[Dict[str, Any]] = [
    {
        "code": "memory_association",
        "title": "词语联想记忆训练",
        "category": "认知训练",
        "domain_weights": {"memory": 1.0, "attention": 0.35},
        "frequency": "每天1次",
        "duration_minutes": 15,
        "evidence_level": "B",
    },
    {
        "code": "orientation_calendar",
        "title": "日历与地点定向练习",
        "category": "定向训练",
        "domain_weights": {"orientation": 1.0, "memory": 0.2},
        "frequency": "每天1次",
        "duration_minutes": 12,
        "evidence_level": "B",
    },
    {
        "code": "attention_serial",
        "title": "专注力与序列计算训练",
        "category": "注意力训练",
        "domain_weights": {"attention": 1.0, "executive": 0.25},
        "frequency": "每天1次",
        "duration_minutes": 15,
        "evidence_level": "B",
    },
    {
        "code": "language_fluency",
        "title": "语言流畅与复述训练",
        "category": "语言训练",
        "domain_weights": {"language": 1.0, "memory": 0.25},
        "frequency": "每天1次",
        "duration_minutes": 15,
        "evidence_level": "B",
    },
    {
        "code": "visuospatial_clock",
        "title": "时钟绘制与视空间训练",
        "category": "视空间训练",
        "domain_weights": {"visuospatial": 1.0, "executive": 0.3},
        "frequency": "隔天1次",
        "duration_minutes": 12,
        "evidence_level": "C",
    },
    {
        "code": "executive_planning",
        "title": "执行功能计划任务训练",
        "category": "执行训练",
        "domain_weights": {"executive": 1.0, "attention": 0.3},
        "frequency": "每周5次",
        "duration_minutes": 15,
        "evidence_level": "B",
    },
    {
        "code": "aerobic_walk",
        "title": "中等强度步行干预",
        "category": "运动干预",
        "domain_weights": {"memory": 0.3, "attention": 0.4, "executive": 0.3},
        "frequency": "每天1次",
        "duration_minutes": 30,
        "evidence_level": "A",
    },
    {
        "code": "social_engagement",
        "title": "社交互动与情绪激活",
        "category": "社交干预",
        "domain_weights": {"language": 0.45, "orientation": 0.25, "executive": 0.3},
        "frequency": "每周3次",
        "duration_minutes": 40,
        "evidence_level": "B",
    },
]


def _safe_domain_scores(result: AssessmentResult) -> Dict[str, float]:
    raw = result.domain_scores if isinstance(result.domain_scores, dict) else {}
    return {
        "memory": float(raw.get("memory", 5.0)),
        "orientation": float(raw.get("orientation", 5.0)),
        "language": float(raw.get("language", 5.0)),
        "attention": float(raw.get("attention", 5.0)),
        "visuospatial": float(raw.get("visuospatial", 5.0)),
        "executive": float(raw.get("executive", 5.0)),
    }


def _build_top5_recommendations(result: AssessmentResult) -> List[InterventionRecommendationItemOut]:
    domain_scores = _safe_domain_scores(result)
    deficits = {key: max(0.0, 10.0 - score) / 10.0 for key, score in domain_scores.items()}
    risk_level = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)

    risk_boost = {
        "high_risk": 1.16,
        "mild_risk": 1.08,
        "normal": 1.0,
    }.get(risk_level, 1.0)

    ranked: List[Dict[str, Any]] = []
    for item in INTERVENTION_CATALOG:
        domain_weights = item["domain_weights"]
        weighted_gap = sum(deficits.get(domain, 0.0) * weight for domain, weight in domain_weights.items())
        score = weighted_gap * 100.0 * risk_boost
        ranked.append({**item, "priority_score": round(score, 2)})

    ranked.sort(key=lambda x: x["priority_score"], reverse=True)
    top5 = ranked[:5]

    outputs: List[InterventionRecommendationItemOut] = []
    for idx, item in enumerate(top5, start=1):
        domain_labels = [DOMAIN_LABELS.get(d, d) for d in item["domain_weights"].keys()]
        separator = "\u3001"
        rationale = (
            f"\u5f53\u524d\u8bc4\u4f30\u663e\u793a\u201c{separator.join(domain_labels[:2])}\u201d\u76f8\u5bf9\u8584\u5f31\uff0c"
            "\u8be5\u5e72\u9884\u53ef\u9488\u5bf9\u6027\u6539\u5584\u76f8\u5173\u8ba4\u77e5\u529f\u80fd\u3002"
        )
        outputs.append(
            InterventionRecommendationItemOut(
                rank=idx,
                code=item["code"],
                title=item["title"],
                category=item["category"],
                target_domains=list(item["domain_weights"].keys()),
                frequency=item["frequency"],
                duration_minutes=item["duration_minutes"],
                rationale=rationale,
                priority_score=item["priority_score"],
                evidence_level=item["evidence_level"],
            )
        )

    return outputs


def _resolve_target_result(
    db: Session,
    current_user: User,
    elder_id: Optional[int],
    session_id: Optional[int],
) -> tuple[AssessmentSession, AssessmentResult]:
    target_elder_id = current_user.id if current_user.role == UserRole.elder else elder_id

    if session_id is not None:
        session = db.query(AssessmentSession).filter(AssessmentSession.id == session_id).first()
        if not session:
            raise HTTPException(status_code=404, detail="Assessment session not found")
        if current_user.role == UserRole.elder and session.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        if target_elder_id is not None and session.user_id != target_elder_id:
            raise HTTPException(status_code=400, detail="Session does not belong to elder_id")

        result = db.query(AssessmentResult).filter(AssessmentResult.session_id == session.id).first()
        if not result:
            raise HTTPException(status_code=404, detail="Assessment result not found for this session")
        return session, result

    query = (
        db.query(AssessmentSession, AssessmentResult)
        .join(AssessmentResult, AssessmentResult.session_id == AssessmentSession.id)
    )
    if target_elder_id is not None:
        query = query.filter(AssessmentSession.user_id == target_elder_id)
    if current_user.role == UserRole.elder:
        query = query.filter(AssessmentSession.user_id == current_user.id)

    row = query.order_by(AssessmentResult.created_at.desc()).first()
    if not row:
        raise HTTPException(status_code=404, detail="No completed assessment result found")
    return row[0], row[1]


@router.get("/recommendations/top5", response_model=InterventionTop5Out)
def get_top5_recommendations(
    elder_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.elder)),
):
    """
    Generate Top-5 personalized intervention recommendations from latest
    completed assessment result (or specified session_id).
    """
    session, result = _resolve_target_result(db, current_user, elder_id, session_id)
    recommendations = _build_top5_recommendations(result)

    shap = result.shap_values if isinstance(result.shap_values, dict) else {}
    risk_level = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)

    return InterventionTop5Out(
        elder_id=session.user_id,
        session_id=session.id,
        risk_level=risk_level,
        mmse_score=result.mmse_score,
        moca_score_corrected=shap.get("moca_score_corrected"),
        generated_at=datetime.utcnow(),
        recommendations=recommendations,
    )


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
