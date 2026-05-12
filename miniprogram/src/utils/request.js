import { getApiBaseUrlCandidates, setApiBaseUrl } from '../config/api'
import { useAuthStore } from '../store/auth'

export { getApiBaseUrl, getApiBaseUrlCandidates, setApiBaseUrl } from '../config/api'

function parseHttpError(res) {
  const detail = res?.data?.detail
  if (Array.isArray(detail)) {
    return detail.map((item) => item.msg).join(', ')
  }
  return detail || res?.data?.message || 'Request failed, please try again later.'
}

export function request(options) {
  return new Promise((resolve, reject) => {
    const auth = useAuthStore()
    const candidates = getApiBaseUrlCandidates()
    let index = 0

    const send = () => {
      const baseUrl = candidates[index]
      const url = `${baseUrl}${options.url}`
      console.log('Sending request - URL:', url, 'Method:', options.method, 'Has token:', !!auth.token, 'Token length:', auth.token?.length || 0)

      wx.request({
        url,
        method: options.method || 'GET',
        data: options.data,
        timeout: options.timeout || 60000,
        header: {
          'Content-Type': 'application/json',
          ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
        },
        success: (res) => {
          console.log('Request success - URL:', url, 'Status:', res.statusCode, 'Data:', res.data)
          // Auto-fallback for local dev when current base URL points to a different service.
          if (res.statusCode === 404 && index < candidates.length - 1) {
            index += 1
            send()
            return
          }

          if (res.statusCode === 401) {
            auth.logout()
            reject(new Error('Login expired, please sign in again.'))
            return
          }
          if (res.statusCode >= 200 && res.statusCode < 300) {
            if (index > 0) setApiBaseUrl(baseUrl)
            resolve(res.data)
            return
          }
          if (res.statusCode === 403) {
            reject(new Error('No permission to access this resource.'))
            return
          }
          if (res.statusCode === 404) {
            reject(new Error('API endpoint not found. Please check API base URL configuration.'))
            return
          }
          if (res.statusCode === 422) {
            reject(new Error(parseHttpError(res) || 'Invalid request payload.'))
            return
          }
          if (res.statusCode >= 500) {
            reject(new Error('Server is temporarily unavailable, please try again later.'))
            return
          }
          reject(new Error(parseHttpError(res)))
        },
        fail: (err) => {
          if (index < candidates.length - 1) {
            index += 1
            send()
            return
          }
          console.error('Request failed:', err)
          if (err.errMsg && err.errMsg.includes('timeout')) {
            reject(new Error('Network timeout, please try again.'))
            return
          }
          reject(new Error('Network connection failed. Check network and mini-program domain whitelist settings.'))
        },
      })
    }

    send()
  })
}

export function uploadFile(options) {
  return new Promise((resolve, reject) => {
    const auth = useAuthStore()
    const candidates = getApiBaseUrlCandidates()
    let index = 0

    const send = () => {
      const baseUrl = candidates[index]
      const url = `${baseUrl}${options.url}`

      wx.uploadFile({
        url,
        filePath: options.filePath,
        name: options.name || 'file',
        formData: options.formData || {},
        timeout: options.timeout || 30000,
        header: {
          ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
          ...(options.header || {}),
        },
        success: (res) => {
          if (res.statusCode === 404 && index < candidates.length - 1) {
            index += 1
            send()
            return
          }

          if (res.statusCode === 401) {
            auth.logout()
            reject(new Error('Login expired, please sign in again.'))
            return
          }

          let data = null
          try {
            data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          } catch {
            data = null
          }

          if (res.statusCode >= 200 && res.statusCode < 300) {
            if (index > 0) setApiBaseUrl(baseUrl)
            resolve(data)
            return
          }

          reject(new Error(parseHttpError({ data }) || 'Upload failed'))
        },
        fail: (err) => {
          if (index < candidates.length - 1) {
            index += 1
            send()
            return
          }
          console.error('Upload failed:', err)
          reject(new Error('File upload failed, please check network and domain whitelist settings.'))
        },
      })
    }

    send()
  })
}

export const api = {
  login: (username, password) => new Promise((resolve, reject) => {
    const auth = useAuthStore()
    wx.request({
      url: `${getApiBaseUrl()}/auth/login`,
      method: 'POST',
      header: { 'Content-Type': 'application/x-www-form-urlencoded' },
      data: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}`,
      success: (res) => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(new Error(res.data?.detail || res.data?.message || 'Login failed'))
        }
      },
      fail: (err) => {
        reject(new Error(err.errMsg || 'Network error'))
      }
    })
  }),

  getMe: () => request({ url: '/auth/me' }),

  createSession: () => request({ url: '/assessments/sessions', method: 'POST' }),

  getQuestions: (sessionId, count = 15) =>
    request({ url: `/assessments/sessions/${sessionId}/questions?count=${count}` }),

  submitAnswer: (sessionId, answer) =>
    request({
      url: `/assessments/sessions/${sessionId}/answers`,
      method: 'POST',
      data: answer,
    }),

  uploadSessionAudio: (sessionId, filePath) =>
    uploadFile({
      url: `/assessments/sessions/${sessionId}/uploads/audio`,
      filePath,
      name: 'file',
    }),

  completeSession: (sessionId) => request({ url: `/assessments/sessions/${sessionId}/complete`, method: 'POST' }),
  pauseSession: (sessionId) => request({ url: `/assessments/sessions/${sessionId}/pause`, method: 'POST' }),
  resumeSession: (sessionId) => request({ url: `/assessments/sessions/${sessionId}/resume`, method: 'POST' }),
  discardSession: (sessionId) => request({ url: `/assessments/sessions/${sessionId}`, method: 'DELETE' }),

  getResult: (sessionId) => request({ url: `/assessments/sessions/${sessionId}/result` }),

  getSessions: (params = {}) => {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    const suffix = query ? `?${query}` : ''
    return request({ url: `/assessments/sessions${suffix}` })
  },

  getMyElders: () => request({ url: '/users/my-elders' }),

  searchElder: (name) => request({ url: `/users/search?name=${encodeURIComponent(name)}` }),

  verifyElderIdCard: (elderId, idCard) =>
    request({
      url: `/users/${elderId}/verify-idcard`,
      method: 'POST',
      data: { id_card: idCard },
    }),

  getElderSessions: (elderId) => request({ url: `/assessments/sessions?elder_id=${elderId}` }),

  getElderSessionResult: (_elderId, sessionId) =>
    request({ url: `/assessments/sessions/${sessionId}/result` }),

  getTaskStatus: (taskId) => request({ url: `/assessments/tasks/${taskId}` }),

  getInterventionTop5: (params = {}) => {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    const suffix = query ? `?${query}` : ''
    return request({ url: `/interventions/recommendations/top5${suffix}` })
  },

  getInterventionMyProgress: () => request({ url: '/interventions/my-progress' }),

  createInterventionPlanFromTop5: (payload) =>
    request({
      url: '/interventions/recommendations/top5/create-plan',
      method: 'POST',
      data: payload,
    }),

  dailyInterventionCheckin: (payload) =>
    request({
      url: '/interventions/daily-checkin',
      method: 'POST',
      data: payload,
    }),

  getAssessmentTrend: (params = {}) => {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    const suffix = query ? `?${query}` : ''
    return request({ url: `/assessments/trend${suffix}` })
  },

  getProfile: () => request({ url: '/auth/me' }),

  updateProfile: (userId, data) => request({ url: `/users/${userId}`, method: 'PUT', data }),

  bindWechatByCode: (data) =>
    request({
      url: '/users/wechat-bindings/by-code',
      method: 'POST',
      data,
    }),

  getTrainingCourses: () => request({ url: '/training/courses' }),

  getTrainingCourseQuestions: (courseId) => request({ url: `/training/courses/${courseId}/questions` }),
}
