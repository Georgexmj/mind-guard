from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.security import get_current_user
from app.database import get_db
from app.models.notification import Notification, NotificationType
from app.models.user import User
from app.schemas.notification import (
    NotificationMarkAllReadOut,
    NotificationMarkReadOut,
    NotificationOut,
    NotificationUnreadCountOut,
)
from app.services.notification_service import mark_all_notifications_read, mark_notification_read

router = APIRouter(prefix="/api/v1/notifications", tags=["Notifications"])


@router.get("", response_model=List[NotificationOut])
def list_notifications(
    unread_only: bool = Query(False),
    n_type: Optional[NotificationType] = Query(None, alias="type"),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    if unread_only:
        query = query.filter(Notification.is_read == False)
    if n_type:
        query = query.filter(Notification.notification_type == n_type)

    return (
        query
        .order_by(Notification.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )


@router.get("/unread-count", response_model=NotificationUnreadCountOut)
def unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )
    return NotificationUnreadCountOut(unread_count=count)


@router.put("/{notification_id}/read", response_model=NotificationMarkReadOut)
def mark_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    item = (
        db.query(Notification)
        .filter(Notification.id == notification_id, Notification.user_id == current_user.id)
        .first()
    )
    if item is None:
        raise HTTPException(status_code=404, detail="Notification not found")

    mark_notification_read(db, item)
    db.commit()
    db.refresh(item)
    return NotificationMarkReadOut(id=item.id, is_read=item.is_read, read_at=item.read_at)


@router.put("/read-all", response_model=NotificationMarkAllReadOut)
def mark_read_all(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    count = mark_all_notifications_read(db, current_user.id)
    db.commit()
    return NotificationMarkAllReadOut(marked_count=count)
