<template>
  <view class="profile-page">
    <!-- User Header -->
    <view class="user-header">
      <view class="avatar-circle">
        <text class="avatar-text">{{ avatarLetter }}</text>
      </view>
      <view class="user-info">
        <text class="user-name">{{ authStore.userName }}</text>
        <text class="user-phone">{{ maskedPhone }}</text>
        <view class="user-role-badge">
          <text class="role-text">{{ roleLabel }}</text>
        </view>
      </view>
    </view>

    <!-- Stats Row -->
    <view class="stats-card">
      <view class="stat-item">
        <text class="stat-number">{{ totalAssessments }}</text>
        <text class="stat-label">累计评估</text>
      </view>
      <view class="stat-divider" />
      <view class="stat-item">
        <text class="stat-number" :style="{ color: latestRiskColor }">{{ latestRiskLabel }}</text>
        <text class="stat-label">最近结果</text>
      </view>
      <view class="stat-divider" />
      <view class="stat-item">
        <text class="stat-number">{{ avgScore }}</text>
        <text class="stat-label">平均分</text>
      </view>
    </view>

    <!-- History Section -->
    <view class="section">
      <view class="section-header">
        <text class="section-title">📋 评估历史记录</text>
      </view>

      <view v-if="loadingHistory" class="loading-box">
        <text class="loading-text">加载中...</text>
      </view>

      <view v-else-if="sessions.length > 0" class="history-list">
        <view
          v-for="session in sessions"
          :key="session.id"
          class="history-item"
          @tap="() => viewResult(session.id)"
        >
          <view class="history-left">
            <view class="risk-indicator" :style="{ backgroundColor: getRiskColor(getSessionRisk(session)) }">
              <text class="risk-indicator-text">{{ getRiskIcon(getSessionRisk(session)) }}</text>
            </view>
            <view class="history-info">
              <text class="history-date">{{ formatDate(session.created_at) }}</text>
              <text class="history-score">{{ getSessionScoreText(session) }}</text>
              <text class="history-risk" :style="{ color: getRiskColor(getSessionRisk(session)) }">
                {{ getRiskLabel(getSessionRisk(session)) }}
              </text>
            </view>
          </view>
          <text class="history-arrow">›</text>
        </view>
      </view>

      <view v-else class="empty-history">
        <text class="empty-icon">📭</text>
        <text class="empty-text">暂无评估记录</text>
        <button class="btn-go-assess" @tap="goToAssessment">开始第一次评估</button>
      </view>
    </view>

    <!-- Menu Items -->
    <view class="section">
      <text class="section-title">⚙️ 更多功能</text>
      <view class="menu-list">
        <view class="menu-item" @tap="bindFamily">
          <view class="menu-left">
            <text class="menu-icon">👨‍👩‍👧</text>
            <text class="menu-text">绑定家属</text>
          </view>
          <view class="menu-right">
            <text class="menu-sub">让家人了解您的健康状态</text>
            <text class="menu-arrow">›</text>
          </view>
        </view>

        <view class="menu-item" @tap="contactUs">
          <view class="menu-left">
            <text class="menu-icon">📞</text>
            <text class="menu-text">联系我们</text>
          </view>
          <view class="menu-right">
            <text class="menu-sub">如有问题请联系</text>
            <text class="menu-arrow">›</text>
          </view>
        </view>

        <view class="menu-item" @tap="showAbout">
          <view class="menu-left">
            <text class="menu-icon">ℹ️</text>
            <text class="menu-text">关于忆守心安</text>
          </view>
          <view class="menu-right">
            <text class="menu-sub">版本 1.0.0</text>
            <text class="menu-arrow">›</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Logout Button -->
    <view class="logout-area">
      <button class="btn-logout" @tap="handleLogout">退出登录</button>
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
const sessions = ref([])
const loadingHistory = ref(false)

// Computed user info
const avatarLetter = computed(() => {
  const name = authStore.userName
  return name ? name.charAt(0) : '用'
})

const maskedPhone = computed(() => {
  const phone = authStore.userPhone
  if (!phone || phone.length < 11) return phone || '未设置'
  return phone.slice(0, 3) + '****' + phone.slice(-4)
})

const roleLabel = computed(() => {
  const role = authStore.userRole
  const labels = {
    elder: '老年用户',
    elderly: '老年用户',
    family: '家属用户',
    doctor: '医护人员',
    admin: '管理员'
  }
  return labels[role] || '用户'
})

// Stats computed
const totalAssessments = computed(() => sessions.value.length)

const latestRiskLabel = computed(() => {
  if (sessions.value.length === 0) return '--'
  return getRiskLabel(getSessionRisk(sessions.value[0]))
})

const latestRiskColor = computed(() => {
  if (sessions.value.length === 0) return '#999999'
  return getRiskColor(getSessionRisk(sessions.value[0]))
})

const avgScore = computed(() => {
  const scored = sessions.value.filter((s) => s.mmse_score !== null && s.mmse_score !== undefined)
  if (scored.length === 0) return '--'
  const sum = scored.reduce((acc, s) => acc + Number(s.mmse_score), 0)
  const avg = sum / scored.length
  return Math.round(avg)
})

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

function getRiskIcon(level) {
  const icons = {
    normal: '🙂',
    low: '🙂',
    mild_risk: '😐',
    mild: '😐',
    moderate: '😐',
    mci: '😐',
    in_progress: '⏳',
    pending: '⏳',
    completed: '⏳',
    high: '⚠️',
    high_risk: '⚠️',
    severe: '⚠️',
    ad: '⚠️',
    failed: '❌'
  }
  return icons[level] || '❔'
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
    return `MMSE: ${score} / 30分`
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
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

function viewResult(sessionId) {
  uni.navigateTo({
    url: `/pages/result/index?sessionId=${sessionId}&fromHistory=true`
  })
}

function goToAssessment() {
  uni.navigateTo({ url: '/pages/assessment/start/index' })
}

function bindFamily() {
  wx.showModal({
    title: '绑定家属',
    content: '该功能正在开发中，将让您的家人能够查看您的认知健康状态。',
    showCancel: false,
    confirmText: '知道了',
    confirmColor: '#4A90D9'
  })
}

function contactUs() {
  wx.showActionSheet({
    itemList: ['拨打咨询电话', '发送意见反馈'],
    success: (res) => {
      if (res.tapIndex === 0) {
        wx.makePhoneCall({
          phoneNumber: '0744-12345678',
          fail: () => {
            wx.showToast({ title: '拨号失败', icon: 'none' })
          }
        })
      } else {
        wx.showModal({
          title: '意见反馈',
          content: '如有任何问题或建议，请发送邮件至：mindguard@zjjxy.edu.cn',
          showCancel: false,
          confirmText: '好的',
          confirmColor: '#4A90D9'
        })
      }
    }
  })
}

function showAbout() {
  wx.showModal({
    title: '关于忆守心安',
    content: '忆守心安 认知评估系统\n版本：1.0.0\n\n由张家界学院社区健康研究中心开发\n用于社区老年认知障碍早期筛查与干预\n\n© 2024 张家界学院',
    showCancel: false,
    confirmText: '关闭',
    confirmColor: '#4A90D9'
  })
}

function handleLogout() {
  wx.showModal({
    title: '退出登录',
    content: '确定要退出登录吗？',
    confirmText: '退出',
    cancelText: '取消',
    confirmColor: '#F5222D',
    success: (res) => {
      if (res.confirm) {
        authStore.logout()
      }
    }
  })
}

async function loadHistory() {
  loadingHistory.value = true
  try {
    const data = await api.getSessions()
    const listRaw = Array.isArray(data) ? data : (data.sessions || data.items || [])
    const list = [...listRaw]
      .filter((item) => isEffectiveSession(item))
      .sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
    sessions.value = await Promise.all(list.map((item) => enrichSessionWithResult(item)))
  } catch (err) {
    console.error('Load history error:', err)
    wx.showToast({ title: '加载历史失败', icon: 'none', duration: 2000 })
  } finally {
    loadingHistory.value = false
  }
}

onShow(() => {
  if (!authStore.enforceElderRole()) return
  loadHistory()
})

onMounted(() => {
  if (!authStore.enforceElderRole()) return
  loadHistory()
})
</script>

<style scoped>
.profile-page {
  min-height: 100vh;
  background: #F0F4F8;
  padding-bottom: 40rpx;
}

/* User Header */
.user-header {
  background: linear-gradient(135deg, #4A90D9, #2c6fad);
  padding: 50rpx 30rpx 70rpx;
  display: flex;
  align-items: center;
  gap: 30rpx;
}

.avatar-circle {
  width: 130rpx;
  height: 130rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.25);
  border: 4rpx solid rgba(255, 255, 255, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.avatar-text {
  font-size: 60rpx;
  font-weight: bold;
  color: #ffffff;
}

.user-info {
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.user-name {
  font-size: 48rpx;
  font-weight: bold;
  color: #ffffff;
}

.user-phone {
  font-size: 30rpx;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 2rpx;
}

.user-role-badge {
  background: rgba(255, 255, 255, 0.25);
  border-radius: 20rpx;
  padding: 6rpx 20rpx;
  display: inline-flex;
  align-self: flex-start;
}

.role-text {
  font-size: 28rpx;
  color: #ffffff;
}

/* Stats Card */
.stats-card {
  background: #ffffff;
  border-radius: 20rpx;
  margin: -30rpx 30rpx 20rpx;
  padding: 30rpx;
  display: flex;
  align-items: center;
  justify-content: space-around;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.1);
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.stat-number {
  font-size: 48rpx;
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

/* Section */
.section {
  margin: 0 30rpx 20rpx;
}

.section-header {
  margin-bottom: 16rpx;
}

.section-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
  display: block;
  margin-bottom: 16rpx;
}

/* Loading */
.loading-box {
  background: #ffffff;
  border-radius: 16rpx;
  padding: 50rpx;
  text-align: center;
}

.loading-text {
  font-size: 32rpx;
  color: #999999;
}

/* History List */
.history-list {
  background: #ffffff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.history-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 28rpx 24rpx;
  border-bottom: 1rpx solid #F5F5F5;
}

.history-item:last-child {
  border-bottom: none;
}

.history-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
  flex: 1;
}

.risk-indicator {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.risk-indicator-text {
  font-size: 32rpx;
}

.history-info {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.history-date {
  font-size: 32rpx;
  font-weight: bold;
  color: #333333;
}

.history-score {
  font-size: 28rpx;
  color: #666666;
}

.history-risk {
  font-size: 28rpx;
  font-weight: bold;
}

.history-arrow {
  font-size: 44rpx;
  color: #CCCCCC;
}

/* Empty History */
.empty-history {
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
  margin-bottom: 30rpx;
}

.btn-go-assess {
  background: linear-gradient(135deg, #52C41A, #389E0D);
  color: #ffffff;
  font-size: 34rpx;
  font-weight: bold;
  height: 88rpx;
  border-radius: 44rpx;
  border: none;
  padding: 0 50rpx;
}

/* Menu List */
.menu-list {
  background: #ffffff;
  border-radius: 20rpx;
  overflow: hidden;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.menu-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 30rpx 24rpx;
  border-bottom: 1rpx solid #F5F5F5;
  min-height: 110rpx;
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-item:active {
  background: #F8F9FA;
}

.menu-left {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.menu-icon {
  font-size: 44rpx;
}

.menu-text {
  font-size: 36rpx;
  color: #333333;
  font-weight: 500;
}

.menu-right {
  display: flex;
  align-items: center;
  gap: 8rpx;
}

.menu-sub {
  font-size: 28rpx;
  color: #AAAAAA;
}

.menu-arrow {
  font-size: 44rpx;
  color: #CCCCCC;
}

/* Logout Area */
.logout-area {
  margin: 20rpx 30rpx 0;
}

.btn-logout {
  width: 100%;
  height: 96rpx;
  background: #ffffff;
  color: #F5222D;
  font-size: 38rpx;
  font-weight: bold;
  border-radius: 48rpx;
  border: 2rpx solid #FFCCC7;
  box-shadow: 0 2rpx 12rpx rgba(245, 34, 45, 0.1);
  letter-spacing: 2rpx;
}
</style>
