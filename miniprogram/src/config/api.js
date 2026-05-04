const API_BASE_URL_STORAGE_KEY = 'mindguard_api_base_url'
const DEFAULT_DEV_API_BASE_URL = 'http://127.0.0.1:30001/api/v1'
const DEFAULT_TRIAL_API_BASE_URL = 'https://api.yishouxinan.site/api/v1'
const DEFAULT_RELEASE_API_BASE_URL = 'https://api.yishouxinan.site/api/v1'
const DEV_FALLBACK_API_BASE_URLS = ['http://127.0.0.1:8000/api/v1']

const NODE_ENV = (typeof process !== 'undefined' && process.env && process.env.NODE_ENV) || ''

function getEnvValue(keys) {
  if (typeof process === 'undefined' || !process.env) return ''
  for (const key of keys) {
    const value = process.env[key]
    if (typeof value === 'string' && value.trim()) return value
  }
  return ''
}

function getMiniProgramEnvVersion() {
  if (typeof wx === 'undefined' || typeof wx.getAccountInfoSync !== 'function') return ''
  try {
    const info = wx.getAccountInfoSync()
    const envVersion = info?.miniProgram?.envVersion || ''
    if (envVersion === 'develop' || envVersion === 'trial' || envVersion === 'release') {
      return envVersion
    }
  } catch (error) {
    // Ignore and fallback to NODE_ENV.
  }
  return ''
}

function getRuntimeStage() {
  const mpEnvVersion = getMiniProgramEnvVersion()
  if (mpEnvVersion) return mpEnvVersion
  return NODE_ENV === 'production' ? 'release' : 'develop'
}

function getPlatform() {
  if (typeof wx === 'undefined' || typeof wx.getSystemInfoSync !== 'function') return ''
  try {
    return (wx.getSystemInfoSync()?.platform || '').toLowerCase()
  } catch (error) {
    return ''
  }
}

function isLocalDevtoolsDebug(stage) {
  // Only local IDE debugging (develop + devtools) should use localhost.
  return stage === 'develop' && getPlatform() === 'devtools'
}

function getEnvApiBaseUrlByStage(stage) {
  if (stage === 'release') {
    return getEnvValue(['UNI_API_BASE_URL_RELEASE', 'VITE_API_BASE_URL_RELEASE', 'UNI_API_BASE_URL', 'VITE_API_BASE_URL'])
  }
  if (stage === 'trial') {
    return getEnvValue([
      'UNI_API_BASE_URL_TRIAL',
      'VITE_API_BASE_URL_TRIAL',
      'UNI_API_BASE_URL_RELEASE',
      'VITE_API_BASE_URL_RELEASE',
      'UNI_API_BASE_URL',
      'VITE_API_BASE_URL',
    ])
  }
  return getEnvValue(['UNI_API_BASE_URL_DEVELOP', 'VITE_API_BASE_URL_DEVELOP', 'UNI_API_BASE_URL', 'VITE_API_BASE_URL'])
}

function getDefaultApiBaseUrlByStage(stage) {
  if (stage === 'release') return DEFAULT_RELEASE_API_BASE_URL
  if (stage === 'trial') return DEFAULT_TRIAL_API_BASE_URL
  return DEFAULT_DEV_API_BASE_URL
}

function normalizeBaseUrl(url) {
  if (!url || typeof url !== 'string') return ''
  // Remove zero-width chars copied from rich text/editors.
  return url.replace(/[\u200B-\u200D\uFEFF]/g, '').trim().replace(/\/+$/, '')
}

function isValidHttpBaseUrl(url) {
  if (!url || typeof url !== 'string') return false
  if (!/^https?:\/\//i.test(url)) return false
  return true
}

function uniqBaseUrls(urls) {
  const seen = new Set()
  const list = []
  urls.forEach((url) => {
    const normalized = normalizeBaseUrl(url)
    if (!normalized || !isValidHttpBaseUrl(normalized) || seen.has(normalized)) return
    seen.add(normalized)
    list.push(normalized)
  })
  return list
}

export function getApiBaseUrlCandidates() {
  const stage = getRuntimeStage()
  const stored = normalizeBaseUrl(uni.getStorageSync(API_BASE_URL_STORAGE_KEY))
  const envUrl = normalizeBaseUrl(getEnvApiBaseUrlByStage(stage))
  const defaultUrl = normalizeBaseUrl(getDefaultApiBaseUrlByStage(stage))
  const useOnlineDomain = !isLocalDevtoolsDebug(stage)

  if (useOnlineDomain) {
    // Except local IDE debugging, enforce online domain and ignore dev-stored overrides.
    const onlineEnv = normalizeBaseUrl(
      getEnvValue([
        'UNI_API_BASE_URL_RELEASE',
        'VITE_API_BASE_URL_RELEASE',
        'UNI_API_BASE_URL_TRIAL',
        'VITE_API_BASE_URL_TRIAL',
        'UNI_API_BASE_URL',
        'VITE_API_BASE_URL',
      ])
    )
    const onlineDefault = normalizeBaseUrl(DEFAULT_RELEASE_API_BASE_URL)
    if (onlineEnv || onlineDefault) {
      return uniqBaseUrls([onlineEnv, onlineDefault])
    }
    return uniqBaseUrls([envUrl, defaultUrl])
  }

  return uniqBaseUrls([stored, envUrl, defaultUrl, ...DEV_FALLBACK_API_BASE_URLS])
}

export function getApiBaseUrl() {
  const candidates = getApiBaseUrlCandidates()
  return candidates[0] || normalizeBaseUrl(getDefaultApiBaseUrlByStage(getRuntimeStage()))
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
