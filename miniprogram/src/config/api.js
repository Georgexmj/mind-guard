const API_BASE_URL_STORAGE_KEY = 'mindguard_api_base_url'
const DEFAULT_DEV_API_BASE_URL = 'http://127.0.0.1:30001/api/v1'
const DEFAULT_PROD_API_BASE_URL = 'https://api.zhouchao5563.online/api/v1'
const DEV_FALLBACK_API_BASE_URLS = ['http://127.0.0.1:8000/api/v1']

const ENV_API_BASE_URL =
  (typeof process !== 'undefined' &&
    process.env &&
    (process.env.UNI_API_BASE_URL || process.env.VITE_API_BASE_URL)) ||
  ''

const IS_PROD = typeof process !== 'undefined' && process.env && process.env.NODE_ENV === 'production'

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
  const defaultUrl = IS_PROD ? DEFAULT_PROD_API_BASE_URL : DEFAULT_DEV_API_BASE_URL
  const fallbackUrls = IS_PROD ? [] : DEV_FALLBACK_API_BASE_URLS

  if (IS_PROD) {
    // In production, enforce configured online domain and ignore dev-stored overrides.
    return uniqBaseUrls([envUrl, defaultUrl])
  }

  return uniqBaseUrls([stored, envUrl, defaultUrl, ...fallbackUrls])
}

export function getApiBaseUrl() {
  const candidates = getApiBaseUrlCandidates()
  return candidates[0] || normalizeBaseUrl(DEFAULT_DEV_API_BASE_URL)
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
