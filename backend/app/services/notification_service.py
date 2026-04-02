from datetime import datetime
from typing import Iterable, Optional

from sqlalchemy.orm import Session

from app.models.assessment import AssessmentSession, RiskLevel
from app.models.notification import Notification, NotificationType
from app.models.user import User, UserRole, UserRelationship


def upsert_notification(
    db: Session,
    *,
    user_id: int,
    notification_type: NotificationType,
    title: str,
    content: str,
    session_id: Optional[int] = None,
    risk_level: Optional[str] = None,
    payload: Optional[dict] = None,
) -> Notification:
    """
    Create or update a notification to avoid duplicates for the same user/session/type.
    """
    existing = (
        db.query(Notification)
        .filter(
            Notification.user_id == user_id,
            Notification.session_id == session_id,
            Notification.notification_type == notification_type,
        )
        .first()
    )

    if existing:
        existing.title = title
        existing.content = content
        existing.risk_level = risk_level
        existing.payload = payload
        existing.updated_at = datetime.utcnow()
        db.flush()
        return existing

    item = Notification(
        user_id=user_id,
        session_id=session_id,
        notification_type=notification_type,
        title=title,
        content=content,
        risk_level=risk_level,
        payload=payload,
        is_read=False,
    )
    db.add(item)
    db.flush()
    return item


def mark_notification_read(db: Session, notification: Notification) -> Notification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
        db.flush()
    return notification


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    items = (
        db.query(Notification)
        .filter(Notification.user_id == user_id, Notification.is_read == False)
        .all()
    )
    now = datetime.utcnow()
    for item in items:
        item.is_read = True
        item.read_at = now
    db.flush()
    return len(items)


def _family_should_receive_high_risk(notify_level: Optional[int]) -> bool:
    """
    Compatibility with both definitions currently present in docs/code:
    - notify_level=2 means high-risk-only (code comment)
    - notify_level=1 means high-risk-only (SQL comment)
    - 0/3 are treated as disabled.
    """
    if notify_level in (0, 3):
        return False
    return notify_level in (1, 2)


def _doctor_ids_in_community(db: Session, community_id: Optional[int]) -> Iterable[int]:
    if community_id is None:
        return []
    rows = (
        db.query(User.id)
        .filter(
            User.role == UserRole.doctor,
            User.is_active == True,
            User.community_id == community_id,
        )
        .all()
    )
    return [r.id for r in rows]


def create_assessment_notifications(
    db: Session,
    *,
    session: AssessmentSession,
    risk_level: RiskLevel,
    mmse_score: Optional[float],
) -> None:
    """
    Create notifications after AI analysis is completed:
    - assessment completion notification for elder
    - high-risk alert for elder/family/doctors when needed
    """
    elder = db.query(User).filter(User.id == session.user_id).first()
    elder_name = elder.name if elder else f"用户#{session.user_id}"

    completion_title = "评估结果已生成"
    completion_content = (
        f"您的认知评估（会话#{session.id}）已完成分析。"
        f"{' 当前评估等级：高风险。' if risk_level == RiskLevel.high_risk else ''}"
    )
    upsert_notification(
        db,
        user_id=session.user_id,
        session_id=session.id,
        notification_type=NotificationType.assessment_completed,
        title=completion_title,
        content=completion_content,
        risk_level=risk_level.value,
        payload={"mmse_score": mmse_score},
    )

    if risk_level != RiskLevel.high_risk:
        return

    # Elder high-risk alert
    upsert_notification(
        db,
        user_id=session.user_id,
        session_id=session.id,
        notification_type=NotificationType.high_risk_alert,
        title="高风险预警",
        content="评估结果提示认知高风险，请尽快联系社区医生进行进一步检查。",
        risk_level=risk_level.value,
        payload={"mmse_score": mmse_score},
    )

    # Family high-risk alert
    family_links = (
        db.query(UserRelationship)
        .filter(UserRelationship.elder_id == session.user_id)
        .all()
    )
    for rel in family_links:
        if _family_should_receive_high_risk(rel.notify_level):
            upsert_notification(
                db,
                user_id=rel.family_id,
                session_id=session.id,
                notification_type=NotificationType.high_risk_alert,
                title=f"{elder_name} 高风险预警",
                content=f"{elder_name} 的评估结果为高风险，建议尽快安排线下复诊。",
                risk_level=risk_level.value,
                payload={"elder_id": session.user_id, "mmse_score": mmse_score},
            )

    # Doctor high-risk alert (same community)
    community_id = elder.community_id if elder else None
    for doctor_id in _doctor_ids_in_community(db, community_id):
        upsert_notification(
            db,
            user_id=doctor_id,
            session_id=session.id,
            notification_type=NotificationType.high_risk_alert,
            title=f"辖区高风险预警：{elder_name}",
            content=f"{elder_name} 评估结果为高风险，请及时跟进干预与复诊安排。",
            risk_level=risk_level.value,
            payload={"elder_id": session.user_id, "mmse_score": mmse_score},
        )

