<template>
  <view class="clock-page">
    <!-- Instructions -->
    <view class="instruction-card">
      <text class="instruction-title">✏️ 时钟绘制任务</text>
      <text class="instruction-text">请在下面的圆圈内画出时钟，使时针指向 <text class="highlight">11点10分</text></text>
    </view>

    <!-- Example Image Hint -->
    <view class="example-hint" @tap="toggleExample">
      <text class="example-icon">🖼</text>
      <text class="example-text">{{ showExample ? '隐藏示例' : '查看示例图' }}</text>
    </view>

    <!-- Example Clock -->
    <view v-if="showExample" class="example-box">
      <canvas
        canvas-id="exampleCanvas"
        id="exampleCanvas"
        class="example-canvas"
        style="width: 200px; height: 200px;"
      />
      <text class="example-caption">示例：11点10分的时钟</text>
    </view>

    <!-- Drawing Canvas -->
    <view class="canvas-container">
      <canvas
        canvas-id="clockCanvas"
        id="clockCanvas"
        class="clock-canvas"
        :style="{ width: canvasSize + 'px', height: canvasSize + 'px' }"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
      />
      <view class="canvas-overlay" v-if="!canvasReady">
        <text class="canvas-loading">画布加载中...</text>
      </view>
    </view>

    <!-- Drawing Controls -->
    <view class="drawing-controls">
      <button class="btn-control btn-undo" @tap="undoLastStroke" :disabled="strokes.length === 0">
        <text>↩ 撤销</text>
      </button>
      <button class="btn-control btn-clear" @tap="clearCanvas" :disabled="strokes.length === 0">
        <text>🗑 清除</text>
      </button>
      <view class="stroke-count">
        <text class="stroke-num">{{ strokes.length }}</text>
        <text class="stroke-label">笔画</text>
      </view>
    </view>

    <!-- Status Message -->
    <view v-if="statusMsg" class="status-box" :class="statusType">
      <text class="status-text">{{ statusMsg }}</text>
    </view>

    <!-- Submit Controls -->
    <view class="submit-area">
      <button
        class="btn-submit"
        :disabled="strokes.length === 0 || submitting"
        :loading="submitting"
        @tap="handleSubmit"
      >
        <text v-if="!submitting">✓ 提交时钟绘制</text>
        <text v-else>提交中...</text>
      </button>

      <button class="btn-skip" @tap="handleSkip">跳过此题</button>
    </view>

    <!-- Tips -->
    <view class="tips-card">
      <text class="tips-title">💡 绘制建议</text>
      <text class="tips-item">• 先画数字1-12，再画时针和分针</text>
      <text class="tips-item">• 11点10分：时针指向11，分针指向2</text>
      <text class="tips-item">• 画错了可以点"撤销"或"清除"重来</text>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

// Page params
const questionIndex = ref(0)
const questionId = ref('')

// Canvas state
const canvasSize = ref(300)
const canvasReady = ref(false)
const showExample = ref(false)
const submitting = ref(false)
const statusMsg = ref('')
const statusType = ref('info')

// Drawing state
const strokes = ref([])        // Array of completed strokes
let currentStroke = []         // Current stroke being drawn
let ctx = null                 // Canvas 2D context
let canvasOffsetX = 0
let canvasOffsetY = 0
const lineWidth = 4
const lineColor = '#222222'

onLoad((options) => {
  if (options.questionIndex !== undefined) {
    questionIndex.value = parseInt(options.questionIndex)
  }
  if (options.questionId) {
    questionId.value = options.questionId
  }
})

onMounted(() => {
  // Get screen info to set canvas size
  const sysInfo = wx.getSystemInfoSync()
  // Canvas fills screen width minus padding
  const size = Math.min(sysInfo.windowWidth - 60, sysInfo.windowHeight * 0.45)
  canvasSize.value = Math.floor(size)

  // Init after DOM settles
  setTimeout(() => {
    initCanvas()
    if (showExample.value) {
      drawExampleClock()
    }
  }, 300)
})

function initCanvas() {
  ctx = wx.createCanvasContext('clockCanvas')
  if (!ctx) {
    statusMsg.value = '画布初始化失败，请刷新重试'
    statusType.value = 'error'
    return
  }

  // Get canvas position for touch offset calculation
  const query = wx.createSelectorQuery()
  query.select('#clockCanvas').boundingClientRect((rect) => {
    if (rect) {
      canvasOffsetX = rect.left
      canvasOffsetY = rect.top
    }
  }).exec()

  canvasReady.value = true
  drawBaseClock()
}

function drawBaseClock() {
  if (!ctx) return

  const size = canvasSize.value
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - 10

  // Clear
  ctx.clearRect(0, 0, size, size)

  // White background
  ctx.setFillStyle('#FFFFFF')
  ctx.fillRect(0, 0, size, size)

  // Outer circle
  ctx.setStrokeStyle('#333333')
  ctx.setLineWidth(4)
  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, Math.PI * 2)
  ctx.stroke()

  // Center dot
  ctx.setFillStyle('#333333')
  ctx.beginPath()
  ctx.arc(cx, cy, 6, 0, Math.PI * 2)
  ctx.fill()

  ctx.draw(false)
}

function drawExampleClock() {
  const exCtx = wx.createCanvasContext('exampleCanvas')
  if (!exCtx) return

  const size = 200
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - 8

  exCtx.clearRect(0, 0, size, size)
  exCtx.setFillStyle('#FFFFFF')
  exCtx.fillRect(0, 0, size, size)

  // Circle
  exCtx.setStrokeStyle('#333333')
  exCtx.setLineWidth(3)
  exCtx.beginPath()
  exCtx.arc(cx, cy, r, 0, Math.PI * 2)
  exCtx.stroke()

  // Numbers
  exCtx.setFillStyle('#333333')
  exCtx.setFontSize(14)
  exCtx.setTextAlign('center')
  exCtx.setTextBaseline('middle')
  const numPositions = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  numPositions.forEach((num, idx) => {
    const angle = (idx * 30 - 90) * Math.PI / 180
    const nx = cx + (r - 18) * Math.cos(angle)
    const ny = cy + (r - 18) * Math.sin(angle)
    exCtx.fillText(String(num), nx, ny)
  })

  // Hour hand (11 o'clock position)
  const hourAngle = ((11 * 30) + (10 * 0.5) - 90) * Math.PI / 180
  exCtx.setStrokeStyle('#222222')
  exCtx.setLineWidth(5)
  exCtx.setLineCap('round')
  exCtx.beginPath()
  exCtx.moveTo(cx, cy)
  exCtx.lineTo(cx + (r * 0.5) * Math.cos(hourAngle), cy + (r * 0.5) * Math.sin(hourAngle))
  exCtx.stroke()

  // Minute hand (10 minutes = 2 position)
  const minAngle = (2 * 30 - 90) * Math.PI / 180
  exCtx.setStrokeStyle('#222222')
  exCtx.setLineWidth(3)
  exCtx.beginPath()
  exCtx.moveTo(cx, cy)
  exCtx.lineTo(cx + (r * 0.75) * Math.cos(minAngle), cy + (r * 0.75) * Math.sin(minAngle))
  exCtx.stroke()

  // Center dot
  exCtx.setFillStyle('#333333')
  exCtx.beginPath()
  exCtx.arc(cx, cy, 4, 0, Math.PI * 2)
  exCtx.fill()

  exCtx.draw(false)
}

function toggleExample() {
  showExample.value = !showExample.value
  if (showExample.value) {
    setTimeout(() => drawExampleClock(), 100)
  }
}

// Touch handlers
function getTouchPoint(e) {
  const touch = e.touches[0] || e.changedTouches[0]
  if (!touch) return null
  return {
    x: touch.clientX - canvasOffsetX,
    y: touch.clientY - canvasOffsetY
  }
}

function onTouchStart(e) {
  if (!canvasReady.value || !ctx) return
  const point = getTouchPoint(e)
  if (!point) return

  currentStroke = [point]
  ctx.beginPath()
  ctx.setStrokeStyle(lineColor)
  ctx.setLineWidth(lineWidth)
  ctx.setLineCap('round')
  ctx.setLineJoin('round')
  ctx.moveTo(point.x, point.y)
}

function onTouchMove(e) {
  if (!canvasReady.value || !ctx || currentStroke.length === 0) return
  const point = getTouchPoint(e)
  if (!point) return

  currentStroke.push(point)

  ctx.lineTo(point.x, point.y)
  ctx.stroke()
  ctx.draw(true) // append=true keeps existing drawing
}

function onTouchEnd(e) {
  if (!canvasReady.value || currentStroke.length === 0) return

  // Save completed stroke
  strokes.value.push([...currentStroke])
  currentStroke = []
}

function undoLastStroke() {
  if (strokes.value.length === 0) return
  strokes.value.pop()
  redrawCanvas()
}

function clearCanvas() {
  wx.showModal({
    title: '清除画布',
    content: '确定要清除所有笔画重新绘制吗？',
    confirmText: '清除',
    cancelText: '取消',
    confirmColor: '#F5222D',
    success: (res) => {
      if (res.confirm) {
        strokes.value = []
        currentStroke = []
        redrawCanvas()
      }
    }
  })
}

function redrawCanvas() {
  if (!ctx) return

  // Redraw base circle
  drawBaseClock()

  // Redraw all saved strokes
  strokes.value.forEach((stroke) => {
    if (stroke.length < 2) return
    ctx.beginPath()
    ctx.setStrokeStyle(lineColor)
    ctx.setLineWidth(lineWidth)
    ctx.setLineCap('round')
    ctx.setLineJoin('round')
    ctx.moveTo(stroke[0].x, stroke[0].y)
    for (let i = 1; i < stroke.length; i++) {
      ctx.lineTo(stroke[i].x, stroke[i].y)
    }
    ctx.stroke()
  })

  ctx.draw(false)
}

async function handleSubmit() {
  if (strokes.value.length === 0) {
    wx.showToast({ title: '请先绘制时钟', icon: 'none' })
    return
  }

  submitting.value = true

  try {
    // Capture canvas as image
    const imageData = await new Promise((resolve, reject) => {
      wx.canvasToTempFilePath({
        canvasId: 'clockCanvas',
        fileType: 'png',
        quality: 0.8,
        success: (res) => resolve(res.tempFilePath),
        fail: (err) => reject(err)
      })
    })

    // Prepare stroke data
    const strokeData = {
      strokes: strokes.value,
      canvas_size: canvasSize.value,
      stroke_count: strokes.value.length,
      total_points: strokes.value.reduce((sum, s) => sum + s.length, 0)
    }

    // Emit event to question page
    uni.$emit('clockDrawCompleted', {
      questionIndex: questionIndex.value,
      strokes: strokeData,
      imageData: imageData
    })

    wx.showToast({ title: '时钟提交成功', icon: 'success', duration: 1200 })

    setTimeout(() => {
      uni.navigateBack()
    }, 1200)
  } catch (err) {
    console.error('Submit clock draw error:', err)
    // Still emit without image
    uni.$emit('clockDrawCompleted', {
      questionIndex: questionIndex.value,
      strokes: { strokes: strokes.value, canvas_size: canvasSize.value },
      imageData: null
    })

    wx.showToast({ title: '已提交（无图片）', icon: 'none', duration: 1500 })
    setTimeout(() => uni.navigateBack(), 1500)
  } finally {
    submitting.value = false
  }
}

function handleSkip() {
  wx.showModal({
    title: '跳过此题',
    content: '时钟绘制对评估很重要，确定要跳过吗？',
    confirmText: '跳过',
    cancelText: '继续绘制',
    confirmColor: '#FA8C16',
    success: (res) => {
      if (res.confirm) {
        uni.$emit('clockDrawCompleted', {
          questionIndex: questionIndex.value,
          strokes: null,
          imageData: null,
          skipped: true
        })
        uni.navigateBack()
      }
    }
  })
}
</script>

<style scoped>
.clock-page {
  min-height: 100vh;
  background: #F0F4F8;
  padding-bottom: 60rpx;
  display: flex;
  flex-direction: column;
}

/* Instruction Card */
.instruction-card {
  background: #ffffff;
  margin: 20rpx 30rpx;
  border-radius: 20rpx;
  padding: 30rpx;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.instruction-title {
  font-size: 36rpx;
  font-weight: bold;
  color: #333333;
  display: block;
  margin-bottom: 16rpx;
}

.instruction-text {
  font-size: 36rpx;
  color: #555555;
  line-height: 1.6;
  display: block;
}

.highlight {
  color: #F5222D;
  font-weight: bold;
  font-size: 40rpx;
}

/* Example */
.example-hint {
  display: flex;
  align-items: center;
  gap: 12rpx;
  margin: 0 30rpx 12rpx;
  padding: 16rpx 20rpx;
  background: #E6F7FF;
  border-radius: 12rpx;
  border: 2rpx solid #91D5FF;
}

.example-icon {
  font-size: 32rpx;
}

.example-text {
  font-size: 30rpx;
  color: #1890FF;
  font-weight: 500;
}

.example-box {
  margin: 0 30rpx 12rpx;
  background: #ffffff;
  border-radius: 16rpx;
  padding: 20rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
  box-shadow: 0 2rpx 12rpx rgba(0, 0, 0, 0.06);
}

.example-canvas {
  border: 2rpx solid #E0E0E0;
  border-radius: 50%;
}

.example-caption {
  font-size: 28rpx;
  color: #999999;
  margin-top: 12rpx;
}

/* Canvas Container */
.canvas-container {
  margin: 0 30rpx;
  display: flex;
  justify-content: center;
  align-items: center;
  position: relative;
  background: #ffffff;
  border-radius: 20rpx;
  padding: 20rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.1);
}

.clock-canvas {
  border: 3rpx solid #E0E0E0;
  border-radius: 8rpx;
  background: #ffffff;
  display: block;
}

.canvas-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 20rpx;
}

.canvas-loading {
  font-size: 32rpx;
  color: #999999;
}

/* Drawing Controls */
.drawing-controls {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin: 20rpx 30rpx 0;
}

.btn-control {
  flex: 1;
  height: 80rpx;
  font-size: 30rpx;
  border-radius: 40rpx;
  border: 2rpx solid #E0E0E0;
}

.btn-undo {
  background: #ffffff;
  color: #4A90D9;
  border-color: #4A90D9;
}

.btn-clear {
  background: #ffffff;
  color: #F5222D;
  border-color: #F5222D;
}

.btn-control[disabled] {
  background: #F5F5F5;
  color: #CCCCCC;
  border-color: #E8E8E8;
}

.stroke-count {
  min-width: 80rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stroke-num {
  font-size: 40rpx;
  font-weight: bold;
  color: #4A90D9;
}

.stroke-label {
  font-size: 28rpx;
  color: #999999;
}

/* Status */
.status-box {
  margin: 16rpx 30rpx 0;
  padding: 16rpx 24rpx;
  border-radius: 12rpx;
}

.status-box.info { background: #E6F7FF; }
.status-box.success { background: #F6FFED; }
.status-box.error { background: #FFF2F0; }

.status-text {
  font-size: 28rpx;
  color: #333333;
}

/* Submit Area */
.submit-area {
  margin: 24rpx 30rpx 0;
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.btn-submit {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #1890FF, #096DD9);
  color: #ffffff;
  font-size: 40rpx;
  font-weight: bold;
  border-radius: 50rpx;
  border: none;
  box-shadow: 0 6rpx 20rpx rgba(24, 144, 255, 0.4);
  letter-spacing: 2rpx;
}

.btn-submit[disabled] {
  background: #B0C4DE;
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
  margin: 20rpx 30rpx 0;
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
