export interface User {
  id: number
  uuid: string
  name: string
  phone?: string
  role: 'elder' | 'family' | 'doctor' | 'admin'
  community_id?: number
  created_at: string
  birth_date?: string
  gender?: 'male' | 'female'
  education_years?: number
}

export interface Community {
  id: number
  name: string
  province: string
  city: string
}

export interface AssessmentSession {
  id: number
  user_id: number
  status: 'pending' | 'in_progress' | 'completed' | 'failed'
  started_at?: string
  completed_at?: string
  task_id?: string
  created_at: string
  pause_deadline?: string
  is_resumable?: boolean
  user?: User
}

export interface DomainScores {
  memory: number
  orientation: number
  language: number
  attention: number
  visuospatial: number
  executive: number
}

export interface AssessmentResult {
  id: number
  session_id: number
  risk_level: 'normal' | 'mild_risk' | 'high_risk'
  nc_probability: number
  mci_probability: number
  ad_probability: number
  mmse_score: number
  moca_score?: number
  moca_score_corrected?: number
  education_correction_applied?: boolean
  education_correction_points?: number
  mmse_subscores?: Record<string, number>
  moca_subscores?: Record<string, number>
  clinical_report?: {
    risk_summary?: string
    scale_interpretation?: {
      mmse?: string
      moca?: string
      education_correction_note?: string
    }
    score_snapshot?: {
      mmse_score?: number
      moca_score_raw?: number
      moca_score_corrected?: number
      confidence_percent?: number
    }
    weak_domains?: Array<{
      domain?: string
      label?: string
      score?: number
    }>
    clinical_note?: string
  }
  domain_scores: DomainScores
  model_confidence?: number
  modality_quality?: Record<string, number>
  modality_contributions?: Record<string, number>
  top_factors?: Array<{
    feature: string
    impact: number
  }>
  data_quality_flag?: string
  model_name?: string
  model_strategy?: string
  recommendation: string
  created_at: string
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: User
}

export interface DashboardStats {
  total_elders: number
  total_sessions: number
  high_risk_count: number
  today_sessions: number
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface NotificationItem {
  id: number
  user_id: number
  session_id?: number
  notification_type: 'assessment_completed' | 'high_risk_alert' | 'system_message'
  title: string
  content: string
  risk_level?: string
  payload?: Record<string, unknown>
  is_read: boolean
  read_at?: string
  created_at: string
}

export interface InterventionRecommendationItem {
  rank: number
  code: string
  title: string
  category: string
  target_domains: string[]
  frequency: string
  duration_minutes: number
  rationale: string
  priority_score: number
  evidence_level: string
}

export interface InterventionTop5Recommendation {
  elder_id: number
  session_id: number
  risk_level: string
  mmse_score?: number
  moca_score_corrected?: number
  generated_at: string
  recommendations: InterventionRecommendationItem[]
}

export interface InterventionAdherenceAlert {
  plan_id: number
  elder_id: number
  elder_name?: string
  plan_title: string
  ticket_id?: number
  ticket_status?: 'open' | 'in_progress' | 'resolved' | 'ignored'
  owner_doctor_id?: number
  owner_doctor_name?: string
  reminder_at?: string
  consecutive_missed_days: number
  completion_rate: number
  latest_interruption_reason?: string
  risk_level?: string
  suggested_action: string
}

export interface AssessmentTrendPoint {
  session_id: number
  assessed_at: string
  mmse_score?: number
  moca_score_corrected?: number
  risk_level: string
}

export interface AssessmentTrend {
  elder_id: number
  points: AssessmentTrendPoint[]
  latest_risk_level?: string
  previous_risk_level?: string
  risk_change: 'improved' | 'stable' | 'worsened' | 'unknown'
  next_reassessment_date?: string
}

export interface FamilyReadableReport {
  elder_id: number
  session_id: number
  assessed_at: string
  risk_level: string
  risk_change: 'improved' | 'stable' | 'worsened' | 'unknown'
  next_reassessment_date?: string
  summary: string
  plain_interpretation: string
  daily_tips: string[]
  warning_signs: string[]
}

export interface FamilyRelationship {
  id: number
  elder_id: number
  elder_name?: string
  family_id: number
  family_name?: string
  relationship: string
  notify_level: number
  is_primary: boolean
  created_at: string
}

export interface WechatBinding {
  id: number
  user_id: number
  openid: string
  unionid?: string
  is_active: boolean
  last_sent_at?: string
  created_at: string
  updated_at: string
}

export interface AdherenceTicket {
  id: number
  plan_id: number
  elder_id: number
  elder_name?: string
  plan_title?: string
  status: 'open' | 'in_progress' | 'resolved' | 'ignored'
  owner_doctor_id?: number
  owner_doctor_name?: string
  reminder_at?: string
  followup_note?: string
  consecutive_missed_days: number
  completion_rate: number
  latest_interruption_reason?: string
  risk_level?: string
  resolved_at?: string
  last_notified_at?: string
  created_at: string
  updated_at: string
}

export interface AdherenceTicketBatchUpdatePayload {
  ticket_ids: number[]
  status?: 'open' | 'in_progress' | 'resolved' | 'ignored'
  owner_doctor_id?: number
  reminder_at?: string
  followup_note?: string
  append_followup_note?: boolean
}

export interface AdherenceTicketBatchUpdateResult {
  requested_count: number
  updated_count: number
  updated_ids: number[]
  skipped_ids: number[]
}

export interface AdherenceTicketStats {
  total_count: number
  open_count: number
  in_progress_count: number
  resolved_count: number
  ignored_count: number
  overdue_open_count: number
  avg_response_hours?: number
  avg_resolution_hours?: number
  resolved_within_24h_rate: number
  resolved_within_48h_rate: number
}

export interface WorkbenchQueues {
  high_risk: Array<{
    session_id: number
    elder_id: number
    elder_name: string
    phone?: string
    mmse_score?: number
    ad_probability?: number
    assessed_at?: string
  }>
  reassessment_due: Array<{
    elder_id: number
    elder_name: string
    session_id: number
    risk_level: string
    next_reassessment_date: string
    days_to_due: number
  }>
  low_adherence: Array<{
    ticket_id: number
    plan_id: number
    elder_id: number
    elder_name?: string
    plan_title?: string
    status: string
    consecutive_missed_days: number
    completion_rate: number
    owner_doctor_id?: number
    owner_doctor_name?: string
    reminder_at?: string
    updated_at?: string
  }>
  counts: {
    high_risk: number
    reassessment_due: number
    low_adherence: number
  }
}

export interface ElderDashboardMetric {
  key: string
  label: string
  value: number
  unit?: string
  delta: number
  trend: 'up' | 'down' | 'flat'
  tone: 'teal' | 'violet' | 'orange' | 'rose'
}

export interface ElderScheduleItem {
  id: number
  title: string
  at: string
  status: 'pending' | 'due' | 'done'
  duration_minutes: number
}

export interface ElderRiskBucket {
  label: string
  count: number
  color: string
}

export interface ElderAlertItem {
  id: number
  title: string
  content: string
  created_at: string
  level: 'normal' | 'mild_risk' | 'high_risk'
}

export interface ElderTrendPoint {
  week: string
  cognitive_score: number
  training_minutes: number
}

export interface ElderDashboardPayload {
  elder_name: string
  greeting: string
  risk_level: 'normal' | 'mild_risk' | 'high_risk'
  next_assessment_at?: string
  metrics: ElderDashboardMetric[]
  schedule: ElderScheduleItem[]
  risk_distribution: ElderRiskBucket[]
  alerts: ElderAlertItem[]
  trend: ElderTrendPoint[]
  tips: string[]
}
