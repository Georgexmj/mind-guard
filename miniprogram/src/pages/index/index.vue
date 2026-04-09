<template>
  <view class="home-page">
    <!-- Welcome Header -->
    <view class="welcome-header">
      <view class="welcome-text-group">
        <text class="greeting">您好，{{ authStore.userName }}！</text>
        <text class="date-text">{{ todayStr }}</text>
      </view>
      <view class="avatar-circle">
        <text class="avatar-text">{{ avatarLetter }}</text>
      </view>
    </view>

    <!-- Start Assessment Card -->
    <view class="assess-card" @tap="goToAssessment">
      <view class="assess-card-left">
        <text class="assess-icon">🧠</text>
        <view class="assess-text-group">
          <text class="assess-title">开始认知评估</text>
          <text class="assess-desc">约15分钟 · 系统全面评估</text>
        </view>
      </view>
      <view class="assess-arrow">
        <text class="arrow-text">▶</text>
      </view>
    </view>

    <!-- Quick Stats Row -->
    <view class="stats-row">
      <view class="stat-item">
        <text class="stat-number">{{ totalSessions }}</text>
        <text class="stat-label">累计评估</text>
      </view>
      <view class="stat-divider" />
      <view class="stat-item">
        <text class="stat-number" :style="{ color: latestRiskColor }">{{ latestRiskLabel }}</text>
        <text class="stat-label">最近结果</text>
      </view>
      <view class="stat-divider" />
      <view class="stat-item">
        <text class="stat-number">{{ daysSinceLastAssess }}</text>
        <text class="stat-label">距上次(天)</text>
      </view>
    </view>

    <!-- Quick Feature Entry -->
    <view class="feature-entry" @tap="goToInterventionTop5">
      <view class="feature-icon-box">
        <text class="feature-icon">💡</text>
      </view>
      <view class="feature-main">
        <text class="feature-title">干预推荐 Top-5</text>
        <text class="feature-desc">根据最近评估结果，生成重点训练建议</text>
      </view>
      <text class="feature-arrow">›</text>
    </view>

    <view class="feature-entry" @tap="goToInterventionCheckin">
      <view class="feature-icon-box" style="background: linear-gradient(135deg, #52C41A, #389E0D);">
        <text class="feature-icon">✅</text>
      </view>
      <view class="feature-main">
        <text class="feature-title">每日干预打卡</text>
        <text class="feature-desc">完成训练后记录打卡，医生可跟进依从性</text>
      </view>
      <text class="feature-arrow">›</text>
    </view>

    <view class="trend-card">
      <view class="trend-head">
        <text class="trend-title">复评与趋势追踪</text>
        <text class="trend-next">下次复评：{{ trendNextDate }}</text>
      </view>
      <view class="trend-meta">
        <text class="trend-meta-item">风险变化：{{ trendChangeLabel }}</text>
        <text class="trend-meta-item">最新风险：{{ trendRiskLabel }}</text>
      </view>
      <view v-if="trendPoints.length > 0" class="trend-list">
        <view v-for="point in trendPoints" :key="point.session_id" class="trend-item">
          <text class="trend-date">{{ formatTrendDate(point.assessed_at) }}</text>
          <text class="trend-score">MMSE {{ point.mmse_score ?? '--' }}</text>
          <text class="trend-score">MoCA {{ point.moca_score_corrected ?? '--' }}</text>
        </view>
      </view>
      <text v-else class="trend-empty">暂无趋势数据，完成两次评估后会显示变化趋势。</text>
    </view>

    <!-- Recent Assessments -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">最近评估记录</text>
        <text class="section-more" @tap="goToProfile">查看更多</text>
      </view>

      <!-- Loading -->
      <view v-if="loadingSessions" class="loading-box">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- Session List -->
      <view v-else-if="recentSessions.length > 0" class="sessions-list">
        <view
          v-for="session in recentSessions"
          :key="session.id"
          class="session-item"
          @tap="() => viewResult(session.id)"
        >
          <view class="session-left">
            <view class="risk-dot" :style="{ backgroundColor: getRiskColor(getSessionRisk(session)) }" />
            <view class="session-info">
              <text class="session-date">{{ formatDate(session.created_at) }}</text>
              <text class="session-score">{{ getSessionScoreText(session) }}</text>
            </view>
          </view>
          <view class="session-right">
            <text class="risk-label" :style="{ color: getRiskColor(getSessionRisk(session)) }">
              {{ getRiskLabel(getSessionRisk(session)) }}
            </text>
            <text class="session-arrow">›</text>
          </view>
        </view>
      </view>

      <!-- Empty State -->
      <view v-else class="empty-box">
        <text class="empty-icon">📋</text>
        <text class="empty-text">暂无评估记录</text>
        <text class="empty-hint">点击上方按钮开始您的第一次评估</text>
      </view>
    </view>

    <!-- Health Tips Carousel -->
    <view class="section">
      <text class="section-title">每日认知健康小贴士</text>
      <swiper
        class="tips-swiper"
        :autoplay="true"
        :interval="4000"
        :circular="true"
        indicator-dots
        indicator-color="rgba(255,255,255,0.5)"
        indicator-active-color="#ffffff"
      >
        <swiper-item v-for="(tip, i) in healthTips" :key="i">
          <view class="tip-card" :style="{ background: tip.color }">
            <text class="tip-icon">{{ tip.icon }}</text>
            <text class="tip-title">{{ tip.title }}</text>
            <text class="tip-content">{{ tip.content }}</text>
          </view>
        </swiper-item>
      </swiper>
    </view>

    <!-- Bottom padding for tab bar -->
    <view style="height: 40rpx;" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '../../store/auth'
import { api } from '../../utils/request'

const authStore = useAuthStore()

// State
const recentSessions = ref([])
const loadingSessions = ref(false)
const allSessionCount = ref(0)
const trendSummary = ref(null)

// Computed
const avatarLetter = computed(() => {
  const name = authStore.userName
  return name ? name.charAt(0) : '用'
})

const todayStr = computed(() => {
  const now = new Date()
  const y = now.getFullYear()
  const m = now.getMonth() + 1
  const d = now.getDate()
  const weekdays = ['日', '一', '二', '三', '四', '五', '六']
  return `${y}年${m}月${d}日 星期${weekdays[now.getDay()]}`
})

const totalSessions = computed(() => allSessionCount.value || 0)

const latestRiskLabel = computed(() => {
  if (recentSessions.value.length === 0) return '暂无'
  return getRiskLabel(getSessionRisk(recentSessions.value[0]))
})

const latestRiskColor = computed(() => {
  if (recentSessions.value.length === 0) return '#999999'
  return getRiskColor(getSessionRisk(recentSessions.value[0]))
})

const daysSinceLastAssess = computed(() => {
  if (recentSessions.value.length === 0) return '--'
  const last = recentSessions.value[0]?.created_at
  if (!last) return '--'
  const diff = Date.now() - new Date(last).getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24))
})

const trendPoints = computed(() => {
  const points = Array.isArray(trendSummary.value?.points) ? trendSummary.value.points : []
  return [...points]
    .sort((a, b) => {
      const aTs = new Date(a?.assessed_at || a?.created_at || 0).getTime()
      const bTs = new Date(b?.assessed_at || b?.created_at || 0).getTime()
      return bTs - aTs
    })
    .slice(0, 3)
})

const trendRiskLabel = computed(() => {
  const level = trendSummary.value?.latest_risk_level
  if (!level) return '--'
  return getRiskLabel(level)
})

const trendChangeLabel = computed(() => {
  const change = trendSummary.value?.risk_change
  const labels = {
    improved: '较上次改善',
    stable: '与上次持平',
    worsened: '较上次加重',
    unknown: '暂无对比',
  }
  return labels[change] || '暂无对比'
})

const trendNextDate = computed(() => trendSummary.value?.next_reassessment_date || '--')

const healthTips = [
  {
    icon: '🚶',
    title: '适量运动',
    content: '每天步行30分钟，有助于改善大脑血液循环，增强记忆力。',
    color: 'linear-gradient(135deg, #52C41A, #389E0D)'
  },
  {
    icon: '🧩',
    title: '动脑游戏',
    content: '玩数独、下棋或拼图，保持大脑活跃，预防认知退化。',
    color: 'linear-gradient(135deg, #4A90D9, #1D6FA4)'
  },
  {
    icon: '😴',
    title: '保证睡眠',
    content: '每晚保持7-8小时高质量睡眠，帮助大脑整理和巩固记忆。',
    color: 'linear-gradient(135deg, #722ED1, #531DAB)'
  },
  {
    icon: '🥗',
    title: '健康饮食',
    content: '多吃深色蔬菜、鱼类和坚果，富含的营养素有助于保护大脑。',
    color: 'linear-gradient(135deg, #FA8C16, #D46B08)'
  },
  {
    icon: '👥',
    title: '社交互动',
    content: '积极参与社区活动，与家人朋友交流，保持心情愉快。',
    color: 'linear-gradient(135deg, #EB2F96, #9E1068)'
  }
]

function getRiskColor(level) {
  const colors = {
    normal: '#52C41A',
    low: '#52C41A',
    mild_risk: '#FA8C16',
    mild: '#FA8C16',
    moderate: '#FA8C16',
    mci: '#FA8C16',
    in_progress: '#4A90D9',
    pending: '#4A90D9',
    completed: '#4A90D9',
    high: '#F5222D',
    high_risk: '#F5222D',
    severe: '#F5222D',
    ad: '#F5222D',
    failed: '#999999'
  }
  return colors[level] || '#999999'
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
    pending: '评估中',
    completed: '分析中',
    high: '高风险',
    high_risk: '高风险',
    severe: '高风险',
    ad: '高风险',
    failed: '失败'
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
    return `MMSE得分：${score}`
  }
  if (session?.status === 'failed') return '结果生成失败'
  if (session?.status === 'completed') return '结果生成中'
  if (session?.status === 'in_progress') return '评估进行中'
  return '评估中'
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
  if (!dateStr) return ''
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

function goToInterventionCheckin() {
  uni.navigateTo({ url: '/pages/intervention/checkin/index' })
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

    const top3 = sessions.slice(0, 3)
    recentSessions.value = await Promise.all(top3.map((item) => enrichSessionWithResult(item)))
  } catch (err) {
    console.error('Load sessions error:', err)
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
    console.warn('Load trend error:', err)
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
  background: #F0F4F8;
  min-height: 100vh;
}

/* Welcome Header */
.welcome-header {
  background: linear-gradient(135deg, #4A90D9, #2c6fad);
  padding: 40rpx 30rpx 60rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.welcome-text-group {
  display: flex;
  flex-direction: column;
}

.greeting {
  font-size: 48rpx;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 10rpx;
}

.date-text {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.8);
}

.avatar-circle {
  width: 100rpx;
  height: 100rpx;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 3rpx solid rgba(255, 255, 255, 0.5);
}

.avatar-text {
  font-size: 44rpx;
  font-weight: bold;
  color: #ffffff;
}

/* Assessment Card */
.assess-card {
  background: linear-gradient(135deg, #52C41A, #389E0D);
  border-radius: 24rpx;
  margin: -30rpx 30rpx 20rpx;
  padding: 36rpx 30rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: 0 8rpx 32rpx rgba(82, 196, 26, 0.35);
}

.assess-card-left {
  display: flex;
  align-items: center;
  gap: 24rpx;
}

.assess-icon {
  font-size: 72rpx;
}

.assess-text-group {
  display: flex;
  flex-direction: column;
}

.assess-title {
  font-size: 44rpx;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 8rpx;
}

.assess-desc {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.85);
}

.assess-arrow {
  width: 72rpx;
  height: 72rpx;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.arrow-text {
  font-size: 32rpx;
  color: #ffffff;
}

/* Stats Row */
.stats-row {
  background: #ffffff;
  border-radius: 20rpx;
  margin: 0 30rpx 20rpx;
  padding: 30rpx;
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-number {
  font-size: 44rpx;
  font-weight: bold;
  color: #4A90D9;
  margin-bottom: 8rpx;
}

.stat-label {
  font-size: 28rpx;
  color: #999999;
}

.stat-divider {
  width: 2rpx;
  height: 60rpx;
  background: #EEEEEE;
}

/* Quick feature entry */
.feature-entry {
  margin: 0 30rpx 20rpx;
  background: linear-gradient(135deg, #ffffff, #f5fbff);
  border-radius: 20rpx;
  padding: 24rpx 24rpx;
  display: flex;
  align-items: center;
  gap: 18rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  border: 1rpx solid #e8f3ff;
}

.feature-icon-box {
  width: 74rpx;
  height: 74rpx;
  border-radius: 18rpx;
  background: linear-gradient(135deg, #4A90D9, #1d6fa4);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.feature-icon {
  font-size: 42rpx;
}

.feature-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.feature-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #1f2d3d;
}

.feature-desc {
  font-size: 28rpx;
  color: #6b7785;
}

.feature-arrow {
  font-size: 44rpx;
  color: #9ab6cf;
}

.trend-card {
  margin: 0 30rpx 20rpx;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 22rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.trend-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 8rpx;
}

.trend-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #1f2d3d;
}

.trend-next {
  font-size: 28rpx;
  color: #6b7785;
}

.trend-meta {
  display: flex;
  gap: 18rpx;
  margin-bottom: 10rpx;
}

.trend-meta-item {
  font-size: 28rpx;
  color: #4a6b8a;
}

.trend-list {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.trend-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #f7fbff;
  border-radius: 12rpx;
  padding: 10rpx 12rpx;
}

.trend-date {
  font-size: 28rpx;
  color: #4A90D9;
  min-width: 90rpx;
}

.trend-score {
  font-size: 28rpx;
  color: #516172;
}

.trend-empty {
  font-size: 28rpx;
  color: #8c9bab;
}

/* Section */
.section {
  margin: 0 30rpx 20rpx;
}

.section-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
  display: block;
  margin-bottom: 16rpx;
}

.section-more {
  font-size: 28rpx;
  color: #4A90D9;
}

/* Loading */
.loading-box {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 40rpx;
  text-align: center;
}

.loading-text {
  font-size: 32rpx;
  color: #999999;
}

/* Sessions List */
.sessions-list {
  background: #ffffff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.session-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 30rpx;
  border-bottom: 1rpx solid #F0F0F0;
}

.session-item:last-child {
  border-bottom: none;
}

.session-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.risk-dot {
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  flex-shrink: 0;
}

.session-info {
  display: flex;
  flex-direction: column;
}

.session-date {
  font-size: 32rpx;
  color: #333333;
  font-weight: 500;
  margin-bottom: 6rpx;
}

.session-score {
  font-size: 28rpx;
  color: #888888;
}

.session-right {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.risk-label {
  font-size: 30rpx;
  font-weight: bold;
}

.session-arrow {
  font-size: 40rpx;
  color: #CCCCCC;
}

/* Empty State */
.empty-box {
  background: #ffffff;
  border-radius: 20rpx;
  padding: 60rpx 30rpx;
  text-align: center;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
}

.empty-text {
  font-size: 36rpx;
  color: #666666;
  margin-bottom: 12rpx;
}

.empty-hint {
  font-size: 28rpx;
  color: #AAAAAA;
  text-align: center;
}

/* Tips Swiper */
.tips-swiper {
  height: 240rpx;
  border-radius: 20rpx;
  overflow: hidden;
}

.tip-card {
  height: 240rpx;
  padding: 36rpx 30rpx;
  display: flex;
  flex-direction: column;
  justify-content: center;
  border-radius: 20rpx;
}

.tip-icon {
  font-size: 48rpx;
  margin-bottom: 12rpx;
}

.tip-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 12rpx;
  display: block;
}

.tip-content {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
  line-height: 1.5;
  display: block;
}
</style>
