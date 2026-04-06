"""
Intervention management models.

Tables:
  - intervention_plans    : a doctor-created care plan for an elder
  - intervention_records  : elder's daily execution logs
"""

import enum
from datetime import datetime, date as date_type

from sqlalchemy import (
    Column, Integer, String, Text, Date, DateTime,
    Boolean, Float, ForeignKey, Enum as SAEnum,
)
from sqlalchemy.orm import relationship

from app.database import Base


class PlanStatus(str, enum.Enum):
    active   = "active"
    paused   = "paused"
    completed = "completed"
    cancelled = "cancelled"


class TicketStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    resolved = "resolved"
    ignored = "ignored"


class InterventionPlan(Base):
    __tablename__ = "intervention_plans"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    elder_id    = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_by  = Column(Integer, ForeignKey("users.id"), nullable=False)   # doctor / admin
    title       = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    # target cognitive domains (comma-separated, e.g. "memory,attention")
    domain_focus = Column(String(200), nullable=True)
    # recommended frequency, e.g. "每天一次", "每周三次"
    frequency   = Column(String(100), nullable=True)
    duration_days = Column(Integer, nullable=True)       # total plan length in days
    start_date  = Column(Date, nullable=True)
    end_date    = Column(Date, nullable=True)
    status      = Column(SAEnum(PlanStatus), default=PlanStatus.active, nullable=False)
    # AI-generated recommendation score (0-10)
    ai_priority = Column(Float, nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)
    updated_at  = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    elder   = relationship("User", foreign_keys=[elder_id], backref="intervention_plans")
    creator = relationship("User", foreign_keys=[created_by])
    records = relationship("InterventionRecord", back_populates="plan", cascade="all, delete-orphan")


class InterventionRecord(Base):
    __tablename__ = "intervention_records"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    plan_id    = Column(Integer, ForeignKey("intervention_plans.id"), nullable=False, index=True)
    elder_id   = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    record_date = Column(Date, nullable=False, default=date_type.today)
    completed  = Column(Boolean, default=False, nullable=False)
    duration_min = Column(Integer, nullable=True)    # actual minutes spent
    notes      = Column(Text, nullable=True)
    mood_score = Column(Integer, nullable=True)      # 1-5 self-reported mood
    created_at = Column(DateTime, default=datetime.utcnow)

    plan  = relationship("InterventionPlan", back_populates="records")
    elder = relationship("User", foreign_keys=[elder_id])


class InterventionAdherenceTicket(Base):
    """
    Trackable doctor/admin workflow for adherence alerts.
    """

    __tablename__ = "intervention_adherence_tickets"

    id = Column(Integer, primary_key=True, autoincrement=True)
    plan_id = Column(Integer, ForeignKey("intervention_plans.id"), nullable=False, index=True)
    elder_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(SAEnum(TicketStatus), default=TicketStatus.open, nullable=False, index=True)
    owner_doctor_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    reminder_at = Column(DateTime, nullable=True)
    followup_note = Column(Text, nullable=True)

    consecutive_missed_days = Column(Integer, nullable=False, default=0)
    completion_rate = Column(Float, nullable=False, default=0.0)
    latest_interruption_reason = Column(String(300), nullable=True)
    risk_level = Column(String(30), nullable=True)

    resolved_at = Column(DateTime, nullable=True)
    last_notified_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    plan = relationship("InterventionPlan", foreign_keys=[plan_id])
    elder = relationship("User", foreign_keys=[elder_id])
    owner_doctor = relationship("User", foreign_keys=[owner_doctor_id])
