<template>
  <view class="start-page">
    <!-- Title Area -->
    <view class="title-area">
      <text class="brain-icon">🧠</text>
      <text class="page-title">认知评估说明</text>
      <text class="page-subtitle">请仔细阅读以下内容，做好准备再开始</text>
    </view>

    <!-- Instruction List -->
    <view class="card">
      <text class="card-title">📋 评估内容</text>
      <view class="instruction-list">
        <view v-for="item in instructions" :key="item.number" class="instruction-item">
          <view class="number-badge">
            <text class="number-text">{{ item.number }}</text>
          </view>
          <view class="instruction-content">
            <text class="instruction-title">{{ item.title }}</text>
            <text class="instruction-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- Preparation Checklist -->
    <view class="card">
      <text class="card-title">✅ 开始前准备</text>
      <text class="checklist-hint">请勾选以下准备事项</text>
      <view class="checklist">
        <view
          v-for="(item, index) in checklist"
          :key="index"
          class="check-item"
          @tap="() => toggleCheck(index)"
        >
          <view class="check-box" :class="{ checked: item.checked }">
            <text v-if="item.checked" class="check-mark">✓</text>
          </view>
          <text class="check-text">{{ item.text }}</text>
        </view>
      </view>
    </view>

    <!-- Tips Box -->
    <view class="tips-box">
      <text class="tips-icon">💡</text>
      <view class="tips-content">
        <text class="tips-title">小提示</text>
        <text class="tips-text">评估过程中请保持安静，如有疑问可随时退出，结果仅供参考，不能代替医生诊断。</text>
      </view>
    </view>

    <!-- Start Button -->
    <view class="bottom-area">
      <view class="progress-info">
        <text class="progress-text">已准备 {{ checkedCount }}/{{ checklist.length }} 项</text>
        <view class="progress-bar">
          <view
            class="progress-fill"
            :style="{ width: (checkedCount / checklist.length * 100) + '%' }"
          />
        </view>
      </view>

      <button
        class="btn-start"
        :loading="loading"
        :disabled="loading"
        @tap="handleStart"
      >
        <text v-if="!loading">开始评估</text>
        <text v-else>准备中...</text>
      </button>

      <button class="btn-back" @tap="goBack">返回首页</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed } from 'vue'
import { useAssessmentStore } from '../../../store/assessment'
import { api } from '../../../utils/request'

const assessmentStore = useAssessmentStore()
const loading = ref(false)

// Instruction items
const instructions = [
  {
    number: 1,
    title: '共15道题目',
    desc: '包含记忆力、定向力、注意力等多个认知维度'
  },
  {
    number: 2,
    title: '约10-15分钟',
    desc: '请在不受打扰的情况下完成全部题目'
  },
  {
    number: 3,
    title: '多种题型',
    desc: '包含选择题、语音朗读、手写时钟等丰富题型'
  },
  {
    number: 4,
    title: '安静环境最佳',
    desc: '语音题目需要录音，请在安静的房间内完成'
  },
  {
    number: 5,
    title: 'AI智能分析',
    desc: '完成后AI系统将自动分析，约1-2分钟出结果'
  }
]

// Preparation checklist
const checklist = ref([
  { text: '我已在安静的环境中', checked: false },
  { text: '我戴上了助听器（如需要）', checked: false },
  { text: '我戴上了眼镜（如需要）', checked: false },
  { text: '我的手机有足够的电量', checked: false }
])

const checkedCount = computed(() => checklist.value.filter(item => item.checked).length)

function toggleCheck(index) {
  checklist.value[index].checked = !checklist.value[index].checked
}

function goBack() {
  uni.switchTab({ url: '/pages/index/index' })
}

async function handleStart() {
  loading.value = true

  try {
    // Reset any previous assessment
    assessmentStore.reset()

    // Create a new session on the backend
    const sessionData = await api.createSession()
    const sessionId = sessionData.id || sessionData.session_id

    if (!sessionId) {
      throw new Error('创建评估会话失败，请重试')
    }

    // Load questions for this session
    const questionsData = await api.getQuestions(sessionId)
    const questions = Array.isArray(questionsData) ? questionsData : (questionsData.questions || [])

    if (questions.length === 0) {
      throw new Error('暂无可用的评估题目，请联系工作人员')
    }

    // Initialize store
    assessmentStore.startSession(sessionId)
    assessmentStore.setQuestions(questions)

    wx.showToast({
      title: '准备完成！',
      icon: 'success',
      duration: 800
    })

    setTimeout(() => {
      uni.navigateTo({ url: '/pages/assessment/question/index' })
    }, 800)
  } catch (err) {
    console.error('Start assessment error:', err)
    wx.showModal({
      title: '无法开始评估',
      content: err.message || '网络异常，请检查网络连接后重试',
      showCancel: false,
      confirmText: '知道了',
      confirmColor: '#4A90D9'
    })
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.start-page {
  min-height: 100vh;
  background: #F0F4F8;
  padding-bottom: 40rpx;
}

/* Title Area */
.title-area {
  background: linear-gradient(135deg, #4A90D9, #2c6fad);
  padding: 50rpx 30rpx 60rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.brain-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
}

.page-title {
  font-size: 50rpx;
  font-weight: bold;
  color: #ffffff;
  margin-bottom: 16rpx;
}

.page-subtitle {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.85);
}

/* Card */
.card {
  background: #ffffff;
  border-radius: 20rpx;
  margin: 20rpx 30rpx 0;
  padding: 36rpx 30rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.card-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
  display: block;
  margin-bottom: 28rpx;
}

/* Instruction List */
.instruction-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.instruction-item {
  display: flex;
  align-items: flex-start;
  gap: 20rpx;
}

.number-badge {
  width: 56rpx;
  height: 56rpx;
  background: #4A90D9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.number-text {
  font-size: 28rpx;
  font-weight: bold;
  color: #ffffff;
}

.instruction-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.instruction-title {
  font-size: 34rpx;
  font-weight: bold;
  color: #333333;
  margin-bottom: 6rpx;
}

.instruction-desc {
  font-size: 28rpx;
  color: #888888;
  line-height: 1.5;
}

/* Checklist */
.checklist-hint {
  font-size: 28rpx;
  color: #888888;
  display: block;
  margin-bottom: 20rpx;
}

.checklist {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.check-item {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 20rpx 24rpx;
  background: #F8F9FA;
  border-radius: 16rpx;
  border: 2rpx solid #E8E8E8;
  transition: all 0.2s;
}

.check-item:active {
  opacity: 0.7;
}

.check-box {
  width: 56rpx;
  height: 56rpx;
  border-radius: 12rpx;
  border: 3rpx solid #CCCCCC;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.2s;
}

.check-box.checked {
  background: #52C41A;
  border-color: #52C41A;
}

.check-mark {
  font-size: 32rpx;
  color: #ffffff;
  font-weight: bold;
}

.check-text {
  font-size: 34rpx;
  color: #333333;
  flex: 1;
}

/* Tips Box */
.tips-box {
  background: #FFF7E6;
  border: 2rpx solid #FFD591;
  border-radius: 16rpx;
  margin: 20rpx 30rpx 0;
  padding: 24rpx;
  display: flex;
  gap: 16rpx;
}

.tips-icon {
  font-size: 36rpx;
  flex-shrink: 0;
}

.tips-content {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.tips-title {
  font-size: 30rpx;
  font-weight: bold;
  color: #AD6800;
  margin-bottom: 8rpx;
}

.tips-text {
  font-size: 28rpx;
  color: #875500;
  line-height: 1.6;
}

/* Bottom Area */
.bottom-area {
  margin: 30rpx 30rpx 0;
}

.progress-info {
  margin-bottom: 24rpx;
}

.progress-text {
  font-size: 28rpx;
  color: #666666;
  display: block;
  margin-bottom: 12rpx;
}

.progress-bar {
  height: 12rpx;
  background: #E8E8E8;
  border-radius: 6rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #52C41A, #389E0D);
  border-radius: 6rpx;
  transition: width 0.3s ease;
}

/* Buttons */
.btn-start {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #52C41A, #389E0D);
  color: #ffffff;
  font-size: 42rpx;
  font-weight: bold;
  border-radius: 50rpx;
  border: none;
  margin-bottom: 20rpx;
  box-shadow: 0 8rpx 24rpx rgba(82, 196, 26, 0.4);
  letter-spacing: 4rpx;
}

.btn-start[disabled] {
  background: #B7EB8F;
  box-shadow: none;
}

.btn-back {
  width: 100%;
  height: 88rpx;
  background: #ffffff;
  color: #4A90D9;
  font-size: 34rpx;
  border: 2rpx solid #4A90D9;
  border-radius: 44rpx;
}
</style>
