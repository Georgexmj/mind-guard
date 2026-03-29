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
            <view class="risk-dot" :style="{ backgroundColor: getRiskColor(session.risk_level) }" />
            <view class="session-info">
              <text class="session-date">{{ formatDate(session.created_at) }}</text>
              <text class="session-score">MMSE得分：{{ session.mmse_score ?? '评估中' }}</text>
            </view>
          </view>
          <view class="session-right">
            <text class="risk-label" :style="{ color: getRiskColor(session.risk_level) }">
              {{ getRiskLabel(session.risk_level) }}
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
import { useAssessmentStore } from '../../store/assessment'
import { api } from '../../utils/request'

const authStore = useAuthStore()
const assessmentStore = useAssessmentStore()

// State
const recentSessions = ref([])
const loadingSessions = ref(false)

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

const totalSessions = computed(() => recentSessions.value.length || 0)

const latestRiskLabel = computed(() => {
  if (recentSessions.value.length === 0) return '暂无'
  return getRiskLabel(recentSessions.value[0]?.risk_level)
})

const latestRiskColor = computed(() => {
  if (recentSessions.value.length === 0) return '#999999'
  return getRiskColor(recentSessions.value[0]?.risk_level)
})

const daysSinceLastAssess = computed(() => {
  if (recentSessions.value.length === 0) return '--'
  const last = recentSessions.value[0]?.created_at
  if (!last) return '--'
  const diff = Date.now() - new Date(last).getTime()
  return Math.floor(diff / (1000 * 60 * 60 * 24))
})

// Health tips data
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

// Methods
function getRiskColor(level) {
  const colors = {
    normal: '#52C41A',
    low: '#52C41A',
    mild: '#FA8C16',
    moderate: '#FA8C16',
    high: '#F5222D',
    severe: '#F5222D'
  }
  return colors[level] || '#999999'
}

function getRiskLabel(level) {
  const labels = {
    normal: '正常',
    low: '正常',
    mild: '轻度风险',
    moderate: '中度风险',
    high: '高风险',
    severe: '高风险'
  }
  return labels[level] || '未知'
}

function formatDate(dateStr) {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

function goToAssessment() {
  uni.navigateTo({ url: '/pages/assessment/start/index' })
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
    const sessions = Array.isArray(data) ? data : (data.sessions || data.items || [])
    // Show most recent 3
    recentSessions.value = sessions.slice(0, 3)
  } catch (err) {
    console.error('Load sessions error:', err)
    // Don't show error toast on home page - just show empty state
  } finally {
    loadingSessions.value = false
  }
}

// Load data when page shows
onShow(() => {
  loadSessions()
})

onMounted(() => {
  loadSessions()
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
  font-size: 26rpx;
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
  font-size: 26rpx;
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
  font-size: 24rpx;
  color: #999999;
}

.stat-divider {
  width: 2rpx;
  height: 60rpx;
  background: #EEEEEE;
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
  font-size: 26rpx;
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
