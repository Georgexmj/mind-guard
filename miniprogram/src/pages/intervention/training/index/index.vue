<template>
  <view class="training-page">
    <view class="top-nav">
      <view class="nav-back" @tap="goBack">←</view>
      <text class="nav-title">{{ courseName }}</text>
      <view class="nav-progress">{{ currentIndex + 1 }}/{{ totalQuestions }}</view>
    </view>

    <view class="question-card" v-if="currentQuestion">
      <view class="question-header">
        <view class="question-type">
          <text class="type-badge">{{ questionTypeText }}</text>
        </view>
        <view class="question-timer" :class="{ warning: timeLeft <= 10 }">
          ⏱️ {{ timeLeft }}s
        </view>
      </view>

      <view class="question-content">
        <text class="question-text">{{ currentQuestion.content }}</text>
      </view>

      <view class="question-options" v-if="currentQuestion.type === 'choice'">
        <view 
          v-for="(option, index) in currentQuestion.options" 
          :key="index"
          class="option-item"
          :class="{ selected: selectedAnswer === option, correct: showResult && option === currentQuestion.answer, wrong: showResult && selectedAnswer === option && option !== currentQuestion.answer }"
          @tap="selectOption(option)"
        >
          <view class="option-letter">{{ String.fromCharCode(65 + index) }}</view>
          <text class="option-text">{{ option }}</text>
        </view>
      </view>

      <view class="question-options" v-else-if="currentQuestion.type === 'color'">
        <view class="color-grid">
          <view 
            v-for="(color, index) in currentQuestion.colors" 
            :key="index"
            class="color-item"
            :style="{ backgroundColor: color }"
            @tap="selectColor(index)"
          ></view>
        </view>
      </view>

      <view class="question-input" v-else-if="currentQuestion.type === 'text' || currentQuestion.type === 'sequence'">
        <input 
          class="input-field"
          v-model="userAnswer"
          placeholder="请输入答案"
          :maxlength="20"
        />
      </view>

      <view class="question-memory" v-else-if="currentQuestion.type === 'memory'">
        <view class="memory-images">
          <view v-for="(img, index) in currentQuestion.images" :key="index" class="memory-item">
            <text class="memory-icon">{{ getImageIcon(img) }}</text>
          </view>
        </view>
        <text class="memory-hint">请记住这些图片</text>
      </view>
    </view>

    <view class="result-card" v-if="showResult">
      <view class="result-header">
        <text class="result-icon" :class="isCorrect ? 'correct' : 'wrong'">
          {{ isCorrect ? '✓' : '✗' }}
        </text>
      </view>
      <text class="result-text">{{ isCorrect ? '回答正确！' : '回答错误' }}</text>
      <text class="result-answer" v-if="!isCorrect">正确答案：{{ currentQuestion.answer }}</text>
    </view>

    <view class="bottom-bar">
      <view class="progress-bar">
        <view class="progress-fill" :style="{ width: progressPercent + '%' }"></view>
      </view>
      <Button 
        class="submit-btn" 
        :disabled="!canSubmit"
        @tap="submitAnswer"
      >
        {{ showResult ? '下一题' : '提交答案' }}
      </Button>
    </view>

    <view class="completion-modal" v-if="showCompletion">
      <view class="modal-content">
        <view class="completion-icon">🎉</view>
        <text class="completion-title">训练完成！</text>
        <view class="completion-stats">
          <view class="stat-item">
            <text class="stat-value">{{ correctCount }}</text>
            <text class="stat-label">正确</text>
          </view>
          <view class="stat-divider"></view>
          <view class="stat-item">
            <text class="stat-value">{{ totalQuestions }}</text>
            <text class="stat-label">总题数</text>
          </view>
          <view class="stat-divider"></view>
          <view class="stat-item">
            <text class="stat-value">{{ accuracy }}%</text>
            <text class="stat-label">正确率</text>
          </view>
        </view>
        <Button class="finish-btn" @tap="finishTraining">完成训练</Button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { getApiBaseUrl } from '@/config/api'

const courseId = ref('')
const courseName = ref('')
const course = ref(null)
const questions = ref([])
const currentIndex = ref(0)
const selectedAnswer = ref('')
const userAnswer = ref('')
const showResult = ref(false)
const showCompletion = ref(false)
const correctCount = ref(0)
const timeLeft = ref(30)
let timer = null

const courses = [
  {
    id: 'find_diff',
    name: '找不同游戏',
    questions: [
      { id: 1, type: 'choice', content: '以下哪个数字最大？', options: ['15', '23', '18', '9'], answer: '23' },
      { id: 2, type: 'choice', content: '苹果和香蕉哪个更重？', options: ['苹果', '香蕉', '一样重', '不确定'], answer: '苹果' },
      { id: 3, type: 'choice', content: '请找出与众不同的一项：猫、狗、鸟、桌子', options: ['猫', '狗', '鸟', '桌子'], answer: '桌子' },
      { id: 4, type: 'choice', content: '3 + 5 = ?', options: ['6', '7', '8', '9'], answer: '8' },
      { id: 5, type: 'choice', content: '以下哪个是水果？', options: ['胡萝卜', '苹果', '土豆', '白菜'], answer: '苹果' },
    ]
  },
  {
    id: 'simple_calc',
    name: '简单计算练习',
    questions: [
      { id: 1, type: 'choice', content: '15 + 23 = ?', options: ['35', '38', '40', '42'], answer: '38' },
      { id: 2, type: 'choice', content: '45 - 18 = ?', options: ['25', '27', '29', '30'], answer: '27' },
      { id: 3, type: 'choice', content: '8 × 7 = ?', options: ['56', '63', '48', '54'], answer: '56' },
      { id: 4, type: 'choice', content: '63 ÷ 9 = ?', options: ['6', '7', '8', '9'], answer: '7' },
      { id: 5, type: 'choice', content: '100 - 7 = ?', options: ['90', '93', '95', '97'], answer: '93' },
    ]
  },
  {
    id: 'color_recognition',
    name: '颜色识别训练',
    questions: [
      { id: 1, type: 'choice', content: '天空是什么颜色？', options: ['红色', '蓝色', '绿色', '黄色'], answer: '蓝色' },
      { id: 2, type: 'choice', content: '树叶是什么颜色？', options: ['红色', '蓝色', '绿色', '黄色'], answer: '绿色' },
      { id: 3, type: 'choice', content: '太阳是什么颜色？', options: ['红色', '蓝色', '绿色', '黄色'], answer: '黄色' },
      { id: 4, type: 'choice', content: '血液是什么颜色？', options: ['红色', '蓝色', '绿色', '黄色'], answer: '红色' },
      { id: 5, type: 'choice', content: '雪是什么颜色？', options: ['黑色', '白色', '灰色', '蓝色'], answer: '白色' },
    ]
  },
  {
    id: 'image_memory',
    name: '图片记忆训练',
    questions: [
      { id: 1, type: 'choice', content: '以下哪种动物会飞？', options: ['狗', '猫', '鸟', '鱼'], answer: '鸟' },
      { id: 2, type: 'choice', content: '以下哪种动物生活在水里？', options: ['狗', '猫', '鸟', '鱼'], answer: '鱼' },
      { id: 3, type: 'choice', content: '以下哪种是交通工具？', options: ['苹果', '汽车', '狗', '书'], answer: '汽车' },
      { id: 4, type: 'choice', content: '以下哪种是水果？', options: ['桌子', '香蕉', '椅子', '书'], answer: '香蕉' },
      { id: 5, type: 'choice', content: '以下哪种是植物？', options: ['猫', '树', '汽车', '手机'], answer: '树' },
    ]
  },
  {
    id: 'word_match',
    name: '词语配对游戏',
    questions: [
      { id: 1, type: 'choice', content: '狗的叫声是？', options: ['喵喵', '汪汪', '叽叽', '咩咩'], answer: '汪汪' },
      { id: 2, type: 'choice', content: '猫的叫声是？', options: ['喵喵', '汪汪', '叽叽', '咩咩'], answer: '喵喵' },
      { id: 3, type: 'choice', content: '牛的叫声是？', options: ['喵喵', '汪汪', '哞哞', '咩咩'], answer: '哞哞' },
      { id: 4, type: 'choice', content: '羊的叫声是？', options: ['喵喵', '汪汪', '叽叽', '咩咩'], answer: '咩咩' },
      { id: 5, type: 'choice', content: '鸡的叫声是？', options: ['喵喵', '汪汪', '叽叽', '咩咩'], answer: '叽叽' },
    ]
  },
  {
    id: 'story_retell',
    name: '故事复述训练',
    questions: [
      { id: 1, type: 'choice', content: '早上我们通常做什么？', options: ['睡觉', '吃饭', '看电视', '跑步'], answer: '吃饭' },
      { id: 2, type: 'choice', content: '晚上我们通常做什么？', options: ['起床', '睡觉', '工作', '上学'], answer: '睡觉' },
      { id: 3, type: 'choice', content: '老师在学校做什么？', options: ['卖东西', '教书', '看病', '开车'], answer: '教书' },
      { id: 4, type: 'choice', content: '医生在医院做什么？', options: ['卖东西', '教书', '看病', '开车'], answer: '看病' },
      { id: 5, type: 'choice', content: '学生在学校做什么？', options: ['卖东西', '学习', '看病', '开车'], answer: '学习' },
    ]
  },
  {
    id: 'number_sequence',
    name: '数字序列训练',
    questions: [
      { id: 1, type: 'choice', content: '2, 4, 6, 8, ?', options: ['9', '10', '11', '12'], answer: '10' },
      { id: 2, type: 'choice', content: '1, 3, 5, 7, ?', options: ['8', '9', '10', '11'], answer: '9' },
      { id: 3, type: 'choice', content: '10, 20, 30, 40, ?', options: ['45', '50', '55', '60'], answer: '50' },
      { id: 4, type: 'choice', content: '1, 4, 9, 16, ?', options: ['20', '25', '30', '36'], answer: '25' },
      { id: 5, type: 'choice', content: '1, 2, 4, 8, ?', options: ['10', '12', '16', '20'], answer: '16' },
    ]
  },
  {
    id: 'logic_puzzle',
    name: '逻辑推理游戏',
    questions: [
      { id: 1, type: 'choice', content: '如果所有的苹果都是水果，所有的水果都是食物，那么苹果是食物吗？', options: ['是', '不是', '不知道', '不一定'], answer: '是' },
      { id: 2, type: 'choice', content: '小明比小红高，小红比小刚高，谁最高？', options: ['小明', '小红', '小刚', '不知道'], answer: '小明' },
      { id: 3, type: 'choice', content: '找规律：2, 4, 8, 16, ?', options: ['24', '32', '20', '18'], answer: '32' },
      { id: 4, type: 'choice', content: '找规律：1, 3, 6, 10, ?', options: ['12', '13', '15', '16'], answer: '15' },
      { id: 5, type: 'choice', content: '一个正方形有几条边？', options: ['3', '4', '5', '6'], answer: '4' },
    ]
  },
]

const currentQuestion = computed(() => questions.value[currentIndex.value])
const totalQuestions = computed(() => questions.value.length)
const progressPercent = computed(() => ((currentIndex.value + 1) / totalQuestions.value) * 100)
const questionTypeText = computed(() => {
  const types = {
    choice: '选择题',
    color: '颜色题',
    text: '填空题',
    memory: '记忆题',
    sequence: '序列题'
  }
  return types[currentQuestion.value?.type] || '问答题'
})
const canSubmit = computed(() => {
  if (showResult.value) return true
  if (currentQuestion.value?.type === 'choice') return selectedAnswer.value !== ''
  return userAnswer.value !== ''
})
const isCorrect = computed(() => {
  const answer = currentQuestion.value?.type === 'choice' ? selectedAnswer.value : userAnswer.value
  return answer === currentQuestion.value?.answer
})
const accuracy = computed(() => {
  if (currentIndex.value === 0) return 0
  return Math.round((correctCount.value / currentIndex.value) * 100)
})

function getImageIcon(img) {
  const icons = {
    apple: '🍎', banana: '🍌', orange: '🍊', grape: '🍇',
    cat: '🐱', dog: '🐶', bird: '🐦', fish: '🐟',
    book: '📖', pen: '✏️', cup: '☕',
    table: '🪑', chair: '🪑', sofa: '🛋️', tv: '📺'
  }
  return icons[img] || '📷'
}

function initCourse() {
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage?.options || {}
  courseId.value = options.id || 'find_diff'
  
  course.value = courses.find(c => c.id === courseId.value) || courses[0]
  courseName.value = course.value.name
  questions.value = [...course.value.questions]
  currentIndex.value = 0
  selectedAnswer.value = ''
  userAnswer.value = ''
  showResult.value = false
  showCompletion.value = false
  correctCount.value = 0
  startTimer()
}

function startTimer() {
  stopTimer()
  timeLeft.value = currentQuestion.value?.timeLimit || 30
  timer = setInterval(() => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      submitAnswer()
    }
  }, 1000)
}

function stopTimer() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

function selectOption(option) {
  if (showResult.value) return
  selectedAnswer.value = option
}

function selectColor(index) {
  if (showResult.value) return
  selectedAnswer.value = String(index)
}

function submitAnswer() {
  stopTimer()
  
  if (!showResult.value) {
    showResult.value = true
    if (isCorrect.value) {
      correctCount.value++
    }
  } else {
    nextQuestion()
  }
}

function nextQuestion() {
  if (currentIndex.value < totalQuestions.value - 1) {
    currentIndex.value++
    selectedAnswer.value = ''
    userAnswer.value = ''
    showResult.value = false
    startTimer()
  } else {
    showCompletion.value = true
  }
}

async function reportTrainingData() {
  const trainingData = {
    userId: uni.getStorageSync('userId') || 'unknown',
    courseId: courseId.value,
    courseName: courseName.value,
    correctCount: correctCount.value,
    totalQuestions: totalQuestions.value,
    accuracy: Math.round((correctCount.value / totalQuestions.value) * 100),
    completedAt: new Date().toISOString(),
    answers: []
  }

  try {
    const baseUrl = getApiBaseUrl()
    console.log('训练数据上报地址:', `${baseUrl}/training/report`)
    console.log('训练数据:', JSON.stringify(trainingData))
    
    const { request } = await import('@/utils/request.js')
    const response = await request({
      url: '/training/report',
      method: 'POST',
      data: trainingData
    })
    
    console.log('训练数据上报成功:', response)
  } catch (error) {
    console.error('训练数据上报失败:', error)
  }
}

function finishTraining() {
  reportTrainingData()
  
  const today = new Date().toISOString().split('T')[0]
  const completedCourses = JSON.parse(uni.getStorageSync('completedCourses') || '{}')
  if (!completedCourses[today]) {
    completedCourses[today] = []
  }
  if (!completedCourses[today].includes(courseId.value)) {
    completedCourses[today].push(courseId.value)
  }
  uni.setStorageSync('completedCourses', JSON.stringify(completedCourses))
  
  showCompletion.value = false
  uni.navigateBack()
}

function goBack() {
  stopTimer()
  uni.navigateBack()
}

onMounted(() => {
  initCourse()
})

onShow(() => {
  if (!showCompletion.value) {
    startTimer()
  }
})

onUnmounted(() => {
  stopTimer()
})
</script>

<style scoped>
.training-page {
  min-height: 100vh;
  background: #f5f8fa;
  padding-bottom: 140rpx;
}

.top-nav {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 60rpx 32rpx 24rpx;
  background: #ffffff;
}

.nav-back {
  font-size: 48rpx;
  color: #17384a;
  padding: 8rpx 16rpx;
}

.nav-title {
  font-size: 36rpx;
  font-weight: 800;
  color: #17384a;
}

.nav-progress {
  font-size: 28rpx;
  color: #6b7c8e;
  font-weight: 600;
  padding: 8rpx 20rpx;
  background: #f5f8fa;
  border-radius: 999rpx;
}

.question-card {
  margin: 24rpx;
  background: #ffffff;
  border-radius: 28rpx;
  padding: 32rpx;
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.type-badge {
  padding: 8rpx 20rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 700;
}

.question-timer {
  font-size: 30rpx;
  font-weight: 700;
  color: #0f766e;
}

.question-timer.warning {
  color: #dc2626;
  animation: pulse 1s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.question-content {
  margin-bottom: 32rpx;
}

.question-text {
  font-size: 36rpx;
  font-weight: 700;
  color: #17384a;
  line-height: 1.6;
}

.question-options {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 28rpx;
  background: #f8fafc;
  border-radius: 20rpx;
  border: 3rpx solid transparent;
  transition: all 0.3s;
}

.option-item.selected {
  border-color: #0f766e;
  background: rgba(15, 118, 110, 0.08);
}

.option-item.correct {
  border-color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
}

.option-item.wrong {
  border-color: #dc2626;
  background: rgba(220, 38, 38, 0.15);
}

.option-letter {
  width: 56rpx;
  height: 56rpx;
  border-radius: 50%;
  background: #e2e8f0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 800;
  color: #64748b;
  margin-right: 20rpx;
  flex-shrink: 0;
}

.option-item.selected .option-letter {
  background: #0f766e;
  color: #ffffff;
}

.option-item.correct .option-letter {
  background: #22c55e;
  color: #ffffff;
}

.option-item.wrong .option-letter {
  background: #dc2626;
  color: #ffffff;
}

.option-text {
  font-size: 32rpx;
  color: #334155;
  font-weight: 600;
}

.question-input {
  margin-top: 20rpx;
}

.input-field {
  width: 100%;
  padding: 28rpx;
  background: #f8fafc;
  border-radius: 16rpx;
  font-size: 32rpx;
  color: #17384a;
  box-sizing: border-box;
}

.question-memory {
  text-align: center;
}

.memory-images {
  display: flex;
  justify-content: center;
  gap: 24rpx;
  margin-bottom: 24rpx;
}

.memory-item {
  width: 120rpx;
  height: 120rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #f0f9ff, #e0f2fe);
  display: flex;
  align-items: center;
  justify-content: center;
}

.memory-icon {
  font-size: 56rpx;
}

.memory-hint {
  font-size: 30rpx;
  color: #64748b;
}

.color-grid {
  display: flex;
  justify-content: center;
  gap: 24rpx;
}

.color-item {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  border: 4rpx solid #e2e8f0;
}

.result-card {
  margin: 24rpx;
  background: #ffffff;
  border-radius: 28rpx;
  padding: 32rpx;
  text-align: center;
}

.result-header {
  margin-bottom: 20rpx;
}

.result-icon {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto;
  font-size: 64rpx;
  font-weight: bold;
}

.result-icon.correct {
  background: linear-gradient(135deg, #22c55e, #16a34a);
  color: #ffffff;
}

.result-icon.wrong {
  background: linear-gradient(135deg, #dc2626, #b91c1c);
  color: #ffffff;
}

.result-text {
  display: block;
  font-size: 36rpx;
  font-weight: 800;
  color: #17384a;
  margin-bottom: 12rpx;
}

.result-answer {
  font-size: 30rpx;
  color: #0f766e;
}

.bottom-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #ffffff;
  padding: 20rpx 32rpx;
  padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
  box-shadow: 0 -4rpx 20rpx rgba(0, 0, 0, 0.08);
}

.progress-bar {
  height: 8rpx;
  background: #e2e8f0;
  border-radius: 999rpx;
  overflow: hidden;
  margin-bottom: 20rpx;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #0f766e, #0284c7);
  border-radius: 999rpx;
  transition: width 0.3s ease;
}

.submit-btn {
  width: 100%;
  height: 96rpx;
  border-radius: 48rpx;
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
  border: none;
}

.submit-btn:disabled {
  background: #cbd5e1;
}

.completion-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 600rpx;
  background: #ffffff;
  border-radius: 32rpx;
  padding: 48rpx;
  text-align: center;
}

.completion-icon {
  font-size: 100rpx;
  margin-bottom: 24rpx;
}

.completion-title {
  display: block;
  font-size: 40rpx;
  font-weight: 800;
  color: #17384a;
  margin-bottom: 32rpx;
}

.completion-stats {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-bottom: 40rpx;
}

.stat-item {
  text-align: center;
  padding: 0 32rpx;
}

.stat-value {
  display: block;
  font-size: 48rpx;
  font-weight: 800;
  color: #0f766e;
}

.stat-label {
  display: block;
  font-size: 26rpx;
  color: #64748b;
  margin-top: 8rpx;
}

.stat-divider {
  width: 2rpx;
  height: 60rpx;
  background: #e2e8f0;
}

.finish-btn {
  width: 100%;
  height: 96rpx;
  border-radius: 48rpx;
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
  border: none;
}
</style>