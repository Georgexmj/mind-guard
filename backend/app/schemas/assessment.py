from datetime import datetime
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict

from app.models.assessment import RiskLevel, SessionStatus


class AnswerSubmit(BaseModel):
    question_id: Union[str, int]
    answer_text: Optional[str] = None
    answer_data: Optional[Dict[str, Any]] = None
    reaction_time_ms: Optional[int] = None


class AnswerOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    question_id: Union[str, int]
    answer_text: Optional[str] = None
    answer_data: Optional[Dict[str, Any]] = None
    reaction_time_ms: Optional[int] = None
    is_correct: Optional[bool] = None
    score: Optional[float] = None
    created_at: datetime


class ResultOut(BaseModel):
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

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
    recommendation_items: Optional[List[Dict[str, Any]]] = None
    domain_scores: Dict[str, float]
    model_confidence: Optional[float] = None
    modality_quality: Optional[Dict[str, Any]] = None
    modality_contributions: Optional[Dict[str, float]] = None
    top_factors: Optional[List[Any]] = None
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
    model_config = ConfigDict(from_attributes=True, protected_namespaces=())

    session_id: int
    status: SessionStatus
    message: str
    pause_deadline: Optional[datetime] = None


class QuestionOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    domain: str
    q_type: str
    content: str
    options: Optional[List[str]] = None
    difficulty: Optional[float] = None


class QuestionCreate(BaseModel):
    domain: str
    q_type: str
    content: str
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    difficulty: Optional[float] = None
    irt_a: Optional[float] = None
    irt_b: Optional[float] = None


class QuestionUpdate(BaseModel):
    domain: Optional[str] = None
    q_type: Optional[str] = None
    content: Optional[str] = None
    options: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    difficulty: Optional[float] = None
    irt_a: Optional[float] = None
    irt_b: Optional[float] = None
    is_active: Optional[bool] = None


class SessionCreate(BaseModel):
    elder_id: Optional[int] = None


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


class TrendPointOut(BaseModel):
    session_id: int
    completed_at: datetime
    risk_level: RiskLevel
    mmse_score: Optional[float] = None
    moca_score: Optional[float] = None
    domain_scores: Dict[str, float]


class AssessmentTrendOut(BaseModel):
    elder_id: int
    trend_points: List[TrendPointOut]
    risk_direction: str
    summary: str


class FamilyReadableReportOut(BaseModel):
    elder_name: str
    assessment_date: str
    risk_level: str
    risk_level_description: str
    mmse_score: Optional[float] = None
    moca_score: Optional[float] = None
    domain_scores: Dict[str, float]
    top_concerns: List[str]
    recommendations: List[str]
    next_assessment_suggestion: str
    disclaimer: str
