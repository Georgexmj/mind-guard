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
