import { useAuthStore } from '../store/auth'

const API_BASE_URL_STORAGE_KEY = 'mindguard_api_base_url'
const DEFAULT_API_BASE_URL = 'http://127.0.0.1:30001/api/v1'
const FALLBACK_API_BASE_URLS = ['http://127.0.0.1:8000/api/v1']
const ENV_API_BASE_URL =
  (typeof process !== 'undefined' && process.env && (process.env.UNI_API_BASE_URL || process.env.VITE_API_BASE_URL)) || ''

function normalizeBaseUrl(url) {
  if (!url || typeof url !== 'string') return ''
  return url.trim().replace(/\/+$/, '')
}

function uniqBaseUrls(urls) {
  const seen = new Set()
  const list = []
  urls.forEach((url) => {
    const normalized = normalizeBaseUrl(url)
    if (!normalized || seen.has(normalized)) return
    seen.add(normalized)
    list.push(normalized)
  })
  return list
}

export function getApiBaseUrlCandidates() {
  const stored = normalizeBaseUrl(uni.getStorageSync(API_BASE_URL_STORAGE_KEY))
  const envUrl = normalizeBaseUrl(ENV_API_BASE_URL)
  return uniqBaseUrls([stored, envUrl, DEFAULT_API_BASE_URL, ...FALLBACK_API_BASE_URLS])
}

export function getApiBaseUrl() {
  const candidates = getApiBaseUrlCandidates()
  return candidates[0] || normalizeBaseUrl(DEFAULT_API_BASE_URL)
}

export function setApiBaseUrl(url) {
  const normalized = normalizeBaseUrl(url)
  if (!normalized) {
    uni.removeStorageSync(API_BASE_URL_STORAGE_KEY)
    return ''
  }
  uni.setStorageSync(API_BASE_URL_STORAGE_KEY, normalized)
  return normalized
}

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

      wx.request({
        url,
        method: options.method || 'GET',
        data: options.data,
        timeout: options.timeout || 20000,
        header: {
          'Content-Type': 'application/json',
          ...(auth.token ? { Authorization: `Bearer ${auth.token}` } : {}),
        },
        success: (res) => {
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

export const api = {
  login: (phone, password) => request({ url: '/auth/login', method: 'POST', data: { phone, password } }),

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

  completeSession: (sessionId) => request({ url: `/assessments/sessions/${sessionId}/complete`, method: 'POST' }),
  pauseSession: (sessionId) => request({ url: `/assessments/sessions/${sessionId}/pause`, method: 'POST' }),
  resumeSession: (sessionId) => request({ url: `/assessments/sessions/${sessionId}/resume`, method: 'POST' }),
  discardSession: (sessionId) => request({ url: `/assessments/sessions/${sessionId}`, method: 'DELETE' }),

  getResult: (sessionId) => request({ url: `/assessments/sessions/${sessionId}/result` }),

  getSessions: () => request({ url: '/assessments/sessions' }),

  getTaskStatus: (taskId) => request({ url: `/assessments/tasks/${taskId}` }),

  getInterventionTop5: (params = {}) => {
    const query = Object.entries(params)
      .filter(([, value]) => value !== undefined && value !== null && value !== '')
      .map(([key, value]) => `${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`)
      .join('&')
    const suffix = query ? `?${query}` : ''
    return request({ url: `/interventions/recommendations/top5${suffix}` })
  },

  getProfile: () => request({ url: '/auth/me' }),

  updateProfile: (userId, data) => request({ url: `/users/${userId}`, method: 'PUT', data }),
}
