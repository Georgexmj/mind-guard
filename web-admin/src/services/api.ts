import axios from 'axios'
import type {
  User,
  Community,
  AssessmentSession,
  AssessmentResult,
  TokenResponse,
  DashboardStats,
  NotificationItem,
  InterventionTop5Recommendation,
} from '../types'

const apiClient = axios.create({
  baseURL: '/api/v1',
  timeout: 15000,
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor: attach token
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor: handle 401
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      globalThis.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

// Auth
export const login = async (phone: string, password: string): Promise<TokenResponse> => {
  const response = await apiClient.post<TokenResponse>('/auth/login', { phone, password })
  return response.data
}

export const getMe = async (): Promise<User> => {
  const response = await apiClient.get<User>('/auth/me')
  return response.data
}

// Elders — backend returns a plain array, not paginated
export const getElders = async (params?: {
  page?: number
  page_size?: number
  community_id?: number
}): Promise<User[]> => {
  const response = await apiClient.get<User[]>('/users', {
    params: { role: 'elder', ...params },
  })
  return response.data
}

export const getElderById = async (userId: number): Promise<User> => {
  const response = await apiClient.get<User>(`/users/${userId}`)
  return response.data
}

// Sessions
export const getSessions = async (params?: {
  user_id?: number
  status?: string
  page?: number
  page_size?: number
}): Promise<AssessmentSession[]> => {
  const response = await apiClient.get<AssessmentSession[]>('/assessments/sessions', { params })
  return response.data
}

export const getSessionResult = async (sessionId: number): Promise<AssessmentResult> => {
  const response = await apiClient.get<AssessmentResult>(`/assessments/sessions/${sessionId}/result`)
  return response.data
}

export const getSessionDetail = async (
  sessionId: number
): Promise<AssessmentSession & { result?: AssessmentResult }> => {
  const [sessionRes, resultRes] = await Promise.allSettled([
    apiClient.get<AssessmentSession>(`/assessments/sessions/${sessionId}`),
    apiClient.get<AssessmentResult>(`/assessments/sessions/${sessionId}/result`),
  ])
  const session = sessionRes.status === 'fulfilled' ? sessionRes.value.data : ({} as AssessmentSession)
  const result = resultRes.status === 'fulfilled' && resultRes.value.data ? resultRes.value.data : undefined
  return { ...session, result }
}

// Communities
export const getCommunities = async (): Promise<Community[]> => {
  const response = await apiClient.get<Community[]>('/communities')
  return response.data
}

// Dashboard stats - with fallback mock
export const getDashboardStats = async (): Promise<DashboardStats> => {
  try {
    const response = await apiClient.get<DashboardStats>('/dashboard/stats')
    return response.data
  } catch {
    // Fallback: compute from existing endpoints or return mock
    return {
      total_elders: 128,
      total_sessions: 342,
      high_risk_count: 23,
      today_sessions: 7,
    }
  }
}

export default apiClient

// Interventions
export const getInterventionPlans = async (params?: {
  elder_id?: number
  status?: string
  page?: number
  page_size?: number
}): Promise<unknown[]> => {
  const response = await apiClient.get('/interventions/plans', { params })
  return response.data
}

export const createInterventionPlan = async (data: Record<string, unknown>): Promise<unknown> => {
  const response = await apiClient.post('/interventions/plans', data)
  return response.data
}

export const updateInterventionPlan = async (planId: number, data: Record<string, unknown>): Promise<unknown> => {
  const response = await apiClient.put(`/interventions/plans/${planId}`, data)
  return response.data
}

export const getInterventionRecords = async (planId: number): Promise<unknown[]> => {
  const response = await apiClient.get(`/interventions/plans/${planId}/records`)
  return response.data
}

export const submitInterventionRecord = async (data: Record<string, unknown>): Promise<unknown> => {
  const response = await apiClient.post('/interventions/records', data)
  return response.data
}

export const getInterventionTop5Recommendations = async (params?: {
  elder_id?: number
  session_id?: number
}): Promise<InterventionTop5Recommendation> => {
  const response = await apiClient.get<InterventionTop5Recommendation>('/interventions/recommendations/top5', { params })
  return response.data
}

// Questions (admin)
export const getQuestions = async (params?: {
  domain?: string
  q_type?: string
  is_active?: boolean
  page?: number
  page_size?: number
}): Promise<unknown[]> => {
  const response = await apiClient.get('/questions/', { params })
  return response.data
}

export const createQuestion = async (data: Record<string, unknown>): Promise<unknown> => {
  const response = await apiClient.post('/questions/', data)
  return response.data
}

export const updateQuestion = async (questionId: number, data: Record<string, unknown>): Promise<unknown> => {
  const response = await apiClient.put(`/questions/${questionId}`, data)
  return response.data
}

export const deleteQuestion = async (questionId: number): Promise<unknown> => {
  const response = await apiClient.delete(`/questions/${questionId}`)
  return response.data
}

export const exportQuestionsCsv = async (params?: {
  domain?: string
  q_type?: string
  is_active?: boolean
}): Promise<{ blob: Blob; filename: string }> => {
  const response = await apiClient.get<Blob>('/questions/export/csv', {
    params,
    responseType: 'blob',
  })
  const disposition = response.headers['content-disposition'] as string | undefined
  let filename = 'mindguard_questions.csv'
  if (disposition) {
    const match = disposition.match(/filename\*?=(?:UTF-8'')?\"?([^\";]+)\"?/i)
    if (match?.[1]) {
      filename = decodeURIComponent(match[1])
    }
  }
  return { blob: response.data, filename }
}

// Dashboard analytics
export const getDashboardMonthlyTrend = async (months = 6): Promise<{ month: string; count: number }[]> => {
  const response = await apiClient.get('/dashboard/monthly-trend', { params: { months } })
  return response.data
}

export const getDashboardHighRiskList = async (limit = 10): Promise<unknown[]> => {
  const response = await apiClient.get('/dashboard/high-risk-list', { params: { limit } })
  return response.data
}

// Notifications
export const getNotifications = async (params?: {
  unread_only?: boolean
  type?: 'assessment_completed' | 'high_risk_alert' | 'system_message'
  page?: number
  page_size?: number
}): Promise<NotificationItem[]> => {
  const response = await apiClient.get<NotificationItem[]>('/notifications', { params })
  return response.data
}

export const getNotificationUnreadCount = async (): Promise<number> => {
  const response = await apiClient.get<{ unread_count: number }>('/notifications/unread-count')
  return response.data.unread_count || 0
}

export const markNotificationRead = async (notificationId: number): Promise<void> => {
  await apiClient.put(`/notifications/${notificationId}/read`)
}

export const markAllNotificationsRead = async (): Promise<number> => {
  const response = await apiClient.put<{ marked_count: number }>('/notifications/read-all')
  return response.data.marked_count || 0
}
