<template>
  <view class="home-page">
    <view class="top-nav">
      <view class="brand-chip">智</view>
      <text class="nav-menu">☰</text>
    </view>

    <view class="welcome-banner">
      <text class="banner-date">{{ todayStr }}</text>
      <text class="banner-title">下午好，{{ authStore.userName || '长者' }} 👋</text>
      <text class="banner-subtitle">今天也要保持好心情，照顾好自己</text>
      <button class="checkin-btn" @tap="onDailyCheckin">🔥 每日打卡</button>
    </view>

    <view class="stats-grid">
      <view class="stat-card lilac">
        <text class="stat-icon">🧠</text>
        <text class="stat-value">{{ totalSessions }}次</text>
        <text class="stat-label">累计测评</text>
      </view>
      <view class="stat-card mint">
        <text class="stat-icon">📈</text>
        <text class="stat-value">{{ trainingDays }}天</text>
        <text class="stat-label">训练天数</text>
      </view>
      <view class="stat-card blush">
        <text class="stat-icon">💗</text>
        <text class="stat-value">{{ healthStatus }}</text>
        <text class="stat-label">健康指数</text>
      </view>
      <view class="stat-card cream">
        <text class="stat-icon">🔥</text>
        <text class="stat-value">{{ streakDays }}天</text>
        <text class="stat-label">连续打卡</text>
      </view>
    </view>

    <view class="section-title">功能菜单</view>
    <view class="menu-grid">
      <view class="menu-card" @tap="goToAssessment">
        <view class="menu-icon purple">🧠</view>
        <text class="menu-title">认知测评</text>
        <text class="menu-desc">了解认知状况</text>
      </view>
      <view class="menu-card" @tap="goToInterventionTop5">
        <view class="menu-icon green">📈</view>
        <text class="menu-title">康复训练</text>
        <text class="menu-desc">脑力锻炼计划</text>
      </view>
      <view class="menu-card" @tap="goToProfile">
        <view class="menu-icon blue">👤</view>
        <text class="menu-title">个人中心</text>
        <text class="menu-desc">查看个人信息</text>
      </view>
      <view class="menu-card" @tap="goToProfile">
        <view class="menu-icon amber">📊</view>
        <text class="menu-title">健康报告</text>
        <text class="menu-desc">健康数据分析</text>
      </view>
    </view>

    <view class="task-head">
      <text class="section-title">今日任务</text>
      <text class="task-progress">{{ doneTaskCount }}/{{ tasks.length }} 完成</text>
    </view>
    <view class="mg-card task-list">
      <view v-for="(task, index) in tasks" :key="task.id" class="task-row" @tap="toggleTask(index)">
        <view class="task-dot" :class="{ done: task.done }">{{ task.done ? '✓' : '' }}</view>
        <text class="task-text" :class="{ done: task.done }">{{ task.title }}</text>
      </view>
    </view>

    <view class="mg-card tip-box">
      <text class="tip-title">🔔 今日健康贴士</text>
      <text class="tip-content">{{ todayTip }}</text>
    </view>

    <view class="bottom-gap" />
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '../../store/auth'
import { api } from '../../utils/request'

const authStore = useAuthStore()
const sessions = ref([])

const tasks = ref([
  { id: 1, title: '完成认知测评', done: false },
  { id: 2, title: '进行康复训练', done: false },
  { id: 3, title: '和心灵小导师聊天', done: false },
])

const tipPool = [
  '做些手工或绘画，动手活动能有效刺激大脑，延缓老化。',
  '每天坚持 30 分钟轻运动，能改善注意力和睡眠质量。',
  '和家人朋友多交流，社交活动有助于维持认知活跃。',
]

const todayTip = computed(() => tipPool[new Date().getDate() % tipPool.length])

const todayStr = computed(() => {
  const now = new Date()
  const weeks = ['日', '一', '二', '三', '四', '五', '六']
  return `${now.getMonth() + 1}月${now.getDate()}日 星期${weeks[now.getDay()]}`
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

async function loadSessions() {
  try {
    const data = await api.getSessions()
    const list = Array.isArray(data) ? data : (data.sessions || data.items || [])
    sessions.value = [...list].sort((a, b) => new Date(b.created_at).getTime() - new Date(a.created_at).getTime())
  } catch (error) {
    console.warn('load sessions failed', error)
    sessions.value = []
  }
}

onShow(() => {
  if (!authStore.enforceElderRole()) return
  loadSessions()
})

onMounted(() => {
  if (!authStore.enforceElderRole()) return
  loadSessions()
})
</script>

<style scoped>
.home-page {
  min-height: 100vh;
  padding: 18rpx 24rpx 24rpx;
}

.top-nav {
  height: 88rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
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
}

.welcome-banner {
  margin-top: 10rpx;
  border-radius: 40rpx;
  padding: 30rpx 34rpx;
  background:
    radial-gradient(circle at 84% 20%, rgba(255, 255, 255, 0.18), transparent 35%),
    radial-gradient(circle at 10% 90%, rgba(255, 255, 255, 0.2), transparent 40%),
    linear-gradient(130deg, #f7c93d 0%, #f89453 55%, #f0788b 100%);
  box-shadow: 0 18rpx 32rpx rgba(212, 117, 90, 0.28);
}

.banner-date {
  display: block;
  color: rgba(255, 255, 255, 0.9);
  font-size: 32rpx;
}

.banner-title {
  display: block;
  margin-top: 6rpx;
  color: #ffffff;
  font-size: 58rpx;
  font-weight: 800;
}

.banner-subtitle {
  display: block;
  margin-top: 6rpx;
  color: rgba(255, 255, 255, 0.95);
  font-size: 33rpx;
}

.checkin-btn {
  margin-top: 18rpx;
  width: 220rpx;
  min-height: 82rpx;
  border-radius: 999rpx;
  font-size: 33rpx;
  font-weight: 700;
  background: #ffffff;
  color: #d36a1f;
  border: none;
}

.stats-grid {
  margin-top: 18rpx;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14rpx;
}

.stat-card {
  border-radius: 24rpx;
  padding: 20rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.7);
  box-shadow: 0 10rpx 20rpx rgba(17, 34, 49, 0.06);
}

.lilac { background: #f2f0ff; }
.mint { background: #e8f9f2; }
.blush { background: #fff0f5; }
.cream { background: #fff8ed; }

.stat-icon {
  display: block;
  font-size: 36rpx;
}

.stat-value {
  display: block;
  margin-top: 2rpx;
  color: #162f40;
  font-size: 48rpx;
  font-weight: 800;
}

.stat-label {
  display: block;
  margin-top: 2rpx;
  color: #687c8a;
  font-size: 28rpx;
}

.section-title {
  margin-top: 18rpx;
  display: block;
  font-size: 40rpx;
  font-weight: 800;
  color: #1d2f3c;
}

.menu-grid {
  margin-top: 14rpx;
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14rpx;
}

.menu-card {
  border-radius: 24rpx;
  background: rgba(255, 255, 255, 0.95);
  border: 2rpx solid rgba(17, 34, 49, 0.08);
  padding: 24rpx;
  box-shadow: 0 8rpx 18rpx rgba(17, 34, 49, 0.06);
}

.menu-icon {
  width: 76rpx;
  height: 76rpx;
  border-radius: 22rpx;
  display: grid;
  place-items: center;
  color: #fff;
  font-size: 40rpx;
}

.purple { background: linear-gradient(135deg, #9147ff, #6f43f3); }
.green { background: linear-gradient(135deg, #1ec68a, #0ea768); }
.blue { background: linear-gradient(135deg, #2b9cf3, #1f7de0); }
.amber { background: linear-gradient(135deg, #ffad1f, #f28d12); }

.menu-title {
  margin-top: 14rpx;
  display: block;
  color: #172f3f;
  font-size: 42rpx;
  font-weight: 800;
}

.menu-desc {
  display: block;
  margin-top: 4rpx;
  color: #778a98;
  font-size: 29rpx;
}

.task-head {
  margin-top: 18rpx;
  display: flex;
  align-items: baseline;
  justify-content: space-between;
}

.task-head .section-title {
  margin-top: 0;
}

.task-progress {
  color: #6e7f8d;
  font-size: 30rpx;
}

.task-list {
  margin-top: 10rpx;
  overflow: hidden;
}

.task-row {
  padding: 20rpx;
  border-bottom: 2rpx solid rgba(17, 34, 49, 0.06);
  display: flex;
  align-items: center;
  gap: 14rpx;
}

.task-row:last-child {
  border-bottom: none;
}

.task-dot {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  border: 3rpx solid #8ea1af;
  color: #ffffff;
  display: grid;
  place-items: center;
  font-size: 25rpx;
}

.task-dot.done {
  background: #1ebd77;
  border-color: #1ebd77;
}

.task-text {
  color: #1f3341;
  font-size: 36rpx;
}

.task-text.done {
  color: #7e909e;
  text-decoration: line-through;
}

.tip-box {
  margin-top: 14rpx;
  padding: 24rpx;
  background: linear-gradient(135deg, #eaf8ff, #d9f0ff);
  border-color: rgba(66, 171, 220, 0.24);
}

.tip-title {
  display: block;
  color: #1f6e95;
  font-size: 36rpx;
  font-weight: 800;
}

.tip-content {
  margin-top: 8rpx;
  display: block;
  color: #416b82;
  font-size: 31rpx;
  line-height: 1.7;
}

.bottom-gap {
  height: 36rpx;
}
</style>

