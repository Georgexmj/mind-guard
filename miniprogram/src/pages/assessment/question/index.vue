<template>
  <view class="question-page">
    <view class="progress-card">
      <view class="progress-row">
        <text class="progress-title">第 {{ currentIndex + 1 }} 题</text>
        <text class="progress-sub">共 {{ totalQuestions }} 题</text>
      </view>
      <view class="progress-line-wrap">
        <view class="progress-line">
          <view class="progress-line-fill" :style="{ width: progressPercent + '%' }" />
        </view>
        <text class="progress-num">{{ progressPercent }}%</text>
      </view>
    </view>

    <view v-if="currentQuestion" class="mg-card question-card">
      <view class="domain-tag" :style="{ backgroundColor: domainColor }">
        <text class="domain-icon">{{ domainIcon }}</text>
        <text class="domain-name">{{ domainName }}</text>
      </view>

      <text class="question-text">{{ currentQuestion.content }}</text>

      <view v-if="isChoiceType" class="options-list">
        <view
          v-for="(option, idx) in currentQuestion.options"
          :key="idx"
          class="option-item"
          :class="{
            selected: selectedOption === idx,
            correct: showFeedback && selectedOption === idx && !wrongAnswer,
            wrong: showFeedback && selectedOption === idx && wrongAnswer,
          }"
          @tap="selectOption(idx, option)"
        >
          <view class="option-index">{{ optionLabels[idx] }}</view>
          <text class="option-content">{{ option }}</text>
          <text v-if="showFeedback && selectedOption === idx" class="option-state">
            {{ wrongAnswer ? '✕' : '✓' }}
          </text>
        </view>
      </view>

      <view v-else-if="isScaleType" class="scale-area">
        <view class="scale-score">
          <text class="scale-value">{{ scaleValue }}</text>
          <text class="scale-total">/ 10 分</text>
        </view>
        <slider
          class="scale-slider"
          :min="0"
          :max="10"
          :step="1"
          :value="scaleValue"
          activeColor="#0f766e"
          backgroundColor="#e2ebf2"
          block-size="42"
          @change="onSliderChange"
        />
        <view class="scale-labels">
          <text class="scale-label">完全不符合</text>
          <text class="scale-label">完全符合</text>
        </view>

        <button class="next-btn" @tap="submitScaleAnswer">确认并继续</button>
      </view>

      <view v-else-if="isVoiceType" class="task-area">
        <view class="task-hint voice">
          <text class="task-icon">🎙️</text>
          <text class="task-text">请点击下方按钮完成语音任务。</text>
        </view>
        <view v-if="voiceAnswered" class="done-tag">
          <text class="done-icon">✓</text>
          <text class="done-text">语音已录制</text>
        </view>
        <button class="task-btn voice" @tap="goToVoiceTask">
          {{ voiceAnswered ? '重新录制语音' : '开始录音' }}
        </button>
        <button v-if="voiceAnswered" class="next-btn" @tap="submitVoiceAnswer">下一题</button>
      </view>

      <view v-else-if="isDrawingType" class="task-area">
        <view class="task-hint draw">
          <text class="task-icon">🕘</text>
          <text class="task-text">请点击下方按钮完成时钟绘制任务。</text>
        </view>
        <view v-if="drawingAnswered" class="done-tag">
          <text class="done-icon">✓</text>
          <text class="done-text">时钟已绘制</text>
        </view>
        <button class="task-btn draw" @tap="goToClockDraw">
          {{ drawingAnswered ? '重新绘制时钟' : '开始绘制' }}
        </button>
        <button v-if="drawingAnswered" class="next-btn" @tap="submitDrawingAnswer">下一题</button>
      </view>

      <view v-else-if="isTextType" class="text-area">
        <textarea
          v-model="textAnswer"
          class="text-input"
          placeholder="请在此输入您的答案..."
          placeholder-class="text-placeholder"
          :maxlength="500"
          auto-height
        />
        <button class="next-btn" :disabled="!textAnswer.trim()" @tap="submitTextAnswer">确认并继续</button>
      </view>

      <view v-else class="task-area">
        <text class="unknown-type">暂不支持题型：{{ currentQuestion.q_type }}</text>
        <button class="next-btn" @tap="advanceQuestion">跳过此题</button>
      </view>
    </view>

    <view v-else-if="initializing || totalQuestions === 0" class="loading-state">
      <text class="loading-icon">⏳</text>
      <text class="loading-text">{{ initializing ? '题目加载中...' : '暂无题目数据' }}</text>
    </view>

    <view class="exit-row">
      <text class="exit-text" @tap="confirmExit">暂停并退出评估</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow, onBackPress } from '@dcloudio/uni-app'
import { useAssessmentStore } from '../../../store/assessment'
import { api } from '../../../utils/request'

const assessmentStore = useAssessmentStore()

const selectedOption = ref(null)
const initializing = ref(false)

function generateDateBasedQuestions() {
  const now = new Date()
  const currentYear = now.getFullYear()
  const currentMonth = now.getMonth() + 1
  const currentDate = now.getDate()
  const weekdays = ['星期日', '星期一', '星期二', '星期三', '星期四', '星期五', '星期六']
  const currentWeekday = weekdays[now.getDay()]
  
  const yearOptions = [currentYear - 3, currentYear - 1, currentYear, currentYear + 1].map(String)
  
  const weekdayOptions = []
  const usedIndices = new Set([now.getDay()])
  weekdayOptions.push(currentWeekday)
  
  while (weekdayOptions.length < 4) {
    const randomIdx = Math.floor(Math.random() * 7)
    if (!usedIndices.has(randomIdx)) {
      usedIndices.add(randomIdx)
      weekdayOptions.push(weekdays[randomIdx])
    }
  }
  
  weekdayOptions.sort(() => Math.random() - 0.5)
  
  const monthOptions = []
  const monthUsed = new Set([currentMonth])
  monthOptions.push(String(currentMonth))
  while (monthOptions.length < 4) {
    const randomMonth = Math.floor(Math.random() * 12) + 1
    if (!monthUsed.has(randomMonth)) {
      monthUsed.add(randomMonth)
      monthOptions.push(String(randomMonth))
    }
  }
  monthOptions.sort(() => Math.random() - 0.5)
  
  const dateOptions = []
  const dateUsed = new Set([currentDate])
  dateOptions.push(String(currentDate))
  const maxDate = new Date(currentYear, currentMonth, 0).getDate()
  while (dateOptions.length < 4) {
    const randomDate = Math.floor(Math.random() * maxDate) + 1
    if (!dateUsed.has(randomDate)) {
      dateUsed.add(randomDate)
      dateOptions.push(String(randomDate))
    }
  }
  dateOptions.sort(() => Math.random() - 0.5)
  
  return {
    yearQuestion: {
      id: 'mmse_1',
      content: `现在是哪一年？`,
      q_type: 'choice',
      options: yearOptions,
      domain: 'orientation',
      correct_answer: String(currentYear)
    },
    weekdayQuestion: {
      id: 'mmse_2',
      content: `今天是星期几？`,
      q_type: 'choice',
      options: weekdayOptions,
      domain: 'orientation',
      correct_answer: currentWeekday
    },
    monthQuestion: {
      id: 'mmse_3',
      content: `现在是几月份？`,
      q_type: 'choice',
      options: monthOptions,
      domain: 'orientation',
      correct_answer: String(currentMonth)
    },
    dateQuestion: {
      id: 'mmse_4',
      content: `今天是几号？`,
      q_type: 'choice',
      options: dateOptions,
      domain: 'orientation',
      correct_answer: String(currentDate)
    },
    year: currentYear,
    month: currentMonth,
    date: currentDate,
    weekday: currentWeekday
  }
}

// Mock题目数据 - MMSE量表
const mmseQuestions = [
  {
    id: 'mmse_1',
    content: '现在是哪一年？',
    q_type: 'choice',
    options: ['2023', '2024', '2025', '2026'],
    domain: 'orientation',
    correct_answer: '2026'
  },
  {
    id: 'mmse_2',
    content: '今天是星期几？',
    q_type: 'choice',
    options: ['星期一', '星期三', '星期五', '星期日'],
    domain: 'orientation',
    correct_answer: ''
  },
  {
    id: 'mmse_3',
    content: '请重复我说的三个词语：苹果、桌子、雨伞',
    q_type: 'text',
    domain: 'memory'
  },
  {
    id: 'mmse_4',
    content: '100减去7等于多少？',
    q_type: 'choice',
    options: ['90', '93', '95', '97'],
    domain: 'attention',
    correct_answer: '93'
  },
  {
    id: 'mmse_5',
    content: '请说出刚才我让你记住的三个词语',
    q_type: 'text',
    domain: 'recall'
  }
]

// Mock题目数据 - MoCA量表
const mocaQuestions = [
  {
    id: 'moca_1',
    content: '请画一个钟表，并标出10点15分',
    q_type: 'drawing',
    domain: 'visuospatial'
  },
  {
    id: 'moca_2',
    content: '请重复以下句子：我只知道今天天气很好',
    q_type: 'text',
    domain: 'language'
  },
  {
    id: 'moca_3',
    content: '请说出尽可能多的动物名称',
    q_type: 'text',
    domain: 'language'
  },
  {
    id: 'moca_4',
    content: '从20开始，每次减3，依次说出数字',
    q_type: 'text',
    domain: 'attention'
  },
  {
    id: 'moca_5',
    content: '这是什么？（指向铅笔）',
    q_type: 'choice',
    options: ['钢笔', '铅笔', '毛笔', '蜡笔'],
    domain: 'language',
    correct_answer: '铅笔'
  }
]

// 默认题目数据（多维综合评估）
const defaultQuestions = [
  {
    id: 'q1',
    content: '请告诉我您今天感觉怎么样？',
    q_type: 'voice',
    domain: 'language'
  },
  {
    id: 'q2',
    content: '请画出您家附近的公园',
    q_type: 'drawing',
    domain: 'visuospatial'
  },
  {
    id: 'q3',
    content: '以下哪个是正确的等式？',
    q_type: 'choice',
    options: ['3+5=7', '9-3=6', '4x2=7', '10÷2=4'],
    domain: 'attention',
    correct_answer: '9-3=6'
  },
  {
    id: 'q4',
    content: '请描述您昨天做了什么',
    q_type: 'voice',
    domain: 'memory'
  },
  {
    id: 'q5',
    content: '请画一个房子',
    q_type: 'drawing',
    domain: 'visuospatial'
  },
  {
    id: 'q6',
    content: '一年有几个季节？',
    q_type: 'choice',
    options: ['2个', '3个', '4个', '5个'],
    domain: 'orientation',
    correct_answer: '4个'
  },
  {
    id: 'q7',
    content: '请用三个词语描述您自己',
    q_type: 'text',
    domain: 'language'
  },
  {
    id: 'q8',
    content: '您对自己的记忆力满意吗？',
    q_type: 'scale',
    domain: 'memory'
  }
]
const showFeedback = ref(false)
const wrongAnswer = ref(false)
const scaleValue = ref(5)
const textAnswer = ref('')
const voiceAnswered = ref(false)
const drawingAnswered = ref(false)
const submitting = ref(false)
const voiceAnswerPayload = ref(null)
const drawingAnswerPayload = ref(null)
const confirmedLeaving = ref(false)

const optionLabels = ['A', 'B', 'C', 'D']

const currentQuestion = computed(() => assessmentStore.currentQuestion)
const currentIndex = computed(() => assessmentStore.currentQuestionIndex)
const totalQuestions = computed(() => assessmentStore.totalQuestions)
const isLastQuestion = computed(() => assessmentStore.isLastQuestion)

const progressPercent = computed(() => {
  if (totalQuestions.value === 0) return 0
  return Math.round(((currentIndex.value + 1) / totalQuestions.value) * 100)
})

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

const domainMap = {
  memory: { name: '记忆', icon: '🧠', color: '#7c3aed' },
  orientation: { name: '定向', icon: '🧭', color: '#0284c7' },
  attention: { name: '注意', icon: '🎯', color: '#d97706' },
  language: { name: '语言', icon: '🗣️', color: '#16a34a' },
  visuospatial: { name: '视空间', icon: '🧩', color: '#0ea5e9' },
  executive: { name: '执行功能', icon: '📋', color: '#dc2626' },
  recall: { name: '延迟回忆', icon: '🔁', color: '#ec4899' },
}

const domainKey = computed(() => {
  const q = currentQuestion.value
  return (q?.domain || 'memory').toLowerCase()
})

const domainInfo = computed(() => domainMap[domainKey.value] || { name: '综合能力', icon: '🧠', color: '#0f766e' })
const domainName = computed(() => domainInfo.value.name)
const domainIcon = computed(() => domainInfo.value.icon)
const domainColor = computed(() => domainInfo.value.color)

function resetAnswerState() {
  selectedOption.value = null
  showFeedback.value = false
  wrongAnswer.value = false
  scaleValue.value = 5
  textAnswer.value = ''
  voiceAnswered.value = false
  drawingAnswered.value = false
  voiceAnswerPayload.value = null
  drawingAnswerPayload.value = null
}

async function submitAnswerToBackend(answerData) {
  if (submitting.value) return
  submitting.value = true
  try {
    const sessionId = assessmentStore.currentSessionId
    const reactionTime = assessmentStore.getReactionTime()
    const payload = {
      question_id: currentQuestion.value?.id,
      answer_text: answerData.answer_value != null ? String(answerData.answer_value) : null,
      answer_data: answerData,
      reaction_time_ms: reactionTime,
    }
    api.submitAnswer(sessionId, payload).catch(() => {})
    assessmentStore.submitAnswer(payload)
  } catch (err) {
    console.error('Submit answer error:', err)
    assessmentStore.submitAnswer({ question_id: currentQuestion.value?.id })
  } finally {
    submitting.value = false
  }
}

async function selectOption(idx, option) {
  if (showFeedback.value || submitting.value) return
  selectedOption.value = idx

  const answerValue = typeof option === 'string' ? option : String(option)
  const correctAnswer = currentQuestion.value?.correct_answer

  if (correctAnswer != null) {
    wrongAnswer.value = answerValue !== correctAnswer
    showFeedback.value = true
  }

  await submitAnswerToBackend({
    answer_type: 'choice',
    selected_index: idx,
    answer_value: answerValue,
  })

  const delay = showFeedback.value ? 800 : 280
  setTimeout(() => {
    showFeedback.value = false
    if (isLastQuestion.value) {
      handleComplete()
    } else {
      resetAnswerState()
      assessmentStore.currentQuestionIndex++
      assessmentStore.markQuestionStart()
    }
  }, delay)
}

function onSliderChange(e) {
  scaleValue.value = e.detail.value
}

async function submitScaleAnswer() {
  await submitAnswerToBackend({
    answer_type: 'scale',
    answer_value: scaleValue.value,
  })
  advanceOrComplete()
}

async function submitTextAnswer() {
  if (!textAnswer.value.trim()) return
  await submitAnswerToBackend({
    answer_type: 'text',
    answer_value: textAnswer.value.trim(),
  })
  advanceOrComplete()
}

async function submitVoiceAnswer() {
  if (!voiceAnswerPayload.value) {
    wx.showToast({ title: '请先完成语音任务', icon: 'none' })
    return
  }
  await submitAnswerToBackend(voiceAnswerPayload.value)
  advanceOrComplete()
}

async function submitDrawingAnswer() {
  if (!drawingAnswerPayload.value) {
    wx.showToast({ title: '请先完成绘图任务', icon: 'none' })
    return
  }
  await submitAnswerToBackend(drawingAnswerPayload.value)
  advanceOrComplete()
}

function goToVoiceTask() {
  const q = currentQuestion.value
  const sessionId = assessmentStore.currentSessionId || ''
  uni.navigateTo({
    url: `/pages/assessment/voice-task/index?questionIndex=${currentIndex.value}&questionId=${q?.id || ''}&sessionId=${sessionId}&taskText=${encodeURIComponent(q?.content || '')}`,
  })
}

function goToClockDraw() {
  const q = currentQuestion.value
  uni.navigateTo({
    url: `/pages/assessment/clock-draw/index?questionIndex=${currentIndex.value}&questionId=${q?.id || ''}`,
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
    assessmentStore.currentQuestionIndex++
    assessmentStore.markQuestionStart()
  } else {
    handleComplete()
  }
}

async function handleComplete() {
  wx.showLoading({ title: '提交中...', mask: true })
  try {
    const sessionId = assessmentStore.currentSessionId
    let taskId = null
    
    try {
      const completeData = await api.completeSession(sessionId)
      taskId = completeData?.task_id || completeData?.id
    } catch (apiErr) {
      console.warn('API complete failed, using local data:', apiErr)
      taskId = 'local_task_' + Date.now()
    }

    if (taskId) {
      assessmentStore.setTaskId(taskId)
    }

    wx.hideLoading()
    uni.redirectTo({
      url: `/pages/result/index?sessionId=${sessionId}${taskId ? `&taskId=${taskId}` : ''}`,
    })
  } catch (err) {
    wx.hideLoading()
    console.error('Complete session error:', err)
    uni.redirectTo({
      url: `/pages/result/index?sessionId=${assessmentStore.currentSessionId}&taskId=local_${Date.now()}`,
    })
  }
}

async function pauseCurrentSession() {
  const sessionId = assessmentStore.currentSessionId
  if (!sessionId) return true
  try {
    await api.pauseSession(sessionId)
    return true
  } catch (err) {
    console.warn('Pause session failed:', err)
    return false
  }
}

function confirmExit() {
  wx.showModal({
    title: '暂停评估',
    content: '退出后系统会自动暂停评估，30 分钟内可继续答题。是否确认退出？',
    confirmText: '暂停并退出',
    cancelText: '继续评估',
    confirmColor: '#0f766e',
    success: async (res) => {
      if (res.confirm) {
        wx.showLoading({ title: '正在退出...', mask: true })
        const paused = await pauseCurrentSession()
        wx.hideLoading()
        if (!paused) {
          wx.showModal({
            title: '暂停失败',
            content: '当前会话暂停失败，请检查网络后重试。',
            showCancel: false,
            confirmText: '知道了',
            confirmColor: '#0f766e',
          })
          return
        }
        wx.showToast({ title: '已暂停，可在 30 分钟内继续', icon: 'none', duration: 1800 })
        confirmedLeaving.value = true
        assessmentStore.reset()
        uni.switchTab({ url: '/pages/index/index' })
      }
    },
  })
}

onBackPress(() => {
  if (confirmedLeaving.value) return false
  confirmExit()
  return true
})

onShow(() => {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  if (currentPage?.options?.voiceCompleted === '1') {
    voiceAnswered.value = true
  }
  if (currentPage?.options?.drawCompleted === '1') {
    drawingAnswered.value = true
  }
})

const handleVoiceTaskCompleted = (data) => {
  if (data?.questionIndex !== currentIndex.value) return
  voiceAnswered.value = true
  voiceAnswerPayload.value = {
    answer_type: 'voice',
    answer_value: data?.transcript || (data?.skipped ? 'skipped' : 'voice_recorded'),
    voice_file: data?.audioUrl || null,
    audio_url: data?.audioUrl || null,
    audio_object_key: data?.objectName || null,
    duration_sec: data?.durationSec || 0,
    skipped: !!data?.skipped,
  }
}

const handleClockDrawCompleted = (data) => {
  if (data?.questionIndex !== currentIndex.value) return
  drawingAnswered.value = true
  drawingAnswerPayload.value = {
    answer_type: 'drawing',
    answer_value: data?.skipped ? 'skipped' : 'drawing_completed',
    strokes: data?.strokes || null,
    image_data: data?.imageData || null,
    skipped: !!data?.skipped,
  }
}

async function initQuestions() {
  if (initializing.value) return
  initializing.value = true
  
  try {
    const pages = getCurrentPages()
    const currentPage = pages[pages.length - 1]
    const scaleType = currentPage?.options?.scale
    
    let questions = defaultQuestions
    if (scaleType === 'mmse') {
      const dateData = generateDateBasedQuestions()
      questions = [
        dateData.yearQuestion,
        dateData.monthQuestion,
        dateData.dateQuestion,
        dateData.weekdayQuestion,
        mmseQuestions[2],
        mmseQuestions[3],
        mmseQuestions[4]
      ]
    } else if (scaleType === 'moca') {
      questions = mocaQuestions
    }
    
    assessmentStore.startSession('mock_session_' + Date.now())
    assessmentStore.setQuestions(questions)
  } catch (err) {
    console.error('Init questions failed:', err)
    uni.showToast({ title: '加载题目失败', icon: 'none' })
  } finally {
    initializing.value = false
  }
}

onMounted(() => {
  uni.$on('voiceTaskCompleted', handleVoiceTaskCompleted)
  uni.$on('clockDrawCompleted', handleClockDrawCompleted)
  initQuestions()
})

onUnmounted(() => {
  uni.$off('voiceTaskCompleted', handleVoiceTaskCompleted)
  uni.$off('clockDrawCompleted', handleClockDrawCompleted)
})
</script>

<style scoped>
.question-page {
  min-height: 100vh;
  padding-bottom: 34rpx;
}

.progress-card {
  margin: 16rpx 24rpx 0;
  border-radius: 20rpx;
  padding: 18rpx 18rpx 16rpx;
  background: rgba(255, 255, 255, 0.92);
  border: 2rpx solid rgba(17, 34, 49, 0.07);
}

.progress-row {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10rpx;
}

.progress-title {
  font-size: 34rpx;
  font-weight: 800;
  color: #0f766e;
}

.progress-sub {
  font-size: 27rpx;
  color: #7390a3;
}

.progress-line-wrap {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.progress-line {
  flex: 1;
  height: 14rpx;
  border-radius: 999rpx;
  overflow: hidden;
  background: #dbe7f0;
}

.progress-line-fill {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #0f766e, #0284c7);
  transition: width 0.25s ease;
}

.progress-num {
  min-width: 64rpx;
  text-align: right;
  color: #0f766e;
  font-size: 27rpx;
  font-weight: 700;
}

.question-card {
  margin: 16rpx 24rpx 0;
  padding: 24rpx;
}

.domain-tag {
  display: inline-flex;
  align-items: center;
  gap: 8rpx;
  padding: 8rpx 18rpx;
  border-radius: 999rpx;
}

.domain-icon {
  font-size: 29rpx;
}

.domain-name {
  color: #ffffff;
  font-size: 29rpx;
  font-weight: 700;
}

.question-text {
  display: block;
  margin-top: 16rpx;
  margin-bottom: 20rpx;
  font-size: 40rpx;
  color: #132f40;
  line-height: 1.7;
  font-weight: 700;
}

.options-list {
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.option-item {
  display: flex;
  align-items: center;
  gap: 12rpx;
  border-radius: 16rpx;
  border: 2rpx solid #d9e5ee;
  background: #f7fbfd;
  padding: 16rpx;
}

.option-item.selected {
  border-color: #0f766e;
  background: #eef9f8;
}

.option-item.correct {
  border-color: #16a34a;
  background: #f6ffed;
}

.option-item.wrong {
  border-color: #dc2626;
  background: #fff2f0;
}

.option-index {
  width: 52rpx;
  height: 52rpx;
  border-radius: 50%;
  background: #0f766e;
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 27rpx;
  font-weight: 700;
  flex-shrink: 0;
}

.option-content {
  flex: 1;
  font-size: 32rpx;
  color: #1d3d50;
  line-height: 1.5;
}

.option-state {
  font-size: 36rpx;
  font-weight: 800;
}

.scale-area {
  display: flex;
  flex-direction: column;
}

.scale-score {
  display: flex;
  align-items: baseline;
  justify-content: center;
  margin-bottom: 14rpx;
}

.scale-value {
  font-size: 72rpx;
  color: #0f766e;
  font-weight: 800;
}

.scale-total {
  font-size: 30rpx;
  color: #6e8797;
}

.scale-slider {
  width: 100%;
}

.scale-labels {
  display: flex;
  justify-content: space-between;
  margin-bottom: 14rpx;
}

.scale-label {
  color: #7894a5;
  font-size: 29rpx;
}

.task-area {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.task-hint {
  border-radius: 16rpx;
  padding: 22rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.task-hint.voice {
  background: #fff0f6;
  border: 2rpx solid #ffadd2;
}

.task-hint.draw {
  background: #eff6ff;
  border: 2rpx solid #bfdbfe;
}

.task-icon {
  font-size: 54rpx;
}

.task-text {
  margin-top: 8rpx;
  color: #4e687a;
  font-size: 30rpx;
}

.done-tag {
  padding: 12rpx 16rpx;
  border-radius: 14rpx;
  background: #f6ffed;
  border: 2rpx solid #b7eb8f;
  display: inline-flex;
  align-items: center;
  gap: 6rpx;
}

.done-icon {
  color: #16a34a;
  font-weight: 700;
}

.done-text {
  color: #237804;
  font-size: 28rpx;
  font-weight: 700;
}

.task-btn {
  width: 100%;
  min-height: 92rpx;
  border-radius: 999rpx;
  border: none;
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
}

.task-btn.voice {
  background: linear-gradient(135deg, #db2777, #be185d);
}

.task-btn.draw {
  background: linear-gradient(135deg, #0284c7, #0369a1);
}

.text-area {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.text-input {
  width: 100%;
  min-height: 168rpx;
  border-radius: 16rpx;
  border: 2rpx solid #d9e5ee;
  background: #f8fbfd;
  padding: 16rpx;
  font-size: 30rpx;
  color: #1d3d50;
}

.text-placeholder {
  color: #93a7b6;
  font-size: 30rpx;
}

.next-btn {
  width: 100%;
  min-height: 92rpx;
  border-radius: 999rpx;
  border: none;
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
}

.next-btn[disabled] {
  background: #afc5d7;
}

.unknown-type {
  color: #7b93a3;
  font-size: 29rpx;
}

.loading-state {
  margin: 20rpx 24rpx 0;
  border-radius: 20rpx;
  padding: 50rpx 20rpx;
  text-align: center;
  background: rgba(255, 255, 255, 0.9);
}

.loading-icon {
  display: block;
  font-size: 68rpx;
}

.loading-text {
  display: block;
  margin-top: 8rpx;
  font-size: 31rpx;
  color: #6f8798;
}

.exit-row {
  text-align: center;
  padding: 20rpx;
}

.exit-text {
  color: #97aab8;
  font-size: 27rpx;
  text-decoration: underline;
}
</style>

