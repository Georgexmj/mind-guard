from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict
from app.models.assessment import QuestionDomain, QuestionType, SessionStatus, RiskLevel


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: QuestionDomain
    q_type: QuestionType
    content: str
    options: Optional[List[str]] = None
    difficulty: float


class QuestionCreate(BaseModel):
    domain: QuestionDomain
    q_type: QuestionType
    content: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    difficulty: float = 0.5
    irt_a: float = 1.0
    irt_b: float = 0.0


class SessionCreate(BaseModel):
    # user_id will be extracted from JWT token
    pass


class SessionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    status: SessionStatus
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    task_id: Optional[str] = None
    created_at: datetime


class AnswerSubmit(BaseModel):
    question_id: int
    answer_text: Optional[str] = None
    answer_data: Optional[Dict[str, Any]] = None  # For audio file path, drawing coordinates, etc.
    reaction_time_ms: Optional[int] = None


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    question_id: int
    answer_text: Optional[str] = None
    answer_data: Optional[Dict[str, Any]] = None
    reaction_time_ms: Optional[int] = None
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    created_at: datetime


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    risk_level: RiskLevel
    nc_probability: float
    mci_probability: float
    ad_probability: float
    mmse_score: Optional[float] = None
    domain_scores: Dict[str, float]
    shap_values: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    created_at: datetime


class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None
