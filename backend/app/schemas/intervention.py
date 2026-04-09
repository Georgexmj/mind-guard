from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.intervention import PlanStatus, TicketStatus


class InterventionPlanCreate(BaseModel):
    elder_id: int
    title: str
    description: Optional[str] = None
    domain_focus: Optional[str] = None
    frequency: Optional[str] = None
    duration_days: Optional[int] = None
    start_date: Optional[date] = None
    end_date: Optional[date] = None


class InterventionPlanFromTop5Create(BaseModel):
    elder_id: Optional[int] = None
    session_id: Optional[int] = None
    recommendation_code: str
    duration_days: int = Field(default=30, ge=1, le=365)
    start_date: Optional[date] = None


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
    interruption_reason: Optional[str] = None


class InterventionDailyCheckinCreate(BaseModel):
    plan_id: int
    record_date: Optional[date] = None
    completed: bool = True
    duration_min: Optional[int] = None
    interruption_reason: Optional[str] = None
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
    interruption_reason: Optional[str] = None
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


class InterventionAdherenceAlertOut(BaseModel):
    plan_id: int
    elder_id: int
    elder_name: Optional[str] = None
    plan_title: str
    ticket_id: Optional[int] = None
    ticket_status: Optional[TicketStatus] = None
    owner_doctor_id: Optional[int] = None
    owner_doctor_name: Optional[str] = None
    reminder_at: Optional[datetime] = None
    consecutive_missed_days: int
    completion_rate: float
    latest_interruption_reason: Optional[str] = None
    risk_level: Optional[str] = None
    suggested_action: str


class InterventionPlanProgressOut(BaseModel):
    plan_id: int
    plan_title: str
    recommendation_code: Optional[str] = None
    frequency: Optional[str] = None
    completion_rate: float
    completed_count: int
    total_records: int
    today_checked: bool
    today_completed: Optional[bool] = None
    consecutive_completed_days: int = 0
    consecutive_missed_days: int
    latest_interruption_reason: Optional[str] = None


class InterventionMyProgressOut(BaseModel):
    elder_id: int
    active_plan_count: int
    plans: List[InterventionPlanProgressOut]


class InterventionAdherenceTicketOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    plan_id: int
    elder_id: int
    elder_name: Optional[str] = None
    plan_title: Optional[str] = None
    status: TicketStatus
    owner_doctor_id: Optional[int] = None
    owner_doctor_name: Optional[str] = None
    reminder_at: Optional[datetime] = None
    followup_note: Optional[str] = None
    consecutive_missed_days: int
    completion_rate: float
    latest_interruption_reason: Optional[str] = None
    risk_level: Optional[str] = None
    resolved_at: Optional[datetime] = None
    last_notified_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class InterventionAdherenceTicketUpdate(BaseModel):
    status: Optional[TicketStatus] = None
    owner_doctor_id: Optional[int] = None
    reminder_at: Optional[datetime] = None
    followup_note: Optional[str] = None


class InterventionAdherenceTicketBatchUpdateIn(BaseModel):
    ticket_ids: List[int] = Field(default_factory=list, min_length=1, max_length=200)
    status: Optional[TicketStatus] = None
    owner_doctor_id: Optional[int] = None
    reminder_at: Optional[datetime] = None
    followup_note: Optional[str] = None
    append_followup_note: bool = False


class InterventionAdherenceTicketBatchUpdateOut(BaseModel):
    requested_count: int
    updated_count: int
    updated_ids: List[int]
    skipped_ids: List[int]


class InterventionAdherenceTicketStatsOut(BaseModel):
    total_count: int
    open_count: int
    in_progress_count: int
    resolved_count: int
    ignored_count: int
    overdue_open_count: int
    avg_response_hours: Optional[float] = None
    avg_resolution_hours: Optional[float] = None
    resolved_within_24h_rate: float
    resolved_within_48h_rate: float


class InterventionAdherenceTicketSyncOut(BaseModel):
    generated_count: int
    open_count: int
    in_progress_count: int
    resolved_count: int


class InterventionReminderDispatchOut(BaseModel):
    candidate_count: int
    pushed_count: int
    skipped_count: int
    detail: List[dict]
