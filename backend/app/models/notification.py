import enum
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, DateTime, Boolean, Text, ForeignKey, JSON, Enum as SAEnum
)
from sqlalchemy.orm import relationship

from app.database import Base


class NotificationType(str, enum.Enum):
    assessment_completed = "assessment_completed"
    high_risk_alert = "high_risk_alert"
    system_message = "system_message"


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=True, index=True)
    notification_type = Column(SAEnum(NotificationType), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    risk_level = Column(String(30), nullable=True)
    payload = Column(JSON, nullable=True)
    is_read = Column(Boolean, nullable=False, default=False)
    read_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship("User", back_populates="notifications")
    session = relationship("AssessmentSession")
