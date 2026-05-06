from datetime import date as date_type
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.config import settings
from app.core.deps import require_role
from app.core.security import get_current_user
from app.database import get_db
from app.models.assessment import AssessmentResult, AssessmentSession
from app.models.intervention import (
    InterventionAdherenceTicket,
    InterventionPlan,
    InterventionRecord,
    PlanStatus,
    TicketStatus,
)
from app.models.notification import NotificationType
from app.models.user import User, UserRelationship, UserRole
from app.schemas.intervention import (
    InterventionAdherenceAlertOut,
    InterventionAdherenceTicketBatchUpdateIn,
    InterventionAdherenceTicketBatchUpdateOut,
    InterventionAdherenceTicketOut,
    InterventionAdherenceTicketStatsOut,
    InterventionReminderDispatchOut,
    InterventionAdherenceTicketSyncOut,
    InterventionAdherenceTicketUpdate,
    InterventionDailyCheckinCreate,
    InterventionMyProgressOut,
    InterventionPlanCreate,
    InterventionPlanFromTop5Create,
    InterventionPlanOut,
    InterventionPlanProgressOut,
    InterventionPlanUpdate,
    InterventionRecommendationItemOut,
    InterventionRecordCreate,
    InterventionRecordOut,
    InterventionTop5Out,
)
from app.services.intervention_reco import (
    build_top5_from_result,
    parse_frequency_expected_per_week,
)
from app.services.reminder_service import dispatch_adherence_reminders as dispatch_adherence_reminders_service
from app.services.notification_service import upsert_notification
from app.services.wechat_service import send_to_user_by_binding

router = APIRouter(prefix="/api/v1/interventions", tags=["Interventions"])

INTERRUPTION_PREFIX = "[INTERRUPTION_REASON]"
TOP5_CODE_PREFIX = "[TOP5_CODE]"


def _resolve_target_result(
    db: Session,
    current_user: User,
    elder_id: Optional[int],
    session_id: Optional[int],
) -> Tuple[AssessmentSession, AssessmentResult]:
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


def _normalize_text_key(raw: Optional[str]) -> str:
    text = str(raw or "").strip().lower()
    if not text:
        return ""
    for ch in [" ", "-", "_", ":", "：", "(", ")", "（", "）", "[", "]", "【", "】", "、", ",", "，", ".", "。"]:
        text = text.replace(ch, "")
    return text


def _extract_top5_code(description: Optional[str]) -> Optional[str]:
    if not description:
        return None
    first_line = description.splitlines()[0].strip()
    prefix = f"{TOP5_CODE_PREFIX}:"
    if not first_line.startswith(prefix):
        return None
    code = first_line[len(prefix):].strip()
    return code or None


def _build_top5_plan_description(recommendation_code: str, rationale: Optional[str]) -> str:
    code_line = f"{TOP5_CODE_PREFIX}:{recommendation_code}"
    plain = (rationale or "").strip()
    return f"{code_line}\n{plain}" if plain else code_line


def _plan_matches_recommendation(
    plan: InterventionPlan,
    recommendation_code: str,
    recommendation_title: str,
) -> bool:
    code = _extract_top5_code(plan.description)
    if code and code == recommendation_code:
        return True

    plan_key = _normalize_text_key(plan.title)
    recommendation_key = _normalize_text_key(recommendation_title)
    if not plan_key or not recommendation_key:
        return False
    return (
        plan_key == recommendation_key
        or recommendation_key in plan_key
        or plan_key in recommendation_key
    )


def _split_notes(raw_notes: Optional[str]) -> Tuple[Optional[str], Optional[str]]:
    if not raw_notes:
        return None, None
    lines = raw_notes.splitlines()
    if not lines:
        return None, None
    first = lines[0].strip()
    if first.startswith(INTERRUPTION_PREFIX):
        reason = first[len(INTERRUPTION_PREFIX):].strip() or None
        plain = "\n".join(lines[1:]).strip() or None
        return reason, plain
    return None, raw_notes


def _compose_notes(interruption_reason: Optional[str], notes: Optional[str]) -> Optional[str]:
    reason = (interruption_reason or "").strip()
    plain = (notes or "").strip()
    if reason and plain:
        return f"{INTERRUPTION_PREFIX} {reason}\n{plain}"
    if reason:
        return f"{INTERRUPTION_PREFIX} {reason}"
    return plain or None


def _record_to_out(record: InterventionRecord) -> InterventionRecordOut:
    reason, plain_notes = _split_notes(record.notes)
    payload = InterventionRecordOut.model_validate(record)
    payload.interruption_reason = reason
    payload.notes = plain_notes
    return payload


def _compute_plan_stats(db: Session, plan_id: int) -> Tuple[int, int]:
    completed = (
        db.query(func.count(InterventionRecord.id))
        .filter(InterventionRecord.plan_id == plan_id, InterventionRecord.completed == True)
        .scalar()
    ) or 0
    total = (
        db.query(func.count(InterventionRecord.id))
        .filter(InterventionRecord.plan_id == plan_id)
        .scalar()
    ) or 0
    return int(completed), int(total)


def _plan_to_out(db: Session, plan: InterventionPlan) -> InterventionPlanOut:
    completed, total = _compute_plan_stats(db, plan.id)
    out = InterventionPlanOut.model_validate(plan)
    out.elder_name = plan.elder.name if plan.elder else None
    out.completed_count = completed
    out.total_records = total
    return out


def _consecutive_missed_days(
    db: Session,
    plan: InterventionPlan,
    window_days: int = 14,
    reference_date: Optional[date_type] = None,
) -> Tuple[int, Optional[str]]:
    ref = reference_date or date_type.today()
    start_boundary = ref - timedelta(days=max(window_days - 1, 0))
    if plan.start_date:
        start_boundary = max(start_boundary, plan.start_date)

    rows = (
        db.query(InterventionRecord)
        .filter(
            InterventionRecord.plan_id == plan.id,
            InterventionRecord.record_date >= start_boundary,
            InterventionRecord.record_date <= ref,
        )
        .all()
    )

    by_date: Dict[date_type, List[InterventionRecord]] = {}
    latest_reason: Optional[str] = None
    for row in rows:
        by_date.setdefault(row.record_date, []).append(row)
        reason, _ = _split_notes(row.notes)
        if row.completed is False and reason and latest_reason is None:
            latest_reason = reason

    streak = 0
    day = ref
    while day >= start_boundary:
        records = by_date.get(day, [])
        has_completed = any(r.completed for r in records)
        if has_completed:
            break
        streak += 1
        day -= timedelta(days=1)

    return streak, latest_reason


def _consecutive_completed_days(
    db: Session,
    plan: InterventionPlan,
    window_days: int = 60,
    reference_date: Optional[date_type] = None,
) -> int:
    ref = reference_date or date_type.today()
    start_boundary = ref - timedelta(days=max(window_days - 1, 0))
    if plan.start_date:
        start_boundary = max(start_boundary, plan.start_date)

    rows = (
        db.query(InterventionRecord)
        .filter(
            InterventionRecord.plan_id == plan.id,
            InterventionRecord.record_date >= start_boundary,
            InterventionRecord.record_date <= ref,
        )
        .all()
    )
    if not rows:
        return 0

    by_date: Dict[date_type, List[InterventionRecord]] = {}
    for row in rows:
        by_date.setdefault(row.record_date, []).append(row)

    day = ref
    while day >= start_boundary and not by_date.get(day):
        day -= timedelta(days=1)

    if day < start_boundary:
        return 0

    streak = 0
    while day >= start_boundary:
        records = by_date.get(day, [])
        has_completed = any(r.completed for r in records)
        if not has_completed:
            break
        streak += 1
        day -= timedelta(days=1)

    return streak


def _completion_rate_for_plan(db: Session, plan: InterventionPlan, lookback_days: int = 7) -> float:
    start = date_type.today() - timedelta(days=max(lookback_days - 1, 0))
    if plan.start_date:
        start = max(start, plan.start_date)

    rows = (
        db.query(InterventionRecord)
        .filter(
            InterventionRecord.plan_id == plan.id,
            InterventionRecord.record_date >= start,
            InterventionRecord.record_date <= date_type.today(),
        )
        .all()
    )
    if not rows:
        return 0.0

    completed_days = len({r.record_date for r in rows if r.completed})
    expected_per_week = parse_frequency_expected_per_week(plan.frequency)
    span_days = max((date_type.today() - start).days + 1, 1)
    expected_days = max(expected_per_week / 7.0 * span_days, 1.0)
    return round(min(completed_days / expected_days * 100.0, 100.0), 1)


def _latest_risk_level(db: Session, elder_id: int) -> Optional[str]:
    row = (
        db.query(AssessmentResult)
        .join(AssessmentSession, AssessmentResult.session_id == AssessmentSession.id)
        .filter(AssessmentSession.user_id == elder_id)
        .order_by(AssessmentResult.created_at.desc())
        .first()
    )
    if not row:
        return None
    return row.risk_level.value if hasattr(row.risk_level, "value") else str(row.risk_level)


def _ticket_to_out(ticket: InterventionAdherenceTicket) -> InterventionAdherenceTicketOut:
    return InterventionAdherenceTicketOut(
        id=ticket.id,
        plan_id=ticket.plan_id,
        elder_id=ticket.elder_id,
        elder_name=ticket.elder.name if ticket.elder else None,
        plan_title=ticket.plan.title if ticket.plan else None,
        status=ticket.status,
        owner_doctor_id=ticket.owner_doctor_id,
        owner_doctor_name=ticket.owner_doctor.name if ticket.owner_doctor else None,
        reminder_at=ticket.reminder_at,
        followup_note=ticket.followup_note,
        consecutive_missed_days=ticket.consecutive_missed_days,
        completion_rate=ticket.completion_rate,
        latest_interruption_reason=ticket.latest_interruption_reason,
        risk_level=ticket.risk_level,
        resolved_at=ticket.resolved_at,
        last_notified_at=ticket.last_notified_at,
        created_at=ticket.created_at,
        updated_at=ticket.updated_at,
    )


def _apply_ticket_update(
    db: Session,
    ticket: InterventionAdherenceTicket,
    *,
    status_set: bool = False,
    status_value: Optional[TicketStatus] = None,
    owner_doctor_id_set: bool = False,
    owner_doctor_id: Optional[int] = None,
    reminder_at_set: bool = False,
    reminder_at: Optional[datetime] = None,
    followup_note_set: bool = False,
    followup_note: Optional[str] = None,
    append_followup_note: bool = False,
) -> None:
    if status_set and status_value is not None:
        ticket.status = status_value
        if status_value in (TicketStatus.resolved, TicketStatus.ignored):
            ticket.resolved_at = datetime.utcnow()
        elif status_value in (TicketStatus.open, TicketStatus.in_progress):
            ticket.resolved_at = None

    if owner_doctor_id_set:
        if owner_doctor_id is None:
            ticket.owner_doctor_id = None
        else:
            owner = db.query(User).filter(User.id == owner_doctor_id, User.role == UserRole.doctor).first()
            if owner is None:
                raise HTTPException(status_code=404, detail=f"Owner doctor not found: {owner_doctor_id}")
            ticket.owner_doctor_id = owner.id

    if reminder_at_set:
        ticket.reminder_at = reminder_at

    if followup_note_set:
        note = (followup_note or "").strip()
        if append_followup_note and note:
            old_note = (ticket.followup_note or "").strip()
            ticket.followup_note = f"{old_note}\n{note}" if old_note else note
        else:
            ticket.followup_note = note or None


def _round_hours(start_at: Optional[datetime], end_at: Optional[datetime]) -> Optional[float]:
    if start_at is None or end_at is None:
        return None
    seconds = (end_at - start_at).total_seconds()
    if seconds < 0:
        return None
    return round(seconds / 3600.0, 2)


def _upsert_adherence_ticket(
    db: Session,
    *,
    plan: InterventionPlan,
    consecutive_missed_days: int,
    completion_rate: float,
    latest_interruption_reason: Optional[str],
    risk_level: Optional[str],
) -> InterventionAdherenceTicket:
    ticket = (
        db.query(InterventionAdherenceTicket)
        .filter(
            InterventionAdherenceTicket.plan_id == plan.id,
            InterventionAdherenceTicket.elder_id == plan.elder_id,
            InterventionAdherenceTicket.status.in_([TicketStatus.open, TicketStatus.in_progress]),
        )
        .order_by(InterventionAdherenceTicket.created_at.desc())
        .first()
    )
    if ticket is None:
        ticket = InterventionAdherenceTicket(
            plan_id=plan.id,
            elder_id=plan.elder_id,
            status=TicketStatus.open,
        )
        db.add(ticket)
        db.flush()

    ticket.consecutive_missed_days = int(consecutive_missed_days)
    ticket.completion_rate = float(completion_rate)
    ticket.latest_interruption_reason = latest_interruption_reason
    ticket.risk_level = risk_level
    return ticket


@router.get("/recommendations/top5", response_model=InterventionTop5Out)
def get_top5_recommendations(
    elder_id: Optional[int] = Query(None),
    session_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.elder)),
):
    session, result = _resolve_target_result(db, current_user, elder_id, session_id)
    recommendations = [
        InterventionRecommendationItemOut(**item)
        for item in build_top5_from_result(result)
    ]
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


@router.post(
    "/recommendations/top5/create-plan",
    response_model=InterventionPlanOut,
    status_code=status.HTTP_201_CREATED,
)
def create_plan_from_top5(
    data: InterventionPlanFromTop5Create,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.elder)),
):
    if data.elder_id is None and data.session_id is None:
        raise HTTPException(status_code=400, detail="elder_id or session_id is required")

    session, result = _resolve_target_result(
        db=db,
        current_user=current_user,
        elder_id=data.elder_id,
        session_id=data.session_id,
    )
    top5 = build_top5_from_result(result)
    selected = next((item for item in top5 if item["code"] == data.recommendation_code), None)
    if not selected:
        raise HTTPException(status_code=404, detail="Recommendation code not found in current Top-5")

    start_date = data.start_date or date_type.today()
    end_date = start_date + timedelta(days=data.duration_days - 1)
    existing_plans = (
        db.query(InterventionPlan)
        .filter(
            InterventionPlan.elder_id == session.user_id,
            InterventionPlan.status == PlanStatus.active,
        )
        .order_by(InterventionPlan.created_at.desc())
        .all()
    )
    for existing in existing_plans:
        if existing.end_date and existing.end_date < start_date:
            continue
        if _plan_matches_recommendation(existing, data.recommendation_code, selected["title"]):
            return _plan_to_out(db, existing)

    plan = InterventionPlan(
        elder_id=session.user_id,
        created_by=current_user.id,
        title=selected["title"],
        description=_build_top5_plan_description(data.recommendation_code, selected.get("rationale")),
        domain_focus=",".join(selected.get("target_domains", [])),
        frequency=selected.get("frequency"),
        duration_days=data.duration_days,
        start_date=start_date,
        end_date=end_date,
        status=PlanStatus.active,
        ai_priority=selected.get("priority_score"),
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_out(db, plan)


@router.get("/plans", response_model=List[InterventionPlanOut])
def list_plans(
    elder_id: Optional[int] = Query(None),
    plan_status: Optional[PlanStatus] = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
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
    return [_plan_to_out(db, plan) for plan in plans]


@router.post("/plans", response_model=InterventionPlanOut, status_code=status.HTTP_201_CREATED)
def create_plan(
    data: InterventionPlanCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    start_date = data.start_date
    end_date = data.end_date
    if start_date and data.duration_days and not end_date:
        end_date = start_date + timedelta(days=data.duration_days - 1)

    plan = InterventionPlan(
        elder_id=data.elder_id,
        created_by=current_user.id,
        title=data.title,
        description=data.description,
        domain_focus=data.domain_focus,
        frequency=data.frequency,
        duration_days=data.duration_days,
        start_date=start_date,
        end_date=end_date,
        status=PlanStatus.active,
    )
    db.add(plan)
    db.commit()
    db.refresh(plan)
    return _plan_to_out(db, plan)


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
    return _plan_to_out(db, plan)


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

    update_payload = data.model_dump(exclude_unset=True)
    for field, value in update_payload.items():
        setattr(plan, field, value)

    if plan.start_date and plan.duration_days and not plan.end_date:
        plan.end_date = plan.start_date + timedelta(days=plan.duration_days - 1)

    db.commit()
    db.refresh(plan)
    return _plan_to_out(db, plan)


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
    return [_record_to_out(record) for record in records]


@router.post("/records", response_model=InterventionRecordOut, status_code=status.HTTP_201_CREATED)
def submit_record(
    data: InterventionRecordCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    plan = db.query(InterventionPlan).filter(InterventionPlan.id == data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if current_user.role == UserRole.elder and plan.elder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    record = InterventionRecord(
        plan_id=data.plan_id,
        elder_id=plan.elder_id,
        record_date=data.record_date or date_type.today(),
        completed=data.completed,
        duration_min=data.duration_min,
        notes=_compose_notes(data.interruption_reason, data.notes),
        mood_score=data.mood_score,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _record_to_out(record)


@router.post("/daily-checkin", response_model=InterventionRecordOut)
def daily_checkin(
    data: InterventionDailyCheckinCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor, UserRole.elder)),
):
    plan = db.query(InterventionPlan).filter(InterventionPlan.id == data.plan_id).first()
    if not plan:
        raise HTTPException(status_code=404, detail="Plan not found")
    if current_user.role == UserRole.elder and plan.elder_id != current_user.id:
        raise HTTPException(status_code=403, detail="Access denied")

    record_date = data.record_date or date_type.today()
    existing = (
        db.query(InterventionRecord)
        .filter(
            InterventionRecord.plan_id == plan.id,
            InterventionRecord.elder_id == plan.elder_id,
            InterventionRecord.record_date == record_date,
        )
        .first()
    )

    if existing:
        existing.completed = data.completed
        existing.duration_min = data.duration_min
        existing.notes = _compose_notes(data.interruption_reason, data.notes)
        existing.mood_score = data.mood_score
        db.commit()
        db.refresh(existing)
        return _record_to_out(existing)

    record = InterventionRecord(
        plan_id=plan.id,
        elder_id=plan.elder_id,
        record_date=record_date,
        completed=data.completed,
        duration_min=data.duration_min,
        notes=_compose_notes(data.interruption_reason, data.notes),
        mood_score=data.mood_score,
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return _record_to_out(record)


@router.get("/my-progress", response_model=InterventionMyProgressOut)
def get_my_progress(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.elder)),
):
    plans = (
        db.query(InterventionPlan)
        .filter(
            InterventionPlan.elder_id == current_user.id,
            InterventionPlan.status == PlanStatus.active,
        )
        .order_by(InterventionPlan.created_at.desc())
        .all()
    )

    today = date_type.today()
    outputs: List[InterventionPlanProgressOut] = []
    for plan in plans:
        completed_count, total_records = _compute_plan_stats(db, plan.id)
        missed_streak, latest_reason = _consecutive_missed_days(db, plan, window_days=14)
        completed_streak = _consecutive_completed_days(db, plan, window_days=60)
        today_record = (
            db.query(InterventionRecord)
            .filter(
                InterventionRecord.plan_id == plan.id,
                InterventionRecord.elder_id == plan.elder_id,
                InterventionRecord.record_date == today,
            )
            .first()
        )
        completion_rate = (
            round(completed_count / total_records * 100.0, 1) if total_records else 0.0
        )
        outputs.append(
            InterventionPlanProgressOut(
                plan_id=plan.id,
                plan_title=plan.title,
                recommendation_code=_extract_top5_code(plan.description),
                frequency=plan.frequency,
                completion_rate=completion_rate,
                completed_count=completed_count,
                total_records=total_records,
                today_checked=today_record is not None,
                today_completed=today_record.completed if today_record else None,
                consecutive_completed_days=completed_streak,
                consecutive_missed_days=missed_streak,
                latest_interruption_reason=latest_reason,
            )
        )

    return InterventionMyProgressOut(
        elder_id=current_user.id,
        active_plan_count=len(outputs),
        plans=outputs,
    )


@router.get("/adherence-alerts", response_model=List[InterventionAdherenceAlertOut])
def get_adherence_alerts(
    days: int = Query(14, ge=3, le=60),
    threshold: int = Query(2, ge=1, le=30),
    elder_id: Optional[int] = Query(None),
    sync_ticket: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    q = db.query(InterventionPlan).filter(InterventionPlan.status == PlanStatus.active)
    if elder_id:
        q = q.filter(InterventionPlan.elder_id == elder_id)
    plans = q.all()

    alerts: List[InterventionAdherenceAlertOut] = []
    for plan in plans:
        streak, latest_reason = _consecutive_missed_days(db, plan, window_days=days)
        if streak < threshold:
            continue
        rate = _completion_rate_for_plan(db, plan, lookback_days=days)
        risk_level = _latest_risk_level(db, plan.elder_id)
        ticket: Optional[InterventionAdherenceTicket] = None
        if sync_ticket:
            ticket = _upsert_adherence_ticket(
                db,
                plan=plan,
                consecutive_missed_days=streak,
                completion_rate=rate,
                latest_interruption_reason=latest_reason,
                risk_level=risk_level,
            )
        alerts.append(
            InterventionAdherenceAlertOut(
                plan_id=plan.id,
                elder_id=plan.elder_id,
                elder_name=plan.elder.name if plan.elder else None,
                plan_title=plan.title,
                ticket_id=ticket.id if ticket else None,
                ticket_status=ticket.status if ticket else None,
                owner_doctor_id=ticket.owner_doctor_id if ticket else None,
                owner_doctor_name=ticket.owner_doctor.name if ticket and ticket.owner_doctor else None,
                reminder_at=ticket.reminder_at if ticket else None,
                consecutive_missed_days=streak,
                completion_rate=rate,
                latest_interruption_reason=latest_reason,
                risk_level=risk_level,
                suggested_action=(
                    "\u5efa\u8bae\u533b\u751f\u6216\u7ba1\u7406\u5458\u5c3d\u5feb\u56de\u8bbf\uff0c"
                    "\u786e\u8ba4\u4e2d\u65ad\u539f\u56e0\u5e76\u8c03\u6574\u5e72\u9884\u8ba1\u5212\u3002"
                ),
            )
        )

    if sync_ticket:
        db.commit()

    alerts.sort(
        key=lambda item: (item.consecutive_missed_days, -item.completion_rate),
        reverse=True,
    )
    return alerts


@router.post("/adherence-tickets/sync", response_model=InterventionAdherenceTicketSyncOut)
def sync_adherence_tickets(
    days: int = Query(14, ge=3, le=60),
    threshold: int = Query(2, ge=1, le=30),
    elder_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    q = db.query(InterventionPlan).filter(InterventionPlan.status == PlanStatus.active)
    if elder_id is not None:
        q = q.filter(InterventionPlan.elder_id == elder_id)
    plans = q.all()

    generated = 0
    for plan in plans:
        streak, latest_reason = _consecutive_missed_days(db, plan, window_days=days)
        if streak < threshold:
            continue
        rate = _completion_rate_for_plan(db, plan, lookback_days=days)
        risk_level = _latest_risk_level(db, plan.elder_id)
        ticket = _upsert_adherence_ticket(
            db,
            plan=plan,
            consecutive_missed_days=streak,
            completion_rate=rate,
            latest_interruption_reason=latest_reason,
            risk_level=risk_level,
        )
        generated += 1 if ticket.created_at == ticket.updated_at else 0

    db.commit()

    open_count = db.query(InterventionAdherenceTicket).filter(InterventionAdherenceTicket.status == TicketStatus.open).count()
    in_progress_count = (
        db.query(InterventionAdherenceTicket)
        .filter(InterventionAdherenceTicket.status == TicketStatus.in_progress)
        .count()
    )
    resolved_count = db.query(InterventionAdherenceTicket).filter(InterventionAdherenceTicket.status == TicketStatus.resolved).count()
    return InterventionAdherenceTicketSyncOut(
        generated_count=generated,
        open_count=int(open_count),
        in_progress_count=int(in_progress_count),
        resolved_count=int(resolved_count),
    )


@router.get("/adherence-tickets", response_model=List[InterventionAdherenceTicketOut])
def list_adherence_tickets(
    status_filter: Optional[TicketStatus] = Query(None, alias="status"),
    owner_doctor_id: Optional[int] = Query(None),
    elder_id: Optional[int] = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    q = db.query(InterventionAdherenceTicket)
    if status_filter is not None:
        q = q.filter(InterventionAdherenceTicket.status == status_filter)
    if owner_doctor_id is not None:
        q = q.filter(InterventionAdherenceTicket.owner_doctor_id == owner_doctor_id)
    if elder_id is not None:
        q = q.filter(InterventionAdherenceTicket.elder_id == elder_id)

    rows = (
        q.order_by(
            InterventionAdherenceTicket.status.asc(),
            InterventionAdherenceTicket.updated_at.desc(),
        )
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return [_ticket_to_out(row) for row in rows]


@router.put("/adherence-tickets/{ticket_id}", response_model=InterventionAdherenceTicketOut)
def update_adherence_ticket(
    ticket_id: int,
    data: InterventionAdherenceTicketUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    ticket = db.query(InterventionAdherenceTicket).filter(InterventionAdherenceTicket.id == ticket_id).first()
    if ticket is None:
        raise HTTPException(status_code=404, detail="Adherence ticket not found")

    fields_set = set(data.model_fields_set)
    _apply_ticket_update(
        db,
        ticket,
        status_set="status" in fields_set,
        status_value=data.status,
        owner_doctor_id_set="owner_doctor_id" in fields_set,
        owner_doctor_id=data.owner_doctor_id,
        reminder_at_set="reminder_at" in fields_set,
        reminder_at=data.reminder_at,
        followup_note_set="followup_note" in fields_set,
        followup_note=data.followup_note,
    )

    db.commit()
    db.refresh(ticket)
    return _ticket_to_out(ticket)


@router.post("/adherence-tickets/batch-update", response_model=InterventionAdherenceTicketBatchUpdateOut)
def batch_update_adherence_tickets(
    data: InterventionAdherenceTicketBatchUpdateIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    _ = current_user
    if not data.ticket_ids:
        raise HTTPException(status_code=400, detail="ticket_ids is required")

    fields_set = set(data.model_fields_set)
    has_update_field = any(
        [
            "status" in fields_set,
            "owner_doctor_id" in fields_set,
            "reminder_at" in fields_set,
            "followup_note" in fields_set,
        ]
    )
    if not has_update_field:
        raise HTTPException(status_code=400, detail="No update fields provided")

    unique_ids = list(dict.fromkeys(data.ticket_ids))
    rows = (
        db.query(InterventionAdherenceTicket)
        .filter(InterventionAdherenceTicket.id.in_(unique_ids))
        .all()
    )
    row_map = {row.id: row for row in rows}
    skipped_ids = [ticket_id for ticket_id in unique_ids if ticket_id not in row_map]

    updated_ids: List[int] = []
    for ticket_id in unique_ids:
        ticket = row_map.get(ticket_id)
        if ticket is None:
            continue
        _apply_ticket_update(
            db,
            ticket,
            status_set="status" in fields_set,
            status_value=data.status,
            owner_doctor_id_set="owner_doctor_id" in fields_set,
            owner_doctor_id=data.owner_doctor_id,
            reminder_at_set="reminder_at" in fields_set,
            reminder_at=data.reminder_at,
            followup_note_set="followup_note" in fields_set,
            followup_note=data.followup_note,
            append_followup_note=data.append_followup_note,
        )
        updated_ids.append(ticket_id)

    db.commit()

    return InterventionAdherenceTicketBatchUpdateOut(
        requested_count=len(unique_ids),
        updated_count=len(updated_ids),
        updated_ids=updated_ids,
        skipped_ids=skipped_ids,
    )


@router.get("/adherence-tickets/stats", response_model=InterventionAdherenceTicketStatsOut)
def get_adherence_ticket_stats(
    owner_doctor_id: Optional[int] = Query(None),
    elder_id: Optional[int] = Query(None),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    _ = current_user
    q = db.query(InterventionAdherenceTicket)
    if owner_doctor_id is not None:
        q = q.filter(InterventionAdherenceTicket.owner_doctor_id == owner_doctor_id)
    if elder_id is not None:
        q = q.filter(InterventionAdherenceTicket.elder_id == elder_id)
    tickets = q.all()

    total_count = len(tickets)
    open_count = len([t for t in tickets if t.status == TicketStatus.open])
    in_progress_count = len([t for t in tickets if t.status == TicketStatus.in_progress])
    resolved_count = len([t for t in tickets if t.status == TicketStatus.resolved])
    ignored_count = len([t for t in tickets if t.status == TicketStatus.ignored])

    now = datetime.utcnow()
    overdue_open_count = len(
        [
            t
            for t in tickets
            if t.status in (TicketStatus.open, TicketStatus.in_progress)
            and t.reminder_at is not None
            and t.reminder_at < now
        ]
    )

    response_hours = [
        hours
        for hours in (
            _round_hours(t.created_at, t.updated_at if t.status != TicketStatus.open else None)
            for t in tickets
        )
        if hours is not None
    ]
    avg_response_hours = round(sum(response_hours) / len(response_hours), 2) if response_hours else None

    closed_tickets = [t for t in tickets if t.status in (TicketStatus.resolved, TicketStatus.ignored)]
    resolution_hours = [
        hours
        for hours in (
            _round_hours(t.created_at, t.resolved_at or t.updated_at)
            for t in closed_tickets
        )
        if hours is not None
    ]
    avg_resolution_hours = round(sum(resolution_hours) / len(resolution_hours), 2) if resolution_hours else None

    closed_count = len(resolution_hours)
    within_24h = len([h for h in resolution_hours if h <= 24.0])
    within_48h = len([h for h in resolution_hours if h <= 48.0])
    resolved_within_24h_rate = round(within_24h / closed_count * 100.0, 1) if closed_count else 0.0
    resolved_within_48h_rate = round(within_48h / closed_count * 100.0, 1) if closed_count else 0.0

    return InterventionAdherenceTicketStatsOut(
        total_count=total_count,
        open_count=open_count,
        in_progress_count=in_progress_count,
        resolved_count=resolved_count,
        ignored_count=ignored_count,
        overdue_open_count=overdue_open_count,
        avg_response_hours=avg_response_hours,
        avg_resolution_hours=avg_resolution_hours,
        resolved_within_24h_rate=resolved_within_24h_rate,
        resolved_within_48h_rate=resolved_within_48h_rate,
    )


@router.post("/reminders/adherence/dispatch", response_model=InterventionReminderDispatchOut)
def dispatch_adherence_reminders(
    due_only: bool = Query(True),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_role(UserRole.admin, UserRole.doctor)),
):
    payload = dispatch_adherence_reminders_service(
        db,
        dispatcher=current_user,
        due_only=due_only,
    )
    return InterventionReminderDispatchOut(**payload)


@router.get("/stats/{elder_id}")
def get_elder_intervention_stats(
    elder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if current_user.role == UserRole.elder and current_user.id != elder_id:
        raise HTTPException(status_code=403, detail="Access denied")

    total_plans = (
        db.query(func.count(InterventionPlan.id))
        .filter(InterventionPlan.elder_id == elder_id)
        .scalar()
    ) or 0
    active_plans = (
        db.query(func.count(InterventionPlan.id))
        .filter(
            InterventionPlan.elder_id == elder_id,
            InterventionPlan.status == PlanStatus.active,
        )
        .scalar()
    ) or 0
    total_records = (
        db.query(func.count(InterventionRecord.id))
        .filter(InterventionRecord.elder_id == elder_id)
        .scalar()
    ) or 0
    completed_records = (
        db.query(func.count(InterventionRecord.id))
        .filter(
            InterventionRecord.elder_id == elder_id,
            InterventionRecord.completed == True,
        )
        .scalar()
    ) or 0

    active_plan_rows = (
        db.query(InterventionPlan)
        .filter(
            InterventionPlan.elder_id == elder_id,
            InterventionPlan.status == PlanStatus.active,
        )
        .all()
    )
    max_missed_streak = 0
    latest_reason: Optional[str] = None
    for plan in active_plan_rows:
        streak, reason = _consecutive_missed_days(db, plan, window_days=14)
        max_missed_streak = max(max_missed_streak, streak)
        if not latest_reason and reason:
            latest_reason = reason

    return {
        "elder_id": elder_id,
        "total_plans": int(total_plans),
        "active_plans": int(active_plans),
        "total_records": int(total_records),
        "completed_records": int(completed_records),
        "completion_rate": round(completed_records / total_records * 100.0, 1) if total_records else 0.0,
        "max_consecutive_missed_days": max_missed_streak,
        "latest_interruption_reason": latest_reason,
    }
