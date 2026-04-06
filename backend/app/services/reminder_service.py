from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

from sqlalchemy.orm import Session

from app.config import settings
from app.models.assessment import AssessmentResult, AssessmentSession
from app.models.intervention import InterventionAdherenceTicket, TicketStatus
from app.models.notification import NotificationType
from app.models.user import User, UserRelationship, UserRole
from app.services.intervention_reco import suggest_next_reassessment_date
from app.services.notification_service import upsert_notification
from app.services.wechat_service import send_to_user_by_binding


def resolve_dispatch_user(db: Session, preferred_user_id: Optional[int] = None) -> Optional[User]:
    """
    Resolve a valid dispatcher user for background jobs.
    Priority:
      1) preferred active admin/doctor
      2) first active admin
      3) first active doctor
    """
    if preferred_user_id is not None:
        preferred = (
            db.query(User)
            .filter(
                User.id == preferred_user_id,
                User.is_active == True,
                User.role.in_([UserRole.admin, UserRole.doctor]),
            )
            .first()
        )
        if preferred is not None:
            return preferred

    admin = (
        db.query(User)
        .filter(User.role == UserRole.admin, User.is_active == True)
        .order_by(User.id.asc())
        .first()
    )
    if admin is not None:
        return admin

    return (
        db.query(User)
        .filter(User.role == UserRole.doctor, User.is_active == True)
        .order_by(User.id.asc())
        .first()
    )


def _resolve_ticket_owner(
    db: Session,
    *,
    ticket: InterventionAdherenceTicket,
    dispatcher: User,
) -> int:
    owner_id: Optional[int] = None

    if ticket.owner_doctor_id is not None:
        owner = (
            db.query(User)
            .filter(
                User.id == ticket.owner_doctor_id,
                User.role == UserRole.doctor,
                User.is_active == True,
            )
            .first()
        )
        if owner is not None:
            owner_id = owner.id

    if owner_id is None:
        elder_community_id = ticket.elder.community_id if ticket.elder else None
        if elder_community_id is not None:
            doctor = (
                db.query(User)
                .filter(
                    User.role == UserRole.doctor,
                    User.is_active == True,
                    User.community_id == elder_community_id,
                )
                .order_by(User.id.asc())
                .first()
            )
            if doctor is not None:
                owner_id = doctor.id

    if owner_id is None and dispatcher.role == UserRole.doctor:
        owner_id = dispatcher.id

    if owner_id is None:
        owner_id = dispatcher.id

    return owner_id


def dispatch_adherence_reminders(
    db: Session,
    *,
    dispatcher: User,
    due_only: bool = True,
) -> Dict[str, Any]:
    now = datetime.utcnow()
    query = db.query(InterventionAdherenceTicket).filter(
        InterventionAdherenceTicket.status.in_([TicketStatus.open, TicketStatus.in_progress]),
    )
    if due_only:
        query = query.filter(
            (InterventionAdherenceTicket.reminder_at.is_(None))
            | (InterventionAdherenceTicket.reminder_at <= now)
        )
    rows = query.order_by(InterventionAdherenceTicket.updated_at.desc()).all()

    pushed_count = 0
    skipped_count = 0
    detail: List[Dict[str, Any]] = []

    for row in rows:
        owner_id = _resolve_ticket_owner(db, ticket=row, dispatcher=dispatcher)
        row.owner_doctor_id = owner_id

        elder_name = row.elder.name if row.elder and row.elder.name else f"老人#{row.elder_id}"
        plan_name = row.plan.title if row.plan and row.plan.title else f"计划#{row.plan_id}"

        upsert_notification(
            db,
            user_id=owner_id,
            notification_type=NotificationType.system_message,
            title=f"依从性提醒：{elder_name}",
            content=f"计划“{plan_name}”连续未完成 {row.consecutive_missed_days} 天，请尽快回访并记录处理结果。",
            payload={
                "kind": "adherence_ticket",
                "ticket_id": row.id,
                "plan_id": row.plan_id,
                "elder_id": row.elder_id,
            },
        )

        wechat_payload = {
            "thing1": {"value": "依从性预警"},
            "thing2": {"value": plan_name[:20]},
            "thing3": {"value": f"连续未完成{row.consecutive_missed_days}天"},
        }
        wechat_result = send_to_user_by_binding(
            db,
            user_id=owner_id,
            template_id=settings.WECHAT_TEMPLATE_ID_ADHERENCE,
            data=wechat_payload,
            page=settings.WECHAT_MINIPROGRAM_PAGE,
        )
        row.last_notified_at = now

        family_rows = (
            db.query(UserRelationship)
            .filter(UserRelationship.elder_id == row.elder_id, UserRelationship.notify_level != 3)
            .all()
        )
        family_wechat_results = []
        for rel in family_rows:
            family_wechat_results.append(
                send_to_user_by_binding(
                    db,
                    user_id=rel.family_id,
                    template_id=settings.WECHAT_TEMPLATE_ID_ADHERENCE,
                    data=wechat_payload,
                    page=settings.WECHAT_MINIPROGRAM_PAGE,
                )
            )

        pushed_count += 1
        if not wechat_result.get("ok"):
            skipped_count += 1
        detail.append(
            {
                "ticket_id": row.id,
                "owner_doctor_id": owner_id,
                "wechat_result": wechat_result,
                "family_wechat_results": family_wechat_results,
            }
        )

    db.commit()
    return {
        "candidate_count": len(rows),
        "pushed_count": pushed_count,
        "skipped_count": skipped_count,
        "detail": detail,
    }


def dispatch_reassessment_reminders(
    db: Session,
    *,
    dispatcher: User,
    within_days: int = 7,
) -> Dict[str, Any]:
    now_date = datetime.utcnow().date()
    elders = db.query(User).filter(User.role == UserRole.elder, User.is_active == True).all()

    detail: List[Dict[str, Any]] = []
    push_count = 0

    for elder in elders:
        latest = (
            db.query(AssessmentResult, AssessmentSession)
            .join(AssessmentSession, AssessmentResult.session_id == AssessmentSession.id)
            .filter(AssessmentSession.user_id == elder.id)
            .order_by(AssessmentResult.created_at.desc())
            .first()
        )
        if not latest:
            continue

        result, session = latest
        risk_level = result.risk_level.value if hasattr(result.risk_level, "value") else str(result.risk_level)
        next_date = suggest_next_reassessment_date(risk_level, result.created_at.date())
        if next_date > now_date + timedelta(days=within_days):
            continue

        title = f"复评提醒：{elder.name}"
        content = f"{elder.name} 建议复评日期为 {next_date.isoformat()}，请尽快安排。"

        doctor_rows = (
            db.query(User)
            .filter(
                User.role == UserRole.doctor,
                User.is_active == True,
                User.community_id == elder.community_id,
            )
            .all()
        )
        doctor_ids = [doctor.id for doctor in doctor_rows]
        if not doctor_ids and dispatcher.role == UserRole.doctor:
            doctor_ids = [dispatcher.id]

        for doctor_id in doctor_ids:
            upsert_notification(
                db,
                user_id=doctor_id,
                notification_type=NotificationType.system_message,
                title=title,
                content=content,
                session_id=session.id,
                risk_level=risk_level,
                payload={
                    "kind": "reassessment_due",
                    "elder_id": elder.id,
                    "session_id": session.id,
                    "next_reassessment_date": next_date.isoformat(),
                },
            )
            send_to_user_by_binding(
                db,
                user_id=doctor_id,
                template_id=settings.WECHAT_TEMPLATE_ID_REASSESSMENT,
                data={
                    "thing1": {"value": "复评提醒"},
                    "thing2": {"value": (elder.name or f"老人#{elder.id}")[:20]},
                    "date3": {"value": next_date.strftime("%Y-%m-%d")},
                },
                page=settings.WECHAT_MINIPROGRAM_PAGE,
            )
            push_count += 1

        family_links = db.query(UserRelationship).filter(UserRelationship.elder_id == elder.id).all()
        family_ids = [rel.family_id for rel in family_links if rel.notify_level != 3]
        for family_id in family_ids:
            upsert_notification(
                db,
                user_id=family_id,
                notification_type=NotificationType.system_message,
                title=f"{elder.name} 复评提醒",
                content=f"{elder.name} 建议在 {next_date.isoformat()} 前后完成复评，请协助安排。",
                session_id=session.id,
                risk_level=risk_level,
                payload={
                    "kind": "reassessment_due",
                    "elder_id": elder.id,
                    "session_id": session.id,
                    "next_reassessment_date": next_date.isoformat(),
                },
            )
            send_to_user_by_binding(
                db,
                user_id=family_id,
                template_id=settings.WECHAT_TEMPLATE_ID_REASSESSMENT,
                data={
                    "thing1": {"value": "家属复评提醒"},
                    "thing2": {"value": (elder.name or f"老人#{elder.id}")[:20]},
                    "date3": {"value": next_date.strftime("%Y-%m-%d")},
                },
                page=settings.WECHAT_MINIPROGRAM_PAGE,
            )
            push_count += 1

        detail.append(
            {
                "elder_id": elder.id,
                "elder_name": elder.name,
                "session_id": session.id,
                "risk_level": risk_level,
                "next_reassessment_date": next_date.isoformat(),
                "doctor_recipients": doctor_ids,
                "family_recipients": family_ids,
            }
        )

    db.commit()
    return {
        "candidate_count": len(detail),
        "pushed_count": push_count,
        "within_days": within_days,
        "detail": detail,
    }
