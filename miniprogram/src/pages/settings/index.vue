<!-- pages/settings/index.vue -->
<template>
  <view class="settings-container" :style="{ fontSize: fontSize + 'rpx' }">
    <!-- 设置内容 -->
    <scroll-view class="settings-content" scroll-y enhanced :show-scrollbar="false">
      <!-- 字体大小设置 -->
      <view class="settings-card">
        <view class="card-header">
          <text class="card-title">🔤 字体大小</text>
          <text class="card-desc">调整界面文字大小</text>
        </view>
        <view class="font-size-section">
          <view class="font-size-preview">
            <text class="preview-label">当前字号预览</text>
            <text class="preview-text">这是一段示例文字，用于预览字体大小效果</text>
          </view>
          <view class="font-size-controls">
            <view class="control-btn" @click="decreaseFontSize">
              <text class="control-icon">−</text>
            </view>
            <view class="font-size-display">
              <text class="font-size-value">{{ fontSize }}</text>
              <text class="font-size-unit">rpx</text>
            </view>
            <view class="control-btn" @click="increaseFontSize">
              <text class="control-icon">+</text>
            </view>
          </view>
          <view class="font-size-presets">
            <view 
              v-for="preset in fontPresets" 
              :key="preset.value"
              :class="['preset-btn', { active: fontSize === preset.value }]"
              @click="setFontSize(preset.value)"
            >
              <text class="preset-label">{{ preset.label }}</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 语音播报设置 -->
      <view class="settings-card">
        <view class="card-header">
          <text class="card-title">🔊 语音播报</text>
          <text class="card-desc">开启后自动播放语音提示</text>
        </view>
        <view class="voice-section">
          <view class="setting-item">
            <view class="setting-info">
              <text class="setting-name">开启语音播报</text>
              <text class="setting-desc">训练和测评时自动朗读题目内容</text>
            </view>
            <view :class="['switch-btn', { active: voiceEnabled }]" @click="toggleVoice">
              <view class="switch-thumb"></view>
            </view>
          </view>
          <view class="setting-item">
            <view class="setting-info">
              <text class="setting-name">播报速度</text>
              <text class="setting-desc">调整语音播放速度</text>
            </view>
            <view class="speed-control">
              <text class="speed-label">慢</text>
              <slider 
                :value="voiceSpeed" 
                :min="0.5" 
                :max="2" 
                :step="0.1"
                activeColor="#0891B2"
                backgroundColor="#e2e8f0"
                block-size="28"
                @change="onSpeedChange"
              />
              <text class="speed-label">快</text>
            </view>
          </view>
          <view class="setting-item">
            <view class="setting-info">
              <text class="setting-name">播报音量</text>
              <text class="setting-desc">调整语音播放音量</text>
            </view>
            <view class="volume-control">
              <text class="volume-label">小</text>
              <slider 
                :value="voiceVolume" 
                :min="0" 
                :max="1" 
                :step="0.1"
                activeColor="#0891B2"
                backgroundColor="#e2e8f0"
                block-size="28"
                @change="onVolumeChange"
              />
              <text class="volume-label">大</text>
            </view>
          </view>
          <view class="voice-preview">
            <view class="preview-btn" @click="previewVoice">
              <text class="preview-icon">🔊</text>
              <text class="preview-text">点击试听</text>
            </view>
          </view>
        </view>
      </view>

      <!-- 辅助功能 -->
      <view class="settings-card">
        <view class="card-header">
          <text class="card-title">⚡ 辅助功能</text>
          <text class="card-desc">适老化辅助设置</text>
        </view>
        <view class="accessibility-section">
          <view class="setting-item">
            <view class="setting-info">
              <text class="setting-name">高对比度模式</text>
              <text class="setting-desc">提高文字与背景的对比度</text>
            </view>
            <view :class="['switch-btn', { active: highContrast }]" @click="toggleHighContrast">
              <view class="switch-thumb"></view>
            </view>
          </view>
          <view class="setting-item">
            <view class="setting-info">
              <text class="setting-name">触觉反馈</text>
              <text class="setting-desc">操作时提供震动反馈</text>
            </view>
            <view :class="['switch-btn', { active: hapticFeedback }]" @click="toggleHaptic">
              <view class="switch-thumb"></view>
            </view>
          </view>
        </view>
      </view>

      <!-- 恢复默认设置 -->
      <view class="settings-card">
        <view class="reset-section">
          <view class="reset-btn" @click="resetSettings">
            <text class="reset-icon">↺</text>
            <text class="reset-text">恢复默认设置</text>
          </view>
        </view>
      </view>

      <!-- 版本信息 -->
      <view class="version-info">
        <text class="version-text">版本号：1.0.0</text>
        <text class="copyright">© 2026 忆守心安认知守护系统</text>
      </view>
    </scroll-view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'

// 字体大小设置
const fontSize = ref(28)
const fontPresets = [
  { label: '小', value: 24 },
  { label: '标准', value: 28 },
  { label: '大', value: 32 },
  { label: '超大', value: 36 }
]

// 语音播报设置
const voiceEnabled = ref(false)
const voiceSpeed = ref(1)
const voiceVolume = ref(0.8)

// 辅助功能设置
const highContrast = ref(false)
const hapticFeedback = ref(true)

// 加载保存的设置
const loadSettings = () => {
  try {
    const saved = uni.getStorageSync('elder_settings')
    if (saved) {
      const settings = typeof saved === 'string' ? JSON.parse(saved) : saved
      if (settings.fontSize !== undefined) fontSize.value = settings.fontSize
      if (settings.voiceEnabled !== undefined) voiceEnabled.value = settings.voiceEnabled
      if (settings.voiceSpeed !== undefined) voiceSpeed.value = settings.voiceSpeed
      if (settings.voiceVolume !== undefined) voiceVolume.value = settings.voiceVolume
      if (settings.highContrast !== undefined) highContrast.value = settings.highContrast
      if (settings.hapticFeedback !== undefined) hapticFeedback.value = settings.hapticFeedback
    }
  } catch (e) {
    console.error('加载设置失败', e)
  }
}

// 保存设置
const saveSettings = () => {
  try {
    const settings = {
      fontSize: fontSize.value,
      voiceEnabled: voiceEnabled.value,
      voiceSpeed: voiceSpeed.value,
      voiceVolume: voiceVolume.value,
      highContrast: highContrast.value,
      hapticFeedback: hapticFeedback.value
    }
    uni.setStorageSync('elder_settings', JSON.stringify(settings))
    // 发送广播通知其他页面更新设置
    uni.$emit('settingsChanged', settings)
  } catch (e) {
    console.error('保存设置失败', e)
  }
}

// 字体大小调节
const increaseFontSize = () => {
  if (fontSize.value < 40) {
    fontSize.value += 2
    saveSettings()
    uni.showToast({ title: '字体已调大', icon: 'none' })
  } else {
    uni.showToast({ title: '已达到最大字号', icon: 'none' })
  }
}

const decreaseFontSize = () => {
  if (fontSize.value > 20) {
    fontSize.value -= 2
    saveSettings()
    uni.showToast({ title: '字体已调小', icon: 'none' })
  } else {
    uni.showToast({ title: '已达到最小字号', icon: 'none' })
  }
}

const setFontSize = (size) => {
  fontSize.value = size
  saveSettings()
  uni.showToast({ title: '字体已设置', icon: 'none' })
}

// 语音播报开关
const toggleVoice = () => {
  voiceEnabled.value = !voiceEnabled.value
  saveSettings()
  if (voiceEnabled.value) {
    uni.showToast({ title: '语音播报已开启', icon: 'none' })
  } else {
    uni.showToast({ title: '语音播报已关闭', icon: 'none' })
  }
}

// 语速调整
const onSpeedChange = (e) => {
  voiceSpeed.value = e.detail.value
  saveSettings()
}

// 音量调整
const onVolumeChange = (e) => {
  voiceVolume.value = e.detail.value
  saveSettings()
}

// 语音预览
const previewVoice = () => {
  if (!voiceEnabled.value) {
    uni.showToast({ title: '请先开启语音播报', icon: 'none' })
    return
  }
  
  uni.showLoading({ title: '正在播放...' })
  
  // 使用微信小程序语音合成API
  const innerAudioContext = uni.createInnerAudioContext()
  
  // 模拟语音播报（实际项目中可接入语音合成服务）
  setTimeout(() => {
    uni.hideLoading()
    uni.showToast({ title: '语音预览功能已就绪', icon: 'none' })
    innerAudioContext.destroy()
  }, 1000)
}

// 高对比度模式
const toggleHighContrast = () => {
  highContrast.value = !highContrast.value
  saveSettings()
  if (highContrast.value) {
    uni.showToast({ title: '高对比度模式已开启', icon: 'none' })
  } else {
    uni.showToast({ title: '高对比度模式已关闭', icon: 'none' })
  }
}

// 触觉反馈
const toggleHaptic = () => {
  hapticFeedback.value = !hapticFeedback.value
  saveSettings()
  if (hapticFeedback.value) {
    uni.vibrateShort({})
    uni.showToast({ title: '触觉反馈已开启', icon: 'none' })
  } else {
    uni.showToast({ title: '触觉反馈已关闭', icon: 'none' })
  }
}

// 恢复默认设置
const resetSettings = () => {
  uni.showModal({
    title: '确认恢复',
    content: '确定要恢复所有设置为默认值吗？',
    confirmText: '确定',
    cancelText: '取消',
    success: (res) => {
      if (res.confirm) {
        fontSize.value = 28
        voiceEnabled.value = false
        voiceSpeed.value = 1
        voiceVolume.value = 0.8
        highContrast.value = false
        hapticFeedback.value = true
        saveSettings()
        uni.showToast({ title: '已恢复默认设置', icon: 'success' })
      }
    }
  })
}

// 返回上一页
const goBack = () => {
  uni.navigateBack()
}

onMounted(() => {
  loadSettings()
})
</script>

<style scoped>
.settings-container {
  min-height: 100vh;
  background-color: #f0f2f5;
}

/* 设置内容 */
.settings-content {
  min-height: calc(100vh - env(safe-area-inset-top));
  padding: 32rpx;
  padding-top: calc(32rpx + env(safe-area-inset-top));
}

/* 设置卡片 */
.settings-card {
  background-color: #ffffff;
  border-radius: 32rpx;
  padding: 32rpx;
  margin-bottom: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.card-header {
  margin-bottom: 28rpx;
}

.card-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #1e293b;
  display: block;
  margin-bottom: 8rpx;
}

.card-desc {
  font-size: 26rpx;
  color: #64748b;
}

/* 字体大小设置 */
.font-size-section {
  padding-top: 16rpx;
}

.font-size-preview {
  background-color: #f8fafc;
  border-radius: 24rpx;
  padding: 32rpx;
  margin-bottom: 32rpx;
}

.preview-label {
  font-size: 26rpx;
  color: #94a3b8;
  display: block;
  margin-bottom: 16rpx;
}

.preview-text {
  font-size: inherit;
  color: #1e293b;
  line-height: 1.8;
}

.font-size-controls {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 48rpx;
  margin-bottom: 32rpx;
}

.control-btn {
  width: 88rpx;
  height: 88rpx;
  background-color: #f1f5f9;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.control-btn:active {
  background-color: #e2e8f0;
}

.control-icon {
  font-size: 56rpx;
  color: #0891B2;
  font-weight: 300;
}

.font-size-display {
  display: flex;
  align-items: baseline;
  gap: 8rpx;
}

.font-size-value {
  font-size: 56rpx;
  font-weight: 800;
  color: #0891B2;
}

.font-size-unit {
  font-size: 28rpx;
  color: #94a3b8;
}

.font-size-presets {
  display: flex;
  justify-content: space-around;
}

.preset-btn {
  padding: 16rpx 32rpx;
  background-color: #f8fafc;
  border-radius: 40rpx;
  border: 2rpx solid transparent;
}

.preset-btn.active {
  background-color: #e0f2fe;
  border-color: #0891B2;
}

.preset-label {
  font-size: 28rpx;
  color: #475569;
}

.preset-btn.active .preset-label {
  color: #0891B2;
  font-weight: 600;
}

/* 设置项 */
.setting-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 0;
  border-bottom: 2rpx solid #f1f5f9;
}

.setting-item:last-child {
  border-bottom: none;
}

.setting-info {
  flex: 1;
}

.setting-name {
  font-size: 32rpx;
  font-weight: 600;
  color: #1e293b;
  display: block;
  margin-bottom: 8rpx;
}

.setting-desc {
  font-size: 26rpx;
  color: #64748b;
}

/* 开关按钮 */
.switch-btn {
  width: 120rpx;
  height: 68rpx;
  background-color: #e2e8f0;
  border-radius: 34rpx;
  padding: 6rpx;
  transition: all 0.3s ease;
}

.switch-btn.active {
  background-color: #0891B2;
}

.switch-thumb {
  width: 56rpx;
  height: 56rpx;
  background-color: #ffffff;
  border-radius: 50%;
  transition: transform 0.3s ease;
}

.switch-btn.active .switch-thumb {
  transform: translateX(52rpx);
}

/* 速度控制 */
.speed-control, .volume-control {
  display: flex;
  align-items: center;
  gap: 24rpx;
  flex: 1;
  justify-content: flex-end;
}

.speed-label, .volume-label {
  font-size: 24rpx;
  color: #94a3b8;
  width: 48rpx;
  text-align: center;
}

.speed-control slider, .volume-control slider {
  flex: 1;
  max-width: 280rpx;
}

/* 语音预览 */
.voice-preview {
  padding-top: 24rpx;
}

.preview-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  padding: 24rpx;
  background-color: #e0f2fe;
  border-radius: 24rpx;
}

.preview-btn:active {
  background-color: #bae6fd;
}

.preview-icon {
  font-size: 40rpx;
}

.preview-text {
  font-size: 30rpx;
  color: #0891B2;
  font-weight: 500;
}

/* 辅助功能 */
.accessibility-section {
  padding-top: 16rpx;
}

/* 恢复默认 */
.reset-section {
  padding-top: 16rpx;
}

.reset-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
  padding: 28rpx;
  background-color: #fef3c7;
  border-radius: 24rpx;
}

.reset-btn:active {
  background-color: #fde68a;
}

.reset-icon {
  font-size: 40rpx;
  color: #f59e0b;
}

.reset-text {
  font-size: 30rpx;
  color: #f59e0b;
  font-weight: 500;
}

/* 版本信息 */
.version-info {
  text-align: center;
  padding: 48rpx 32rpx;
}

.version-text {
  font-size: 26rpx;
  color: #94a3b8;
  display: block;
  margin-bottom: 12rpx;
}

.copyright {
  font-size: 24rpx;
  color: #cbd5e1;
}
</style>