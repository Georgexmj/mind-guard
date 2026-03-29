from datetime import datetime, timezone
from typing import Annotated
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.core.deps import require_role
from app.models.user import User, UserRole
from app.models.assessment import AssessmentSession, AssessmentResult, SessionStatus, RiskLevel

router = APIRouter(prefix="/api/v1/dashboard", tags=["Dashboard"])

DbDep = Annotated[Session, Depends(get_db)]
StaffDep = Annotated[User, Depends(require_role(UserRole.admin, UserRole.doctor))]


@router.get("/stats")
def get_dashboard_stats(db: DbDep, _: StaffDep):
    """Aggregate KPI statistics for the dashboard overview cards."""
    total_elders = db.query(User).filter(
        User.role == UserRole.elder, User.is_active == True
    ).count()

    total_sessions = db.query(AssessmentSession).filter(
        AssessmentSession.status == SessionStatus.completed
    ).count()

    high_risk_count = (
        db.query(AssessmentResult)
        .filter(AssessmentResult.risk_level == RiskLevel.high_risk)
        .count()
    )

    today = datetime.now(timezone.utc).date()
    today_sessions = (
        db.query(AssessmentSession)
        .filter(
            AssessmentSession.status == SessionStatus.completed,
            func.date(AssessmentSession.completed_at) == today,
        )
        .count()
    )

    return {
        "total_elders": total_elders,
        "total_sessions": total_sessions,
        "high_risk_count": high_risk_count,
        "today_sessions": today_sessions,
    }


@router.get("/monthly-trend")
def get_monthly_trend(db: DbDep, _: StaffDep, months: int = 6):
    """
    Month-by-month completed session counts for the past N months.
    Response: [{month: "2026-01", count: 42}, ...]
    """
    now = datetime.now(timezone.utc)
    result = []

    for i in range(months - 1, -1, -1):
        total_months = now.year * 12 + (now.month - 1) - i
        year_val = total_months // 12
        month_val = total_months % 12 + 1
        month_label = f"{year_val:04d}-{month_val:02d}"

        count = (
            db.query(func.count(AssessmentSession.id))
            .filter(
                AssessmentSession.status == SessionStatus.completed,
                func.year(AssessmentSession.completed_at) == year_val,
                func.month(AssessmentSession.completed_at) == month_val,
            )
            .scalar()
        ) or 0

        result.append({"month": month_label, "count": count})

    return result


@router.get("/risk-distribution")
def get_risk_distribution(db: DbDep, _: StaffDep):
    """Count of assessment results by risk level."""
    rows = (
        db.query(AssessmentResult.risk_level, func.count(AssessmentResult.id).label("cnt"))
        .group_by(AssessmentResult.risk_level)
        .all()
    )
    dist = {
        (row.risk_level.value if hasattr(row.risk_level, "value") else row.risk_level): row.cnt
        for row in rows
    }
    return {
        "normal": dist.get("normal", 0),
        "mild_risk": dist.get("mild_risk", 0),
        "high_risk": dist.get("high_risk", 0),
    }


@router.get("/high-risk-list")
def get_high_risk_list(db: DbDep, _: StaffDep, limit: int = 10):
    """Most recent high-risk assessment results with elder info."""
    rows = (
        db.query(AssessmentResult, AssessmentSession, User)
        .join(AssessmentSession, AssessmentResult.session_id == AssessmentSession.id)
        .join(User, AssessmentSession.user_id == User.id)
        .filter(AssessmentResult.risk_level == RiskLevel.high_risk)
        .order_by(AssessmentResult.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "session_id": session.id,
            "elder_id": user.id,
            "elder_name": user.name,
            "phone": user.phone,
            "mmse_score": ar.mmse_score,
            "ad_probability": ar.ad_probability,
            "assessed_at": ar.created_at.isoformat() if ar.created_at else None,
        }
        for ar, session, user in rows
    ]
