<template>
  <view class="question-page">
    <!-- Progress Header -->
    <view class="progress-header">
      <view class="progress-info">
        <text class="progress-num">第 {{ currentIndex + 1 }} 题</text>
        <text class="progress-total">共 {{ totalQuestions }} 题</text>
      </view>
      <view class="progress-bar-wrap">
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: progressPercent + '%' }" />
        </view>
        <text class="progress-pct">{{ progressPercent }}%</text>
      </view>
    </view>

    <!-- Question Card -->
    <view v-if="currentQuestion" class="question-card">
      <!-- Domain Badge -->
      <view class="domain-badge" :style="{ backgroundColor: domainColor }">
        <text class="domain-icon">{{ domainIcon }}</text>
        <text class="domain-name">{{ domainName }}</text>
      </view>

      <!-- Question Text -->
      <text class="question-text">{{ currentQuestion.content }}</text>

      <!-- CHOICE TYPE -->
      <view v-if="isChoiceType" class="options-list">
        <view
          v-for="(option, idx) in currentQuestion.options"
          :key="idx"
          class="option-btn"
          :class="{
            selected: selectedOption === idx,
            correct: showFeedback && selectedOption === idx && !wrongAnswer,
            wrong: showFeedback && selectedOption === idx && wrongAnswer
          }"
          @tap="() => selectOption(idx, option)"
        >
          <view class="option-label-circle">
            <text class="option-label">{{ optionLabels[idx] }}</text>
          </view>
          <text class="option-text">{{ option }}</text>
          <text v-if="showFeedback && selectedOption === idx" class="option-indicator">
            {{ wrongAnswer ? '✗' : '✓' }}
          </text>
        </view>
      </view>

      <!-- SCALE TYPE (slider 0-10) -->
      <view v-else-if="isScaleType" class="scale-area">
        <view class="scale-display">
          <text class="scale-value">{{ scaleValue }}</text>
          <text class="scale-unit">/ 10 分</text>
        </view>
        <slider
          class="scale-slider"
          :min="0"
          :max="10"
          :step="1"
          :value="scaleValue"
          activeColor="#4A90D9"
          backgroundColor="#E0E0E0"
          block-size="44"
          @change="onSliderChange"
        />
        <view class="scale-labels">
          <text class="scale-label-left">完全不符合</text>
          <text class="scale-label-right">完全符合</text>
        </view>

        <button class="btn-next" @tap="submitScaleAnswer">确认并继续</button>
      </view>

      <!-- VOICE TYPE -->
      <view v-else-if="isVoiceType" class="task-area">
        <view class="task-hint-box task-hint-voice">
          <text class="task-hint-icon">🎤</text>
          <text class="task-hint-text">请点击下方按钮，录制您的语音回答</text>
        </view>
        <view v-if="voiceAnswered" class="answered-badge">
          <text class="answered-icon">✓</text>
          <text class="answered-text">语音已录制</text>
        </view>
        <button class="btn-task btn-voice" @tap="goToVoiceTask">
          {{ voiceAnswered ? '重新录音' : '点击录音' }}
        </button>
        <button
          v-if="voiceAnswered"
          class="btn-next"
          @tap="advanceOrComplete"
        >下一题</button>
      </view>

      <!-- DRAWING TYPE -->
      <view v-else-if="isDrawingType" class="task-area">
        <view class="task-hint-box task-hint-draw">
          <text class="task-hint-icon">✏️</text>
          <text class="task-hint-text">请点击下方按钮，在画布上绘制时钟</text>
        </view>
        <view v-if="drawingAnswered" class="answered-badge">
          <text class="answered-icon">✓</text>
          <text class="answered-text">时钟已绘制</text>
        </view>
        <button class="btn-task btn-draw" @tap="goToClockDraw">
          {{ drawingAnswered ? '重新绘制' : '开始绘制时钟' }}
        </button>
        <button
          v-if="drawingAnswered"
          class="btn-next"
          @tap="advanceOrComplete"
        >下一题</button>
      </view>

      <!-- TEXT INPUT TYPE -->
      <view v-else-if="isTextType" class="text-area">
        <textarea
          v-model="textAnswer"
          class="text-input"
          placeholder="请在此输入您的答案..."
          placeholder-class="text-placeholder"
          :maxlength="500"
          auto-height
        />
        <button
          class="btn-next"
          :disabled="!textAnswer.trim()"
          @tap="submitTextAnswer"
        >确认并继续</button>
      </view>

      <!-- UNKNOWN TYPE FALLBACK -->
      <view v-else class="task-area">
        <text class="unknown-type">题目类型：{{ currentQuestion.q_type }}</text>
        <button class="btn-next" @tap="advanceQuestion">跳过</button>
      </view>
    </view>

    <!-- Loading State -->
    <view v-else class="loading-state">
      <text class="loading-icon">⏳</text>
      <text class="loading-text">题目加载中...</text>
    </view>

    <!-- Exit Confirm Button (small, top right handled by nav bar back) -->
    <view class="exit-row">
      <text class="exit-text" @tap="confirmExit">退出评估</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAssessmentStore } from '../../../store/assessment'
import { api } from '../../../utils/request'

const assessmentStore = useAssessmentStore()

// State
const selectedOption = ref(null)
const showFeedback = ref(false)
const wrongAnswer = ref(false)
const scaleValue = ref(5)
const textAnswer = ref('')
const voiceAnswered = ref(false)
const drawingAnswered = ref(false)
const submitting = ref(false)

const optionLabels = ['A', 'B', 'C', 'D']

// Computed from store
const currentQuestion = computed(() => assessmentStore.currentQuestion)
const currentIndex = computed(() => assessmentStore.currentQuestionIndex)
const totalQuestions = computed(() => assessmentStore.totalQuestions)
const isLastQuestion = computed(() => assessmentStore.isLastQuestion)

const progressPercent = computed(() => {
  if (totalQuestions.value === 0) return 0
  return Math.round((currentIndex.value / totalQuestions.value) * 100)
})

// Question type helpers
const qType = computed(() => {
  const q = currentQuestion.value
  if (!q) return ''
  return (q.q_type || '').toLowerCase()
})

const isChoiceType = computed(() => qType.value === 'choice')
const isScaleType = computed(() => qType.value === 'scale')
const isVoiceType = computed(() => qType.value === 'voice')
const isDrawingType = computed(() => qType.value === 'drawing')
const isTextType = computed(() => qType.value === 'text')

// Domain display
const domainMap = {
  memory: { name: '记忆力', icon: '💭', color: '#722ED1' },
  orientation: { name: '定向力', icon: '🧭', color: '#1890FF' },
  attention: { name: '注意力', icon: '🎯', color: '#FA8C16' },
  language: { name: '语言能力', icon: '💬', color: '#52C41A' },
  visuospatial: { name: '视空间', icon: '🗺️', color: '#13C2C2' },
  executive: { name: '执行功能', icon: '⚙️', color: '#F5222D' },
  recall: { name: '延迟回忆', icon: '🔄', color: '#EB2F96' }
}

const domainKey = computed(() => {
  const q = currentQuestion.value
  return (q?.domain || 'memory').toLowerCase()
})

const domainInfo = computed(() => domainMap[domainKey.value] || { name: '综合能力', icon: '🧠', color: '#4A90D9' })
const domainName = computed(() => domainInfo.value.name)
const domainIcon = computed(() => domainInfo.value.icon)
const domainColor = computed(() => domainInfo.value.color)

// Methods
function resetAnswerState() {
  selectedOption.value = null
  showFeedback.value = false
  wrongAnswer.value = false
  scaleValue.value = 5
  textAnswer.value = ''
  voiceAnswered.value = false
  drawingAnswered.value = false
}

async function submitAnswerToBackend(answerData) {
  if (submitting.value) return
  submitting.value = true
  try {
    const sessionId = assessmentStore.currentSessionId
    const reactionTime = assessmentStore.getReactionTime()
    // Map to backend AnswerSubmit schema: {question_id, answer_text, answer_data, reaction_time_ms}
    const payload = {
      question_id: currentQuestion.value?.id,
      answer_text: answerData.answer_value != null ? String(answerData.answer_value) : null,
      answer_data: answerData,
      reaction_time_ms: reactionTime,
    }
    await api.submitAnswer(sessionId, payload)
    assessmentStore.submitAnswer(payload)
  } catch (err) {
    console.error('Submit answer error:', err)
    // Non-blocking — record locally even if server fails
    assessmentStore.submitAnswer({ question_id: currentQuestion.value?.id })
    wx.showToast({ title: '答案已暂存', icon: 'none', duration: 1500 })
  } finally {
    submitting.value = false
  }
}

async function selectOption(idx, option) {
  if (showFeedback.value || submitting.value) return // prevent double tap
  selectedOption.value = idx

  // option is a plain string (backend returns List[str])
  const answerValue = typeof option === 'string' ? option : String(option)
  const correctAnswer = currentQuestion.value?.correct_answer

  // Show brief feedback if answer key exists
  if (correctAnswer != null) {
    wrongAnswer.value = answerValue !== correctAnswer
    showFeedback.value = true
  }

  // Submit answer (store.submitAnswer auto-advances index)
  await submitAnswerToBackend({
    answer_type: 'choice',
    selected_index: idx,
    answer_value: answerValue,
  })

  // Auto advance after brief delay (index already advanced by submitAnswerToBackend)
  const delay = showFeedback.value ? 800 : 300
  setTimeout(() => {
    showFeedback.value = false
    if (isLastQuestion.value) {
      handleComplete()
    } else {
      resetAnswerState()
    }
  }, delay)
}

function onSliderChange(e) {
  scaleValue.value = e.detail.value
}

async function submitScaleAnswer() {
  await submitAnswerToBackend({
    answer_type: 'scale',
    answer_value: scaleValue.value
  })
  advanceOrComplete()
}

async function submitTextAnswer() {
  if (!textAnswer.value.trim()) return
  await submitAnswerToBackend({
    answer_type: 'text',
    answer_value: textAnswer.value.trim()
  })
  advanceOrComplete()
}

function goToVoiceTask() {
  const q = currentQuestion.value
  uni.navigateTo({
    url: `/pages/assessment/voice-task/index?questionIndex=${currentIndex.value}&questionId=${q?.id || ''}&taskText=${encodeURIComponent(q?.question_text || q?.text || '')}`
  })
}

function goToClockDraw() {
  const q = currentQuestion.value
  uni.navigateTo({
    url: `/pages/assessment/clock-draw/index?questionIndex=${currentIndex.value}&questionId=${q?.id || ''}`
  })
}

function advanceQuestion() {
  if (!isLastQuestion.value) {
    resetAnswerState()
    assessmentStore.currentQuestionIndex++
    assessmentStore.markQuestionStart()
  } else {
    handleComplete()
  }
}

function advanceOrComplete() {
  if (!isLastQuestion.value) {
    resetAnswerState()
  } else {
    handleComplete()
  }
}

async function handleComplete() {
  wx.showLoading({ title: '提交中...', mask: true })
  try {
    const sessionId = assessmentStore.currentSessionId
    const completeData = await api.completeSession(sessionId)
    const taskId = completeData?.task_id || completeData?.id

    if (taskId) {
      assessmentStore.setTaskId(taskId)
    }

    wx.hideLoading()
    uni.redirectTo({
      url: `/pages/result/index?sessionId=${sessionId}${taskId ? '&taskId=' + taskId : ''}`
    })
  } catch (err) {
    wx.hideLoading()
    console.error('Complete session error:', err)
    wx.showModal({
      title: '提交遇到问题',
      content: err.message || '提交失败，请重试',
      showCancel: false,
      confirmText: '重试',
      confirmColor: '#4A90D9',
      success: () => handleComplete()
    })
  }
}

function confirmExit() {
  wx.showModal({
    title: '退出评估',
    content: '退出后本次评估将不会保存，确定要退出吗？',
    confirmText: '退出',
    cancelText: '继续评估',
    confirmColor: '#F5222D',
    success: (res) => {
      if (res.confirm) {
        assessmentStore.reset()
        uni.switchTab({ url: '/pages/index/index' })
      }
    }
  })
}

// Handle returning from voice/draw sub-pages
onShow(() => {
  // Check if voice task was completed (stored in pages stack)
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  if (currentPage?.options?.voiceCompleted === '1') {
    voiceAnswered.value = true
  }
  if (currentPage?.options?.drawCompleted === '1') {
    drawingAnswered.value = true
  }
})

// Listen for voice/draw completion via event bus (uni.$emit)
onMounted(() => {
  uni.$on('voiceTaskCompleted', (data) => {
    voiceAnswered.value = true
    // Record answer from voice task
    if (data?.questionIndex === currentIndex.value) {
      assessmentStore.submitAnswer({
        answer_type: 'voice',
        question_index: data.questionIndex,
        voice_file: data.filePath,
        reaction_time_ms: assessmentStore.getReactionTime()
      })
    }
  })

  uni.$on('clockDrawCompleted', (data) => {
    drawingAnswered.value = true
    if (data?.questionIndex === currentIndex.value) {
      assessmentStore.submitAnswer({
        answer_type: 'drawing',
        question_index: data.questionIndex,
        strokes: data.strokes,
        image_data: data.imageData,
        reaction_time_ms: assessmentStore.getReactionTime()
      })
    }
  })
})
</script>

<style scoped>
.question-page {
  min-height: 100vh;
  background: #F0F4F8;
  padding-bottom: 40rpx;
}

/* Progress Header */
.progress-header {
  background: #ffffff;
  padding: 24rpx 30rpx 20rpx;
  box-shadow: 0 2rpx 8rpx rgba(0, 0, 0, 0.06);
}

.progress-info {
  display: flex;
  align-items: baseline;
  gap: 16rpx;
  margin-bottom: 16rpx;
}

.progress-num {
  font-size: 44rpx;
  font-weight: bold;
  color: #4A90D9;
}

.progress-total {
  font-size: 30rpx;
  color: #999999;
}

.progress-bar-wrap {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.progress-bar {
  flex: 1;
  height: 16rpx;
  background: #E8E8E8;
  border-radius: 8rpx;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #4A90D9, #2c6fad);
  border-radius: 8rpx;
  transition: width 0.4s ease;
}

.progress-pct {
  font-size: 26rpx;
  color: #4A90D9;
  font-weight: bold;
  min-width: 60rpx;
  text-align: right;
}

/* Question Card */
.question-card {
  background: #ffffff;
  border-radius: 20rpx;
  margin: 20rpx 30rpx;
  padding: 36rpx 30rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
}

.domain-badge {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  padding: 10rpx 24rpx;
  border-radius: 30rpx;
  margin-bottom: 28rpx;
}

.domain-icon {
  font-size: 28rpx;
}

.domain-name {
  font-size: 26rpx;
  color: #ffffff;
  font-weight: bold;
}

.question-text {
  font-size: 44rpx;
  font-weight: bold;
  color: #222222;
  line-height: 1.6;
  display: block;
  margin-bottom: 36rpx;
}

/* Option Buttons */
.options-list {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.option-btn {
  display: flex;
  align-items: center;
  gap: 20rpx;
  padding: 24rpx 24rpx;
  background: #F8F9FA;
  border: 3rpx solid #E0E0E0;
  border-radius: 16rpx;
  min-height: 100rpx;
  transition: all 0.2s;
  position: relative;
}

.option-btn:active {
  transform: scale(0.98);
  opacity: 0.85;
}

.option-btn.selected {
  border-color: #4A90D9;
  background: #EBF5FF;
}

.option-btn.correct {
  border-color: #52C41A;
  background: #F6FFED;
}

.option-btn.wrong {
  border-color: #F5222D;
  background: #FFF2F0;
}

.option-label-circle {
  width: 60rpx;
  height: 60rpx;
  background: #4A90D9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.option-label {
  font-size: 30rpx;
  font-weight: bold;
  color: #ffffff;
}

.option-text {
  flex: 1;
  font-size: 36rpx;
  color: #333333;
  line-height: 1.5;
}

.option-indicator {
  font-size: 40rpx;
  font-weight: bold;
}

/* Scale */
.scale-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20rpx;
}

.scale-display {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.scale-value {
  font-size: 80rpx;
  font-weight: bold;
  color: #4A90D9;
}

.scale-unit {
  font-size: 32rpx;
  color: #888888;
}

.scale-slider {
  width: 100%;
}

.scale-labels {
  width: 100%;
  display: flex;
  justify-content: space-between;
}

.scale-label-left, .scale-label-right {
  font-size: 26rpx;
  color: #999999;
}

/* Task Area (voice/draw) */
.task-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 24rpx;
}

.task-hint-box {
  width: 100%;
  padding: 30rpx;
  border-radius: 16rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  text-align: center;
}

.task-hint-voice {
  background: #FFF0F6;
  border: 2rpx solid #FFADD2;
}

.task-hint-draw {
  background: #F0F5FF;
  border: 2rpx solid #ADC6FF;
}

.task-hint-icon {
  font-size: 60rpx;
}

.task-hint-text {
  font-size: 32rpx;
  color: #555555;
  line-height: 1.5;
}

.answered-badge {
  display: flex;
  align-items: center;
  gap: 12rpx;
  background: #F6FFED;
  border: 2rpx solid #B7EB8F;
  border-radius: 12rpx;
  padding: 16rpx 30rpx;
}

.answered-icon {
  font-size: 36rpx;
  color: #52C41A;
  font-weight: bold;
}

.answered-text {
  font-size: 32rpx;
  color: #52C41A;
  font-weight: bold;
}

.btn-task {
  width: 100%;
  height: 100rpx;
  font-size: 38rpx;
  font-weight: bold;
  border-radius: 50rpx;
  border: none;
  letter-spacing: 2rpx;
}

.btn-voice {
  background: linear-gradient(135deg, #EB2F96, #C41D7F);
  color: #ffffff;
  box-shadow: 0 6rpx 20rpx rgba(235, 47, 150, 0.35);
}

.btn-draw {
  background: linear-gradient(135deg, #1890FF, #096DD9);
  color: #ffffff;
  box-shadow: 0 6rpx 20rpx rgba(24, 144, 255, 0.35);
}

/* Text Input */
.text-area {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.text-input {
  width: 100%;
  min-height: 160rpx;
  background: #F8F9FA;
  border: 2rpx solid #E0E0E0;
  border-radius: 16rpx;
  padding: 20rpx;
  font-size: 36rpx;
  color: #333333;
  box-sizing: border-box;
}

.text-placeholder {
  color: #AAAAAA;
  font-size: 32rpx;
}

/* Next Button */
.btn-next {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, #4A90D9, #2c6fad);
  color: #ffffff;
  font-size: 38rpx;
  font-weight: bold;
  border-radius: 48rpx;
  border: none;
  box-shadow: 0 6rpx 20rpx rgba(74, 144, 217, 0.35);
  letter-spacing: 2rpx;
}

.btn-next[disabled] {
  background: #B0C4DE;
  box-shadow: none;
}

/* Unknown type */
.unknown-type {
  font-size: 30rpx;
  color: #999999;
}

/* Loading State */
.loading-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 100rpx 30rpx;
}

.loading-icon {
  font-size: 80rpx;
  margin-bottom: 20rpx;
}

.loading-text {
  font-size: 36rpx;
  color: #888888;
}

/* Exit Row */
.exit-row {
  text-align: center;
  padding: 20rpx;
}

.exit-text {
  font-size: 28rpx;
  color: #CCCCCC;
  text-decoration: underline;
}
</style>
