from datetime import datetime, date
from typing import List, Optional
from pydantic import BaseModel, ConfigDict

from app.models.intervention import PlanStatus


class InterventionPlanCreate(BaseModel):
    elder_id: int
    title: str
    description: Optional[str] = None
    domain_focus: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class InterventionPlanUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    domain_focus: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: Optional[PlanStatus] = None


class InterventionPlanOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    elder_id: int
    created_by: int
    title: str
    description: Optional[str] = None
    domain_focus: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    status: PlanStatus
    ai_priority: Optional[float] = None
    created_at: datetime
    updated_at: datetime
    # Computed fields (injected from queries)
    elder_name: Optional[str] = None
    completed_count: Optional[int] = None
    total_records: Optional[int] = None


class InterventionRecordCreate(BaseModel):
    plan_id: int
    record_date: Optional[date] = None
    completed: bool = True
    duration_min: Optional[int] = None
    notes: Optional[str] = None
    mood_score: Optional[int] = None


class InterventionRecordOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    elder_id: int
    record_date: date
    completed: bool
    duration_min: Optional[int] = None
    notes: Optional[str] = None
    mood_score: Optional[int] = None
    created_at: datetime


class InterventionRecommendationItemOut(BaseModel):
    rank: int
    code: str
    title: str
    category: str
    target_domains: List[str]
    frequency: str
    duration_minutes: int
    rationale: str
    priority_score: float
    evidence_level: str


class InterventionTop5Out(BaseModel):
    elder_id: int
    session_id: int
    risk_level: str
    mmse_score: Optional[float] = None
    moca_score_corrected: Optional[float] = None
    generated_at: datetime
    recommendations: List[InterventionRecommendationItemOut]
