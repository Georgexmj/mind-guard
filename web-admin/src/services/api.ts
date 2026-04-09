import axios from 'axios'
import type {
  AdherenceTicket,
  AdherenceTicketBatchUpdatePayload,
  AdherenceTicketBatchUpdateResult,
  AdherenceTicketStats,
  User,
  Community,
  AssessmentSession,
  AssessmentResult,
  AssessmentTrend,
  FamilyRelationship,
  FamilyReadableReport,
  WechatBinding,
  TokenResponse,
  WorkbenchQueues,
  DashboardStats,
  NotificationItem,
  InterventionAdherenceAlert,
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

type UserListParams = {
  page?: number
  page_size?: number
  community_id?: number
}

const USER_LIST_PAGE_LIMIT = 100

async function fetchUserList(
  endpoint: string,
  params?: UserListParams,
  extraParams?: Record<string, unknown>
): Promise<User[]> {
  const page = Math.max(params?.page ?? 1, 1)
  const pageSize = Math.max(params?.page_size ?? 20, 1)
  const sharedParams = {
    ...extraParams,
    community_id: params?.community_id,
  }

  if (pageSize <= USER_LIST_PAGE_LIMIT) {
    const response = await apiClient.get<User[]>(endpoint, {
      params: { ...sharedParams, page, page_size: pageSize },
    })
    return response.data
  }

  const logicalOffset = (page - 1) * pageSize
  const startPage = Math.floor(logicalOffset / USER_LIST_PAGE_LIMIT) + 1
  const endOffsetExclusive = logicalOffset + pageSize
  const endPage = Math.ceil(endOffsetExclusive / USER_LIST_PAGE_LIMIT)

  const responses = await Promise.all(
    Array.from({ length: endPage - startPage + 1 }, (_, index) =>
      apiClient.get<User[]>(endpoint, {
        params: {
          ...sharedParams,
          page: startPage + index,
          page_size: USER_LIST_PAGE_LIMIT,
        },
      })
    )
  )

  const mergedRows = responses.flatMap((response) => response.data)
  const sliceStart = logicalOffset - (startPage - 1) * USER_LIST_PAGE_LIMIT
  return mergedRows.slice(sliceStart, sliceStart + pageSize)
}

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
export const getElders = async (params?: UserListParams): Promise<User[]> =>
  fetchUserList('/users/elders', params)

export const getFamilies = async (params?: UserListParams): Promise<User[]> => {
  return fetchUserList('/users', params, { role: 'family' })
}

export const getDoctors = async (params?: UserListParams): Promise<User[]> => {
  return fetchUserList('/users', params, { role: 'doctor' })
}

export const getElderById = async (userId: number): Promise<User> => {
  const response = await apiClient.get<User>(`/users/${userId}`)
  return response.data
}

export const createFamilyRelationship = async (data: {
  elder_id: number
  family_id: number
  relationship: string
  notify_level?: number
  is_primary?: boolean
}): Promise<Record<string, unknown>> => {
  const response = await apiClient.post('/users/bind-family', data)
  return response.data
}

export const getFamilyRelationships = async (params?: {
  elder_id?: number
  family_id?: number
}): Promise<FamilyRelationship[]> => {
  const response = await apiClient.get<FamilyRelationship[]>('/users/family-relationships', { params })
  return response.data
}

export const deleteFamilyRelationship = async (relationId: number): Promise<{ deleted_id: number; message: string }> => {
  const response = await apiClient.delete<{ deleted_id: number; message: string }>(`/users/family-relationships/${relationId}`)
  return response.data
}

export const getWechatBindings = async (params?: { user_id?: number }): Promise<WechatBinding[]> => {
  const response = await apiClient.get<WechatBinding[]>('/users/wechat-bindings', { params })
  return response.data
}

export const upsertWechatBinding = async (data: {
  user_id: number
  openid: string
  unionid?: string
  is_active?: boolean
}): Promise<WechatBinding> => {
  const response = await apiClient.post<WechatBinding>('/users/wechat-bindings', data)
  return response.data
}

export const removeWechatBinding = async (bindingId: number): Promise<{ deleted_id: number; message: string }> => {
  const response = await apiClient.delete<{ deleted_id: number; message: string }>(`/users/wechat-bindings/${bindingId}`)
  return response.data
}

// Sessions
export const getSessions = async (params?: {
  user_id?: number
  status?: string
  page?: number
  page_size?: number
}): Promise<AssessmentSession[]> => {
  const response = await apiClient.get<AssessmentSession[]>('/assessments/sessions')
  let sessions = Array.isArray(response.data) ? response.data : []

  if (typeof params?.user_id === 'number') {
    sessions = sessions.filter((session) => session.user_id === params.user_id)
  }

  if (params?.status) {
    sessions = sessions.filter((session) => session.status === params.status)
  }

  try {
    const [elders, communities] = await Promise.all([
      getElders({ page: 1, page_size: 1000 }),
      getCommunities(),
    ])

    const elderMap = new Map(elders.map((elder) => [elder.id, elder]))
    const communityMap = new Map(communities.map((community) => [community.id, community.name]))

    sessions = sessions.map((session) => {
      const elder = elderMap.get(session.user_id)
      const communityName = elder?.community_id ? communityMap.get(elder.community_id) : undefined

      return {
        ...session,
        user: session.user ?? elder,
        user_name: elder?.name,
        community_name: communityName,
      } as AssessmentSession
    })
  } catch {
    // Keep raw session data when supplemental elder/community lookup fails.
  }

  if (typeof params?.page_size === 'number' && params.page_size > 0) {
    const page = Math.max(params.page ?? 1, 1)
    const start = (page - 1) * params.page_size
    sessions = sessions.slice(start, start + params.page_size)
  }

  return sessions
}

export const getSessionResult = async (sessionId: number): Promise<AssessmentResult> => {
  const response = await apiClient.get<AssessmentResult>(`/assessments/sessions/${sessionId}/result`)
  return response.data
}

export const getSessionDetail = async (
  sessionId: number
): Promise<AssessmentSession & { result?: AssessmentResult }> => {
  const sessionRes = await apiClient.get<AssessmentSession>(`/assessments/sessions/${sessionId}`)
  let result: AssessmentResult | undefined
  try {
    const resultRes = await apiClient.get<AssessmentResult>(`/assessments/sessions/${sessionId}/result`)
    result = resultRes.data
  } catch {
    result = undefined
  }
  return { ...sessionRes.data, result }
}

// Communities
export const getCommunities = async (): Promise<Community[]> => {
  const response = await apiClient.get<Community[]>('/communities')
  return response.data
}

export const getDashboardStats = async (): Promise<DashboardStats> => {
  const response = await apiClient.get<DashboardStats>('/dashboard/stats')
  return response.data
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

export const createInterventionPlanFromTop5 = async (data: {
  elder_id?: number
  session_id?: number
  recommendation_code: string
  duration_days?: number
  start_date?: string
}): Promise<unknown> => {
  const response = await apiClient.post('/interventions/recommendations/top5/create-plan', data)
  return response.data
}

export const getInterventionAdherenceAlerts = async (params?: {
  days?: number
  threshold?: number
  elder_id?: number
  sync_ticket?: boolean
}): Promise<InterventionAdherenceAlert[]> => {
  const response = await apiClient.get<InterventionAdherenceAlert[]>('/interventions/adherence-alerts', { params })
  return response.data
}

export const syncAdherenceTickets = async (params?: {
  days?: number
  threshold?: number
  elder_id?: number
}): Promise<{ generated_count: number; open_count: number; in_progress_count: number; resolved_count: number }> => {
  const response = await apiClient.post('/interventions/adherence-tickets/sync', null, { params })
  return response.data
}

export const getAdherenceTickets = async (params?: {
  status?: string
  owner_doctor_id?: number
  elder_id?: number
  page?: number
  page_size?: number
}): Promise<AdherenceTicket[]> => {
  const response = await apiClient.get<AdherenceTicket[]>('/interventions/adherence-tickets', { params })
  return response.data
}

export const updateAdherenceTicket = async (
  ticketId: number,
  data: {
    status?: 'open' | 'in_progress' | 'resolved' | 'ignored'
    owner_doctor_id?: number
    reminder_at?: string
    followup_note?: string
  }
): Promise<AdherenceTicket> => {
  const response = await apiClient.put<AdherenceTicket>(`/interventions/adherence-tickets/${ticketId}`, data)
  return response.data
}

export const batchUpdateAdherenceTickets = async (
  data: AdherenceTicketBatchUpdatePayload
): Promise<AdherenceTicketBatchUpdateResult> => {
  const response = await apiClient.post<AdherenceTicketBatchUpdateResult>(
    '/interventions/adherence-tickets/batch-update',
    data
  )
  return response.data
}

export const getAdherenceTicketStats = async (params?: {
  owner_doctor_id?: number
  elder_id?: number
}): Promise<AdherenceTicketStats> => {
  const response = await apiClient.get<AdherenceTicketStats>('/interventions/adherence-tickets/stats', { params })
  return response.data
}

export const dispatchAdherenceReminders = async (due_only = true): Promise<{
  candidate_count: number
  pushed_count: number
  skipped_count: number
  detail: Record<string, unknown>[]
}> => {
  const response = await apiClient.post('/interventions/reminders/adherence/dispatch', null, {
    params: { due_only },
  })
  return response.data
}

export const getAssessmentTrend = async (params?: {
  elder_id?: number
  months?: number
}): Promise<AssessmentTrend> => {
  const response = await apiClient.get<AssessmentTrend>('/assessments/trend', { params })
  return response.data
}

export const downloadDoctorReportPdf = async (sessionId: number): Promise<Blob> => {
  const response = await apiClient.get(`/assessments/sessions/${sessionId}/doctor-report.pdf`, {
    responseType: 'blob',
  })
  return response.data
}

export const downloadDoctorReportsBatchZip = async (
  sessionIds: number[],
  options?: { hospital_name?: string; doctor_name?: string; signature_text?: string }
): Promise<Blob> => {
  const params = new URLSearchParams()
  sessionIds.forEach((id) => params.append('session_ids', String(id)))
  if (options?.hospital_name) params.append('hospital_name', options.hospital_name)
  if (options?.doctor_name) params.append('doctor_name', options.doctor_name)
  if (options?.signature_text) params.append('signature_text', options.signature_text)
  const response = await apiClient.get(`/assessments/reports/doctor/batch?${params.toString()}`, {
    responseType: 'blob',
  })
  return response.data
}

export const getFamilyReadableReport = async (sessionId: number): Promise<FamilyReadableReport> => {
  const response = await apiClient.get<FamilyReadableReport>(`/assessments/sessions/${sessionId}/family-report`)
  return response.data
}

export const dispatchReassessmentReminders = async (within_days = 7): Promise<{
  candidate_count: number
  pushed_count: number
  within_days: number
  detail: Record<string, unknown>[]
}> => {
  const response = await apiClient.post('/assessments/reminders/reassessment/dispatch', null, {
    params: { within_days },
  })
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

export const getDashboardWorkbenchQueues = async (limit = 20): Promise<WorkbenchQueues> => {
  const response = await apiClient.get<WorkbenchQueues>('/dashboard/workbench-queues', { params: { limit } })
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
