<template>
  <view class="voice-page">
    <!-- Instructions -->
    <view class="instruction-card">
      <text class="instruction-label">📋 任务说明</text>
      <text class="instruction-text">{{ taskText }}</text>
    </view>

    <!-- Main Recording Area -->
    <view class="recording-area">
      <!-- Timer Display -->
      <view class="timer-display" :class="{ active: isRecording }">
        <text class="timer-text">{{ timerDisplay }}</text>
        <text class="timer-label">{{ isRecording ? '正在录音' : '时长' }}</text>
      </view>

      <!-- Mic Button -->
      <view
        class="mic-button-wrap"
        :class="{ recording: isRecording, recorded: isRecorded && !isRecording }"
        @tap="toggleRecording"
      >
        <view class="mic-ripple" v-if="isRecording" />
        <view class="mic-ripple mic-ripple-2" v-if="isRecording" />
        <view class="mic-circle">
          <text class="mic-icon">{{ isRecording ? '⏹' : (isRecorded ? '🔁' : '🎤') }}</text>
        </view>
      </view>

      <!-- Mic Button Label -->
      <text class="mic-label">{{ micLabel }}</text>

      <!-- Recording Progress Bar -->
      <view v-if="isRecording" class="record-progress">
        <view class="record-progress-fill" :style="{ width: recordProgressPercent + '%' }" />
      </view>
      <text v-if="isRecording" class="record-limit-hint">最长可录制 {{ maxSeconds }} 秒</text>
    </view>

    <!-- Playback Area (after recording) -->
    <view v-if="isRecorded" class="playback-card">
      <text class="playback-title">录音预览</text>
      <view class="playback-controls">
        <button
          class="btn-play"
          :class="{ playing: isPlaying }"
          @tap="togglePlayback"
        >
          <text class="play-icon">{{ isPlaying ? '⏸' : '▶' }}</text>
          <text class="play-text">{{ isPlaying ? '暂停播放' : '播放录音' }}</text>
        </button>

        <button class="btn-rerecord" @tap="reRecord">
          <text>🔄 重新录音</text>
        </button>
      </view>
    </view>

    <!-- Status Messages -->
    <view class="status-area">
      <view v-if="statusMsg" class="status-box" :class="statusType">
        <text class="status-text">{{ statusMsg }}</text>
      </view>
    </view>

    <!-- Action Buttons -->
    <view class="actions-area">
      <!-- Upload & Submit -->
      <button
        v-if="isRecorded && !uploading"
        class="btn-submit"
        @tap="handleSubmit"
      >
        <text>✓ 提交录音</text>
      </button>

      <button
        v-if="uploading"
        class="btn-submit btn-uploading"
        loading
        disabled
      >
        <text>上传中...</text>
      </button>

      <!-- Skip (fallback) -->
      <button class="btn-skip" @tap="handleSkip">跳过此题</button>
    </view>

    <!-- Tips -->
    <view class="tips-card">
      <text class="tips-title">💡 录音建议</text>
      <text class="tips-item">• 靠近手机麦克风，保持约20厘米距离</text>
      <text class="tips-item">• 说话速度适中，吐字清晰</text>
      <text class="tips-item">• 录制完成后可先试听再提交</text>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

// Page params
const questionIndex = ref(0)
const questionId = ref('')
const taskText = ref('请大声朗读以下词语，并尝试记忆：\n苹果、汽车、诚实、丝绸、玫瑰')

// Recording state
const isRecording = ref(false)
const isRecorded = ref(false)
const isPlaying = ref(false)
const uploading = ref(false)
const tempFilePath = ref('')
const statusMsg = ref('')
const statusType = ref('info')

// Timer
const seconds = ref(0)
const maxSeconds = 60
let timerInterval = null
let autoStopTimeout = null

// Recorder manager
let recorderManager = null
let innerAudioContext = null

// Computed
const timerDisplay = computed(() => {
  const s = seconds.value
  const m = Math.floor(s / 60)
  const sec = s % 60
  return `${String(m).padStart(2, '0')}:${String(sec).padStart(2, '0')}`
})

const recordProgressPercent = computed(() => {
  return Math.min((seconds.value / maxSeconds) * 100, 100)
})

const micLabel = computed(() => {
  if (isRecording.value) return '点击停止录音'
  if (isRecorded.value) return '点击重新录音'
  return '点击开始录音'
})

// Init on load
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
    statusMsg.value = '正在录音，请说话...'
    statusType.value = 'recording'
    startTimer()
  })

  recorderManager.onStop((res) => {
    isRecording.value = false
    stopTimer()
    if (res.tempFilePath) {
      tempFilePath.value = res.tempFilePath
      isRecorded.value = true
      statusMsg.value = '录音完成！可以试听或直接提交'
      statusType.value = 'success'
    } else {
      statusMsg.value = '录音出现问题，请重试'
      statusType.value = 'error'
    }
  })

  recorderManager.onError((err) => {
    isRecording.value = false
    stopTimer()
    console.error('Recorder error:', err)
    if (err.errMsg && err.errMsg.includes('auth')) {
      statusMsg.value = '请先授权麦克风权限后重试'
    } else {
      statusMsg.value = '录音失败：' + (err.errMsg || '未知错误')
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
  // Check permission first
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
        format: 'mp3'
      })

      // Auto stop safety net
      autoStopTimeout = setTimeout(() => {
        if (isRecording.value) {
          stopRecording()
        }
      }, maxSeconds * 1000 + 500)
    },
    fail: () => {
      wx.showModal({
        title: '需要麦克风权限',
        content: '请在设置中开启麦克风权限，才能进行语音录制',
        confirmText: '去设置',
        cancelText: '取消',
        success: (res) => {
          if (res.confirm) {
            wx.openSetting()
          }
        }
      })
    }
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
    seconds.value++
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

function togglePlayback() {
  if (!tempFilePath.value) return

  if (isPlaying.value) {
    if (innerAudioContext) {
      innerAudioContext.pause()
    }
    isPlaying.value = false
    return
  }

  innerAudioContext = wx.createInnerAudioContext()
  innerAudioContext.src = tempFilePath.value
  innerAudioContext.onPlay(() => {
    isPlaying.value = true
    statusMsg.value = '正在播放...'
    statusType.value = 'info'
  })
  innerAudioContext.onEnded(() => {
    isPlaying.value = false
    statusMsg.value = '播放完成'
    statusType.value = 'success'
  })
  innerAudioContext.onError((err) => {
    isPlaying.value = false
    console.error('Playback error:', err)
    statusMsg.value = '播放失败，但您可以直接提交'
    statusType.value = 'error'
  })
  innerAudioContext.play()
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
      transcript: ''
    })

    wx.showToast({ title: '语音已保存', icon: 'success', duration: 1200 })

    setTimeout(() => {
      uni.navigateBack()
    }, 1200)
  } catch (err) {
    console.error('Save voice task error:', err)
    statusMsg.value = '保存失败，请重试'
    statusType.value = 'error'
  } finally {
    uploading.value = false
  }
}

function handleSkip() {
  wx.showModal({
    title: '跳过此题',
    content: '跳过语音题会影响评估准确性，确定要跳过吗？',
    confirmText: '跳过',
    cancelText: '继续录音',
    confirmColor: '#FA8C16',
    success: (res) => {
      if (res.confirm) {
        uni.$emit('voiceTaskCompleted', {
          questionIndex: questionIndex.value,
          filePath: null,
          skipped: true
        })
        uni.navigateBack()
      }
    }
  })
}

function cleanup() {
  stopTimer()
  if (autoStopTimeout) clearTimeout(autoStopTimeout)
  if (isRecording.value) {
    try { recorderManager.stop() } catch (e) {}
  }
  if (innerAudioContext) {
    try { innerAudioContext.stop(); innerAudioContext.destroy() } catch (e) {}
  }
}
</script>

<style scoped>
.voice-page {
  min-height: 100vh;
  background: #F0F4F8;
  padding: 0 0 60rpx;
  display: flex;
  flex-direction: column;
}

/* Instruction Card */
.instruction-card {
  background: #ffffff;
  padding: 30rpx;
  margin: 20rpx 30rpx;
  border-radius: 20rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.instruction-label {
  font-size: 30rpx;
  font-weight: bold;
  color: #4A90D9;
  display: block;
  margin-bottom: 16rpx;
}

.instruction-text {
  font-size: 40rpx;
  color: #222222;
  line-height: 1.8;
  font-weight: 500;
  display: block;
  white-space: pre-wrap;
}

/* Recording Area */
.recording-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 40rpx 30rpx;
  background: #ffffff;
  margin: 0 30rpx;
  border-radius: 24rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.08);
}

/* Timer */
.timer-display {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: 40rpx;
  padding: 20rpx 40rpx;
  border-radius: 16rpx;
  background: #F8F9FA;
  min-width: 200rpx;
}

.timer-display.active {
  background: #FFF0F6;
}

.timer-text {
  font-size: 72rpx;
  font-weight: bold;
  color: #333333;
  font-variant-numeric: tabular-nums;
}

.timer-display.active .timer-text {
  color: #EB2F96;
}

.timer-label {
  font-size: 28rpx;
  color: #999999;
  margin-top: 4rpx;
}

/* Mic Button */
.mic-button-wrap {
  width: 220rpx;
  height: 220rpx;
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 30rpx;
}

.mic-ripple {
  position: absolute;
  width: 220rpx;
  height: 220rpx;
  border-radius: 50%;
  background: rgba(235, 47, 150, 0.15);
  animation: ripple 1.5s ease-out infinite;
}

.mic-ripple-2 {
  background: rgba(235, 47, 150, 0.1);
  animation-delay: 0.75s;
}

@keyframes ripple {
  0% { transform: scale(1); opacity: 1; }
  100% { transform: scale(1.6); opacity: 0; }
}

.mic-circle {
  width: 180rpx;
  height: 180rpx;
  border-radius: 50%;
  background: linear-gradient(135deg, #EB2F96, #C41D7F);
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 8rpx 30rpx rgba(235, 47, 150, 0.4);
  z-index: 1;
  transition: all 0.2s;
}

.mic-button-wrap.recording .mic-circle {
  background: linear-gradient(135deg, #F5222D, #A8071A);
  box-shadow: 0 8rpx 30rpx rgba(245, 34, 45, 0.4);
}

.mic-button-wrap.recorded .mic-circle {
  background: linear-gradient(135deg, #52C41A, #389E0D);
  box-shadow: 0 8rpx 30rpx rgba(82, 196, 26, 0.4);
}

.mic-icon {
  font-size: 72rpx;
}

.mic-label {
  font-size: 34rpx;
  color: #555555;
  font-weight: 500;
  margin-bottom: 20rpx;
}

/* Record Progress */
.record-progress {
  width: 100%;
  height: 10rpx;
  background: #E8E8E8;
  border-radius: 5rpx;
  overflow: hidden;
  margin-bottom: 8rpx;
}

.record-progress-fill {
  height: 100%;
  background: linear-gradient(90deg, #52C41A, #F5222D);
  border-radius: 5rpx;
  transition: width 1s linear;
}

.record-limit-hint {
  font-size: 28rpx;
  color: #AAAAAA;
}

/* Playback Card */
.playback-card {
  background: #ffffff;
  border-radius: 20rpx;
  margin: 20rpx 30rpx 0;
  padding: 30rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.playback-title {
  font-size: 32rpx;
  font-weight: bold;
  color: #333333;
  display: block;
  margin-bottom: 20rpx;
}

.playback-controls {
  display: flex;
  gap: 16rpx;
}

.btn-play {
  flex: 1;
  height: 88rpx;
  background: #4A90D9;
  color: #ffffff;
  font-size: 32rpx;
  border-radius: 44rpx;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8rpx;
}

.btn-play.playing {
  background: #FA8C16;
}

.play-icon {
  font-size: 32rpx;
}

.play-text {
  font-size: 32rpx;
}

.btn-rerecord {
  flex: 1;
  height: 88rpx;
  background: #ffffff;
  color: #666666;
  font-size: 30rpx;
  border-radius: 44rpx;
  border: 2rpx solid #E0E0E0;
}

/* Status Area */
.status-area {
  margin: 16rpx 30rpx 0;
}

.status-box {
  padding: 20rpx 24rpx;
  border-radius: 12rpx;
}

.status-box.info { background: #E6F7FF; }
.status-box.recording { background: #FFF0F6; }
.status-box.success { background: #F6FFED; }
.status-box.error { background: #FFF2F0; }

.status-text {
  font-size: 30rpx;
  color: #333333;
}

/* Actions Area */
.actions-area {
  margin: 24rpx 30rpx 0;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.btn-submit {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #52C41A, #389E0D);
  color: #ffffff;
  font-size: 40rpx;
  font-weight: bold;
  border-radius: 50rpx;
  border: none;
  box-shadow: 0 6rpx 20rpx rgba(82, 196, 26, 0.4);
  letter-spacing: 2rpx;
}

.btn-uploading {
  background: #B7EB8F;
  box-shadow: none;
}

.btn-skip {
  width: 100%;
  height: 80rpx;
  background: transparent;
  color: #AAAAAA;
  font-size: 30rpx;
  border: 2rpx solid #E0E0E0;
  border-radius: 40rpx;
}

/* Tips */
.tips-card {
  background: #FFFBE6;
  border: 2rpx solid #FFE58F;
  border-radius: 16rpx;
  margin: 24rpx 30rpx 0;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  gap: 10rpx;
}

.tips-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #875500;
  margin-bottom: 8rpx;
}

.tips-item {
  font-size: 28rpx;
  color: #AD6800;
  line-height: 1.5;
}
</style>
