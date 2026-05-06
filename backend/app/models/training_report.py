"""
Training report models for tracking elder training activities.
"""

from datetime import datetime

from sqlalchemy import Column, Integer, String, Text, DateTime, Float, JSON, ForeignKey
from sqlalchemy.orm import relationship

from app.database import Base


class TrainingReport(Base):
    __tablename__ = "training_reports"
    id = Column(Integer, primary_key=True, autoincrement=True)
    elder_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    course_id = Column(String(100), nullable=False)
    course_name = Column(String(200), nullable=False)
    correct_count = Column(Integer, nullable=False)
    total_questions = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False)
    completed_at = Column(DateTime, nullable=False)
    answers = Column(JSON, nullable=True)  # Store detailed answers as JSON
    created_at = Column(DateTime, default=datetime.utcnow)

    elder = relationship("User", foreign_keys=[elder_id])
