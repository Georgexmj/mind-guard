<template>
  <view class="result-page">
    <!-- AI Processing State -->
    <view v-if="isPolling" class="polling-state">
      <view class="spinner-wrap">
        <view class="spinner" />
        <view class="spinner-inner" />
      </view>
      <text class="polling-title">AI正在分析中...</text>
      <text class="polling-subtitle">系统正在对您的答题情况进行智能评估，请稍候</text>
      <view class="polling-progress">
        <view class="polling-bar">
          <view class="polling-fill" :style="{ width: pollingProgress + '%' }" />
        </view>
        <text class="polling-time">已等待 {{ pollingSeconds }} 秒</text>
      </view>
      <text class="polling-hint">评估分析通常需要1-2分钟，请耐心等待</text>
    </view>

    <!-- Error State -->
    <view v-else-if="errorMsg" class="error-state">
      <text class="error-icon">⚠️</text>
      <text class="error-title">获取结果失败</text>
      <text class="error-msg">{{ errorMsg }}</text>
      <button class="btn-retry" @tap="retryFetch">重新获取</button>
      <button class="btn-home" @tap="goHome">返回首页</button>
    </view>

    <!-- Result State -->
    <view v-else-if="result" class="result-content">
      <!-- Result Header -->
      <view class="result-header" :style="{ background: headerGradient }">
        <!-- Risk Level Circle -->
        <view class="risk-circle" :style="{ borderColor: riskBorderColor }">
          <text class="risk-icon-big">{{ riskIcon }}</text>
          <text class="risk-level-text">{{ riskLabel }}</text>
        </view>
        <text class="result-date">评估日期：{{ assessDate }}</text>
      </view>

      <!-- MMSE Score Card -->
      <view class="card">
        <view class="score-row">
          <view class="score-left">
            <text class="score-label">MMSE 总分</text>
            <text class="score-hint">满分30分</text>
          </view>
          <view class="score-right">
            <text class="score-value" :style="{ color: riskColor }">{{ result.mmse_score ?? result.total_score ?? '--' }}</text>
            <text class="score-max">/ 30</text>
          </view>
        </view>
        <!-- MMSE Progress Bar -->
        <view class="mmse-bar-wrap">
          <view class="mmse-bar">
            <view
              class="mmse-fill"
              :style="{ width: mmsePercent + '%', backgroundColor: riskColor }"
            />
          </view>
          <text class="mmse-pct">{{ mmsePercent }}%</text>
        </view>
        <text class="mmse-interpretation">{{ mmseInterpretation }}</text>
      </view>

      <!-- Domain Scores Bar Chart -->
      <view class="card">
        <text class="card-title">各项认知能力评分</text>
        <view class="domain-list">
          <view
            v-for="domain in domainScores"
            :key="domain.key"
            class="domain-item"
          >
            <view class="domain-header">
              <text class="domain-icon-text">{{ domain.icon }}</text>
              <text class="domain-name">{{ domain.name }}</text>
              <text class="domain-score" :style="{ color: getDomainColor(domain.score, domain.max) }">
                {{ domain.score }}<text class="domain-max">/{{ domain.max }}</text>
              </text>
            </view>
            <view class="domain-bar-wrap">
              <view class="domain-bar">
                <view
                  class="domain-bar-fill"
                  :style="{
                    width: (domain.score / domain.max * 100) + '%',
                    backgroundColor: getDomainColor(domain.score, domain.max)
                  }"
                />
              </view>
            </view>
          </view>
        </view>
      </view>

      <!-- Risk Probabilities -->
      <view class="card">
        <text class="card-title">风险概率分析</text>
        <view class="prob-list">
          <view class="prob-item">
            <view class="prob-dot" style="background: #52C41A;" />
            <text class="prob-label">认知正常</text>
            <view class="prob-bar-wrap">
              <view class="prob-bar">
                <view class="prob-fill" :style="{ width: probNormal + '%', background: '#52C41A' }" />
              </view>
            </view>
            <text class="prob-value">{{ probNormal }}%</text>
          </view>
          <view class="prob-item">
            <view class="prob-dot" style="background: #FA8C16;" />
            <text class="prob-label">轻度风险</text>
            <view class="prob-bar-wrap">
              <view class="prob-bar">
                <view class="prob-fill" :style="{ width: probMCI + '%', background: '#FA8C16' }" />
              </view>
            </view>
            <text class="prob-value">{{ probMCI }}%</text>
          </view>
          <view class="prob-item">
            <view class="prob-dot" style="background: #F5222D;" />
            <text class="prob-label">认知障碍</text>
            <view class="prob-bar-wrap">
              <view class="prob-bar">
                <view class="prob-fill" :style="{ width: probAD + '%', background: '#F5222D' }" />
              </view>
            </view>
            <text class="prob-value">{{ probAD }}%</text>
          </view>
        </view>
        <text class="prob-disclaimer">* 以上概率由AI模型计算，仅供参考，不作为临床诊断依据</text>
      </view>

      <!-- Recommendations Card -->
      <view class="card recommendation-card">
        <text class="card-title">📋 医生建议</text>
        <text class="recommendation-text">{{ recommendationText }}</text>
      </view>

      <!-- Action Buttons -->
      <view class="action-buttons">
        <button class="btn-share" @tap="handleShare">
          <text>📤 分享给家人</text>
        </button>
        <button class="btn-home" @tap="goHome">
          <text>🏠 返回首页</text>
        </button>
        <button class="btn-reassess" @tap="goToAssessment">
          <text>🔄 重新评估</text>
        </button>
      </view>

      <!-- Disclaimer -->
      <view class="disclaimer">
        <text class="disclaimer-text">
          本评估结果仅用于初步筛查参考，不能替代专业医疗诊断。如有疑虑，请及时就医。
        </text>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onLoad, onShareAppMessage } from '@dcloudio/uni-app'
import { useAssessmentStore } from '../../store/assessment'
import { api } from '../../utils/request'

const assessmentStore = useAssessmentStore()

// Page params
const sessionId = ref('')
const taskId = ref('')
const fromHistory = ref(false)

// State
const isPolling = ref(false)
const errorMsg = ref('')
const result = ref(null)
const pollingSeconds = ref(0)
const pollingProgress = ref(0)

const maxPollingSeconds = 120
const pollInterval = 3000
let pollTimer = null
let countTimer = null

onLoad((options) => {
  sessionId.value = options.sessionId || assessmentStore.currentSessionId || ''
  taskId.value = options.taskId || assessmentStore.taskId || ''
  fromHistory.value = options.fromHistory === 'true'

  if (sessionId.value) {
    if (fromHistory.value) {
      // Viewing historical result - fetch directly
      fetchResult()
    } else {
      // New assessment - poll for completion
      startPolling()
    }
  } else {
    errorMsg.value = '评估会话信息丢失，请重新进行评估'
  }
})

onUnmounted(() => {
  stopPolling()
})

// Computed: risk level display
const riskLevel = computed(() => {
  if (!result.value) return 'normal'
  return result.value.risk_level || result.value.classification || 'normal'
})

const riskConfig = computed(() => {
  const normalCfg = { label: '认知状态正常', icon: '😊', color: '#52C41A', borderColor: '#B7EB8F', gradient: 'linear-gradient(135deg, #52C41A, #389E0D)' }
  const mildCfg  = { label: '轻度认知风险', icon: '🤔', color: '#FA8C16', borderColor: '#FFD591', gradient: 'linear-gradient(135deg, #FA8C16, #D46B08)' }
  const highCfg  = { label: '认知风险较高', icon: '🚨', color: '#F5222D', borderColor: '#FFADD2', gradient: 'linear-gradient(135deg, #F5222D, #A8071A)' }
  const configs = {
    normal: normalCfg, low: normalCfg,
    mild_risk: mildCfg, mild: mildCfg, moderate: mildCfg, mci: mildCfg,
    high_risk: highCfg, high: highCfg, severe: highCfg, ad: highCfg,
  }
  return configs[riskLevel.value] || normalCfg
})

const riskLabel = computed(() => riskConfig.value.label)
const riskIcon = computed(() => riskConfig.value.icon)
const riskColor = computed(() => riskConfig.value.color)
const riskBorderColor = computed(() => riskConfig.value.borderColor)
const headerGradient = computed(() => riskConfig.value.gradient)

const mmseScore = computed(() => result.value?.mmse_score ?? result.value?.total_score ?? 0)
const mmsePercent = computed(() => Math.round((mmseScore.value / 30) * 100))

const mmseInterpretation = computed(() => {
  const score = mmseScore.value
  if (score >= 27) return '正常范围 (27-30分)'
  if (score >= 24) return '轻度认知下降 (24-26分)'
  if (score >= 19) return '中度认知下降 (19-23分)'
  return '重度认知下降 (≤18分)'
})

const assessDate = computed(() => {
  const d = result.value?.created_at ? new Date(result.value.created_at) : new Date()
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
})

// Domain scores
const domainScores = computed(() => {
  const domains = result.value?.domain_scores || result.value?.domains || {}
  return [
    { key: 'memory', name: '记忆力', icon: '💭', score: domains.memory ?? domains.memory_score ?? 0, max: 6 },
    { key: 'orientation', name: '定向力', icon: '🧭', score: domains.orientation ?? domains.orientation_score ?? 0, max: 10 },
    { key: 'attention', name: '注意力', icon: '🎯', score: domains.attention ?? domains.attention_score ?? 0, max: 5 },
    { key: 'language', name: '语言能力', icon: '💬', score: domains.language ?? domains.language_score ?? 0, max: 5 },
    { key: 'visuospatial', name: '视空间', icon: '🗺️', score: domains.visuospatial ?? domains.visuospatial_score ?? 0, max: 1 },
    { key: 'recall', name: '延迟回忆', icon: '🔄', score: domains.recall ?? domains.recall_score ?? 0, max: 3 }
  ]
})

function getDomainColor(score, max) {
  const pct = score / max
  if (pct >= 0.8) return '#52C41A'
  if (pct >= 0.6) return '#FA8C16'
  return '#F5222D'
}

// Probability values — backend sends nc_probability / mci_probability / ad_probability at top level
const probNormal = computed(() => {
  const r = result.value
  if (!r) return 0
  return Math.round((r.nc_probability ?? r.probabilities?.normal ?? r.probabilities?.healthy ?? 0) * 100)
})

const probMCI = computed(() => {
  const r = result.value
  if (!r) return 0
  return Math.round((r.mci_probability ?? r.probabilities?.mci ?? r.probabilities?.mild ?? 0) * 100)
})

const probAD = computed(() => {
  const r = result.value
  if (!r) return 0
  return Math.round((r.ad_probability ?? r.probabilities?.ad ?? r.probabilities?.high ?? 0) * 100)
})

const recommendationText = computed(() => {
  if (!result.value) return ''
  if (result.value.recommendation) return result.value.recommendation
  if (result.value.recommendations) {
    return Array.isArray(result.value.recommendations)
      ? result.value.recommendations.join('\n')
      : result.value.recommendations
  }
  // Default recommendations based on risk level
  const level = riskLevel.value
  if (level === 'normal' || level === 'low') {
    return '您的认知功能处于正常范围内。建议保持良好的生活习惯，坚持适量运动，积极参与社交活动，定期进行认知健康评估。'
  }
  if (level === 'mild_risk' || level === 'mild' || level === 'moderate' || level === 'mci') {
    return '评估显示您存在轻度认知功能下降迹象。建议尽快前往医院神经科或记忆门诊进行专业检查，同时加强脑力锻炼，保持规律作息。'
  }
  return '评估显示您的认知功能存在明显下降。请尽快就医，寻求专业医疗帮助。家属也请给予更多关注和支持。'
})

// Polling logic
function startPolling() {
  isPolling.value = true
  pollingSeconds.value = 0
  pollingProgress.value = 0

  // Count timer
  countTimer = setInterval(() => {
    pollingSeconds.value++
    pollingProgress.value = Math.min((pollingSeconds.value / maxPollingSeconds) * 90, 90)

    if (pollingSeconds.value >= maxPollingSeconds) {
      stopPolling()
      // Try to get result anyway
      fetchResult()
    }
  }, 1000)

  // Poll timer
  pollTimer = setInterval(async () => {
    await checkTaskStatus()
  }, pollInterval)

  // Also check immediately after 2 seconds
  setTimeout(checkTaskStatus, 2000)
}

async function checkTaskStatus() {
  try {
    let statusData = null

    if (taskId.value) {
      statusData = await api.getTaskStatus(taskId.value)
    }

    const status = statusData?.status || statusData?.state
    if (status === 'completed' || status === 'SUCCESS' || status === 'success') {
      stopPolling()
      pollingProgress.value = 100
      await fetchResult()
    } else if (status === 'failed' || status === 'FAILURE' || status === 'error') {
      stopPolling()
      errorMsg.value = statusData?.error || '分析任务失败，请重试'
    }
    // Otherwise keep polling (pending/processing state)
  } catch (err) {
    console.error('Check task status error:', err)
    // Try fetching result directly
    try {
      await fetchResult()
    } catch (e) {
      // Continue polling
    }
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
    } else if (isPolling.value) {
      // Result not ready yet, keep polling
    } else {
      errorMsg.value = '结果数据格式异常，请重试'
    }
  } catch (err) {
    console.error('Fetch result error:', err)
    if (!isPolling.value) {
      errorMsg.value = err.message || '获取评估结果失败，请重试'
    }
  }
}

function stopPolling() {
  isPolling.value = false
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
  if (countTimer) { clearInterval(countTimer); countTimer = null }
}

function retryFetch() {
  errorMsg.value = ''
  if (taskId.value) {
    startPolling()
  } else {
    fetchResult()
  }
}

function handleShare() {
  wx.showShareMenu({
    withShareTicket: true,
    menus: ['shareAppMessage', 'shareTimeline']
  })
  wx.showToast({ title: '请点击右上角分享', icon: 'none', duration: 2000 })
}

function goHome() {
  assessmentStore.reset()
  uni.switchTab({ url: '/pages/index/index' })
}

function goToAssessment() {
  assessmentStore.reset()
  uni.navigateTo({ url: '/pages/assessment/start/index' })
}

// Share configuration
onShareAppMessage(() => {
  const score = result.value?.mmse_score ?? '--'
  return {
    title: `我完成了CogniCare认知评估，得分${score}分，快来关注老年认知健康！`,
    path: '/pages/index/index'
  }
})
</script>

<style scoped>
.result-page {
  min-height: 100vh;
  background: #F0F4F8;
  padding-bottom: 60rpx;
}

/* Polling State */
.polling-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 60rpx;
  text-align: center;
}

.spinner-wrap {
  position: relative;
  width: 160rpx;
  height: 160rpx;
  margin-bottom: 50rpx;
}

.spinner {
  position: absolute;
  width: 160rpx;
  height: 160rpx;
  border: 8rpx solid #E0E0E0;
  border-top-color: #4A90D9;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

.spinner-inner {
  position: absolute;
  top: 20rpx;
  left: 20rpx;
  width: 120rpx;
  height: 120rpx;
  border: 6rpx solid #E0E0E0;
  border-top-color: #52C41A;
  border-radius: 50%;
  animation: spin 0.7s linear infinite reverse;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.polling-title {
  font-size: 48rpx;
  font-weight: bold;
  color: #333333;
  margin-bottom: 20rpx;
}

.polling-subtitle {
  font-size: 32rpx;
  color: #666666;
  line-height: 1.6;
  margin-bottom: 40rpx;
}

.polling-progress {
  width: 100%;
  margin-bottom: 20rpx;
}

.polling-bar {
  height: 12rpx;
  background: #E0E0E0;
  border-radius: 6rpx;
  overflow: hidden;
  margin-bottom: 12rpx;
}

.polling-fill {
  height: 100%;
  background: linear-gradient(90deg, #4A90D9, #52C41A);
  border-radius: 6rpx;
  transition: width 1s linear;
}

.polling-time {
  font-size: 28rpx;
  color: #999999;
}

.polling-hint {
  font-size: 26rpx;
  color: #AAAAAA;
}

/* Error State */
.error-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 80rpx 40rpx;
  text-align: center;
}

.error-icon {
  font-size: 100rpx;
  margin-bottom: 24rpx;
}

.error-title {
  font-size: 44rpx;
  font-weight: bold;
  color: #333333;
  margin-bottom: 16rpx;
}

.error-msg {
  font-size: 32rpx;
  color: #666666;
  margin-bottom: 50rpx;
  line-height: 1.6;
}

.btn-retry {
  width: 80%;
  height: 96rpx;
  background: linear-gradient(135deg, #4A90D9, #2c6fad);
  color: #ffffff;
  font-size: 38rpx;
  font-weight: bold;
  border-radius: 48rpx;
  border: none;
  margin-bottom: 20rpx;
}

/* Result Content */
.result-content {
  display: flex;
  flex-direction: column;
}

/* Result Header */
.result-header {
  padding: 50rpx 30rpx 70rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.risk-circle {
  width: 200rpx;
  height: 200rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.2);
  border: 8rpx solid;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
}

.risk-icon-big {
  font-size: 72rpx;
  margin-bottom: 8rpx;
}

.risk-level-text {
  font-size: 26rpx;
  color: #ffffff;
  font-weight: bold;
  text-align: center;
}

.result-date {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.85);
}

/* Card */
.card {
  background: #ffffff;
  border-radius: 20rpx;
  margin: -30rpx 30rpx 20rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
  display: block;
  margin-bottom: 24rpx;
}

/* MMSE Score */
.score-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20rpx;
}

.score-left {
  display: flex;
  flex-direction: column;
}

.score-label {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
}

.score-hint {
  font-size: 26rpx;
  color: #999999;
}

.score-right {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
}

.score-value {
  font-size: 80rpx;
  font-weight: bold;
}

.score-max {
  font-size: 36rpx;
  color: #CCCCCC;
}

.mmse-bar-wrap {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.mmse-bar {
  flex: 1;
  height: 20rpx;
  background: #F0F0F0;
  border-radius: 10rpx;
  overflow: hidden;
}

.mmse-fill {
  height: 100%;
  border-radius: 10rpx;
  transition: width 0.5s ease;
}

.mmse-pct {
  font-size: 28rpx;
  color: #888888;
  min-width: 60rpx;
  text-align: right;
}

.mmse-interpretation {
  font-size: 28rpx;
  color: #888888;
  display: block;
}

/* Domain Scores */
.domain-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.domain-item {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.domain-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.domain-icon-text {
  font-size: 30rpx;
}

.domain-name {
  flex: 1;
  font-size: 30rpx;
  color: #333333;
  font-weight: 500;
}

.domain-score {
  font-size: 32rpx;
  font-weight: bold;
}

.domain-max {
  font-size: 24rpx;
  color: #CCCCCC;
  font-weight: normal;
}

.domain-bar-wrap {
  padding-left: 42rpx;
}

.domain-bar {
  height: 14rpx;
  background: #F0F0F0;
  border-radius: 7rpx;
  overflow: hidden;
}

.domain-bar-fill {
  height: 100%;
  border-radius: 7rpx;
  transition: width 0.5s ease;
}

/* Probabilities */
.prob-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
  margin-bottom: 16rpx;
}

.prob-item {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.prob-dot {
  width: 20rpx;
  height: 20rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.prob-label {
  font-size: 28rpx;
  color: #555555;
  min-width: 100rpx;
}

.prob-bar-wrap {
  flex: 1;
}

.prob-bar {
  height: 16rpx;
  background: #F0F0F0;
  border-radius: 8rpx;
  overflow: hidden;
}

.prob-fill {
  height: 100%;
  border-radius: 8rpx;
  transition: width 0.5s ease;
}

.prob-value {
  font-size: 28rpx;
  font-weight: bold;
  color: #333333;
  min-width: 60rpx;
  text-align: right;
}

.prob-disclaimer {
  font-size: 24rpx;
  color: #AAAAAA;
  display: block;
  line-height: 1.5;
}

/* Recommendation */
.recommendation-card {
  border-left: 6rpx solid #4A90D9;
}

.recommendation-text {
  font-size: 32rpx;
  color: #444444;
  line-height: 1.8;
  display: block;
  white-space: pre-wrap;
}

/* Action Buttons */
.action-buttons {
  margin: 0 30rpx;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.btn-share {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, #1890FF, #096DD9);
  color: #ffffff;
  font-size: 38rpx;
  font-weight: bold;
  border-radius: 48rpx;
  border: none;
  box-shadow: 0 6rpx 20rpx rgba(24, 144, 255, 0.35);
  letter-spacing: 2rpx;
}

.btn-home {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, #52C41A, #389E0D);
  color: #ffffff;
  font-size: 38rpx;
  font-weight: bold;
  border-radius: 48rpx;
  border: none;
  box-shadow: 0 6rpx 20rpx rgba(82, 196, 26, 0.35);
  letter-spacing: 2rpx;
}

.btn-reassess {
  width: 100%;
  height: 88rpx;
  background: #ffffff;
  color: #4A90D9;
  font-size: 34rpx;
  border: 2rpx solid #4A90D9;
  border-radius: 44rpx;
}

/* Disclaimer */
.disclaimer {
  margin: 20rpx 30rpx 0;
  padding: 20rpx;
  background: #F9F9F9;
  border-radius: 12rpx;
  border: 1rpx solid #EEEEEE;
}

.disclaimer-text {
  font-size: 24rpx;
  color: #AAAAAA;
  line-height: 1.6;
  text-align: center;
  display: block;
}
</style>
