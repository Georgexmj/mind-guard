import enum
from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, DateTime, Float, Text, JSON,
    Enum, ForeignKey, Boolean, UniqueConstraint
)
from sqlalchemy.orm import relationship
from app.database import Base


class QuestionDomain(str, enum.Enum):
    memory = "memory"
    orientation = "orientation"
    language = "language"
    attention = "attention"
    visuospatial = "visuospatial"
    executive = "executive"


class QuestionType(str, enum.Enum):
    choice = "choice"
    voice = "voice"
    drawing = "drawing"
    scale = "scale"


class SessionStatus(str, enum.Enum):
    pending = "pending"
    in_progress = "in_progress"
    completed = "completed"
    failed = "failed"


class RiskLevel(str, enum.Enum):
    normal = "normal"
    mild_risk = "mild_risk"
    moderate_risk = "moderate_risk"
    high_risk = "high_risk"


class Question(Base):
    __tablename__ = "questions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    domain = Column(Enum(QuestionDomain), nullable=False, index=True)
    q_type = Column(Enum(QuestionType), nullable=False)
    content = Column(Text, nullable=False)
    options = Column(JSON, nullable=True)          # List of strings for choice questions
    correct_answer = Column(String(500), nullable=True)
    difficulty = Column(Float, default=0.5)        # 0.0 (easy) to 1.0 (hard)
    irt_a = Column(Float, default=1.0)             # IRT discrimination parameter
    irt_b = Column(Float, default=0.0)             # IRT difficulty parameter
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    responses = relationship("AssessmentResponse", back_populates="question")


class AssessmentSession(Base):
    __tablename__ = "assessment_sessions"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    status = Column(Enum(SessionStatus), default=SessionStatus.pending, nullable=False)
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
    task_id = Column(String(255), nullable=True)   # Celery task ID
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    user = relationship("User", back_populates="assessment_sessions")
    responses = relationship("AssessmentResponse", back_populates="session")
    result = relationship("AssessmentResult", back_populates="session", uselist=False)


class AssessmentResponse(Base):
    __tablename__ = "assessment_responses"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False)
    question_id = Column(Integer, ForeignKey("questions.id"), nullable=False)
    answer_text = Column(Text, nullable=True)
    answer_data = Column(JSON, nullable=True)      # Audio file path, drawing coordinates, etc.
    reaction_time_ms = Column(Integer, nullable=True)
    is_correct = Column(Boolean, nullable=True)
    score = Column(Float, nullable=True)           # Partial score 0.0-1.0
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("AssessmentSession", back_populates="responses")
    question = relationship("Question", back_populates="responses")


class AssessmentResult(Base):
    __tablename__ = "assessment_results"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    session_id = Column(Integer, ForeignKey("assessment_sessions.id"), nullable=False, unique=True)
    risk_level = Column(Enum(RiskLevel), nullable=False)
    nc_probability = Column(Float, nullable=False)   # Normal Cognition probability
    mci_probability = Column(Float, nullable=False)  # Mild Cognitive Impairment probability
    ad_probability = Column(Float, nullable=False)   # Alzheimer's Disease probability
    mmse_score = Column(Float, nullable=True)        # Mini-Mental State Examination equivalent score
    domain_scores = Column(JSON, nullable=False)     # {memory, orientation, language, attention, visuospatial, executive}
    shap_values = Column(JSON, nullable=True)        # SHAP feature importance values
    recommendation = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    session = relationship("AssessmentSession", back_populates="result")

    __table_args__ = (
        UniqueConstraint("session_id", name="uq_result_session"),
    )
