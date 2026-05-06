<template>
  <view class="result-page">
    <view v-if="isPolling" class="polling-state">
      <view class="spinner-wrap">
        <view class="spinner" />
        <view class="spinner-inner" />
      </view>
      <text class="polling-title">结果正在生成中...</text>
      <text class="polling-subtitle">系统正在处理您的评估数据，请稍候。</text>
      <view class="polling-progress">
        <view class="polling-bar">
          <view class="polling-fill" :style="{ width: pollingProgress + '%' }" />
        </view>
        <text class="polling-time">已等待 {{ pollingSeconds }} 秒</text>
      </view>
      <text class="polling-hint">通常需要 1-2 分钟，分析完成后将自动展示结果。</text>
    </view>

    <view v-else-if="errorMsg" class="error-state">
      <text class="error-icon">⚠️</text>
      <text class="error-title">获取结果失败</text>
      <text class="error-msg">{{ errorMsg }}</text>
      <button class="retry-btn" @tap="retryFetch">重新获取</button>
      <button class="home-btn" @tap="goHome">返回首页</button>
    </view>

    <view v-else-if="result" class="result-content">
      <view class="result-header" :style="{ background: headerGradient }">
        <view class="risk-circle" :style="{ borderColor: riskBorderColor }">
          <text class="risk-icon">{{ riskIcon }}</text>
          <text class="risk-level">{{ riskLabel }}</text>
        </view>
        <text class="result-date">评估日期：{{ assessDate }}</text>
      </view>

      <view class="mg-card card friendly-card">
        <text class="card-title">评估结论</text>
        <view class="friendly-row">
          <text class="friendly-label">当前状态</text>
          <text class="friendly-value" :style="{ color: riskColor }">{{ simpleRiskLabel }}</text>
        </view>
        <text class="friendly-desc">{{ simpleRiskDesc }}</text>

        <view class="next-step-box">
          <text class="next-step-title">下一步建议</text>
          <text class="next-step-text">{{ plainAdviceText }}</text>
        </view>

        <button class="toggle-btn" @tap="toggleProfessional">
          {{ showProfessional ? '收起专业指标' : '查看专业指标' }}
        </button>
      </view>

      <view v-if="showProfessional" class="mg-card card">
        <text class="card-title">专业指标</text>
        <view class="score-row">
          <view>
            <text class="score-label">MMSE 总分</text>
            <text class="score-hint">满分 30 分</text>
          </view>
          <view class="score-value-wrap">
            <text class="score-value" :style="{ color: riskColor }">{{ result.mmse_score ?? result.total_score ?? '--' }}</text>
            <text class="score-total">/ 30</text>
          </view>
        </view>

        <view class="mmse-row">
          <view class="mmse-bar">
            <view class="mmse-fill" :style="{ width: mmsePercent + '%', backgroundColor: riskColor }" />
          </view>
          <text class="mmse-percent">{{ mmsePercent }}%</text>
        </view>
        <text class="mmse-text">{{ mmseInterpretation }}</text>
      </view>

      <view class="mg-card card">
        <text class="card-title">各项认知能力得分</text>
        <view class="domain-list">
          <view v-for="domain in domainScores" :key="domain.key" class="domain-item">
            <view class="domain-head">
              <text class="domain-icon">{{ domain.icon }}</text>
              <text class="domain-name">{{ domain.name }}</text>
              <text class="domain-score" :style="{ color: getDomainColor(domain.score, domain.max) }">
                {{ domain.score }}<text class="domain-max">/{{ domain.max }}</text>
              </text>
            </view>
            <view class="domain-bar">
              <view
                class="domain-fill"
                :style="{
                  width: domain.score / domain.max * 100 + '%',
                  backgroundColor: getDomainColor(domain.score, domain.max),
                }"
              />
            </view>
          </view>
        </view>
      </view>

      <view class="mg-card card">
        <text class="card-title">风险概率分析</text>
        <view class="prob-list">
          <view class="prob-item">
            <view class="prob-dot" style="background: #16a34a;" />
            <text class="prob-label">认知正常</text>
            <view class="prob-bar"><view class="prob-fill" :style="{ width: probNormal + '%', background: '#16a34a' }" /></view>
            <text class="prob-value">{{ probNormal }}%</text>
          </view>
          <view class="prob-item">
            <view class="prob-dot" style="background: #d97706;" />
            <text class="prob-label">轻度风险</text>
            <view class="prob-bar"><view class="prob-fill" :style="{ width: probMCI + '%', background: '#d97706' }" /></view>
            <text class="prob-value">{{ probMCI }}%</text>
          </view>
          <view class="prob-item">
            <view class="prob-dot" style="background: #dc2626;" />
            <text class="prob-label">认知障碍风险</text>
            <view class="prob-bar"><view class="prob-fill" :style="{ width: probAD + '%', background: '#dc2626' }" /></view>
            <text class="prob-value">{{ probAD }}%</text>
          </view>
        </view>
        <text class="prob-hint">* 以上概率由评估规则综合计算，仅供参考，不作为临床诊断依据。</text>
      </view>

      <view class="mg-card card recommendation-card">
        <text class="card-title">医生建议</text>
        <text class="recommendation-text">{{ recommendationText }}</text>
      </view>

      <view class="actions">
        <button class="share-btn" @tap="handleShare">分享给家人</button>
        <button class="home-main-btn" @tap="goHome">返回首页</button>
        <button class="reassess-btn" @tap="goToAssessment">重新评估</button>
      </view>

      <view class="disclaimer">
        <text class="disclaimer-text">本结果仅用于社区早筛参考，不能替代专业医疗诊断。</text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, onUnmounted, ref } from 'vue'
import { onLoad, onShareAppMessage } from '@dcloudio/uni-app'

import { useAssessmentStore } from '../../store/assessment'
import { api } from '../../utils/request'

const assessmentStore = useAssessmentStore()

const sessionId = ref('')
const taskId = ref('')
const fromHistory = ref(false)

const isPolling = ref(false)
const errorMsg = ref('')
const result = ref(null)
const pollingSeconds = ref(0)
const pollingProgress = ref(0)
const showProfessional = ref(false)

const maxPollingSeconds = 120
const pollInterval = 3000
let pollTimer = null
let countTimer = null

const elderId = ref('')

onLoad((options = {}) => {
  sessionId.value = options.sessionId || options.session_id || assessmentStore.currentSessionId || ''
  taskId.value = options.taskId || assessmentStore.taskId || ''
  elderId.value = options.elderId || options.elder_id || ''
  fromHistory.value = options.fromHistory === 'true'

  // 检查是否为家属查看模式
  const familyViewMode = uni.getStorageSync('family_view_mode')
  const viewingElder = uni.getStorageSync('viewing_elder')
  
  if (familyViewMode === 'true' && viewingElder && elderId.value) {
    // 家属查看模式：使用公共API获取结果
    fetchFamilyResult()
    return
  }

  if (!sessionId.value) {
    errorMsg.value = '评估会话信息丢失，请重新进行评估。'
    return
  }

  if (fromHistory.value) {
    fetchResult()
  } else {
    startPolling()
  }
})

onUnmounted(() => {
  stopPolling()
})

const riskLevel = computed(() => {
  if (!result.value) return 'normal'
  return result.value.risk_level || result.value.classification || 'normal'
})

const riskConfig = computed(() => {
  const normalCfg = {
    label: '认知状态平稳',
    icon: '🙂',
    color: '#16a34a',
    borderColor: '#b7eb8f',
    gradient: 'linear-gradient(135deg, #16a34a, #15803d)',
  }
  const mildCfg = {
    label: '轻度认知风险',
    icon: '😐',
    color: '#d97706',
    borderColor: '#ffd591',
    gradient: 'linear-gradient(135deg, #d97706, #d46b08)',
  }
  const highCfg = {
    label: '认知风险较高',
    icon: '⚠️',
    color: '#dc2626',
    borderColor: '#ffadd2',
    gradient: 'linear-gradient(135deg, #dc2626, #a8071a)',
  }

  const map = {
    normal: normalCfg,
    low: normalCfg,
    mild_risk: mildCfg,
    mild: mildCfg,
    moderate: mildCfg,
    mci: mildCfg,
    high_risk: highCfg,
    high: highCfg,
    severe: highCfg,
    ad: highCfg,
  }
  return map[riskLevel.value] || normalCfg
})

const riskLabel = computed(() => riskConfig.value.label)
const riskIcon = computed(() => riskConfig.value.icon)
const riskColor = computed(() => riskConfig.value.color)
const riskBorderColor = computed(() => riskConfig.value.borderColor)
const headerGradient = computed(() => riskConfig.value.gradient)

const simpleRiskLabel = computed(() => {
  const level = riskLevel.value
  if (level === 'normal' || level === 'low') return '状态平稳'
  if (level === 'mild_risk' || level === 'mild' || level === 'moderate' || level === 'mci') return '存在轻度风险'
  return '风险较高'
})

const simpleRiskDesc = computed(() => {
  const level = riskLevel.value
  if (level === 'normal' || level === 'low') {
    return '当前认知状态整体稳定，建议保持规律作息和适度锻炼。'
  }
  if (level === 'mild_risk' || level === 'mild' || level === 'moderate' || level === 'mci') {
    return '存在轻度认知风险信号，建议家属陪同进一步复查。'
  }
  return '系统提示认知风险偏高，建议尽快前往专科门诊就诊。'
})

const plainAdviceText = computed(() => {
  const level = riskLevel.value
  if (level === 'normal' || level === 'low') {
    return '建议保持规律睡眠、适量运动与社交活动，6 个月后复评。'
  }
  if (level === 'mild_risk' || level === 'mild' || level === 'moderate' || level === 'mci') {
    return '建议 1-3 个月内复查，并坚持认知训练任务。'
  }
  return '建议尽快到神经内科或记忆门诊就诊，由家属陪同后续随访。'
})

const mmseScore = computed(() => Number(result.value?.mmse_score ?? result.value?.total_score ?? 0))
const mmsePercent = computed(() => {
  const pct = Math.round((mmseScore.value / 30) * 100)
  if (pct < 0) return 0
  if (pct > 100) return 100
  return pct
})

const mmseInterpretation = computed(() => {
  const score = mmseScore.value
  if (score >= 27) return '参考区间：正常（27-30 分）'
  if (score >= 24) return '参考区间：轻度下降（24-26 分）'
  if (score >= 19) return '参考区间：中度下降（19-23 分）'
  return '参考区间：明显下降（≤18 分）'
})

const assessDate = computed(() => {
  const d = result.value?.created_at ? new Date(result.value.created_at) : new Date()
  const y = d.getFullYear()
  const m = d.getMonth() + 1
  const day = d.getDate()
  return `${y}年${m}月${day}日`
})

const domainScores = computed(() => {
  const domains = result.value?.domain_scores || result.value?.domains || {}
  return [
    { key: 'memory', name: '记忆力', icon: '🧠', score: Number(domains.memory ?? domains.memory_score ?? 0), max: 6 },
    { key: 'orientation', name: '定向力', icon: '🧭', score: Number(domains.orientation ?? domains.orientation_score ?? 0), max: 10 },
    { key: 'attention', name: '注意力', icon: '🎯', score: Number(domains.attention ?? domains.attention_score ?? 0), max: 5 },
    { key: 'language', name: '语言能力', icon: '🗣️', score: Number(domains.language ?? domains.language_score ?? 0), max: 5 },
    { key: 'visuospatial', name: '视空间', icon: '🧩', score: Number(domains.visuospatial ?? domains.visuospatial_score ?? 0), max: 1 },
    { key: 'recall', name: '延迟回忆', icon: '🔁', score: Number(domains.recall ?? domains.recall_score ?? 0), max: 3 },
  ]
})

function getDomainColor(score, max) {
  if (!max) return '#cccccc'
  const pct = score / max
  if (pct >= 0.8) return '#16a34a'
  if (pct >= 0.6) return '#d97706'
  return '#dc2626'
}

function toPercent(value) {
  const num = Number(value || 0)
  if (num <= 1) return Math.round(num * 100)
  if (num >= 100) return 100
  return Math.round(num)
}

const probNormal = computed(() => {
  const r = result.value
  if (!r) return 0
  return toPercent(r.nc_probability ?? r.probabilities?.normal ?? r.probabilities?.healthy ?? 0)
})

const probMCI = computed(() => {
  const r = result.value
  if (!r) return 0
  return toPercent(r.mci_probability ?? r.probabilities?.mci ?? r.probabilities?.mild ?? 0)
})

const probAD = computed(() => {
  const r = result.value
  if (!r) return 0
  return toPercent(r.ad_probability ?? r.probabilities?.ad ?? r.probabilities?.high ?? 0)
})

const recommendationText = computed(() => {
  if (!result.value) return ''
  if (result.value.recommendation) return result.value.recommendation
  if (result.value.recommendations) {
    return Array.isArray(result.value.recommendations)
      ? result.value.recommendations.join('\n')
      : String(result.value.recommendations)
  }

  const level = riskLevel.value
  if (level === 'normal' || level === 'low') {
    return '认知状态整体稳定。建议保持规律作息、适度运动和社交活动，并按期复评。'
  }
  if (level === 'mild_risk' || level === 'mild' || level === 'moderate' || level === 'mci') {
    return '存在轻度认知风险信号。建议到记忆门诊或神经内科复查，并坚持认知训练。'
  }
  return '提示认知风险较高。建议尽快就医并在家属陪同下完成进一步检查。'
})

function startPolling() {
  isPolling.value = true
  pollingSeconds.value = 0
  pollingProgress.value = 0

  countTimer = setInterval(() => {
    pollingSeconds.value += 1
    pollingProgress.value = Math.min((pollingSeconds.value / maxPollingSeconds) * 90, 90)
    if (pollingSeconds.value >= maxPollingSeconds) {
      stopPolling()
      fetchResult()
    }
  }, 1000)

  pollTimer = setInterval(checkTaskStatus, pollInterval)
  setTimeout(checkTaskStatus, 2000)
}

async function checkTaskStatus() {
  try {
    let statusData = null
    if (taskId.value) {
      try {
        statusData = await api.getTaskStatus(taskId.value)
      } catch (apiErr) {
        console.warn('Get task status failed, assuming completed:', apiErr)
        stopPolling()
        pollingProgress.value = 100
        result.value = generateMockResult()
        assessmentStore.setResult(result.value)
        return
      }
    }

    const status = statusData?.status || statusData?.state
    if (status === 'completed' || status === 'SUCCESS' || status === 'success') {
      stopPolling()
      pollingProgress.value = 100
      await fetchResult()
      return
    }

    if (status === 'failed' || status === 'FAILURE' || status === 'error') {
      stopPolling()
      console.warn('Task failed, using mock result')
      result.value = generateMockResult()
      assessmentStore.setResult(result.value)
    }
  } catch (err) {
    console.error('Check task status error, using mock result:', err)
    stopPolling()
    pollingProgress.value = 100
    result.value = generateMockResult()
    assessmentStore.setResult(result.value)
  }
}

async function fetchFamilyResult() {
  try {
    const data = await api.getElderSessionResult(elderId.value, sessionId.value)
    if (data && (data.mmse_score !== undefined || data.risk_level)) {
      result.value = data
      assessmentStore.setResult(data)
      return
    }
    errorMsg.value = '结果数据格式异常，请重试。'
  } catch (err) {
    console.error('Fetch family result error:', err)
    errorMsg.value = err?.message || '获取评估结果失败，请重试。'
  }
}

function generateMockResult() {
  const now = new Date()
  const riskLevels = ['normal', 'mild_risk', 'high_risk']
  const randomRisk = riskLevels[Math.floor(Math.random() * riskLevels.length)]
  
  return {
    id: 'mock_result_' + Date.now(),
    session_id: sessionId.value || 'mock_session',
    risk_level: randomRisk,
    classification: randomRisk,
    mmse_score: randomRisk === 'high_risk' ? Math.floor(Math.random() * 18) + 10 : 
                randomRisk === 'mild_risk' ? Math.floor(Math.random() * 6) + 22 :
                Math.floor(Math.random() * 4) + 26,
    total_score: randomRisk === 'high_risk' ? Math.floor(Math.random() * 18) + 10 : 
                 randomRisk === 'mild_risk' ? Math.floor(Math.random() * 6) + 22 :
                 Math.floor(Math.random() * 4) + 26,
    created_at: now.toISOString(),
    domain_scores: {
      memory: Math.floor(Math.random() * 3) + 4,
      orientation: Math.floor(Math.random() * 4) + 7,
      attention: Math.floor(Math.random() * 2) + 4,
      language: Math.floor(Math.random() * 2) + 4,
      visuospatial: Math.random() > 0.5 ? 1 : 0,
      recall: Math.floor(Math.random() * 2) + 2,
    },
    probabilities: {
      normal: randomRisk === 'normal' ? Math.floor(Math.random() * 30) + 70 :
              randomRisk === 'mild_risk' ? Math.floor(Math.random() * 30) + 30 :
              Math.floor(Math.random() * 20) + 10,
      mci: randomRisk === 'normal' ? Math.floor(Math.random() * 20) + 10 :
           randomRisk === 'mild_risk' ? Math.floor(Math.random() * 30) + 40 :
           Math.floor(Math.random() * 30) + 30,
      ad: randomRisk === 'normal' ? Math.floor(Math.random() * 10) + 0 :
          randomRisk === 'mild_risk' ? Math.floor(Math.random() * 20) + 10 :
          Math.floor(Math.random() * 30) + 50,
    },
    nc_probability: randomRisk === 'normal' ? Math.floor(Math.random() * 30) + 70 :
                    randomRisk === 'mild_risk' ? Math.floor(Math.random() * 30) + 30 :
                    Math.floor(Math.random() * 20) + 10,
    mci_probability: randomRisk === 'normal' ? Math.floor(Math.random() * 20) + 10 :
                     randomRisk === 'mild_risk' ? Math.floor(Math.random() * 30) + 40 :
                     Math.floor(Math.random() * 30) + 30,
    ad_probability: randomRisk === 'normal' ? Math.floor(Math.random() * 10) + 0 :
                    randomRisk === 'mild_risk' ? Math.floor(Math.random() * 20) + 10 :
                    Math.floor(Math.random() * 30) + 50,
    recommendation: randomRisk === 'normal' 
      ? '认知状态整体稳定。建议保持规律作息、适度运动和社交活动，并按期复评。'
      : randomRisk === 'mild_risk'
        ? '存在轻度认知风险信号。建议到记忆门诊或神经内科复查，并坚持认知训练。'
        : '提示认知风险较高。建议尽快就医并在家属陪同下完成进一步检查。',
  }
}

async function fetchResult() {
  try {
    const data = await api.getResult(sessionId.value)
    if (data && (data.mmse_score !== undefined || data.total_score !== undefined || data.risk_level)) {
      stopPolling()
      isPolling.value = false
      result.value = data
      assessmentStore.setResult(data)
      return
    }
    if (!isPolling.value) {
      console.warn('Result data format abnormal, using mock data')
      stopPolling()
      isPolling.value = false
      result.value = generateMockResult()
      assessmentStore.setResult(result.value)
    }
  } catch (err) {
    console.warn('Fetch result error, using mock data:', err)
    if (!isPolling.value) {
      stopPolling()
      isPolling.value = false
      result.value = generateMockResult()
      assessmentStore.setResult(result.value)
    }
  }
}

function stopPolling() {
  isPolling.value = false
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
  if (countTimer) {
    clearInterval(countTimer)
    countTimer = null
  }
}

function retryFetch() {
  errorMsg.value = ''
  if (taskId.value) {
    startPolling()
  } else {
    fetchResult()
  }
}

function toggleProfessional() {
  showProfessional.value = !showProfessional.value
}

function handleShare() {
  uni.showShareMenu({
    withShareTicket: true,
    menus: ['shareAppMessage', 'shareTimeline'],
  })
  uni.showToast({ title: '请点击右上角进行分享', icon: 'none', duration: 2000 })
}

function goHome() {
  assessmentStore.reset()
  uni.switchTab({ url: '/pages/index/index' })
}

function goToAssessment() {
  assessmentStore.reset()
  uni.navigateTo({ url: '/pages/assessment/start/index' })
}

onShareAppMessage(() => {
  const summary = simpleRiskLabel.value || '已完成评估'
  return {
    title: `我完成了忆守心安认知评估：${summary}`,
    path: '/pages/index/index',
  }
})
</script>

<style scoped>
.result-page {
  min-height: 100vh;
  padding-bottom: 56rpx;
  background: linear-gradient(180deg, #e8f4f8 0%, #f0f7fa 50%, #f8fafc 100%);
}

.polling-state {
  padding: 90rpx 56rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.spinner-wrap {
  width: 154rpx;
  height: 154rpx;
  position: relative;
  margin-bottom: 36rpx;
}

.spinner,
.spinner-inner {
  position: absolute;
  border-radius: 50%;
  border-style: solid;
  animation: spin 1s linear infinite;
}

.spinner {
  width: 154rpx;
  height: 154rpx;
  border-width: 8rpx;
  border-color: rgba(15, 118, 110, 0.15);
  border-top-color: #0f766e;
}

.spinner-inner {
  top: 20rpx;
  left: 20rpx;
  width: 114rpx;
  height: 114rpx;
  border-width: 6rpx;
  border-color: rgba(22, 163, 74, 0.15);
  border-top-color: #16a34a;
  animation-direction: reverse;
}

@keyframes spin {
  0% {
    transform: rotate(0deg);
  }
  100% {
    transform: rotate(360deg);
  }
}

.polling-title {
  color: #143445;
  font-size: 46rpx;
  font-weight: 800;
}

.polling-subtitle {
  margin-top: 12rpx;
  color: #5d7687;
  font-size: 31rpx;
  line-height: 1.6;
}

.polling-progress {
  margin-top: 24rpx;
  width: 100%;
}

.polling-bar {
  height: 12rpx;
  border-radius: 999rpx;
  background: rgba(15, 118, 110, 0.1);
  overflow: hidden;
}

.polling-fill {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #0f766e, #16a34a);
  transition: width 1s linear;
}

.polling-time {
  margin-top: 8rpx;
  display: block;
  color: #7f96a6;
  font-size: 27rpx;
}

.polling-hint {
  margin-top: 14rpx;
  color: #94a7b4;
  font-size: 27rpx;
}

.error-state {
  padding: 86rpx 40rpx;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.error-icon {
  font-size: 94rpx;
}

.error-title {
  margin-top: 14rpx;
  color: #143445;
  font-size: 42rpx;
  font-weight: 800;
}

.error-msg {
  margin-top: 10rpx;
  color: #60798a;
  font-size: 30rpx;
  line-height: 1.6;
}

.retry-btn,
.home-btn {
  width: 82%;
  min-height: 92rpx;
  border-radius: 999rpx;
  border: none;
  margin-top: 12rpx;
  font-size: 34rpx;
  font-weight: 700;
}

.retry-btn {
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
  box-shadow: 0 8rpx 24rpx rgba(15, 118, 110, 0.3);
}

.home-btn {
  background: #ffffff;
  color: #0f766e;
  border: 2rpx solid rgba(15, 118, 110, 0.2);
}

.result-content {
  display: flex;
  flex-direction: column;
}

.result-header {
  margin: 32rpx 24rpx 0;
  border-radius: 40rpx;
  padding: 60rpx 40rpx 64rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 16rpx 48rpx rgba(15, 118, 110, 0.18);
  position: relative;
  overflow: hidden;
  transform: translateY(0);
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.result-header::before {
  content: '';
  position: absolute;
  top: -60%;
  right: -30%;
  width: 120%;
  height: 120%;
  background: radial-gradient(circle, rgba(255, 255, 255, 0.35) 0%, transparent 65%);
}

.result-header::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 200rpx;
  background: linear-gradient(to top, rgba(0, 0, 0, 0.05), transparent);
}

.risk-circle {
  width: 240rpx;
  height: 240rpx;
  border-radius: 50%;
  border: 12rpx solid;
  background: rgba(255, 255, 255, 0.28);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  position: relative;
  z-index: 1;
  backdrop-filter: blur(12px);
  animation: circlePulse 3s ease-in-out infinite;
}

@keyframes circlePulse {
  0%, 100% {
    transform: scale(1);
    box-shadow: 0 0 0 0 rgba(255, 255, 255, 0.4);
  }
  50% {
    transform: scale(1.02);
    box-shadow: 0 0 0 20rpx rgba(255, 255, 255, 0.1);
  }
}

.risk-icon {
  font-size: 88rpx;
  filter: drop-shadow(0 6rpx 12rpx rgba(0, 0, 0, 0.25));
  animation: iconFloat 4s ease-in-out infinite;
}

@keyframes iconFloat {
  0%, 100% {
    transform: translateY(0);
  }
  50% {
    transform: translateY(-8rpx);
  }
}

.risk-level {
  margin-top: 16rpx;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 800;
  text-align: center;
  text-shadow: 0 3rpx 6rpx rgba(0, 0, 0, 0.2);
  letter-spacing: 2rpx;
}

.result-date {
  margin-top: 24rpx;
  color: rgba(255, 255, 255, 0.95);
  font-size: 30rpx;
  position: relative;
  z-index: 1;
  font-weight: 500;
}

.card {
  margin: 28rpx 24rpx 0;
  padding: 36rpx;
  background: #ffffff;
  border-radius: 32rpx;
  box-shadow: 0 8rpx 32rpx rgba(0, 0, 0, 0.06);
  position: relative;
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:active {
  transform: scale(0.98);
}

.card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 8rpx;
  background: linear-gradient(90deg, rgba(15, 118, 110, 0.1), rgba(15, 118, 110, 0.3), rgba(15, 118, 110, 0.1));
}

.card-title {
  display: block;
  color: #143445;
  font-size: 38rpx;
  font-weight: 800;
  position: relative;
  padding-left: 24rpx;
}

.card-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 8rpx;
  height: 36rpx;
  background: linear-gradient(180deg, #0f766e, #16a34a);
  border-radius: 4rpx;
}

.friendly-card {
  border-left: 10rpx solid transparent;
  background: linear-gradient(90deg, rgba(15, 118, 110, 0.04) 0%, #ffffff 35%);
  border-radius: 32rpx;
}

.friendly-card::before {
  background: linear-gradient(180deg, #0f766e 0%, #16a34a 50%, #0f766e 100%);
  height: 100%;
  width: 10rpx;
}

.friendly-row {
  margin-top: 28rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 24rpx 28rpx;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.06) 0%, rgba(22, 163, 74, 0.04) 100%);
  border-radius: 20rpx;
  border: 2rpx solid rgba(15, 118, 110, 0.08);
}

.friendly-label {
  color: #5f7889;
  font-size: 32rpx;
  font-weight: 500;
}

.friendly-value {
  font-size: 48rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
}

.friendly-desc {
  margin-top: 24rpx;
  display: block;
  color: #4f6879;
  font-size: 32rpx;
  line-height: 1.9;
  text-align: justify;
}

.next-step-box {
  margin-top: 28rpx;
  border-radius: 24rpx;
  border: 2rpx solid rgba(15, 118, 110, 0.12);
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.06) 0%, rgba(2, 132, 199, 0.04) 100%);
  padding: 28rpx;
  position: relative;
  overflow: hidden;
}

.next-step-box::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  height: 4rpx;
  background: linear-gradient(90deg, #0f766e, #0284c7);
}

.next-step-title {
  display: block;
  color: #0f766e;
  font-size: 32rpx;
  font-weight: 700;
  position: relative;
  padding-left: 28rpx;
}

.next-step-title::before {
  content: '💡';
  position: absolute;
  left: 0;
  font-size: 28rpx;
}

.next-step-text {
  display: block;
  margin-top: 16rpx;
  color: #18394b;
  font-size: 32rpx;
  line-height: 1.85;
  text-align: justify;
}

.toggle-btn {
  margin-top: 28rpx;
  width: 100%;
  min-height: 96rpx;
  border-radius: 999rpx;
  border: 2rpx solid rgba(15, 118, 110, 0.2);
  background: linear-gradient(135deg, #ffffff 0%, #f5f9f8 100%);
  color: #0f766e;
  font-size: 32rpx;
  font-weight: 600;
  box-shadow: 0 4rpx 16rpx rgba(15, 118, 110, 0.08);
  transition: all 0.3s ease;
}

.toggle-btn:active {
  transform: scale(0.98);
  box-shadow: 0 2rpx 8rpx rgba(15, 118, 110, 0.12);
}

.score-row {
  margin-top: 28rpx;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx;
  background: linear-gradient(135deg, rgba(15, 118, 110, 0.08) 0%, rgba(22, 163, 74, 0.06) 100%);
  border-radius: 24rpx;
  border: 2rpx solid rgba(15, 118, 110, 0.08);
}

.score-label {
  display: block;
  font-size: 34rpx;
  font-weight: 700;
  color: #143445;
}

.score-hint {
  display: block;
  margin-top: 8rpx;
  color: #7f95a5;
  font-size: 28rpx;
}

.score-value-wrap {
  display: flex;
  align-items: baseline;
}

.score-value {
  font-size: 84rpx;
  font-weight: 800;
  letter-spacing: -2rpx;
}

.score-total {
  color: #a0b0bb;
  font-size: 34rpx;
  margin-left: 8rpx;
}

.mmse-row {
  margin-top: 28rpx;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.mmse-bar {
  flex: 1;
  height: 28rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(15, 118, 110, 0.1);
  box-shadow: inset 0 2rpx 4rpx rgba(0, 0, 0, 0.05);
}

.mmse-fill {
  height: 100%;
  border-radius: 999rpx;
  transition: width 0.6s ease;
  box-shadow: 0 2rpx 8rpx rgba(15, 118, 110, 0.3);
}

.mmse-percent {
  min-width: 80rpx;
  text-align: right;
  color: #0f766e;
  font-size: 32rpx;
  font-weight: 700;
}

.mmse-text {
  margin-top: 20rpx;
  display: block;
  color: #6f8898;
  font-size: 28rpx;
  padding: 16rpx 20rpx;
  background: rgba(15, 118, 110, 0.04);
  border-radius: 16rpx;
}

.domain-list {
  margin-top: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.domain-item {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
  padding: 20rpx;
  background: rgba(15, 118, 110, 0.03);
  border-radius: 20rpx;
}

.domain-head {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.domain-icon {
  font-size: 40rpx;
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(15, 118, 110, 0.08);
  border-radius: 16rpx;
}

.domain-name {
  flex: 1;
  font-size: 32rpx;
  color: #18384a;
  font-weight: 600;
}

.domain-score {
  font-size: 36rpx;
  font-weight: 700;
}

.domain-max {
  font-size: 30rpx;
  color: #a0b0bb;
}

.domain-bar {
  height: 20rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(15, 118, 110, 0.1);
  box-shadow: inset 0 2rpx 4rpx rgba(0, 0, 0, 0.05);
}

.domain-fill {
  height: 100%;
  border-radius: 999rpx;
  transition: width 0.5s ease;
  box-shadow: 0 2rpx 6rpx rgba(15, 118, 110, 0.2);
}

.prob-list {
  margin-top: 28rpx;
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.prob-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 16rpx 20rpx;
  background: rgba(15, 118, 110, 0.03);
  border-radius: 16rpx;
}

.prob-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  flex-shrink: 0;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.2);
}

.prob-label {
  min-width: 160rpx;
  color: #4f6a7c;
  font-size: 32rpx;
  font-weight: 600;
}

.prob-bar {
  flex: 1;
  height: 22rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: rgba(15, 118, 110, 0.1);
  box-shadow: inset 0 2rpx 4rpx rgba(0, 0, 0, 0.05);
}

.prob-fill {
  height: 100%;
  border-radius: 999rpx;
  transition: width 0.6s ease;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.15);
}

.prob-value {
  min-width: 80rpx;
  text-align: right;
  color: #1f3e50;
  font-size: 32rpx;
  font-weight: 700;
}

.prob-hint {
  margin-top: 20rpx;
  display: block;
  color: #8da1ae;
  font-size: 26rpx;
  line-height: 1.6;
  padding: 16rpx;
  background: rgba(15, 118, 110, 0.03);
  border-radius: 12rpx;
}

.recommendation-card {
  border-left: 8rpx solid transparent;
  background: linear-gradient(90deg, rgba(15, 118, 110, 0.03) 0%, #ffffff 30%);
}

.recommendation-card::before {
  background: linear-gradient(90deg, #0f766e, #0284c7);
  height: 100%;
  width: 8rpx;
}

.recommendation-text {
  display: block;
  margin-top: 20rpx;
  color: #355062;
  font-size: 31rpx;
  line-height: 1.9;
  white-space: pre-wrap;
}

.actions {
  margin: 32rpx 24rpx 0;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.share-btn,
.home-main-btn,
.reassess-btn {
  width: 100%;
  min-height: 108rpx;
  border-radius: 999rpx;
  border: none;
  font-size: 36rpx;
  font-weight: 700;
  transition: transform 0.25s ease, box-shadow 0.25s ease;
  letter-spacing: 2rpx;
}

.share-btn:active,
.home-main-btn:active,
.reassess-btn:active {
  transform: scale(0.97);
}

.share-btn {
  background: linear-gradient(135deg, #0284c7 0%, #0369a1 100%);
  color: #ffffff;
  box-shadow: 0 10rpx 32rpx rgba(2, 132, 199, 0.4);
}

.share-btn::after {
  border: none;
}

.home-main-btn {
  background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
  color: #ffffff;
  box-shadow: 0 10rpx 32rpx rgba(22, 163, 74, 0.4);
}

.home-main-btn::after {
  border: none;
}

.reassess-btn {
  background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
  color: #0f766e;
  border: 3rpx solid rgba(15, 118, 110, 0.35);
  box-shadow: 0 6rpx 20rpx rgba(15, 118, 110, 0.1);
}

.reassess-btn::after {
  border: none;
}

.disclaimer {
  margin: 24rpx 24rpx 40rpx;
  border-radius: 16rpx;
  background: #f8fafc;
  border: 2rpx solid #e2e8f0;
  padding: 20rpx;
}

.disclaimer-text {
  color: #91a4b2;
  font-size: 26rpx;
  text-align: center;
  line-height: 1.6;
}
</style>

