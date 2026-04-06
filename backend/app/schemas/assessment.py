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
    correct_answer: Optional[str] = None
    difficulty: float
    irt_a: float
    irt_b: float
    is_active: bool


class QuestionCreate(BaseModel):
    domain: QuestionDomain
    q_type: QuestionType
    content: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    difficulty: float = 0.5
    irt_a: float = 1.0
    irt_b: float = 0.0


class QuestionUpdate(BaseModel):
    domain: Optional[QuestionDomain] = None
    q_type: Optional[QuestionType] = None
    content: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    difficulty: Optional[float] = None
    irt_a: Optional[float] = None
    irt_b: Optional[float] = None
    is_active: Optional[bool] = None


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
    pause_deadline: Optional[datetime] = None
    is_resumable: Optional[bool] = None


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
    moca_score: Optional[float] = None
    moca_score_corrected: Optional[float] = None
    education_correction_applied: Optional[bool] = None
    education_correction_points: Optional[float] = None
    mmse_subscores: Optional[Dict[str, float]] = None
    moca_subscores: Optional[Dict[str, float]] = None
    clinical_report: Optional[Dict[str, Any]] = None
    domain_scores: Dict[str, float]
    model_confidence: Optional[float] = None
    modality_quality: Optional[Dict[str, float]] = None
    modality_contributions: Optional[Dict[str, float]] = None
    top_factors: Optional[List[Dict[str, Any]]] = None
    data_quality_flag: Optional[str] = None
    model_name: Optional[str] = None
    model_strategy: Optional[str] = None
    engine_info: Optional[Dict[str, Any]] = None
    attention_matrix: Optional[List[List[float]]] = None
    shap_values: Optional[Dict[str, Any]] = None
    recommendation: Optional[str] = None
    created_at: datetime


class TaskStatusOut(BaseModel):
    task_id: str
    status: str
    result: Optional[Dict[str, Any]] = None


class PauseResumeOut(BaseModel):
    session_id: int
    status: SessionStatus
    message: str
    pause_deadline: Optional[datetime] = None
    is_resumable: Optional[bool] = None


class TrendPointOut(BaseModel):
    session_id: int
    assessed_at: datetime
    mmse_score: Optional[float] = None
    moca_score_corrected: Optional[float] = None
    risk_level: str


class AssessmentTrendOut(BaseModel):
    elder_id: int
    points: List[TrendPointOut]
    latest_risk_level: Optional[str] = None
    previous_risk_level: Optional[str] = None
    risk_change: str = "unknown"
    next_reassessment_date: Optional[str] = None


class FamilyReadableReportOut(BaseModel):
    elder_id: int
    session_id: int
    assessed_at: datetime
    risk_level: str
    risk_change: str = "unknown"
    next_reassessment_date: Optional[str] = None
    summary: str
    plain_interpretation: str
    daily_tips: List[str]
    warning_signs: List[str]
