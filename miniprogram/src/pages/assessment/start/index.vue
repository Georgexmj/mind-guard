<template>
  <view class="assessment-page">
    <view class="top-nav">
      <view class="brand-chip">智</view>
      <view class="nav-menu" @click="showMenu">≡</view>
    </view>

    <view class="hero-banner">
      <text class="hero-title">认知测评</text>
      <text class="hero-subtitle">科学评估认知健康，早发现早干预</text>
      <view class="tag-list">
        <view class="tag">
          <text class="tag-icon">🔬</text>
          <text class="tag-text">科学专业</text>
        </view>
        <view class="tag">
          <text class="tag-icon">⚡</text>
          <text class="tag-text">辅助评估</text>
        </view>
        <view class="tag">
          <text class="tag-icon">🎯</text>
          <text class="tag-text">综合参考</text>
        </view>
      </view>
    </view>

    <view class="ai-card" @tap="goToAssessment">
      <view class="ai-icon">
        <view class="star-icon"></view>
      </view>
      <view class="ai-content">
        <view class="ai-header">
          <text class="ai-title">多维综合评估</text>
          <view class="recommend-badge">强烈推荐</view>
        </view>
        <text class="ai-desc">结合语音、绘图与答题表现进行综合评估，结果更便于参考</text>
        <view class="ai-meta">
          <view class="meta-item">
            <text class="meta-icon">⏱️</text>
            <text class="meta-text">约15分钟</text>
          </view>
          <view class="meta-item">
            <text class="meta-icon">📋</text>
            <text class="meta-text">4项任务</text>
          </view>
          <view class="meta-item">
            <text class="meta-icon">🧠</text>
            <text class="meta-text">结果说明</text>
          </view>
        </view>
      </view>
      <view class="ai-arrow">›</view>
    </view>

    <view class="section-title">
      <text class="section-icon">🛡️</text>
      <text class="section-text">传统量表评估</text>
    </view>

    <view class="scale-list">
      <view class="scale-card mmse-card">
        <view class="scale-icon blue">
          <view class="brain-icon"></view>
        </view>
        <view class="scale-info">
          <text class="scale-title">MMSE认知量表</text>
          <text class="scale-desc">简易智能精神状态检查量表，用于快速评估认知功能</text>
          <view class="scale-meta">
            <view class="meta-item">
              <text class="meta-icon">⏱️</text>
              <text class="meta-text">约10分钟</text>
            </view>
            <view class="meta-item">
              <text class="meta-icon">📝</text>
              <text class="meta-text">5道题</text>
            </view>
          </view>
        </view>
        <view class="scale-start-btn" @tap="startScale('mmse')">
          <text class="start-icon">▶</text>
          <text class="start-text">开始</text>
        </view>
      </view>

      <view class="scale-card moca-card">
        <view class="scale-icon green">
          <view class="brain-icon"></view>
        </view>
        <view class="scale-info">
          <text class="scale-title">MoCA认知评估</text>
          <text class="scale-desc">蒙特利尔认知评估量表，用于检测轻度认知障碍</text>
          <view class="scale-meta">
            <view class="meta-item">
              <text class="meta-icon">⏱️</text>
              <text class="meta-text">约10分钟</text>
            </view>
            <view class="meta-item">
              <text class="meta-icon">📝</text>
              <text class="meta-text">5道题</text>
            </view>
          </view>
        </view>
        <view class="scale-start-btn" @tap="startScale('moca')">
          <text class="start-icon">▶</text>
          <text class="start-text">开始</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAssessmentStore } from '../../../store/assessment'
import { useAuthStore } from '../../../store/auth'
import { api } from '../../../utils/request'

const assessmentStore = useAssessmentStore()
const authStore = useAuthStore()
const loading = ref(false)
const resumableSession = ref(null)

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

function goToAssessment() {
  uni.navigateTo({ url: '/pages/assessment/question/index' })
}

function startScale(scaleType) {
  const scaleInfo = {
    mmse: { name: 'MMSE认知量表', duration: '约10分钟', questions: 5 },
    moca: { name: 'MoCA认知评估', duration: '约10分钟', questions: 5 },
  }
  
  uni.showToast({ 
    title: `即将开始${scaleInfo[scaleType].name}`, 
    icon: 'none',
    duration: 1500 
  })
  
  setTimeout(() => {
    uni.navigateTo({ url: `/pages/assessment/question/index?scale=${scaleType}` })
  }, 1500)
}

async function detectResumableSession() {
  try {
    const sessions = await api.getSessions()
    if (!Array.isArray(sessions)) {
      resumableSession.value = null
      return
    }
    const latest = sessions.find(
      (session) =>
        session &&
        (session.status === 'in_progress' || (session.status === 'pending' && session.is_resumable !== false))
    )
    resumableSession.value = latest || null
  } catch (err) {
    console.warn('Detect resumable session failed:', err)
    resumableSession.value = null
  }
}

onMounted(() => {
  detectResumableSession()
})
</script>

<style scoped>
.assessment-page {
  min-height: 100vh;
  padding: 0 24rpx 40rpx;
  background: linear-gradient(180deg, #FFF9E8 0%, #FEF7E8 30%, #FEF7E8 100%);
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 60rpx 0 20rpx;
}

.brand-chip {
  width: 80rpx;
  height: 80rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #d36a1f, #f59e0b);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 36rpx;
  font-weight: 800;
}

.nav-menu {
  font-size: 48rpx;
  color: #1d2f3c;
  font-weight: 300;
}

.hero-banner {
  margin-top: 16rpx;
  border-radius: 36rpx;
  padding: 40rpx 32rpx;
  background:
    radial-gradient(circle at 85% 10%, rgba(255, 255, 255, 0.3), transparent 50%),
    linear-gradient(145deg, #9575cd, #6366f1);
  position: relative;
  overflow: hidden;
}

.hero-banner::after {
  content: '';
  position: absolute;
  top: -30%;
  right: -20%;
  width: 300rpx;
  height: 300rpx;
  border-radius: 50%;
  background: rgba(255, 255, 255, 0.15);
}

.hero-title {
  display: block;
  font-size: 56rpx;
  color: #ffffff;
  font-weight: 800;
}

.hero-subtitle {
  display: block;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.88);
  margin-top: 12rpx;
}

.tag-list {
  margin-top: 24rpx;
  display: flex;
  gap: 16rpx;
}

.tag {
  display: flex;
  align-items: center;
  gap: 6rpx;
  padding: 12rpx 20rpx;
  background: rgba(255, 255, 255, 0.2);
  border-radius: 999rpx;
}

.tag-icon {
  font-size: 24rpx;
}

.tag-text {
  font-size: 24rpx;
  color: #ffffff;
  font-weight: 500;
}

.ai-card {
  margin-top: 24rpx;
  border-radius: 28rpx;
  padding: 28rpx;
  background: #ffffff;
  border: 2rpx solid rgba(149, 117, 205, 0.15);
  box-shadow: 0 4rpx 16rpx rgba(149, 117, 205, 0.08);
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.ai-icon {
  width: 100rpx;
  height: 100rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #9575cd, #7e57c2);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.star-icon {
  width: 52rpx;
  height: 52rpx;
  position: relative;
}

.star-icon::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z'/%3E%3C/svg%3E") no-repeat center;
  background-size: 100%;
}

.ai-content {
  flex: 1;
  min-width: 0;
}

.ai-header {
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.ai-title {
  font-size: 36rpx;
  color: #1a2f3f;
  font-weight: 700;
}

.recommend-badge {
  padding: 4rpx 14rpx;
  background: linear-gradient(135deg, #9575cd, #7e57c2);
  border-radius: 999rpx;
  font-size: 22rpx;
  color: #ffffff;
  font-weight: 600;
}

.ai-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: #6b7c8e;
  line-height: 1.5;
}

.ai-meta {
  margin-top: 14rpx;
  display: flex;
  gap: 24rpx;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.meta-icon {
  font-size: 24rpx;
}

.meta-text {
  font-size: 24rpx;
  color: #8a9ba8;
}

.ai-arrow {
  font-size: 48rpx;
  color: #c4cdd5;
  flex-shrink: 0;
}

.section-title {
  margin-top: 32rpx;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.section-icon {
  font-size: 32rpx;
}

.section-text {
  font-size: 34rpx;
  color: #1e3342;
  font-weight: 700;
}

.empty-state {
  margin-top: 16rpx;
  border-radius: 24rpx;
  padding: 60rpx 24rpx;
  background: #f8fafc;
  border: 2rpx dashed #d1d9e0;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.empty-icon {
  font-size: 80rpx;
  opacity: 0.4;
}

.empty-text {
  margin-top: 16rpx;
  font-size: 30rpx;
  color: #8a9ba8;
}

.scale-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.scale-card {
  border-radius: 24rpx;
  padding: 24rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.scale-card.mmse-card {
  border: 2rpx solid #3b82f6;
}

.scale-card.moca-card {
  border: 2rpx solid #22c55e;
}

.scale-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.scale-icon.blue {
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
}

.scale-icon.green {
  background: linear-gradient(135deg, #22c55e, #15803d);
}

.brain-icon {
  width: 52rpx;
  height: 52rpx;
  position: relative;
}

.brain-icon::before {
  content: '';
  position: absolute;
  width: 100%;
  height: 100%;
  background: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M12 3C8.696 3 6 5.696 6 9v1c0 2.76 2.24 5 5 5s5-2.24 5-5V9c0-3.304-2.696-6-6-6zm-4 10c-1.1 0-2-.9-2-2 0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.1-.9 2-2 2H8zm6 0c-1.1 0-2-.9-2-2 0-2.21 1.79-4 4-4s4 1.79 4 4c0 1.1-.9 2-2 2h-2z'/%3E%3C/svg%3E") no-repeat center;
  background-size: 100%;
}

.scale-info {
  flex: 1;
  min-width: 0;
}

.scale-title {
  display: block;
  font-size: 34rpx;
  color: #1a2f3f;
  font-weight: 700;
}

.scale-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 26rpx;
  color: #6b7c8e;
  line-height: 1.5;
}

.scale-meta {
  margin-top: 12rpx;
  display: flex;
  gap: 20rpx;
}

.scale-meta .meta-item {
  display: flex;
  align-items: center;
  gap: 6rpx;
}

.scale-meta .meta-icon {
  font-size: 24rpx;
}

.scale-meta .meta-text {
  font-size: 24rpx;
  color: #8a9ba8;
}

.scale-start-btn {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  background: #f5f9fc;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.start-icon {
  font-size: 28rpx;
  color: #6b7c8e;
  font-weight: bold;
}

.start-text {
  font-size: 22rpx;
  color: #8a9ba8;
  margin-top: 4rpx;
}
</style>
