import { useAuthStore } from '../store/auth'

// Change this for production deployment
const BASE_URL = 'http://localhost:8000/api/v1'

/**
 * Core HTTP request function
 * Handles auth headers, error responses, and 401 redirect
 */
export function request(options) {
  return new Promise((resolve, reject) => {
    const auth = useAuthStore()

    wx.request({
      url: BASE_URL + options.url,
      method: options.method || 'GET',
      data: options.data,
      header: {
        'Content-Type': 'application/json',
        ...(auth.token ? { 'Authorization': `Bearer ${auth.token}` } : {})
      },
      success: (res) => {
        if (res.statusCode === 401) {
          auth.logout()
          reject(new Error('登录已过期，请重新登录'))
        } else if (res.statusCode === 403) {
          reject(new Error('没有权限执行此操作'))
        } else if (res.statusCode === 404) {
          reject(new Error('请求的资源不存在'))
        } else if (res.statusCode === 422) {
          const detail = res.data?.detail
          if (Array.isArray(detail)) {
            reject(new Error(detail.map(d => d.msg).join('；')))
          } else {
            reject(new Error(detail || '提交的数据格式有误'))
          }
        } else if (res.statusCode >= 500) {
          reject(new Error('服务器暂时无法响应，请稍后再试'))
        } else if (res.statusCode >= 200 && res.statusCode < 300) {
          resolve(res.data)
        } else {
          reject(new Error(res.data?.detail || res.data?.message || '请求失败，请重试'))
        }
      },
      fail: (err) => {
        console.error('Request failed:', err)
        if (err.errMsg && err.errMsg.includes('timeout')) {
          reject(new Error('网络超时，请检查网络后重试'))
        } else if (err.errMsg && err.errMsg.includes('fail')) {
          reject(new Error('网络连接失败，请检查网络设置'))
        } else {
          reject(new Error('网络请求失败，请重试'))
        }
      }
    })
  })
}

/**
 * Upload file (for voice recordings)
 */
export function uploadFile(options) {
  return new Promise((resolve, reject) => {
    const auth = useAuthStore()

    wx.uploadFile({
      url: BASE_URL + options.url,
      filePath: options.filePath,
      name: options.name || 'file',
      formData: options.formData || {},
      header: {
        ...(auth.token ? { 'Authorization': `Bearer ${auth.token}` } : {})
      },
      success: (res) => {
        if (res.statusCode === 401) {
          auth.logout()
          reject(new Error('登录已过期，请重新登录'))
        } else if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            const data = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
            resolve(data)
          } catch (e) {
            resolve(res.data)
          }
        } else {
          let errData = {}
          try {
            errData = typeof res.data === 'string' ? JSON.parse(res.data) : res.data
          } catch (e) {}
          reject(new Error(errData?.detail || '上传失败，请重试'))
        }
      },
      fail: (err) => {
        console.error('Upload failed:', err)
        reject(new Error('文件上传失败，请检查网络后重试'))
      }
    })
  })
}

/**
 * All API endpoint functions
 */
export const api = {
  // Auth
  login: (phone, password) =>
    request({ url: '/auth/login', method: 'POST', data: { phone, password } }),

  getMe: () =>
    request({ url: '/auth/me' }),

  // Assessment Sessions
  createSession: () =>
    request({ url: '/assessments/sessions', method: 'POST' }),

  getQuestions: (sessionId) =>
    request({ url: `/assessments/sessions/${sessionId}/questions` }),

  submitAnswer: (sessionId, answer) =>
    request({ url: `/assessments/sessions/${sessionId}/answers`, method: 'POST', data: answer }),

  completeSession: (sessionId) =>
    request({ url: `/assessments/sessions/${sessionId}/complete`, method: 'POST' }),

  getResult: (sessionId) =>
    request({ url: `/assessments/sessions/${sessionId}/result` }),

  getSessions: () =>
    request({ url: '/assessments/sessions' }),

  // Background Tasks (for AI analysis polling)
  getTaskStatus: (taskId) =>
    request({ url: `/assessments/tasks/${taskId}` }),

  // Voice upload
  uploadVoice: (sessionId, questionId, filePath) =>
    uploadFile({
      url: `/assessments/sessions/${sessionId}/voice`,
      filePath: filePath,
      name: 'audio',
      formData: { question_id: questionId }
    }),

  // Profile
  getProfile: () =>
    request({ url: '/users/me' }),

  updateProfile: (data) =>
    request({ url: '/users/me', method: 'PUT', data }),
}
