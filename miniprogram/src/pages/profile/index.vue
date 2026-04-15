<template>
  <view class="profile-page">
    <view class="profile-hero">
      <view class="hero-avatar">
        <text class="hero-avatar-text">{{ avatarLetter }}</text>
      </view>
      <view class="hero-info">
        <text class="hero-name">{{ authStore.userName }}</text>
        <text class="hero-phone">{{ maskedPhone }}</text>
        <text class="hero-role">{{ roleLabel }}</text>
      </view>
    </view>

    <view class="mg-card stats-card">
      <view class="stat-item">
        <text class="stat-value">{{ totalAssessments }}</text>
        <text class="stat-label">累计评估</text>
      </view>
      <view class="stat-divider" />
      <view class="stat-item">
        <text class="stat-value" :style="{ color: latestRiskColor }">{{ latestRiskLabel }}</text>
        <text class="stat-label">最近风险</text>
      </view>
      <view class="stat-divider" />
      <view class="stat-item">
        <text class="stat-value">{{ avgScore }}</text>
        <text class="stat-label">平均分</text>
      </view>
    </view>

    <view class="section">
      <text class="section-title">评估历史记录</text>
      <view v-if="loadingHistory" class="mg-card loading-box">
        <text class="loading-text">正在加载历史...</text>
      </view>
      <view v-else-if="sessions.length > 0" class="mg-card history-list">
        <view v-for="session in sessions" :key="session.id" class="history-item" @tap="() => viewResult(session.id)">
          <view class="history-left">
            <view class="history-icon" :style="{ backgroundColor: getRiskColor(getSessionRisk(session)) }">
              <text class="history-icon-text">{{ getRiskIcon(getSessionRisk(session)) }}</text>
            </view>
            <view>
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
      <view v-else class="mg-card empty-box">
        <text class="empty-title">暂无评估记录</text>
        <text class="empty-tip">完成首次评估后，这里会显示您的历史变化趋势。</text>
        <button class="mg-button-primary empty-btn" @tap="goToAssessment">去做评估</button>
      </view>
    </view>

    <view class="section">
      <text class="section-title">更多服务</text>
      <view class="mg-card menu-list">
        <view class="menu-item" @tap="bindFamily">
          <view>
            <text class="menu-title">绑定家属</text>
            <text class="menu-desc">让家人一起关注您的认知健康状态</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="contactUs">
          <view>
            <text class="menu-title">联系客服</text>
            <text class="menu-desc">遇到问题可联系社区健康研究团队</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
        <view class="menu-item" @tap="showAbout">
          <view>
            <text class="menu-title">关于忆守心安</text>
            <text class="menu-desc">版本 1.0.0</text>
          </view>
          <text class="menu-arrow">›</text>
        </view>
      </view>
    </view>

    <view class="logout-wrap">
      <button class="logout-btn" @tap="handleLogout">退出登录</button>
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

const sessions = ref([])
const loadingHistory = ref(false)

const avatarLetter = computed(() => {
  const name = authStore.userName
  return name ? name.charAt(0) : '您'
})

const maskedPhone = computed(() => {
  const phone = authStore.userPhone
  if (!phone || phone.length < 11) return phone || '未设置'
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
})

const roleLabel = computed(() => {
  const labels = {
    elder: '老年用户',
    elderly: '老年用户',
    family: '家属用户',
    doctor: '医护人员',
    admin: '系统管理员',
  }
  return labels[authStore.userRole] || '用户'
})

const totalAssessments = computed(() => sessions.value.length)

const latestRiskLabel = computed(() => {
  if (sessions.value.length === 0) return '--'
  return getRiskLabel(getSessionRisk(sessions.value[0]))
})

const latestRiskColor = computed(() => {
  if (sessions.value.length === 0) return '#7890a0'
  return getRiskColor(getSessionRisk(sessions.value[0]))
})

const avgScore = computed(() => {
  const scored = sessions.value.filter((item) => item.mmse_score !== null && item.mmse_score !== undefined)
  if (scored.length === 0) return '--'
  const total = scored.reduce((sum, item) => sum + Number(item.mmse_score), 0)
  return Math.round(total / scored.length)
})

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

function getRiskIcon(level) {
  const icons = {
    normal: '✓',
    low: '✓',
    mild_risk: '!',
    mild: '!',
    moderate: '!',
    mci: '!',
    in_progress: '…',
    pending: '…',
    completed: '…',
    high: '!',
    high_risk: '!',
    severe: '!',
    ad: '!',
    failed: '×',
  }
  return icons[level] || '?'
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
    return `MMSE：${score} / 30`
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
  return `${d.getFullYear()}年${d.getMonth() + 1}月${d.getDate()}日`
}

function viewResult(sessionId) {
  uni.navigateTo({ url: `/pages/result/index?sessionId=${sessionId}&fromHistory=true` })
}

function goToAssessment() {
  uni.navigateTo({ url: '/pages/assessment/start/index' })
}

function bindFamily() {
  wx.showModal({
    title: '绑定家属',
    content: '该功能正在开发中，后续将支持家属查看评估进展并接收提醒。',
    showCancel: false,
    confirmText: '我知道了',
  })
}

function contactUs() {
  wx.showActionSheet({
    itemList: ['拨打咨询电话', '发送意见反馈'],
    success: (res) => {
      if (res.tapIndex === 0) {
        wx.makePhoneCall({
          phoneNumber: '0744-12345678',
          fail: () => wx.showToast({ title: '拨号失败', icon: 'none' }),
        })
      } else {
        wx.showModal({
          title: '意见反馈',
          content: '如有建议，请发送邮件至：mindguard@zjjxy.edu.cn',
          showCancel: false,
          confirmText: '好的',
        })
      }
    },
  })
}

function showAbout() {
  wx.showModal({
    title: '关于忆守心安',
    content: '忆守心安 · 认知评估系统\n版本：1.0.0\n\n由张家界学院社区健康研究中心开发。',
    showCancel: false,
    confirmText: '关闭',
  })
}

function handleLogout() {
  wx.showModal({
    title: '退出登录',
    content: '确定要退出当前账号吗？',
    confirmText: '退出',
    cancelText: '取消',
    confirmColor: '#dc2626',
    success: (res) => {
      if (res.confirm) authStore.logout()
    },
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
    console.error('load history error', err)
    wx.showToast({ title: '加载历史失败', icon: 'none' })
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
  padding: 24rpx;
}

.profile-hero {
  border-radius: 30rpx;
  padding: 26rpx 24rpx;
  background:
    radial-gradient(circle at 100% -10%, rgba(124, 58, 237, 0.26), transparent 44%),
    linear-gradient(140deg, #0f766e, #0284c7);
  box-shadow: var(--mg-shadow-strong);
  display: flex;
  align-items: center;
  gap: 18rpx;
}

.hero-avatar {
  width: 112rpx;
  height: 112rpx;
  border-radius: 32rpx;
  background: rgba(255, 255, 255, 0.2);
  border: 2rpx solid rgba(255, 255, 255, 0.44);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.hero-avatar-text {
  color: #ffffff;
  font-size: 48rpx;
  font-weight: 800;
}

.hero-info {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.hero-name {
  color: #ffffff;
  font-size: 42rpx;
  font-weight: 800;
}

.hero-phone {
  color: rgba(238, 252, 255, 0.9);
  font-size: 27rpx;
}

.hero-role {
  color: #e5faff;
  font-size: 28rpx;
}

.stats-card {
  margin-top: -14rpx;
  padding: 22rpx 12rpx;
  display: flex;
  align-items: center;
  box-shadow: var(--mg-shadow-soft);
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-value {
  display: block;
  color: #0f766e;
  font-size: 42rpx;
  font-weight: 800;
}

.stat-label {
  display: block;
  margin-top: 4rpx;
  color: #708899;
  font-size: 28rpx;
}

.stat-divider {
  width: 2rpx;
  height: 52rpx;
  background: rgba(17, 34, 49, 0.1);
}

.section {
  margin-top: 18rpx;
}

.section-title {
  display: block;
  margin-bottom: 12rpx;
  color: #143445;
  font-size: 34rpx;
  font-weight: 800;
}

.loading-box {
  padding: 28rpx;
  text-align: center;
}

.loading-text {
  color: #6f8696;
  font-size: 28rpx;
}

.history-list {
  overflow: hidden;
}

.history-item {
  padding: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2rpx solid rgba(17, 34, 49, 0.06);
}

.history-item:last-child {
  border-bottom: none;
}

.history-left {
  display: flex;
  align-items: center;
  gap: 12rpx;
  flex: 1;
}

.history-icon {
  width: 60rpx;
  height: 60rpx;
  border-radius: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.history-icon-text {
  color: #ffffff;
  font-size: 30rpx;
  font-weight: 800;
}

.history-date {
  display: block;
  color: #1f3d4f;
  font-size: 30rpx;
  font-weight: 700;
}

.history-score {
  display: block;
  margin-top: 2rpx;
  color: #6d8595;
  font-size: 29rpx;
}

.history-risk {
  display: block;
  margin-top: 2rpx;
  font-size: 29rpx;
  font-weight: 700;
}

.history-arrow {
  color: #8ba0ae;
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
}

.empty-tip {
  display: block;
  margin-top: 8rpx;
  color: #738b9b;
  font-size: 27rpx;
}

.empty-btn {
  margin-top: 16rpx;
}

.menu-list {
  overflow: hidden;
}

.menu-item {
  padding: 20rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2rpx solid rgba(17, 34, 49, 0.06);
}

.menu-item:last-child {
  border-bottom: none;
}

.menu-title {
  display: block;
  color: #1f3d4f;
  font-size: 30rpx;
  font-weight: 700;
}

.menu-desc {
  display: block;
  margin-top: 4rpx;
  color: #6e8595;
  font-size: 28rpx;
}

.menu-arrow {
  color: #8aa0ae;
  font-size: 36rpx;
}

.logout-wrap {
  margin-top: 20rpx;
}

.logout-btn {
  width: 100%;
  min-height: 92rpx;
  border-radius: 999rpx;
  background: #ffffff;
  color: #dc2626;
  border: 2rpx solid rgba(220, 38, 38, 0.28);
  font-size: 34rpx;
  font-weight: 700;
  box-shadow: 0 10rpx 18rpx rgba(220, 38, 38, 0.08);
}
</style>

