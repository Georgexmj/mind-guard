<template>
  <view class="home-page">
    <view class="hero-card">
      <view class="hero-top">
        <view>
          <text class="hero-greeting">您好，{{ authStore.userName }}</text>
          <text class="hero-date">{{ todayStr }}</text>
        </view>
        <view class="hero-avatar">
          <text class="hero-avatar-text">{{ avatarLetter }}</text>
        </view>
      </view>

      <view class="hero-metrics">
        <view class="hero-metric">
          <text class="metric-value">{{ totalSessions }}</text>
          <text class="metric-label">累计评估</text>
        </view>
        <view class="hero-divider" />
        <view class="hero-metric">
          <text class="metric-value" :style="{ color: latestRiskColor }">{{ latestRiskLabel }}</text>
          <text class="metric-label">最近结论</text>
        </view>
        <view class="hero-divider" />
        <view class="hero-metric">
          <text class="metric-value">{{ daysSinceLastAssess }}</text>
          <text class="metric-label">距上次(天)</text>
        </view>
      </view>
    </view>

    <view class="mg-card action-card" @tap="goToAssessment">
      <view class="action-left">
        <view class="action-icon">🧠</view>
        <view>
          <text class="action-title">开始认知评估</text>
          <text class="action-desc">约 15 分钟，系统将综合分析认知风险</text>
        </view>
      </view>
      <text class="action-arrow">›</text>
    </view>

    <view class="mg-card section-card" @tap="goToInterventionTop5">
      <view class="section-head">
        <text class="section-title">干预推荐 Top-5</text>
        <text class="section-more">查看建议 ›</text>
      </view>
      <text class="section-desc">根据最新评估结论，生成可执行的每日认知训练方案。</text>
    </view>

    <view class="mg-card section-card">
      <view class="section-head">
        <text class="section-title">复评趋势</text>
        <text class="section-more">下次建议：{{ trendNextDate }}</text>
      </view>
      <view class="trend-meta">
        <text class="trend-chip">风险变化：{{ trendChangeLabel }}</text>
        <text class="trend-chip">当前风险：{{ trendRiskLabel }}</text>
      </view>
      <view v-if="trendPoints.length > 0" class="trend-list">
        <view v-for="point in trendPoints" :key="point.session_id" class="trend-item">
          <text class="trend-date">{{ formatTrendDate(point.assessed_at) }}</text>
          <text class="trend-score">MMSE {{ point.mmse_score ?? '--' }}</text>
          <text class="trend-score">MoCA {{ point.moca_score_corrected ?? '--' }}</text>
        </view>
      </view>
      <text v-else class="empty-tip">暂无趋势数据，完成至少 2 次评估后可查看变化。</text>
    </view>

    <view class="section">
      <view class="section-head-inline">
        <text class="section-title">最近评估记录</text>
        <text class="section-more" @tap="goToProfile">查看更多 ›</text>
      </view>
      <view v-if="loadingSessions" class="mg-card loading-box">
        <text class="loading-text">正在加载记录...</text>
      </view>
      <view v-else-if="recentSessions.length > 0" class="mg-card session-list">
        <view v-for="session in recentSessions" :key="session.id" class="session-item" @tap="() => viewResult(session.id)">
          <view class="session-left">
            <view class="session-dot" :style="{ backgroundColor: getRiskColor(getSessionRisk(session)) }" />
            <view>
              <text class="session-date">{{ formatDate(session.created_at) }}</text>
              <text class="session-score">{{ getSessionScoreText(session) }}</text>
            </view>
          </view>
          <view class="session-right">
            <text class="session-risk" :style="{ color: getRiskColor(getSessionRisk(session)) }">
              {{ getRiskLabel(getSessionRisk(session)) }}
            </text>
            <text class="session-arrow">›</text>
          </view>
        </view>
      </view>
      <view v-else class="mg-card empty-box">
        <text class="empty-title">暂无评估记录</text>
        <text class="empty-tip">点击上方入口开始首次评估。</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">每日认知健康建议</text>
      <swiper class="tip-swiper" :autoplay="true" :interval="4200" :circular="true" indicator-dots indicator-active-color="#ffffff">
        <swiper-item v-for="(tip, idx) in healthTips" :key="idx">
          <view class="tip-card" :style="{ background: tip.color }">
            <text class="tip-title">{{ tip.title }}</text>
            <text class="tip-content">{{ tip.content }}</text>
          </view>
        </swiper-item>
      </swiper>
    </view>

    <view style="height: 40rpx;" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '../../store/auth'
import { api } from '../../utils/request'

const authStore = useAuthStore()

const recentSessions = ref([])
const loadingSessions = ref(false)
const allSessionCount = ref(0)
const trendSummary = ref(null)

const avatarLetter = computed(() => {
  const name = authStore.userName
  return name ? name.charAt(0) : '您'
})

const todayStr = computed(() => {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth() + 1
  const d = now.getDate()
  const weeks = ['日', '一', '二', '三', '四', '五', '六']
  return `${y}年${m}月${d}日 星期${weeks[now.getDay()]}`
})

const totalSessions = computed(() => allSessionCount.value || 0)

const latestRiskLabel = computed(() => {
  if (recentSessions.value.length === 0) return '暂无'
  return getRiskLabel(getSessionRisk(recentSessions.value[0]))
})

const latestRiskColor = computed(() => {
  if (recentSessions.value.length === 0) return '#7890a0'
  return getRiskColor(getSessionRisk(recentSessions.value[0]))
})

const daysSinceLastAssess = computed(() => {
  if (recentSessions.value.length === 0) return '--'
  const latest = recentSessions.value[0]?.created_at
  if (!latest) return '--'
  const diff = Date.now() - new Date(latest).getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24))
})

const trendPoints = computed(() => {
  const points = Array.isArray(trendSummary.value?.points) ? trendSummary.value.points : []
  return [...points]
    .sort((a, b) => {
      const tsA = new Date(a?.assessed_at || a?.created_at || 0).getTime()
      const tsB = new Date(b?.assessed_at || b?.created_at || 0).getTime()
      return tsB - tsA
    })
    .slice(0, 3)
})

const trendRiskLabel = computed(() => {
  const level = trendSummary.value?.latest_risk_level
  return level ? getRiskLabel(level) : '--'
})

const trendChangeLabel = computed(() => {
  const labels = {
    improved: '较上次改善',
    stable: '与上次持平',
    worsened: '较上次加重',
    unknown: '暂无对比',
  }
  return labels[trendSummary.value?.risk_change] || '暂无对比'
})

const trendNextDate = computed(() => trendSummary.value?.next_reassessment_date || '--')

const healthTips = [
  {
    title: '保持规律运动',
    content: '每天步行 30 分钟以上，有助于改善脑部血液循环与注意力。',
    color: 'linear-gradient(135deg, #0f766e, #0284c7)',
  },
  {
    title: '坚持动脑训练',
    content: '通过阅读、下棋、计算等活动，持续刺激记忆与执行功能。',
    color: 'linear-gradient(135deg, #1d4ed8, #2563eb)',
  },
  {
    title: '保证高质量睡眠',
    content: '建议每晚保持 7~8 小时睡眠，帮助巩固当天记忆。',
    color: 'linear-gradient(135deg, #4f46e5, #7c3aed)',
  },
  {
    title: '多与家人交流',
    content: '积极社交可缓解孤独感，也有助于维持认知活跃与情绪稳定。',
    color: 'linear-gradient(135deg, #c2410c, #ea580c)',
  },
]

function getRiskColor(level) {
  const colors = {
    normal: '#16a34a',
    low: '#16a34a',
    mild_risk: '#d97706',
    mild: '#d97706',
    moderate: '#d97706',
    mci: '#d97706',
    in_progress: '#0284c7',
    pending: '#0284c7',
    completed: '#0284c7',
    high: '#dc2626',
    high_risk: '#dc2626',
    severe: '#dc2626',
    ad: '#dc2626',
    failed: '#94a3b8',
  }
  return colors[level] || '#94a3b8'
}

function getRiskLabel(level) {
  const labels = {
    normal: '正常',
    low: '正常',
    mild_risk: '轻度风险',
    mild: '轻度风险',
    moderate: '中度风险',
    mci: '轻度风险',
    in_progress: '评估中',
    pending: '待处理',
    completed: '分析中',
    high: '高风险',
    high_risk: '高风险',
    severe: '高风险',
    ad: '高风险',
    failed: '失败',
  }
  return labels[level] || '未知'
}

function getSessionRisk(session) {
  if (!session) return 'pending'
  if (session.risk_level) return session.risk_level
  if (session.status) return session.status
  return 'pending'
}

function getSessionScoreText(session) {
  if (session?.mmse_score !== null && session?.mmse_score !== undefined) {
    const score = Math.round(Number(session.mmse_score) * 10) / 10
    return `MMSE 得分：${score}`
  }
  if (session?.status === 'failed') return '结果生成失败'
  if (session?.status === 'completed') return '结果整理中'
  if (session?.status === 'in_progress') return '评估进行中'
  return '等待处理中'
}

function isEffectiveSession(session) {
  const status = String(session?.status || '').toLowerCase()
  if (status === 'completed' || status === 'failed') return true
  if (session?.risk_level) return true
  return session?.mmse_score !== null && session?.mmse_score !== undefined
}

async function enrichSessionWithResult(session) {
  const merged = { ...session }

  if (session?.status === 'completed' || session?.status === 'failed' || session?.task_id) {
    try {
      const result = await api.getResult(session.id)
      if (result) {
        merged.mmse_score = result.mmse_score
        merged.risk_level = result.risk_level
      } else if (session?.status === 'completed') {
        merged.risk_level = 'completed'
      }
    } catch (err) {
      console.warn('fetch session result failed', session.id, err)
      if (session?.status === 'completed') {
        merged.risk_level = 'completed'
      }
    }
  }

  return merged
}

function formatDate(dateStr) {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function formatTrendDate(dateStr) {
  if (!dateStr) return '--'
  const d = new Date(dateStr)
  return `${String(d.getMonth() + 1).padStart(2, '0')}/${String(d.getDate()).padStart(2, '0')}`
}

function goToAssessment() {
  uni.navigateTo({ url: '/pages/assessment/start/index' })
}

function goToInterventionTop5() {
  uni.navigateTo({ url: '/pages/intervention/top5/index' })
}

function goToProfile() {
  uni.switchTab({ url: '/pages/profile/index' })
}

function viewResult(sessionId) {
  uni.navigateTo({ url: `/pages/result/index?sessionId=${sessionId}&fromHistory=true` })
}

async function loadSessions() {
  loadingSessions.value = true
  try {
    const data = await api.getSessions()
    const sessionsRaw = Array.isArray(data) ? data : (data.sessions || data.items || [])
    const sessions = [...sessionsRaw]
      .filter((item) => isEffectiveSession(item))
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())

    allSessionCount.value = sessions.length
    recentSessions.value = await Promise.all(sessions.slice(0, 3).map((item) => enrichSessionWithResult(item)))
  } catch (err) {
    console.error('load sessions error', err)
    allSessionCount.value = 0
    recentSessions.value = []
  } finally {
    loadingSessions.value = false
  }
}

async function loadTrend() {
  try {
    const data = await api.getAssessmentTrend()
    trendSummary.value = data || null
  } catch (err) {
    console.warn('load trend error', err)
    trendSummary.value = null
  }
}

onShow(() => {
  if (!authStore.enforceElderRole()) return
  loadSessions()
  loadTrend()
})

onMounted(() => {
  if (!authStore.enforceElderRole()) return
  loadSessions()
  loadTrend()
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  padding: 24rpx;
}

.hero-card {
  border-radius: 30rpx;
  padding: 26rpx 24rpx;
  background:
    radial-gradient(circle at 100% -10%, rgba(124, 58, 237, 0.26), transparent 44%),
    linear-gradient(140deg, #0f766e, #0284c7);
  box-shadow: var(--mg-shadow-strong);
  margin-bottom: 20rpx;
}

.hero-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.hero-greeting {
  display: block;
  color: #ffffff;
  font-size: 44rpx;
  font-weight: 800;
}

.hero-date {
  display: block;
  margin-top: 6rpx;
  color: rgba(236, 252, 255, 0.9);
  font-size: 28rpx;
}

.hero-avatar {
  width: 88rpx;
  height: 88rpx;
  border-radius: 26rpx;
  background: rgba(255, 255, 255, 0.2);
  border: 2rpx solid rgba(255, 255, 255, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
}

.hero-avatar-text {
  color: #ffffff;
  font-size: 40rpx;
  font-weight: 700;
}

.hero-metrics {
  margin-top: 18rpx;
  border-radius: 22rpx;
  padding: 18rpx 10rpx;
  background: rgba(255, 255, 255, 0.14);
  display: flex;
  align-items: center;
}

.hero-metric {
  flex: 1;
  text-align: center;
}

.metric-value {
  display: block;
  color: #ffffff;
  font-size: 40rpx;
  font-weight: 800;
}

.metric-label {
  display: block;
  color: rgba(236, 252, 255, 0.88);
  font-size: 28rpx;
  margin-top: 4rpx;
}

.hero-divider {
  width: 2rpx;
  height: 54rpx;
  background: rgba(255, 255, 255, 0.35);
}

.action-card {
  margin-bottom: 16rpx;
  padding: 24rpx 22rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.action-left {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.action-icon {
  width: 74rpx;
  height: 74rpx;
  border-radius: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: linear-gradient(145deg, #16a34a, #15803d);
  box-shadow: 0 10rpx 16rpx rgba(21, 128, 61, 0.24);
}

.action-title {
  display: block;
  color: #143445;
  font-size: 34rpx;
  font-weight: 800;
}

.action-desc {
  display: block;
  margin-top: 4rpx;
  color: #5d7485;
  font-size: 29rpx;
}

.action-arrow {
  color: #6f8595;
  font-size: 48rpx;
}

.section-card {
  margin-bottom: 16rpx;
  padding: 20rpx;
}

.section-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.section-head-inline {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14rpx;
}

.section-title {
  font-size: 34rpx;
  font-weight: 800;
  color: #143445;
}

.section-more {
  font-size: 29rpx;
  color: var(--mg-brand);
}

.section-desc {
  display: block;
  margin-top: 10rpx;
  color: #5e7485;
  font-size: 28rpx;
}

.trend-meta {
  margin-top: 12rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 10rpx;
}

.trend-chip {
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  border: 2rpx solid rgba(15, 118, 110, 0.22);
  background: rgba(15, 118, 110, 0.08);
  color: #0f766e;
  font-size: 28rpx;
}

.trend-list {
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.trend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12rpx 14rpx;
  border-radius: 14rpx;
  background: #f0f8fb;
}

.trend-date {
  min-width: 100rpx;
  color: #0f766e;
  font-size: 29rpx;
  font-weight: 700;
}

.trend-score {
  color: #516879;
  font-size: 29rpx;
}

.section {
  margin-bottom: 16rpx;
}

.loading-box {
  padding: 28rpx;
  text-align: center;
}

.loading-text {
  color: #6e8595;
  font-size: 28rpx;
}

.session-list {
  overflow: hidden;
}

.session-item {
  padding: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2rpx solid rgba(17, 34, 49, 0.06);
}

.session-item:last-child {
  border-bottom: none;
}

.session-left {
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.session-dot {
  width: 18rpx;
  height: 18rpx;
  border-radius: 50%;
}

.session-date {
  display: block;
  color: #19384a;
  font-size: 30rpx;
  font-weight: 700;
}

.session-score {
  display: block;
  margin-top: 4rpx;
  color: #6d8495;
  font-size: 29rpx;
}

.session-right {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.session-risk {
  font-size: 28rpx;
  font-weight: 700;
}

.session-arrow {
  color: #8da2b0;
  font-size: 36rpx;
}

.empty-box {
  padding: 34rpx 24rpx;
  text-align: center;
}

.empty-title {
  display: block;
  color: #2c4759;
  font-size: 32rpx;
  font-weight: 700;
  margin-bottom: 6rpx;
}

.empty-tip {
  color: #738b9b;
  font-size: 27rpx;
}

.tip-swiper {
  margin-top: 12rpx;
  height: 230rpx;
  border-radius: 24rpx;
  overflow: hidden;
}

.tip-card {
  height: 230rpx;
  padding: 28rpx 26rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.tip-title {
  color: #ffffff;
  font-size: 35rpx;
  font-weight: 800;
  margin-bottom: 10rpx;
}

.tip-content {
  color: rgba(255, 255, 255, 0.92);
  font-size: 28rpx;
}
</style>

