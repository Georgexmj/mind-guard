<template>
  <view class="clock-page">
    <view class="mg-card head-card">
      <text class="head-title">时钟绘制任务</text>
      <text class="head-desc">请在圆形画布内绘制时钟，要求时间为 <text class="highlight">11:10</text>。</text>
    </view>

    <view class="example-toggle" @tap="toggleExample">
      <text class="example-toggle-text">{{ showExample ? '收起示例' : '查看示例图' }}</text>
    </view>

    <view v-if="showExample" class="mg-card example-card">
      <canvas canvas-id="exampleCanvas" id="exampleCanvas" class="example-canvas" style="width: 200px; height: 200px;" />
      <text class="example-caption">示例：11 点 10 分</text>
    </view>

    <view class="mg-card canvas-card">
      <canvas
        canvas-id="clockCanvas"
        id="clockCanvas"
        class="clock-canvas"
        :style="{ width: canvasSize + 'px', height: canvasSize + 'px' }"
        @touchstart="onTouchStart"
        @touchmove="onTouchMove"
        @touchend="onTouchEnd"
      />
      <view v-if="!canvasReady" class="canvas-mask">
        <text class="canvas-mask-text">画布加载中...</text>
      </view>
    </view>

    <view class="control-row">
      <button class="ctrl-btn undo" :disabled="strokes.length === 0" @tap="undoLastStroke">撤销</button>
      <button class="ctrl-btn clear" :disabled="strokes.length === 0" @tap="clearCanvas">清空</button>
      <view class="stroke-info">
        <text class="stroke-value">{{ strokes.length }}</text>
        <text class="stroke-label">笔</text>
      </view>
    </view>

    <view v-if="statusMsg" class="status-box" :class="statusType">
      <text class="status-text">{{ statusMsg }}</text>
    </view>

    <view class="action-row">
      <button class="submit-btn" :disabled="strokes.length === 0 || submitting" :loading="submitting" @tap="handleSubmit">
        {{ submitting ? '提交中...' : '提交绘图' }}
      </button>
      <button class="skip-btn" @tap="handleSkip">跳过此题</button>
    </view>

    <view class="tip-card">
      <text class="tip-title">绘制建议</text>
      <text class="tip-item">1. 建议先画数字，再画时针和分针。</text>
      <text class="tip-item">2. 11:10 对应时针指向 11 附近，分针指向 2。</text>
      <text class="tip-item">3. 画错可使用“撤销”或“清空”。</text>
    </view>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onLoad } from '@dcloudio/uni-app'

const questionIndex = ref(0)
const questionId = ref('')

const canvasSize = ref(300)
const canvasReady = ref(false)
const showExample = ref(false)
const submitting = ref(false)
const statusMsg = ref('')
const statusType = ref('info')

const strokes = ref([])
let currentStroke = []
let ctx = null
let canvasOffsetX = 0
let canvasOffsetY = 0
const lineWidth = 4
const lineColor = '#1f2d3d'

onLoad((options) => {
  if (options.questionIndex !== undefined) {
    questionIndex.value = parseInt(options.questionIndex)
  }
  if (options.questionId) {
    questionId.value = options.questionId
  }
})

onMounted(() => {
  const sysInfo = wx.getSystemInfoSync()
  const size = Math.min(sysInfo.windowWidth - 72, sysInfo.windowHeight * 0.46)
  canvasSize.value = Math.floor(size)

  setTimeout(() => {
    initCanvas()
    if (showExample.value) drawExampleClock()
  }, 260)
})

function initCanvas() {
  ctx = wx.createCanvasContext('clockCanvas')
  if (!ctx) {
    statusMsg.value = '画布初始化失败，请刷新重试。'
    statusType.value = 'error'
    return
  }

  const query = wx.createSelectorQuery()
  query
    .select('#clockCanvas')
    .boundingClientRect((rect) => {
      if (rect) {
        canvasOffsetX = rect.left
        canvasOffsetY = rect.top
      }
    })
    .exec()

  canvasReady.value = true
  drawBaseClock()
}

function drawBaseClock() {
  if (!ctx) return

  const size = canvasSize.value
  const cx = size / 2
  const cy = size / 2
  const r = size / 2 - 10

  ctx.clearRect(0, 0, size, size)
  ctx.setFillStyle('#ffffff')
  ctx.fillRect(0, 0, size, size)

  ctx.setStrokeStyle('#143445')
  ctx.setLineWidth(4)
  ctx.beginPath()
  ctx.arc(cx, cy, r, 0, Math.PI * 2)
  ctx.stroke()

  ctx.setFillStyle('#143445')
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
  exCtx.setFillStyle('#ffffff')
  exCtx.fillRect(0, 0, size, size)

  exCtx.setStrokeStyle('#143445')
  exCtx.setLineWidth(3)
  exCtx.beginPath()
  exCtx.arc(cx, cy, r, 0, Math.PI * 2)
  exCtx.stroke()

  exCtx.setFillStyle('#143445')
  exCtx.setFontSize(14)
  exCtx.setTextAlign('center')
  exCtx.setTextBaseline('middle')

  const nums = [12, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11]
  nums.forEach((num, idx) => {
    const angle = (idx * 30 - 90) * Math.PI / 180
    const nx = cx + (r - 18) * Math.cos(angle)
    const ny = cy + (r - 18) * Math.sin(angle)
    exCtx.fillText(String(num), nx, ny)
  })

  const hourAngle = ((11 * 30) + (10 * 0.5) - 90) * Math.PI / 180
  exCtx.setStrokeStyle('#1f2d3d')
  exCtx.setLineWidth(5)
  exCtx.setLineCap('round')
  exCtx.beginPath()
  exCtx.moveTo(cx, cy)
  exCtx.lineTo(cx + (r * 0.5) * Math.cos(hourAngle), cy + (r * 0.5) * Math.sin(hourAngle))
  exCtx.stroke()

  const minAngle = (2 * 30 - 90) * Math.PI / 180
  exCtx.setLineWidth(3)
  exCtx.beginPath()
  exCtx.moveTo(cx, cy)
  exCtx.lineTo(cx + (r * 0.75) * Math.cos(minAngle), cy + (r * 0.75) * Math.sin(minAngle))
  exCtx.stroke()

  exCtx.setFillStyle('#143445')
  exCtx.beginPath()
  exCtx.arc(cx, cy, 4, 0, Math.PI * 2)
  exCtx.fill()

  exCtx.draw(false)
}

function toggleExample() {
  showExample.value = !showExample.value
  if (showExample.value) {
    setTimeout(() => drawExampleClock(), 120)
  }
}

function getTouchPoint(e) {
  const touch = e.touches[0] || e.changedTouches[0]
  if (!touch) return null
  return {
    x: touch.clientX - canvasOffsetX,
    y: touch.clientY - canvasOffsetY,
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
  ctx.draw(true)
}

function onTouchEnd() {
  if (!canvasReady.value || currentStroke.length === 0) return
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
    title: '清空画布',
    content: '确定要清空当前绘制内容吗？',
    confirmText: '清空',
    cancelText: '取消',
    confirmColor: '#dc2626',
    success: (res) => {
      if (res.confirm) {
        strokes.value = []
        currentStroke = []
        redrawCanvas()
      }
    },
  })
}

function redrawCanvas() {
  if (!ctx) return

  drawBaseClock()

  strokes.value.forEach((stroke) => {
    if (stroke.length < 2) return
    ctx.beginPath()
    ctx.setStrokeStyle(lineColor)
    ctx.setLineWidth(lineWidth)
    ctx.setLineCap('round')
    ctx.setLineJoin('round')
    ctx.moveTo(stroke[0].x, stroke[0].y)
    for (let i = 1; i < stroke.length; i += 1) {
      ctx.lineTo(stroke[i].x, stroke[i].y)
    }
    ctx.stroke()
  })

  ctx.draw(false)
}

async function handleSubmit() {
  if (strokes.value.length === 0) {
    wx.showToast({ title: '请先完成绘制', icon: 'none' })
    return
  }

  submitting.value = true

  try {
    const imageData = await new Promise((resolve, reject) => {
      wx.canvasToTempFilePath({
        canvasId: 'clockCanvas',
        fileType: 'png',
        quality: 0.8,
        success: (res) => resolve(res.tempFilePath),
        fail: (err) => reject(err),
      })
    })

    const strokeData = {
      strokes: strokes.value,
      canvas_size: canvasSize.value,
      stroke_count: strokes.value.length,
      total_points: strokes.value.reduce((sum, item) => sum + item.length, 0),
    }

    uni.$emit('clockDrawCompleted', {
      questionIndex: questionIndex.value,
      strokes: strokeData,
      imageData,
    })

    wx.showToast({ title: '绘图提交成功', icon: 'success', duration: 1200 })
    setTimeout(() => {
      uni.navigateBack()
    }, 1200)
  } catch (err) {
    console.error('Submit clock draw error:', err)

    uni.$emit('clockDrawCompleted', {
      questionIndex: questionIndex.value,
      strokes: { strokes: strokes.value, canvas_size: canvasSize.value },
      imageData: null,
    })

    wx.showToast({ title: '已提交（未保存图片）', icon: 'none', duration: 1500 })
    setTimeout(() => {
      uni.navigateBack()
    }, 1500)
  } finally {
    submitting.value = false
  }
}

function handleSkip() {
  wx.showModal({
    title: '跳过此题',
    content: '时钟绘制题对评估很重要，确定要跳过吗？',
    confirmText: '跳过',
    cancelText: '继续绘制',
    confirmColor: '#d97706',
    success: (res) => {
      if (res.confirm) {
        uni.$emit('clockDrawCompleted', {
          questionIndex: questionIndex.value,
          strokes: null,
          imageData: null,
          skipped: true,
        })
        uni.navigateBack()
      }
    },
  })
}
</script>

<style scoped>
.clock-page {
  min-height: 100vh;
  padding-bottom: 52rpx;
}

.head-card {
  margin: 16rpx 24rpx 0;
  padding: 22rpx;
}

.head-title {
  display: block;
  color: #143445;
  font-size: 36rpx;
  font-weight: 800;
}

.head-desc {
  display: block;
  margin-top: 8rpx;
  color: #5d7485;
  font-size: 30rpx;
  line-height: 1.7;
}

.highlight {
  color: #dc2626;
  font-size: 34rpx;
  font-weight: 700;
}

.example-toggle {
  margin: 12rpx 24rpx 0;
  border-radius: 14rpx;
  background: #e6f7ff;
  border: 2rpx solid #91d5ff;
  padding: 14rpx 16rpx;
}

.example-toggle-text {
  color: #0284c7;
  font-size: 29rpx;
  font-weight: 700;
}

.example-card {
  margin: 12rpx 24rpx 0;
  padding: 18rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.example-canvas {
  border-radius: 50%;
  border: 2rpx solid #dbe6ef;
}

.example-caption {
  margin-top: 8rpx;
  color: #7b93a3;
  font-size: 27rpx;
}

.canvas-card {
  margin: 12rpx 24rpx 0;
  padding: 18rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  position: relative;
}

.clock-canvas {
  border-radius: 10rpx;
  border: 3rpx solid #dbe6ef;
  background: #ffffff;
}

.canvas-mask {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.8);
  border-radius: 26rpx;
}

.canvas-mask-text {
  color: #7e97a7;
  font-size: 30rpx;
}

.control-row {
  margin: 14rpx 24rpx 0;
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.ctrl-btn {
  flex: 1;
  min-height: 92rpx;
  border-radius: 999rpx;
  font-size: 30rpx;
  border: 2rpx solid #d6e1ea;
  background: #ffffff;
}

.ctrl-btn.undo {
  color: #0f766e;
  border-color: rgba(15, 118, 110, 0.3);
}

.ctrl-btn.clear {
  color: #dc2626;
  border-color: rgba(220, 38, 38, 0.3);
}

.ctrl-btn[disabled] {
  color: #b2c1cc;
  border-color: #dfe8ef;
}

.stroke-info {
  min-width: 70rpx;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stroke-value {
  color: #0f766e;
  font-size: 38rpx;
  font-weight: 700;
}

.stroke-label {
  color: #7893a4;
  font-size: 28rpx;
}

.status-box {
  margin: 12rpx 24rpx 0;
  border-radius: 14rpx;
  padding: 12rpx 14rpx;
}

.status-box.info {
  background: #e6f7ff;
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

.action-row {
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
  background: linear-gradient(135deg, #0284c7, #0369a1);
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
}

.submit-btn[disabled] {
  background: #afc5d7;
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
  color: #875500;
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

