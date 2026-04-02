from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationType


class NotificationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    session_id: Optional[int] = None
    notification_type: NotificationType
    title: str
    content: str
    risk_level: Optional[str] = None
    payload: Optional[Dict[str, Any]] = None
    is_read: bool
    read_at: Optional[datetime] = None
    created_at: datetime


class NotificationUnreadCountOut(BaseModel):
    unread_count: int


class NotificationMarkReadOut(BaseModel):
    id: int
    is_read: bool
    read_at: Optional[datetime] = None


class NotificationMarkAllReadOut(BaseModel):
    marked_count: int
