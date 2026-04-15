<template>
  <view class="voice-page">
    <view class="mg-card top-card">
      <text class="top-title">语音任务</text>
      <text class="top-desc">请清晰朗读下列内容：</text>
      <text class="task-text">{{ taskText }}</text>
    </view>

    <view class="mg-card recorder-card">
      <view class="timer-wrap" :class="{ active: isRecording }">
        <text class="timer-value">{{ timerDisplay }}</text>
        <text class="timer-label">{{ isRecording ? '正在录音' : '录音时长' }}</text>
      </view>

      <view class="mic-wrap" :class="{ recording: isRecording, recorded: isRecorded && !isRecording }" @tap="toggleRecording">
        <view v-if="isRecording" class="mic-wave wave-1" />
        <view v-if="isRecording" class="mic-wave wave-2" />
        <view class="mic-main">
          <text class="mic-icon">{{ micIcon }}</text>
        </view>
      </view>

      <text class="mic-tip">{{ micLabel }}</text>

      <view v-if="isRecording" class="record-progress">
        <view class="record-progress-fill" :style="{ width: recordProgressPercent + '%' }" />
      </view>
      <text v-if="isRecording" class="record-hint">最长可录制 {{ maxSeconds }} 秒</text>
    </view>

    <view v-if="isRecorded" class="mg-card play-card">
      <text class="play-title">录音预览</text>
      <view class="play-actions">
        <button class="play-btn" :class="{ playing: isPlaying }" @tap="togglePlayback">
          {{ isPlaying ? '暂停播放' : '播放录音' }}
        </button>
        <button class="reset-btn" @tap="reRecord">重新录音</button>
      </view>
    </view>

    <view class="status-zone">
      <view v-if="statusMsg" class="status-box" :class="statusType">
        <text class="status-text">{{ statusMsg }}</text>
      </view>
    </view>

    <view class="action-zone">
      <button v-if="isRecorded && !uploading" class="submit-btn" @tap="handleSubmit">提交语音</button>
      <button v-if="uploading" class="submit-btn uploading" loading disabled>上传中...</button>
      <button class="skip-btn" @tap="handleSkip">跳过此题</button>
    </view>

    <view class="tip-card">
      <text class="tip-title">录音建议</text>
      <text class="tip-item">1. 尽量靠近麦克风，保持稳定音量。</text>
      <text class="tip-item">2. 语速适中，吐字清晰。</text>
      <text class="tip-item">3. 提交前可先回放确认质量。</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const questionIndex = ref(0)
const questionId = ref('')
const taskText = ref('请大声朗读并尝试记忆：苹果、汽车、诚信、丝绸、玫瑰。')

const isRecording = ref(false)
const isRecorded = ref(false)
const isPlaying = ref(false)
const uploading = ref(false)
const tempFilePath = ref('')
const statusMsg = ref('')
const statusType = ref('info')

const seconds = ref(0)
const maxSeconds = 60
let timerInterval = null
let autoStopTimeout = null

let recorderManager = null
let innerAudioContext = null

const timerDisplay = computed(() => {
  const m = Math.floor(seconds.value / 60)
  const sec = seconds.value % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
})

const recordProgressPercent = computed(() => Math.min((seconds.value / maxSeconds) * 100, 100))

const micIcon = computed(() => {
  if (isRecording.value) return '■'
  if (isRecorded.value) return '✓'
  return '🎙️'
})

const micLabel = computed(() => {
  if (isRecording.value) return '点击停止录音'
  if (isRecorded.value) return '点击可重新录制'
  return '点击开始录音'
})

onLoad((options) => {
  if (options.questionIndex !== undefined) {
    questionIndex.value = parseInt(options.questionIndex)
  }
  if (options.questionId) {
    questionId.value = options.questionId
  }
  if (options.taskText) {
    taskText.value = decodeURIComponent(options.taskText)
  }
})

onMounted(() => {
  initRecorder()
})

onUnmounted(() => {
  cleanup()
})

function initRecorder() {
  recorderManager = wx.getRecorderManager()

  recorderManager.onStart(() => {
    isRecording.value = true
    statusMsg.value = '正在录音，请开始作答...'
    statusType.value = 'recording'
    startTimer()
  })

  recorderManager.onStop((res) => {
    isRecording.value = false
    stopTimer()

    if (res.tempFilePath) {
      tempFilePath.value = res.tempFilePath
      isRecorded.value = true
      statusMsg.value = '录音完成，可试听后提交。'
      statusType.value = 'success'
    } else {
      statusMsg.value = '录音失败，请重新尝试。'
      statusType.value = 'error'
    }
  })

  recorderManager.onError((err) => {
    isRecording.value = false
    stopTimer()
    console.error('Recorder error:', err)
    if (err.errMsg && err.errMsg.includes('auth')) {
      statusMsg.value = '请先授权麦克风权限。'
    } else {
      statusMsg.value = `录音失败：${err.errMsg || '未知错误'}`
    }
    statusType.value = 'error'
  })
}

function toggleRecording() {
  if (isRecording.value) {
    stopRecording()
  } else {
    startRecording()
  }
}

function startRecording() {
  wx.authorize({
    scope: 'scope.record',
    success: () => {
      seconds.value = 0
      statusMsg.value = ''
      recorderManager.start({
        duration: maxSeconds * 1000,
        sampleRate: 16000,
        numberOfChannels: 1,
        encodeBitRate: 48000,
        format: 'mp3',
      })

      autoStopTimeout = setTimeout(() => {
        if (isRecording.value) {
          stopRecording()
        }
      }, maxSeconds * 1000 + 500)
    },
    fail: () => {
      wx.showModal({
        title: '需要麦克风权限',
        content: '请在设置中开启麦克风权限后再试。',
        confirmText: '去设置',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) wx.openSetting()
        },
      })
    },
  })
}

function stopRecording() {
  if (autoStopTimeout) {
    clearTimeout(autoStopTimeout)
    autoStopTimeout = null
  }
  recorderManager.stop()
}

function startTimer() {
  timerInterval = setInterval(() => {
    seconds.value += 1
    if (seconds.value >= maxSeconds) {
      stopRecording()
    }
  }, 1000)
}

function stopTimer() {
  if (timerInterval) {
    clearInterval(timerInterval)
    timerInterval = null
  }
}

function ensureAudioContext() {
  if (!innerAudioContext) {
    innerAudioContext = wx.createInnerAudioContext()
    innerAudioContext.onEnded(() => {
      isPlaying.value = false
      statusMsg.value = '播放完成'
      statusType.value = 'success'
    })
    innerAudioContext.onError((err) => {
      isPlaying.value = false
      console.error('Playback error:', err)
      statusMsg.value = '播放失败，但仍可提交录音。'
      statusType.value = 'error'
    })
  }
}

function togglePlayback() {
  if (!tempFilePath.value) return

  ensureAudioContext()

  if (isPlaying.value) {
    innerAudioContext.pause()
    isPlaying.value = false
    return
  }

  innerAudioContext.src = tempFilePath.value
  innerAudioContext.play()
  isPlaying.value = true
  statusMsg.value = '正在播放录音...'
  statusType.value = 'info'
}

function reRecord() {
  if (isPlaying.value && innerAudioContext) {
    innerAudioContext.stop()
  }
  isPlaying.value = false
  isRecorded.value = false
  tempFilePath.value = ''
  seconds.value = 0
  statusMsg.value = ''
}

async function handleSubmit() {
  if (!tempFilePath.value) {
    wx.showToast({ title: '请先录制语音', icon: 'none' })
    return
  }

  uploading.value = true
  statusMsg.value = '正在保存录音...'
  statusType.value = 'info'

  try {
    uni.$emit('voiceTaskCompleted', {
      questionIndex: questionIndex.value,
      filePath: tempFilePath.value,
      durationSec: seconds.value,
      transcript: '',
    })

    wx.showToast({ title: '语音已保存', icon: 'success', duration: 1200 })

    setTimeout(() => {
      uni.navigateBack()
    }, 1200)
  } catch (err) {
    console.error('Save voice task error:', err)
    statusMsg.value = '保存失败，请重试。'
    statusType.value = 'error'
  } finally {
    uploading.value = false
  }
}

function handleSkip() {
  wx.showModal({
    title: '跳过此题',
    content: '跳过语音题会影响评估准确性，确定跳过吗？',
    confirmText: '跳过',
    cancelText: '继续录音',
    confirmColor: '#d97706',
    success: (res) => {
      if (res.confirm) {
        uni.$emit('voiceTaskCompleted', {
          questionIndex: questionIndex.value,
          filePath: null,
          skipped: true,
        })
        uni.navigateBack()
      }
    },
  })
}

function cleanup() {
  stopTimer()
  if (autoStopTimeout) {
    clearTimeout(autoStopTimeout)
    autoStopTimeout = null
  }
  if (isRecording.value) {
    try {
      recorderManager.stop()
    } catch (e) {
      // ignore
    }
  }
  if (innerAudioContext) {
    try {
      innerAudioContext.stop()
      innerAudioContext.destroy()
    } catch (e) {
      // ignore
    }
  }
}
</script>

<style scoped>
.voice-page {
  min-height: 100vh;
  padding-bottom: 52rpx;
}

.top-card {
  margin: 16rpx 24rpx 0;
  padding: 24rpx;
}

.top-title {
  display: block;
  font-size: 36rpx;
  font-weight: 800;
  color: #143445;
}

.top-desc {
  display: block;
  margin-top: 8rpx;
  font-size: 29rpx;
  color: #607889;
}

.task-text {
  display: block;
  margin-top: 10rpx;
  font-size: 35rpx;
  color: #16384b;
  font-weight: 700;
  line-height: 1.7;
}

.recorder-card {
  margin: 16rpx 24rpx 0;
  padding: 28rpx 20rpx;
  text-align: center;
}

.timer-wrap {
  border-radius: 16rpx;
  padding: 10rpx 14rpx;
  background: #f4f8fb;
  display: inline-flex;
  flex-direction: column;
  align-items: center;
}

.timer-wrap.active {
  background: #fff0f6;
}

.timer-value {
  font-size: 66rpx;
  color: #143445;
  font-weight: 800;
  font-variant-numeric: tabular-nums;
}

.timer-wrap.active .timer-value {
  color: #db2777;
}

.timer-label {
  color: #6e8899;
  font-size: 29rpx;
}

.mic-wrap {
  width: 210rpx;
  height: 210rpx;
  margin: 22rpx auto 10rpx;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
}

.mic-wave {
  position: absolute;
  width: 210rpx;
  height: 210rpx;
  border-radius: 50%;
  background: rgba(219, 39, 119, 0.14);
  animation: ripple 1.5s ease-out infinite;
}

.wave-2 {
  animation-delay: 0.75s;
}

@keyframes ripple {
  0% {
    transform: scale(1);
    opacity: 1;
  }
  100% {
    transform: scale(1.5);
    opacity: 0;
  }
}

.mic-main {
  width: 170rpx;
  height: 170rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #db2777, #be185d);
  box-shadow: 0 12rpx 24rpx rgba(219, 39, 119, 0.3);
  display: flex;
  align-items: center;
  justify-content: center;
}

.mic-wrap.recording .mic-main {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
}

.mic-wrap.recorded .mic-main {
  background: linear-gradient(135deg, #16a34a, #15803d);
}

.mic-icon {
  color: #ffffff;
  font-size: 52rpx;
  font-weight: 800;
}

.mic-tip {
  display: block;
  font-size: 31rpx;
  color: #486273;
  font-weight: 600;
}

.record-progress {
  margin-top: 16rpx;
  width: 100%;
  height: 10rpx;
  border-radius: 999rpx;
  background: #dce7ef;
  overflow: hidden;
}

.record-progress-fill {
  height: 100%;
  border-radius: 999rpx;
  background: linear-gradient(90deg, #16a34a, #dc2626);
  transition: width 1s linear;
}

.record-hint {
  display: block;
  margin-top: 8rpx;
  font-size: 29rpx;
  color: #8199a8;
}

.play-card {
  margin: 16rpx 24rpx 0;
  padding: 20rpx;
}

.play-title {
  display: block;
  font-size: 32rpx;
  color: #16384b;
  font-weight: 700;
  margin-bottom: 12rpx;
}

.play-actions {
  display: flex;
  gap: 10rpx;
}

.play-btn,
.reset-btn {
  flex: 1;
  min-height: 94rpx;
  border-radius: 999rpx;
  font-size: 30rpx;
  font-weight: 700;
  border: none;
}

.play-btn {
  background: #0f766e;
  color: #ffffff;
}

.play-btn.playing {
  background: #d97706;
}

.reset-btn {
  background: #ffffff;
  color: #5f7889;
  border: 2rpx solid #d3dee7;
}

.status-zone {
  margin: 12rpx 24rpx 0;
}

.status-box {
  border-radius: 14rpx;
  padding: 14rpx 16rpx;
}

.status-box.info {
  background: #e6f7ff;
}

.status-box.recording {
  background: #fff0f6;
}

.status-box.success {
  background: #f6ffed;
}

.status-box.error {
  background: #fff2f0;
}

.status-text {
  color: #1f3e50;
  font-size: 28rpx;
}

.action-zone {
  margin: 14rpx 24rpx 0;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.submit-btn {
  width: 100%;
  min-height: 92rpx;
  border-radius: 999rpx;
  border: none;
  background: linear-gradient(135deg, #16a34a, #15803d);
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
}

.submit-btn.uploading {
  background: #9fd5bb;
}

.skip-btn {
  width: 100%;
  min-height: 92rpx;
  border-radius: 999rpx;
  border: 2rpx solid #d3dee7;
  background: #ffffff;
  color: #8ba0ae;
  font-size: 30rpx;
}

.tip-card {
  margin: 14rpx 24rpx 0;
  border-radius: 16rpx;
  border: 2rpx solid #ffe58f;
  background: #fffbe6;
  padding: 18rpx;
}

.tip-title {
  display: block;
  color: #8a5b00;
  font-size: 29rpx;
  font-weight: 700;
}

.tip-item {
  display: block;
  margin-top: 6rpx;
  color: #ad6800;
  font-size: 27rpx;
  line-height: 1.6;
}
</style>

