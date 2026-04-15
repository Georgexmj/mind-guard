<template>
  <view class="start-page">
    <view class="hero-banner">
      <text class="hero-icon">🧠</text>
      <text class="hero-title">认知评估说明</text>
      <text class="hero-subtitle">请先阅读说明并完成准备，再开始正式评估。</text>
    </view>

    <view class="mg-card block-card">
      <text class="block-title">评估内容</text>
      <view class="guide-list">
        <view v-for="item in instructions" :key="item.number" class="guide-item">
          <view class="guide-index">{{ item.number }}</view>
          <view class="guide-main">
            <text class="guide-name">{{ item.title }}</text>
            <text class="guide-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="mg-card block-card">
      <text class="block-title">开始前准备</text>
      <text class="block-subtitle">请确认以下事项：</text>
      <view class="check-list">
        <view v-for="(item, index) in checklist" :key="index" class="check-item" @tap="toggleCheck(index)">
          <view class="check-box" :class="{ checked: item.checked }">
            <text v-if="item.checked" class="check-mark">✓</text>
          </view>
          <text class="check-text">{{ item.text }}</text>
        </view>
      </view>
    </view>

    <view class="tip-box">
      <text class="tip-title">温馨提示</text>
      <text class="tip-text">评估结果仅用于初步筛查，不替代专业医疗诊断。如有明显异常，请尽快就医。</text>
    </view>

    <view v-if="resumableSession" class="resume-box">
      <text class="resume-title">检测到未完成评估</text>
      <text class="resume-desc">
        会话 #{{ resumableSession.id }} 可在 {{ resumableSession.pause_deadline || '30 分钟内' }} 继续。
      </text>
      <button class="resume-btn" :loading="loading" :disabled="loading" @tap="resumeExistingSession">
        继续上次评估
      </button>
    </view>

    <view class="bottom-panel">
      <view class="progress-info">
        <text class="progress-text">已准备 {{ checkedCount }}/{{ checklist.length }} 项</text>
        <view class="progress-track">
          <view class="progress-fill" :style="{ width: checkedCount / checklist.length * 100 + '%' }" />
        </view>
      </view>

      <button class="mg-button-primary start-btn" :loading="loading" :disabled="loading" @tap="handleStart">
        {{ loading ? '准备中...' : '开始评估' }}
      </button>
      <button class="back-btn" @tap="goBack">返回首页</button>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useAssessmentStore } from '../../../store/assessment'
import { api } from '../../../utils/request'

const assessmentStore = useAssessmentStore()
const loading = ref(false)
const resumableSession = ref(null)

const instructions = [
  {
    number: 1,
    title: '共 15 道题目',
    desc: '涵盖记忆力、定向力、注意力、语言能力等认知维度。',
  },
  {
    number: 2,
    title: '约 10-15 分钟',
    desc: '请在安静环境中连续完成，避免中断影响结果。',
  },
  {
    number: 3,
    title: '多种题型',
    desc: '包含选择题、语音朗读、时钟绘制等任务。',
  },
  {
    number: 4,
    title: '建议佩戴辅助设备',
    desc: '如有助听器、眼镜等，请提前佩戴。',
  },
  {
    number: 5,
    title: 'AI 自动分析',
    desc: '完成后系统会自动生成风险分析与干预建议。',
  },
]

const checklist = ref([
  { text: '我已处于相对安静的环境', checked: false },
  { text: '我已佩戴助听器（如需要）', checked: false },
  { text: '我已佩戴眼镜（如需要）', checked: false },
  { text: '我的设备电量充足，网络正常', checked: false },
])

const checkedCount = computed(() => checklist.value.filter((item) => item.checked).length)

function toggleCheck(index) {
  checklist.value[index].checked = !checklist.value[index].checked
}

function goBack() {
  uni.switchTab({ url: '/pages/index/index' })
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

async function continueWithSession(sessionId) {
  const questionsData = await api.getQuestions(sessionId, 15)
  const questions = Array.isArray(questionsData) ? questionsData : (questionsData.questions || [])
  if (questions.length === 0) {
    throw new Error('未获取到可继续的题目，请重新开始评估。')
  }

  assessmentStore.reset()
  assessmentStore.startSession(sessionId)
  assessmentStore.setQuestions(questions)

  uni.navigateTo({ url: '/pages/assessment/question/index' })
}

async function resumeExistingSession() {
  if (!resumableSession.value || loading.value) return
  loading.value = true
  try {
    const targetSession = resumableSession.value
    if (targetSession.status === 'pending') {
      await api.resumeSession(targetSession.id)
    }
    await continueWithSession(targetSession.id)
  } catch (err) {
    wx.showModal({
      title: '继续失败',
      content: err.message || '当前会话已失效，请重新开始评估。',
      showCancel: false,
      confirmText: '知道了',
      confirmColor: '#0f766e',
    })
    await detectResumableSession()
  } finally {
    loading.value = false
  }
}

async function startNewSession() {
  loading.value = true
  let createdSessionId = null

  try {
    assessmentStore.reset()

    const sessionData = await api.createSession()
    const sessionId = sessionData.id || sessionData.session_id
    createdSessionId = sessionId

    if (!sessionId) {
      throw new Error('创建评估会话失败，请重试。')
    }

    const questionsData = await api.getQuestions(sessionId, 15)
    const questions = Array.isArray(questionsData) ? questionsData : (questionsData.questions || [])

    if (questions.length === 0) {
      throw new Error('暂无可用评估题目，请稍后重试。')
    }

    assessmentStore.startSession(sessionId)
    assessmentStore.setQuestions(questions)

    wx.showToast({
      title: '准备完成',
      icon: 'success',
      duration: 800,
    })

    setTimeout(() => {
      uni.navigateTo({ url: '/pages/assessment/question/index' })
    }, 800)

    await detectResumableSession()
  } catch (err) {
    if (createdSessionId) {
      try {
        await api.discardSession(createdSessionId)
      } catch (discardErr) {
        console.warn('Discard temporary session failed:', discardErr)
      }
    }

    console.error('Start assessment error:', err)
    wx.showModal({
      title: '无法开始评估',
      content: err.message || '网络异常，请检查网络后重试。',
      showCancel: false,
      confirmText: '知道了',
      confirmColor: '#0f766e',
    })
  } finally {
    loading.value = false
  }
}

async function handleStart() {
  if (loading.value) return

  if (resumableSession.value) {
    const resumeTarget = resumableSession.value
    wx.showModal({
      title: '发现未完成评估',
      content: '您有一个可继续的评估会话，是否继续上次进度？',
      confirmText: '继续',
      cancelText: '重新开始',
      confirmColor: '#0f766e',
      success: async (modalResult) => {
        if (modalResult.confirm) {
          await resumeExistingSession()
          return
        }

        loading.value = true
        try {
          await api.discardSession(resumeTarget.id)
        } catch (discardErr) {
          console.warn('Discard previous resumable session failed:', discardErr)
        } finally {
          loading.value = false
        }
        resumableSession.value = null
        await startNewSession()
      },
    })
    return
  }

  await startNewSession()
}

onMounted(() => {
  detectResumableSession()
})
</script>

<style scoped>
.start-page {
  min-height: 100vh;
  padding-bottom: 46rpx;
}

.hero-banner {
  margin: 18rpx 24rpx 0;
  border-radius: 30rpx;
  padding: 34rpx 26rpx;
  text-align: center;
  background:
    radial-gradient(circle at 88% 5%, rgba(255, 255, 255, 0.28), transparent 42%),
    linear-gradient(145deg, #0f766e, #0284c7);
  box-shadow: var(--mg-shadow-strong);
}

.hero-icon {
  display: block;
  font-size: 64rpx;
  margin-bottom: 10rpx;
}

.hero-title {
  display: block;
  font-size: 48rpx;
  color: #ffffff;
  font-weight: 800;
}

.hero-subtitle {
  display: block;
  font-size: 28rpx;
  color: rgba(237, 252, 255, 0.92);
  margin-top: 8rpx;
}

.block-card {
  margin: 16rpx 24rpx 0;
  padding: 28rpx 24rpx;
}

.block-title {
  display: block;
  font-size: 35rpx;
  font-weight: 800;
  color: #143445;
}

.block-subtitle {
  display: block;
  margin-top: 8rpx;
  font-size: 28rpx;
  color: #698191;
}

.guide-list {
  margin-top: 16rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.guide-item {
  display: flex;
  align-items: flex-start;
  gap: 14rpx;
  padding: 12rpx;
  border-radius: 14rpx;
  background: #f5fbff;
}

.guide-index {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  background: #0f766e;
  color: #ffffff;
  font-size: 29rpx;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.guide-main {
  flex: 1;
  display: flex;
  flex-direction: column;
}

.guide-name {
  font-size: 31rpx;
  color: #153648;
  font-weight: 700;
}

.guide-desc {
  margin-top: 2rpx;
  font-size: 27rpx;
  color: #5e7585;
  line-height: 1.6;
}

.check-list {
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
  gap: 12rpx;
}

.check-item {
  border-radius: 14rpx;
  background: #f8fbfd;
  border: 2rpx solid rgba(17, 34, 49, 0.08);
  display: flex;
  align-items: center;
  gap: 12rpx;
  padding: 16rpx;
}

.check-box {
  width: 44rpx;
  height: 44rpx;
  border-radius: 10rpx;
  border: 2rpx solid #b7c6d2;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #ffffff;
}

.check-box.checked {
  background: #16a34a;
  border-color: #16a34a;
}

.check-mark {
  color: #ffffff;
  font-size: 28rpx;
  font-weight: 700;
}

.check-text {
  flex: 1;
  color: #1d3d50;
  font-size: 30rpx;
}

.tip-box {
  margin: 16rpx 24rpx 0;
  border-radius: 18rpx;
  padding: 20rpx;
  border: 2rpx solid #ffd591;
  background: #fff8e8;
}

.tip-title {
  display: block;
  font-size: 29rpx;
  color: #ad6800;
  font-weight: 700;
}

.tip-text {
  display: block;
  margin-top: 6rpx;
  font-size: 27rpx;
  color: #8a5b00;
  line-height: 1.6;
}

.resume-box {
  margin: 16rpx 24rpx 0;
  border-radius: 18rpx;
  padding: 20rpx;
  border: 2rpx solid #b7eb8f;
  background: #f6ffed;
}

.resume-title {
  display: block;
  color: #237804;
  font-size: 32rpx;
  font-weight: 700;
}

.resume-desc {
  display: block;
  margin-top: 6rpx;
  color: #3f8600;
  font-size: 28rpx;
  line-height: 1.6;
}

.resume-btn {
  margin-top: 12rpx;
  width: 100%;
  min-height: 96rpx;
  border-radius: 999rpx;
  border: none;
  background: #52c41a;
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 700;
}

.bottom-panel {
  margin: 18rpx 24rpx 0;
}

.progress-info {
  margin-bottom: 14rpx;
}

.progress-text {
  display: block;
  font-size: 27rpx;
  color: #638090;
  margin-bottom: 8rpx;
}

.progress-track {
  height: 12rpx;
  border-radius: 8rpx;
  background: #dbe8f1;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 8rpx;
  background: linear-gradient(90deg, #16a34a, #0f766e);
  transition: width 0.25s ease;
}

.start-btn {
  width: 100%;
}

.back-btn {
  width: 100%;
  margin-top: 12rpx;
  min-height: 90rpx;
  border-radius: 999rpx;
  border: 2rpx solid rgba(15, 118, 110, 0.32);
  background: #ffffff;
  color: #0f766e;
  font-size: 33rpx;
  font-weight: 700;
}
</style>

