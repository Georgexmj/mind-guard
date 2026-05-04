<template>
  <view class="home-page">
    <!-- 家属查看模式界面 -->
    <view v-if="isFamilyViewMode && viewingElder" class="family-view-page">
      <view class="family-header">
        <view class="family-header-content">
          <view class="family-info">
            <text class="family-title">欢迎回来</text>
            <text class="family-subtitle">{{ viewingElder.name }}的家属</text>
            <view class="family-badge">
              <text class="badge-icon">❤️</text>
              <text class="badge-text">共关注1位老人</text>
            </view>
          </view>
          <view class="exit-btn" @tap="exitFamilyViewMode">
            <text class="exit-text">退出</text>
          </view>
        </view>
        <view class="elder-card-mini" @tap="goToElderDetail">
          <view class="elder-avatar-small">{{ viewingElder.name?.charAt(0) || '?' }}</view>
          <view class="elder-info-mini">
            <text class="elder-name-mini">{{ viewingElder.age || '未知年龄' }} · {{ viewingElder.gender === 'male' ? '男' : '女' }}</text>
            <view class="elder-stats">
              <text class="stat-item">测评 {{ sessions.length }}次</text>
              <text class="stat-divider">|</text>
              <text class="stat-item">训练 0次</text>
            </view>
          </view>
          <view class="arrow-icon">›</view>
        </view>
      </view>

      <view class="family-content">
        <!-- 评估报告一键查询 -->
        <view class="quick-report-card" @tap="goToAllReports">
          <view class="report-header">
            <view class="report-icon">📊</view>
            <view class="report-title-wrap">
              <text class="report-title">评估报告总览</text>
              <text class="report-desc">一键查看所有项目情况</text>
            </view>
            <view class="report-arrow">›</view>
          </view>
          <view class="report-stats">
            <view class="report-stat">
              <text class="report-stat-value">{{ sessions.length }}</text>
              <text class="report-stat-label">测评次数</text>
            </view>
            <view class="report-divider"></view>
            <view class="report-stat">
              <text class="report-stat-value">{{ healthStatus }}</text>
              <text class="report-stat-label">健康状况</text>
            </view>
            <view class="report-divider"></view>
            <view class="report-stat">
              <text class="report-stat-value">{{ trainingDays }}</text>
              <text class="report-stat-label">训练天数</text>
            </view>
          </view>
        </view>

        <!-- 功能菜单 -->
        <view class="family-menu-section">
          <text class="family-section-title">功能菜单</text>
          <view class="family-menu-grid">
            <view class="family-menu-card" @tap="goToResult">
              <view class="family-menu-icon report">
                <text class="icon-text">📋</text>
              </view>
              <text class="family-menu-title">查看报告</text>
              <text class="family-menu-desc">认知评估报告</text>
            </view>
            <view class="family-menu-card" @tap="goToAiAnalysis">
              <view class="family-menu-icon ai">
                <text class="icon-text">🤖</text>
              </view>
              <text class="family-menu-title">AI分析</text>
              <text class="family-menu-desc">智能健康分析</text>
            </view>
            <view class="family-menu-card" @tap="goToAssessment">
              <view class="family-menu-icon assessment">
                <text class="icon-text">🧠</text>
              </view>
              <text class="family-menu-title">老人评估</text>
              <text class="family-menu-desc">认知能力测评</text>
            </view>
            <view class="family-menu-card" @tap="goToNotifications">
              <view class="family-menu-icon notification">
                <text class="icon-text">🔔</text>
                <view class="notification-badge" v-if="notificationCount > 0">{{ notificationCount }}</view>
              </view>
              <text class="family-menu-title">消息通知</text>
              <text class="family-menu-desc">训练与评估通知</text>
            </view>
          </view>
        </view>

        <!-- 最近测评记录 -->
        <view class="family-history-section">
          <view class="history-header">
            <text class="family-section-title">最近测评记录</text>
            <text class="history-more" @tap="goToAllReports">查看全部 ›</text>
          </view>
          <view class="history-list">
            <view v-for="session in recentSessions" :key="session.id" class="history-item" @tap="goToSessionDetail(session.id)">
              <view class="history-date">
                <text class="date-day">{{ formatDate(session.created_at).day }}</text>
                <text class="date-month">{{ formatDate(session.created_at).month }}</text>
              </view>
              <view class="history-info">
                <text class="history-title">认知测评</text>
                <text class="history-time">{{ formatTime(session.created_at) }}</text>
              </view>
              <view class="history-result" :class="getRiskClass(session.risk_level)">
                <text class="result-text">{{ getRiskText(session.risk_level) }}</text>
              </view>
            </view>
          </view>
        </view>

        <view class="bottom-gap" />
      </view>
    </view>

    <!-- 正常首页界面 -->
    <view v-else>
      <view class="top-nav">
        <view class="brand-chip">智</view>
        <view class="nav-menu" @click="showMenu">≡</view>
      </view>

      <view class="welcome-banner">
        <text class="banner-date">📅 {{ todayStr }}</text>
        <text class="banner-title">{{ greeting }}{{ authStore.userName || '长者' }} 👋</text>
        <text class="banner-subtitle">{{ authStore.userRole === 'family' ? '查看家人健康数据' : '今天也要保持好心情，照顾好自己' }}</text>
        <view class="checkin-btn" @tap="onDailyCheckin">
  <text class="checkin-icon">🔥</text>
  <text class="checkin-text">每日打卡</text>
</view>
      </view>

      <view v-if="authStore.userRole === 'family' && elders.length > 0" class="elder-selector">
        <text class="selector-label">选择老人：</text>
        <view class="elder-list">
          <view
            v-for="elder in elders"
            :key="elder.id"
            :class="['elder-item', { active: selectedElderId === elder.id }]"
            @tap="handleElderChange(elder.id)"
          >
            <text>{{ elder.name || '未命名' }}</text>
          </view>
        </view>
      </view>

      <view class="content-area">
      <view class="stats-grid">
        <view class="stat-card lilac">
          <view class="stat-icon-wrap">
            <text class="stat-icon">🧠</text>
          </view>
          <text class="stat-value">{{ totalSessions || 12 }}次</text>
          <text class="stat-label">累计测评</text>
        </view>
        <view class="stat-card mint">
          <view class="stat-icon-wrap">
            <text class="stat-icon">📈</text>
          </view>
          <text class="stat-value">{{ trainingDays || 28 }}天</text>
          <text class="stat-label">训练天数</text>
        </view>
        <view class="stat-card blush">
          <view class="stat-icon-wrap">
            <text class="stat-icon">💗</text>
          </view>
          <text class="stat-value">{{ healthStatus }}</text>
          <text class="stat-label">健康指数</text>
        </view>
        <view class="stat-card cream">
          <view class="stat-icon-wrap">
            <text class="stat-icon">🔥</text>
          </view>
          <text class="stat-value">{{ streakDays }}天</text>
          <text class="stat-label">连续打卡</text>
        </view>
      </view>

      <view class="section-title">功能菜单</view>
      <view class="menu-grid">
        <view class="menu-card" @tap="goToAssessment">
          <view class="menu-icon purple">
            <view class="icon-brain"></view>
          </view>
          <text class="menu-title">认知测评</text>
          <text class="menu-desc">了解认知状况</text>
        </view>
        <view class="menu-card" @tap="goToInterventionTop5">
          <view class="menu-icon green">
            <view class="icon-chart"></view>
          </view>
          <text class="menu-title">康复训练</text>
          <text class="menu-desc">脑力锻炼计划</text>
        </view>
        <view class="menu-card" @tap="goToProfile">
          <view class="menu-icon blue">
            <view class="icon-user"></view>
          </view>
          <text class="menu-title">个人中心</text>
          <text class="menu-desc">查看个人信息</text>
        </view>
        <view class="menu-card" @tap="goToResult">
          <view class="menu-icon amber">
            <view class="icon-bar"></view>
          </view>
          <text class="menu-title">健康报告</text>
          <text class="menu-desc">健康数据分析</text>
        </view>
      </view>

      <view class="task-head">
        <text class="section-title">今日任务</text>
        <text class="task-progress">{{ doneTaskCount }}/{{ tasks.length }} 完成</text>
      </view>
      <view class="task-list">
        <view v-for="(task, index) in tasks" :key="task.id" class="task-row" @tap="toggleTask(index)">
          <view class="task-radio" :class="{ checked: task.done }">
            <view class="radio-inner" v-if="task.done"></view>
          </view>
          <text class="task-text" :class="{ done: task.done }">{{ task.title }}</text>
        </view>
      </view>

      <view class="tip-box">
        <view class="tip-header">
          <view class="tip-icon">🔔</view>
          <text class="tip-title">今日健康贴士</text>
        </view>
        <text class="tip-content">{{ todayTip }}</text>
      </view>

      <view class="bottom-gap" />
      </view> <!-- content-area -->
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow, onReady, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { api } from '@/utils/request'

const authStore = useAuthStore()
const sessions = ref([])
const elders = ref([])
const selectedElderId = ref(null)
const viewingElder = ref(null)  // 家属通过身份证验证后查看的老人
const isFamilyViewMode = ref(false)  // 是否是家属查看模式
const notificationCount = ref(2)  // 通知数量（模拟数据）

const showMenu = () => {
  uni.showActionSheet({
    itemList: ['关于', '设置', '退出登录'],
    success: (res) => {
      switch (res.tapIndex) {
        case 0:
          uni.showModal({
            title: '关于',
            content: '忆守心安 - 老年认知障碍早筛与干预系统\n版本 1.0.0',
            showCancel: false
          })
          break
        case 1:
          uni.navigateTo({ url: '/pages/settings/index' })
          break
        case 2:
          uni.showModal({
            title: '提示',
            content: '确定要退出登录吗？',
            success: (modalRes) => {
              if (modalRes.confirm) authStore.logout()
            }
          })
          break
      }
    }
  })
}

const tasks = ref([
  { id: 1, title: '完成认知测评', done: false },
  { id: 2, title: '进行康复训练', done: false },
  { id: 3, title: '和心灵小导师聊天', done: false },
])

const tipPool = [
  '多喝温水，每天保持1500ml以上的饮用量，有助于大脑保持活跃。',
  '每天坚持30分钟轻运动，能改善注意力和睡眠质量。',
  '和家人朋友多交流，社交活动有助于维持认知活跃。',
  '保证每晚7-8小时睡眠，充足的休息对大脑健康至关重要。',
  '多吃富含Omega-3的食物，如鱼、坚果，有助于大脑健康。',
  '学习新技能可以刺激大脑，延缓认知衰退。',
  '保持积极心态，笑口常开有助于减轻压力，有益身心健康。',
  '每天阅读30分钟，可以锻炼记忆力和思维能力。',
  '适当晒太阳，补充维生素D，对情绪和认知功能都有帮助。',
  '练习冥想或深呼吸，有助于放松身心，提升专注力。',
  '定期进行认知训练游戏，可以保持大脑灵活性。',
  '多吃蔬菜水果，补充抗氧化剂，保护脑细胞。',
  '保持规律的作息，有助于稳定生物钟和情绪。',
  '与家人一起散步聊天，增进感情的同时也锻炼了身体。',
  '尝试新的爱好，如书法、绘画、园艺，丰富精神生活。',
  '控制盐分摄入，保持血压稳定，保护脑血管健康。',
  '每天做一些简单的手指操，可以锻炼手部灵活性和大脑协调能力。',
  '保持好奇心，对新鲜事物保持兴趣，促进大脑活跃。',
  '定期体检，关注身体健康状况，早发现早预防。',
  '听舒缓的音乐，可以放松心情，减轻焦虑和压力。',
  '保持良好的坐姿和站姿，保护颈椎和腰椎健康。',
  '多喝水可以促进新陈代谢，帮助身体排出废物。',
  '适量摄入蛋白质，如鸡蛋、牛奶，为大脑提供充足营养。',
  '培养感恩之心，每天记录一件值得感恩的事情。',
  '参与社区活动，拓展社交圈子，丰富晚年生活。',
  '练习太极拳或瑜伽，有助于平衡和柔韧性训练。',
  '保持学习的习惯，可以通过书籍、电视或手机获取新知识。',
  '定期与子女或亲友通话，保持情感联系。',
  '保持室内通风，呼吸新鲜空气，有助于大脑清醒。',
  '做一些简单的数学题或填字游戏，锻炼思维能力。',
]

const todayTip = computed(() => {
  const now = new Date()
  const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000)
  return tipPool[dayOfYear % tipPool.length]
})

const todayStr = computed(() => {
  const now = new Date()
  const weeks = ['日', '一', '二', '三', '四', '五', '六']
  return `${now.getMonth() + 1}月${now.getDate()}日 星期${weeks[now.getDay()]}`
})

const greeting = computed(() => {
  const hour = new Date().getHours()
  if (hour < 12) return '上午好，'
  if (hour < 18) return '下午好，'
  return '晚上好，'
})

const totalSessions = computed(() => sessions.value.length)
const trainingDays = computed(() => Math.max(totalSessions.value * 2 + 4, 7))
const streakDays = ref(Number(uni.getStorageSync('daily_streak') || 7))
const doneTaskCount = computed(() => tasks.value.filter((task) => task.done).length)

const latestRisk = computed(() => {
  if (!sessions.value.length) return 'normal'
  return sessions.value[0]?.risk_level || sessions.value[0]?.status || 'normal'
})

const healthStatus = computed(() => {
  if (latestRisk.value === 'high_risk') return '关注'
  if (latestRisk.value === 'mild_risk') return '稳定'
  return '良好'
})

function toggleTask(index) {
  tasks.value[index].done = !tasks.value[index].done
}

function onDailyCheckin() {
  streakDays.value += 1
  uni.setStorageSync('daily_streak', streakDays.value)
  uni.showToast({ title: '打卡成功', icon: 'success' })
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

function goToResult() {
  if (isFamilyViewMode.value && viewingElder.value && sessions.value.length > 0) {
    // 家属查看模式：跳转到最新测评报告
    const latestSession = sessions.value[0]
    uni.navigateTo({ 
      url: `/pages/result/index?elder_id=${viewingElder.value.id}&session_id=${latestSession.id}` 
    })
  } else {
    uni.navigateTo({ url: '/pages/result/index' })
  }
}

function goToElderDetail() {
  uni.navigateTo({ url: '/pages/elder-detail/index' })
}

function goToLogin() {
  uni.navigateTo({ url: '/pages/login/index' })
}

function checkNewUser() {
  const hasVisited = uni.getStorageSync('hasVisited')
  if (!hasVisited) {
    uni.setStorageSync('hasVisited', 'true')
    uni.setStorageSync('daily_streak', '0')
    uni.setStorageSync('completedCourses', JSON.stringify({}))
    uni.setStorageSync('trainingCourses', '')
  }
}

function checkFamilyViewMode() {
  const familyViewMode = uni.getStorageSync('family_view_mode')
  const elderStr = uni.getStorageSync('viewing_elder')
  if (familyViewMode === 'true' && elderStr) {
    isFamilyViewMode.value = true
    viewingElder.value = JSON.parse(elderStr)
    selectedElderId.value = viewingElder.value.id
  } else {
    isFamilyViewMode.value = false
    viewingElder.value = null
  }
}

async function loadElders() {
  try {
    const data = await api.getMyElders()
    elders.value = Array.isArray(data) ? data : []
    if (elders.value.length > 0 && !selectedElderId.value) {
      selectedElderId.value = elders.value[0].id
    }
  } catch (error) {
    console.warn('load elders failed', error)
    elders.value = []
  }
}

async function loadSessions() {
  checkNewUser()
  // 直接检查存储值，确保在家属查看模式下不会调用需要认证的API
  const familyViewMode = uni.getStorageSync('family_view_mode')
  if (familyViewMode === 'true' && viewingElder.value) {
    // 家属查看模式：调用公共API获取真实的老人测评数据
    try {
      const data = await api.getElderSessions(viewingElder.value.id)
      sessions.value = Array.isArray(data) ? data : []
    } catch (error) {
      console.warn('load elder sessions failed', error)
      // 使用模拟数据作为备选
      sessions.value = [
        { id: 1, created_at: new Date().toISOString(), risk_level: 'normal' },
        { id: 2, created_at: new Date(Date.now() - 86400000).toISOString(), risk_level: 'normal' },
      ]
    }
    return
  }
  try {
    const params = {}
    if (selectedElderId.value) {
      params.elder_id = selectedElderId.value
    }
    const data = await api.getSessions(params)
    const list = Array.isArray(data) ? data : (data.sessions || data.items || [])
    sessions.value = [...list].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  } catch (error) {
    console.warn('load sessions failed', error)
    sessions.value = []
  }
}

function handleElderChange(elderId) {
  selectedElderId.value = elderId
  loadSessions()
}

function exitFamilyViewMode() {
  uni.setStorageSync('family_view_mode', '')
  uni.setStorageSync('viewing_elder', '')
  isFamilyViewMode.value = false
  viewingElder.value = null
  selectedElderId.value = null
  uni.switchTab({ url: '/pages/index/index' })
}

// 家属查看模式的导航方法
function goToAiAnalysis() {
  uni.showToast({ title: 'AI分析功能开发中', icon: 'none' })
}

function goToNotifications() {
  uni.showToast({ title: '消息通知功能开发中', icon: 'none' })
}

function goToAllReports() {
  if (isFamilyViewMode.value && viewingElder.value) {
    uni.showToast({ title: '查看全部报告', icon: 'none' })
  } else {
    uni.showToast({ title: '查看全部报告', icon: 'none' })
  }
}

function goToSessionDetail(sessionId) {
  if (isFamilyViewMode.value && viewingElder.value) {
    uni.navigateTo({ 
      url: `/pages/result/index?elder_id=${viewingElder.value.id}&session_id=${sessionId}` 
    })
  } else {
    uni.showToast({ title: `查看测评详情 ${sessionId}`, icon: 'none' })
  }
}

// 辅助函数
const recentSessions = computed(() => {
  return sessions.value.slice(0, 3)
})

function formatDate(dateStr) {
  const date = new Date(dateStr)
  return {
    day: date.getDate(),
    month: `${date.getMonth() + 1}月`
  }
}

function formatTime(dateStr) {
  const date = new Date(dateStr)
  return `${date.getHours().toString().padStart(2, '0')}:${date.getMinutes().toString().padStart(2, '0')}`
}

function getRiskClass(riskLevel) {
  switch (riskLevel) {
    case 'high': return 'risk-high'
    case 'medium': return 'risk-medium'
    case 'low': return 'risk-low'
    default: return 'risk-normal'
  }
}

function getRiskText(riskLevel) {
  switch (riskLevel) {
    case 'high': return '高风险'
    case 'medium': return '中风险'
    case 'low': return '低风险'
    default: return '正常'
  }
}

onShow(() => {
  checkNewUser()
  checkFamilyViewMode()
  if (authStore.userRole === 'family' && !isFamilyViewMode.value) {
    loadElders()
  }
  loadSessions()
})

onMounted(() => {
  checkNewUser()
  checkFamilyViewMode()
  if (authStore.userRole === 'family' && !isFamilyViewMode.value) {
    loadElders()
  }
  loadSessions()
})

onReady(() => {
  uni.showShareMenu({
    withShareTicket: true,
    menus: ['shareAppMessage', 'shareTimeline'],
  })
})

onShareAppMessage(() => ({
  title: '忆守心安：社区老年认知障碍早筛与干预系统',
  path: '/pages/index/index',
}))

onShareTimeline(() => ({
  title: '忆守心安：社区老年认知障碍早筛与干预系统',
  query: '',
}))
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  padding: 0;
  background: #F5F7FA;
}

/* 家属查看模式头部 */
.family-header {
  background: linear-gradient(135deg, #4A90D9 0%, #357ABD 100%);
  padding: 60rpx 32rpx 40rpx;
  border-radius: 0 0 48rpx 48rpx;
}

.family-header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32rpx;
}

.family-info {
  color: #fff;
}

.family-title {
  font-size: 28rpx;
  opacity: 0.9;
  display: block;
}

.family-subtitle {
  font-size: 40rpx;
  font-weight: 700;
  display: block;
  margin-top: 8rpx;
}

.family-badge {
  display: flex;
  align-items: center;
  margin-top: 12rpx;
}

.badge-icon {
  font-size: 24rpx;
}

.badge-text {
  font-size: 24rpx;
  opacity: 0.9;
  margin-left: 8rpx;
}

.exit-btn {
  background: rgba(255, 255, 255, 0.2);
  padding: 12rpx 24rpx;
  border-radius: 32rpx;
}

.exit-text {
  font-size: 26rpx;
  color: #fff;
}

.elder-card-mini {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 24rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}

.elder-avatar-small {
  width: 80rpx;
  height: 80rpx;
  border-radius: 50%;
  background: linear-gradient(145deg, #d1733c, #cc5e36);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
  font-size: 36rpx;
  font-weight: 700;
}

.elder-info-mini {
  flex: 1;
  margin-left: 20rpx;
}

.elder-name-mini {
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
  display: block;
}

.elder-stats {
  display: flex;
  align-items: center;
  margin-top: 8rpx;
}

.stat-item {
  font-size: 24rpx;
  color: #999;
}

.stat-divider {
  margin: 0 12rpx;
  color: #ddd;
}

.arrow-icon {
  font-size: 40rpx;
  color: #ccc;
}

.bind-tip {
  background: rgba(255, 255, 255, 0.15);
  border: 2rpx dashed rgba(255, 255, 255, 0.4);
  border-radius: 20rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.bind-icon {
  font-size: 32rpx;
  margin-right: 12rpx;
}

.bind-text {
  font-size: 28rpx;
  color: #fff;
  font-weight: 500;
}

.bind-desc {
  background: rgba(255, 255, 255, 0.95);
  border-radius: 16rpx;
  padding: 20rpx;
  display: flex;
  align-items: flex-start;
}

.desc-icon {
  font-size: 28rpx;
  margin-right: 12rpx;
}

.desc-text {
  font-size: 24rpx;
  color: #666;
  line-height: 1.6;
}

/* 内容区域 */
.content-area {
  padding: 18rpx 24rpx 24rpx;
  background: #F5F7FA;
}

.elder-selector {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.selector-label {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 16rpx;
  display: block;
}

.elder-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.elder-item {
  padding: 16rpx 32rpx;
  background: #f5f5f5;
  border-radius: 32rpx;
  font-size: 26rpx;
  color: #666;
  transition: all 0.3s;
}

.elder-item.active {
  background: linear-gradient(145deg, #d1733c, #cc5e36);
  color: #fff;
  box-shadow: 0 4rpx 12rpx rgba(184, 101, 62, 0.3);
}

.top-nav {
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(180deg, #FFF9E8 0%, #FEF7E8 100%);
  padding: 0 24rpx;
}

.elder-selector {
  background: rgba(255, 255, 255, 0.8);
  border-radius: 20rpx;
  padding: 24rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.05);
}

.selector-label {
  font-size: 28rpx;
  color: #666;
  margin-bottom: 16rpx;
  display: block;
}

.elder-list {
  display: flex;
  flex-wrap: wrap;
  gap: 16rpx;
}

.elder-item {
  padding: 16rpx 32rpx;
  background: #f5f5f5;
  border-radius: 32rpx;
  font-size: 26rpx;
  color: #666;
  transition: all 0.3s;
}

.elder-item.active {
  background: linear-gradient(145deg, #d1733c, #cc5e36);
  color: #fff;
  box-shadow: 0 4rpx 12rpx rgba(184, 101, 62, 0.3);
}

.top-nav {
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: linear-gradient(180deg, #FFF9E8 0%, #FEF7E8 100%);
}

.brand-chip {
  width: 56rpx;
  height: 56rpx;
  border-radius: 16rpx;
  display: grid;
  place-items: center;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 800;
  background: linear-gradient(145deg, #d1733c, #cc5e36);
  box-shadow: 0 8rpx 16rpx rgba(184, 101, 62, 0.3);
}

.nav-menu {
  font-size: 56rpx;
  color: #222c36;
  font-weight: 700;
  width: 80rpx;
  height: 80rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.welcome-banner {
  margin-top: 10rpx;
  border-radius: 40rpx;
  padding: 36rpx 34rpx;
  background:
    radial-gradient(circle at 70% 15%, rgba(255, 255, 255, 0.2), transparent 40%),
    radial-gradient(circle at 10% 90%, rgba(255, 255, 255, 0.15), transparent 40%),
    linear-gradient(130deg, #f7c93d 0%, #f89453 55%, #f0788b 100%);
  box-shadow: 0 18rpx 32rpx rgba(212, 117, 90, 0.28);
}

.banner-date {
  display: block;
  color: rgba(255, 255, 255, 0.9);
  font-size: 30rpx;
}

.banner-title {
  display: block;
  margin-top: 12rpx;
  color: #ffffff;
  font-size: 56rpx;
  font-weight: 800;
}

.banner-subtitle {
  display: block;
  margin-top: 8rpx;
  color: rgba(255, 255, 255, 0.95);
  font-size: 32rpx;
}

.checkin-btn {
  margin-top: 32rpx;
  width: 240rpx;
  height: 88rpx;
  border-radius: 999rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 24rpx rgba(211, 106, 31, 0.2);
}

.checkin-icon {
  font-size: 36rpx;
  margin-right: 8rpx;
}

.checkin-text {
  font-size: 32rpx;
  font-weight: 700;
  color: #d36a1f;
  white-space: nowrap;
}

.login-card {
  margin-top: 20rpx;
  display: flex;
  align-items: center;
  background: linear-gradient(135deg, #fff8e7 0%, #fff3e0 100%);
  border-radius: 24rpx;
  padding: 24rpx 28rpx;
}

.login-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background-color: #ffb74d;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  color: #e65100;
  font-weight: bold;
}

.login-info {
  flex: 1;
  margin-left: 20rpx;
}

.login-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #333;
}

.login-desc {
  display: block;
  font-size: 26rpx;
  color: #999;
  margin-top: 4rpx;
}

.login-btn {
  background: linear-gradient(135deg, #ff8f00 0%, #ff6f00 100%);
  color: #fff;
  font-size: 28rpx;
  font-weight: 600;
  border-radius: 999rpx;
  padding: 16rpx 32rpx;
  border: none;
}

/* 统计卡片网格 */
.stats-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 24rpx;
  margin-bottom: 40rpx;
}

/* 统计卡片 - 各色背景 */
.stat-card {
  border-radius: 32rpx;
  padding: 28rpx 24rpx;
  text-align: center;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

/* 累计测评 - 紫色背景 */
.stat-card:nth-child(1) {
  background: #F5F3FF;
}

/* 训练天数 - 绿色背景 */
.stat-card:nth-child(2) {
  background: #ECFDF5;
}

/* 健康指数 - 粉色背景 */
.stat-card:nth-child(3) {
  background: #FFF1F2;
}

/* 连续打卡 - 橙色背景 */
.stat-card:nth-child(4) {
  background: #FFF7ED;
}

.stat-icon {
  font-size: 48rpx;
  display: block;
  margin-bottom: 16rpx;
}

/* 数值 - 橙色 */
.stat-value {
  font-size: 44rpx;
  font-weight: 800;
  color: #E8A74C;
  display: block;
  margin-bottom: 8rpx;
}

/* 标签 - 浅棕色/米色 */
.stat-label {
  font-size: 26rpx;
  color: #C09060;
}

.section-title {
  margin-top: 24rpx;
  display: block;
  font-size: 40rpx;
  font-weight: 800;
  color: #1d2f3c;
}

.menu-grid {
  margin-top: 16rpx;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 18rpx;
}

.menu-card {
  border-radius: 28rpx;
  background: #ffffff;
  border: 2rpx solid rgba(17, 34, 49, 0.06);
  padding: 32rpx 28rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
  display: flex;
  flex-direction: column;
  align-items: center;
}

.menu-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 20rpx;
}

.purple { background: linear-gradient(135deg, #9575cd 0%, #7e57c2 100%); }
.green { background: linear-gradient(135deg, #43a047 0%, #2e7d32 100%); }
.blue { background: linear-gradient(135deg, #1e88e5 0%, #1565c0 100%); }
.amber { background: linear-gradient(135deg, #ff8f00 0%, #f57c00 100%); }

.icon-brain, .icon-chart, .icon-user, .icon-bar {
  width: 48rpx;
  height: 48rpx;
  position: relative;
}

.icon-brain::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 3C8.696 3 6 5.696 6 9v1c0 2.76 2.24 5 5 5s5-2.24 5-5V9c0-3.304-2.696-6-6-6zm-4 10c-1.1 0-2-.9-2-2 0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.1-.9 2-2 2H8zm6 0c-1.1 0-2-.9-2-2 0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.1-.9 2-2 2h-2z'/%3E%3C/svg%3E") no-repeat center;
  background-size: 100%;
}

.icon-chart::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M18 20V10c0-2.21-1.79-4-4-4H4c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c2.21 0 4-1.79 4-4zm-6-7l3 3-3 3-3-3 3-3z'/%3E%3C/svg%3E") no-repeat center;
  background-size: 100%;
}

.icon-user::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z'/%3E%3C/svg%3E") no-repeat center;
  background-size: 100%;
}

.icon-bar::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z'/%3E%3C/svg%3E") no-repeat center;
  background-size: 100%;
}

.menu-title {
  margin-top: 4rpx;
  display: block;
  color: #172f3f;
  font-size: 38rpx;
  font-weight: 700;
  text-align: center;
}

.menu-desc {
  display: block;
  margin-top: 6rpx;
  color: #778a98;
  font-size: 28rpx;
  text-align: center;
}

.task-head {
  margin-top: 24rpx;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.task-head .section-title {
  margin-top: 0;
}

.task-progress {
  color: #6e7f8d;
  font-size: 28rpx;
}

.task-list {
  margin-top: 12rpx;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 8rpx 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.04);
}

.task-row {
  display: flex;
  align-items: center;
  padding: 24rpx 0;
  border-bottom: 2rpx solid #f0f0f0;
}

.task-row:last-child {
  border-bottom: none;
}

.task-radio {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  border: 3rpx solid #ccc;
  margin-right: 20rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-radio.checked {
  border-color: #26c6da;
  background-color: #26c6da;
}

.radio-inner {
  width: 24rpx;
  height: 24rpx;
  border-radius: 50%;
  background-color: #fff;
}

.task-text {
  flex: 1;
  color: #333;
  font-size: 34rpx;
}

.task-text.done {
  color: #999;
  text-decoration: line-through;
}

.tip-box {
  margin-top: 20rpx;
  background: #EFF9FF;
  border-radius: 24rpx;
  padding: 28rpx;
}

.tip-header {
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
}

.tip-icon {
  font-size: 36rpx;
  margin-right: 12rpx;
}

.tip-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #01579b;
}

.tip-content {
  display: block;
  color: #0288d1;
  font-size: 32rpx;
  line-height: 1.6;
}

.bottom-gap {
  height: 40rpx;
}

/* 家属查看模式样式 */
.family-view-page {
  min-height: 100vh;
  background: #F5F7FA;
}

.family-content {
  padding: 24rpx;
  margin-top: -20rpx;
}

/* 评估报告一键查询卡片 */
.quick-report-card {
  background: #fff;
  border-radius: 24rpx;
  padding: 32rpx;
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.06);
  margin-bottom: 24rpx;
}

.report-header {
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
}

.report-icon {
  font-size: 48rpx;
  margin-right: 20rpx;
}

.report-title-wrap {
  flex: 1;
}

.report-title {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
  color: #172f3f;
}

.report-desc {
  display: block;
  font-size: 26rpx;
  color: #778a98;
  margin-top: 8rpx;
}

.report-arrow {
  font-size: 48rpx;
  color: #ccc;
}

.report-stats {
  display: flex;
  justify-content: space-around;
  padding-top: 24rpx;
  border-top: 2rpx solid #f0f0f0;
}

.report-stat {
  text-align: center;
}

.report-stat-value {
  display: block;
  font-size: 48rpx;
  font-weight: 700;
  color: #4A90D9;
}

.report-stat-label {
  display: block;
  font-size: 26rpx;
  color: #778a98;
  margin-top: 8rpx;
}

.report-divider {
  width: 2rpx;
  background: #f0f0f0;
}

/* 家属功能菜单 */
.family-menu-section {
  margin-bottom: 24rpx;
}

.family-section-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #172f3f;
  margin-bottom: 20rpx;
  display: block;
}

.family-menu-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 20rpx;
}

.family-menu-card {
  background: #fff;
  border-radius: 20rpx;
  padding: 32rpx 24rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
  text-align: center;
}

.family-menu-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 20rpx;
  position: relative;
}

.family-menu-icon.report {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
}

.family-menu-icon.ai {
  background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
}

.family-menu-icon.assessment {
  background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
}

.family-menu-icon.notification {
  background: linear-gradient(135deg, #43e97b 0%, #38f9d7 100%);
}

.icon-text {
  font-size: 44rpx;
}

.notification-badge {
  position: absolute;
  top: -8rpx;
  right: -8rpx;
  background: #ff4757;
  color: #fff;
  font-size: 22rpx;
  padding: 4rpx 12rpx;
  border-radius: 20rpx;
  min-width: 36rpx;
  text-align: center;
}

.family-menu-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #172f3f;
}

.family-menu-desc {
  display: block;
  font-size: 24rpx;
  color: #778a98;
  margin-top: 8rpx;
}

/* 最近测评记录 */
.family-history-section {
  background: #fff;
  border-radius: 24rpx;
  padding: 28rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.history-more {
  font-size: 28rpx;
  color: #4A90D9;
}

.history-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.history-item {
  display: flex;
  align-items: center;
  padding: 20rpx 0;
  border-bottom: 2rpx solid #f5f5f5;
}

.history-item:last-child {
  border-bottom: none;
}

.history-date {
  width: 80rpx;
  text-align: center;
}

.date-day {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #172f3f;
}

.date-month {
  display: block;
  font-size: 24rpx;
  color: #778a98;
}

.history-info {
  flex: 1;
  margin-left: 24rpx;
}

.history-title {
  display: block;
  font-size: 32rpx;
  font-weight: 600;
  color: #172f3f;
}

.history-time {
  display: block;
  font-size: 26rpx;
  color: #778a98;
  margin-top: 8rpx;
}

.history-result {
  padding: 12rpx 24rpx;
  border-radius: 32rpx;
  font-size: 26rpx;
}

.history-result.risk-normal {
  background: #E8F5E9;
  color: #2E7D32;
}

.history-result.risk-low {
  background: #E3F2FD;
  color: #1976D2;
}

.history-result.risk-medium {
  background: #FFF3E0;
  color: #F57C00;
}

.history-result.risk-high {
  background: #FFEBEE;
  color: #C62828;
}

.result-text {
  font-weight: 600;
}
</style>
