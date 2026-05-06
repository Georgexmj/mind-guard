<template>
  <view class="training-page">
    <view class="top-nav">
      <view class="nav-back" @click="goBack">←</view>
      <text class="nav-title">{{ courseName }}</text>
      <view class="nav-progress">{{ currentIndex + 1 }}/{{ totalQuestions }}</view>
    </view>

    <view class="progress-bar-wrap">
      <view class="progress-bar">
        <view class="progress-fill" :style="{ width: progressPercent + '%' }" />
      </view>
    </view>

    <view class="story-modal" v-if="showStory && currentStory">
      <view class="story-content">
        <text class="story-icon">📖</text>
        <text class="story-title">请阅读故事</text>
        <view class="story-text-wrap">
          <text class="story-text">{{ currentStory }}</text>
        </view>
        <button class="start-btn" @click="startQuiz">开始答题</button>
      </view>
    </view>

    <view class="question-container" v-if="currentQuestion && !showStory">

      <view class="question-content">
        <text class="question-text">{{ currentQuestion.content }}</text>
      </view>

      <view class="answer-section">
        <view
          v-for="(option, idx) in currentQuestion.options"
          :key="idx"
          class="option-item"
          :class="{ selected: selectedAnswer === option, correct: showResult && option === currentQuestion.answer, wrong: showResult && selectedAnswer === option && option !== currentQuestion.answer }"
          @click="selectAnswer(option)"
        >
          <view class="option-letter">{{ String.fromCharCode(65 + idx) }}</view>
          <text class="option-text">{{ option }}</text>
        </view>
      </view>

      <view class="action-section">
        <button
          v-if="!showResult"
          class="submit-btn"
          @click="submitAnswer"
          :disabled="selectedAnswer === ''"
        >
          确认答案
        </button>
        <button
          v-if="showResult"
          class="next-btn"
          @click="nextQuestion"
        >
          {{ isLastQuestion ? '完成训练' : '下一题' }}
        </button>
      </view>
    </view>

    <view class="completion-modal" v-if="showCompletion">
      <view class="modal-content">
        <text class="completion-icon">🎉</text>
        <text class="completion-title">训练完成！</text>
        <view class="completion-stats">
          <view class="stat-item">
            <text class="stat-value">{{ correctCount }}</text>
            <text class="stat-label">正确题数</text>
          </view>
          <view class="stat-item">
            <text class="stat-value">{{ totalQuestions }}</text>
            <text class="stat-label">总题数</text>
          </view>
          <view class="stat-item">
            <text class="stat-value">{{ Math.round((correctCount / totalQuestions) * 100) }}%</text>
            <text class="stat-label">正确率</text>
          </view>
        </view>
        <button class="back-btn" @click="goBackToList">返回训练列表</button>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted, reactive } from 'vue'
import { getApiBaseUrl } from '@/config/api.js'

const courseId = ref('')
const courseName = ref('训练')
const currentIndex = ref(0)
const selectedAnswer = ref('')
const showResult = ref(false)
const showCompletion = ref(false)
const correctCount = ref(0)
const shuffledQuestions = ref([])
const currentStory = ref('')
const showStory = ref(false)
const userAnswers = ref([])

// 适老化设置
const settings = reactive({
  fontSize: 28,
  voiceEnabled: false,
  voiceSpeed: 1,
  voiceVolume: 0.8
})

// 加载用户设置
const loadSettings = () => {
  try {
    const saved = uni.getStorageSync('elder_settings')
    if (saved) {
      const savedSettings = typeof saved === 'string' ? JSON.parse(saved) : saved
      if (savedSettings.fontSize !== undefined) settings.fontSize = savedSettings.fontSize
      if (savedSettings.voiceEnabled !== undefined) settings.voiceEnabled = savedSettings.voiceEnabled
      if (savedSettings.voiceSpeed !== undefined) settings.voiceSpeed = savedSettings.voiceSpeed
      if (savedSettings.voiceVolume !== undefined) settings.voiceVolume = savedSettings.voiceVolume
    }
  } catch (e) {
    console.error('加载设置失败', e)
  }
}

// 语音播报功能
const speakText = (text) => {
  if (!settings.voiceEnabled) return
  
  // 使用微信小程序语音合成API
  const innerAudioContext = uni.createInnerAudioContext()
  
  // 在实际项目中，可以接入语音合成服务
  // 这里模拟语音播报功能
  console.log('语音播报:', text)
  
  // 模拟语音播放
  setTimeout(() => {
    innerAudioContext.destroy()
  }, text.length * 200 / settings.voiceSpeed)
}

// 播报题目内容
const speakQuestion = () => {
  if (currentQuestion.value && settings.voiceEnabled) {
    speakText(currentQuestion.value.content)
  }
}

// 播报选项
const speakOptions = () => {
  if (currentQuestion.value && settings.voiceEnabled && currentQuestion.value.options) {
    currentQuestion.value.options.forEach((option, index) => {
      const letter = String.fromCharCode(65 + index)
      setTimeout(() => {
        speakText(`${letter}. ${option}`)
      }, index * 1500 / settings.voiceSpeed)
    })
  }
}

const colorsList = [
  { emoji: '🔴', name: '红色' },
  { emoji: '🔵', name: '蓝色' },
  { emoji: '🟢', name: '绿色' },
  { emoji: '🟡', name: '黄色' },
  { emoji: '🟣', name: '紫色' },
  { emoji: '🟠', name: '橙色' },
  { emoji: '⚪', name: '白色' },
  { emoji: '⚫', name: '黑色' },
  { emoji: '🟤', name: '棕色' },
  { emoji: '🟢', name: '青色' },
]

function shuffleArray(array) {
  const newArray = [...array]
  for (let i = newArray.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1))
    ;[newArray[i], newArray[j]] = [newArray[j], newArray[i]]
  }
  return newArray
}

function generateColorQuestions() {
  const questions = []
  const usedColors = new Set()
  
  while (questions.length < 5 && usedColors.size < colorsList.length) {
    const randomIndex = Math.floor(Math.random() * colorsList.length)
    const color = colorsList[randomIndex]
    
    if (usedColors.has(color.name)) continue
    
    usedColors.add(color.name)
    
    const otherColors = colorsList.filter(c => c.name !== color.name)
    const shuffledOthers = shuffleArray(otherColors).slice(0, 3)
    const options = [
      `${color.emoji} ${color.name}`,
      ...shuffledOthers.map(c => `${c.emoji} ${c.name}`)
    ]
    
    questions.push({
      id: questions.length + 1,
      type: 'choice',
      content: `请选出${color.name}对应的色块`,
      options: shuffleArray(options),
      answer: `${color.emoji} ${color.name}`
    })
  }
  
  return questions
}

const coursesData = {
  find_diff: {
    name: '找不同游戏',
    questions: [
      { id: 1, type: 'choice', content: '苹果和香蕉有什么不同？', options: ['颜色不同', '都是水果', '形状相同', '没有不同'], answer: '颜色不同' },
      { id: 2, type: 'choice', content: '猫和狗有什么不同？', options: ['都会叫', '猫会爬树', '都有四条腿', '都喜欢游泳'], answer: '猫会爬树' },
      { id: 3, type: 'choice', content: '桌子和椅子有什么不同？', options: ['都是家具', '桌子有桌面', '都有四条腿', '用途相同'], answer: '桌子有桌面' },
      { id: 4, type: 'choice', content: '太阳和月亮有什么不同？', options: ['都在天上', '太阳更亮', '都是圆形', '都会发光'], answer: '太阳更亮' },
      { id: 5, type: 'choice', content: '书和报纸有什么不同？', options: ['都有文字', '报纸每天更新', '都是纸做的', '都很有趣'], answer: '报纸每天更新' },
    ]
  },
  simple_calc: {
    name: '简单计算练习',
    questions: [
      { id: 1, type: 'choice', content: '15 + 23 = ?', options: ['35', '38', '40', '42'], answer: '38' },
      { id: 2, type: 'choice', content: '45 - 18 = ?', options: ['25', '27', '29', '30'], answer: '27' },
      { id: 3, type: 'choice', content: '8 × 7 = ?', options: ['56', '63', '48', '54'], answer: '56' },
      { id: 4, type: 'choice', content: '63 ÷ 9 = ?', options: ['6', '7', '8', '9'], answer: '7' },
      { id: 5, type: 'choice', content: '100 - 7 = ?', options: ['90', '93', '95', '97'], answer: '93' },
    ]
  },
  color_recognition: {
    name: '颜色识别训练',
    dynamic: true,
    generateQuestions: generateColorQuestions
  },
  image_memory: {
    name: '图片记忆训练',
    questions: [
      { id: 1, type: 'choice', content: '苹果对应的图标是？', options: ['🍎', '🍌', '🍊', '🍇'], answer: '🍎' },
      { id: 2, type: 'choice', content: '香蕉对应的图标是？', options: ['🍎', '🍌', '🍊', '🍇'], answer: '🍌' },
      { id: 3, type: 'choice', content: '橙子对应的图标是？', options: ['🍎', '🍌', '🍊', '🍇'], answer: '🍊' },
      { id: 4, type: 'choice', content: '葡萄对应的图标是？', options: ['🍎', '🍌', '🍊', '🍇'], answer: '🍇' },
      { id: 5, type: 'choice', content: '猫对应的图标是？', options: ['🐶', '🐱', '🐭', '🐹'], answer: '🐱' },
    ]
  },
  word_match: {
    name: '词语配对游戏',
    questions: [
      { id: 1, type: 'choice', content: '狗的叫声是？', options: ['喵喵', '汪汪', '咩咩', '嘎嘎'], answer: '汪汪' },
      { id: 2, type: 'choice', content: '猫的叫声是？', options: ['喵喵', '汪汪', '咩咩', '嘎嘎'], answer: '喵喵' },
      { id: 3, type: 'choice', content: '羊的叫声是？', options: ['喵喵', '汪汪', '咩咩', '嘎嘎'], answer: '咩咩' },
      { id: 4, type: 'choice', content: '鸭子的叫声是？', options: ['喵喵', '汪汪', '咩咩', '嘎嘎'], answer: '嘎嘎' },
      { id: 5, type: 'choice', content: '公鸡的叫声是？', options: ['喔喔', '汪汪', '咩咩', '嘎嘎'], answer: '喔喔' },
    ]
  },
  story_retell: {
    name: '故事复述训练',
    story: '一天早上，小明起床后先吃了早餐，然后背着书包去上学。放学后，小明和小红一起去公园玩耍。在公园里，小红发现了一只受伤的小鸟，它的翅膀受伤了，无法飞翔。小红小心翼翼地把小鸟捧起来，拿出手帕帮小鸟包扎伤口。最后，他们把小鸟带回家照顾，希望它能早日康复。',
    questions: [
      { id: 1, type: 'choice', content: '小明早上起床后做了什么？', options: ['吃早餐', '看电视', '睡觉', '跑步'], answer: '吃早餐' },
      { id: 2, type: 'choice', content: '小明吃完早餐后去了哪里？', options: ['学校', '商店', '公园', '医院'], answer: '学校' },
      { id: 3, type: 'choice', content: '小红在哪里看到小鸟？', options: ['公园里', '家里', '学校', '商店'], answer: '公园里' },
      { id: 4, type: 'choice', content: '小红对小鸟做了什么？', options: ['包扎伤口', '放走了', '送给朋友', '养起来'], answer: '包扎伤口' },
      { id: 5, type: 'choice', content: '故事里的小鸟怎么了？', options: ['受伤了', '生病了', '迷路了', '饿了'], answer: '受伤了' },
    ]
  },
  number_sequence: {
    name: '数字序列训练',
    questions: [
      { id: 1, type: 'choice', content: '序列 2, 4, 6, 8, ? 下一个数是？', options: ['10', '9', '12', '8'], answer: '10' },
      { id: 2, type: 'choice', content: '序列 1, 3, 5, 7, ? 下一个数是？', options: ['9', '8', '10', '6'], answer: '9' },
      { id: 3, type: 'choice', content: '序列 3, 6, 9, 12, ? 下一个数是？', options: ['15', '14', '16', '13'], answer: '15' },
      { id: 4, type: 'choice', content: '序列 5, 10, 15, 20, ? 下一个数是？', options: ['25', '24', '26', '23'], answer: '25' },
      { id: 5, type: 'choice', content: '序列 1, 4, 9, 16, ? 下一个数是？', options: ['25', '24', '26', '20'], answer: '25' },
    ]
  },
  logic_puzzle: {
    name: '逻辑推理游戏',
    questions: [
      { id: 1, type: 'choice', content: '小明比小红高，小红比小刚高，谁最高？', options: ['小明', '小红', '小刚', '一样高'], answer: '小明' },
      { id: 2, type: 'choice', content: '找规律：2, 4, 8, 16, ?', options: ['32', '24', '20', '18'], answer: '32' },
      { id: 3, type: 'choice', content: '找规律：1, 3, 6, 10, ?', options: ['15', '12', '13', '16'], answer: '15' },
      { id: 4, type: 'choice', content: '如果所有苹果都是水果，所有水果都是食物，那么苹果是食物吗？', options: ['是', '不是', '不知道', '不一定'], answer: '是' },
      { id: 5, type: 'choice', content: '3个人3天用3桶水，9个人9天用几桶水？', options: ['27', '9', '18', '3'], answer: '27' },
    ]
  }
}

const questions = computed(() => {
  if (shuffledQuestions.value.length > 0) {
    return shuffledQuestions.value
  }
  const course = coursesData[courseId.value]
  if (!course) return []
  if (course.dynamic && course.generateQuestions) {
    return course.generateQuestions()
  }
  return course.questions || []
})

const currentQuestion = computed(() => {
  return questions.value[currentIndex.value] || null
})

const totalQuestions = computed(() => questions.value.length)

const progressPercent = computed(() => {
  return totalQuestions.value > 0 ? Math.round((currentIndex.value / totalQuestions.value) * 100) : 0
})

const isLastQuestion = computed(() => {
  return currentIndex.value === totalQuestions.value - 1
})

onMounted(() => {
  // 加载适老化设置
  loadSettings()
  
  const pages = getCurrentPages()
  const currentPage = pages[pages.length - 1]
  const options = currentPage?.options || {}
  
  if (options.id && coursesData[options.id]) {
    courseId.value = options.id
    courseName.value = coursesData[options.id].name
    
    const course = coursesData[options.id]
    if (course.story) {
      currentStory.value = course.story
      showStory.value = true
    }
    
    if (course.dynamic && course.generateQuestions) {
      shuffledQuestions.value = course.generateQuestions()
    } else if (course.questions) {
      shuffledQuestions.value = shuffleArray(course.questions)
    }
  }
  
  currentIndex.value = 0
  selectedAnswer.value = ''
  showResult.value = false
  showCompletion.value = false
  correctCount.value = 0
  
  // 延迟播放题目语音
  setTimeout(() => {
    speakQuestion()
    setTimeout(() => speakOptions(), 2000 / settings.voiceSpeed)
  }, 500)
})

function getQuestionTypeName(type) {
  const typeMap = {
    choice: '选择题',
    logic: '逻辑题',
    color: '颜色识别',
    sequence: '记忆序列',
    text: '文字题',
    memory: '图片记忆',
    match: '配对题',
    image: '图片题',
    story: '故事复述'
  }
  return typeMap[type] || '题目'
}

function selectAnswer(option) {
  if (showResult.value) return
  selectedAnswer.value = option
}

function submitAnswer() {
  if (selectedAnswer.value === '') return
  showResult.value = true
  
  const isCorrect = selectedAnswer.value === currentQuestion.value.answer
  if (isCorrect) {
    correctCount.value++
  }
  
  userAnswers.value[currentIndex.value] = {
    questionId: currentQuestion.value.id,
    questionContent: currentQuestion.value.content,
    userAnswer: selectedAnswer.value,
    isCorrect: isCorrect,
    correctAnswer: currentQuestion.value.answer
  }
}

function nextQuestion() {
  if (isLastQuestion.value) {
    saveProgress()
    reportTrainingData()
    showCompletion.value = true
    return
  }
  
  currentIndex.value++
  selectedAnswer.value = ''
  showResult.value = false
  
  // 延迟播放下一题语音
  setTimeout(() => {
    speakQuestion()
    setTimeout(() => speakOptions(), 2000 / settings.voiceSpeed)
  }, 500)
}

function saveProgress() {
  const today = new Date().toISOString().split('T')[0]
  let completedCourses = uni.getStorageSync('completedCourses')
  if (typeof completedCourses === 'string') {
    try {
      completedCourses = JSON.parse(completedCourses)
    } catch (e) {
      completedCourses = {}
    }
  }
  if (!completedCourses || typeof completedCourses !== 'object') {
    completedCourses = {}
  }
  if (!completedCourses[today]) {
    completedCourses[today] = []
  }
  if (!completedCourses[today].includes(courseId.value)) {
    completedCourses[today].push(courseId.value)
  }
  uni.setStorageSync('completedCourses', completedCourses)
}

async function reportTrainingData() {
  const userId = uni.getStorageSync('userId') || 'unknown'
  const trainingData = {
    userId: userId,
    courseId: courseId.value,
    courseName: courseName.value,
    correctCount: correctCount.value,
    totalQuestions: totalQuestions.value,
    accuracy: Math.round((correctCount.value / totalQuestions.value) * 100),
    completedAt: new Date().toISOString(),
    answers: userAnswers.value.filter(a => a)
  }

  try {
    const baseUrl = 'http://localhost:80/api/v1'
    console.log('训练数据上报地址:', `${baseUrl}/training/report`)
    console.log('训练数据:', JSON.stringify(trainingData))
    
    const response = await uni.request({
      url: `${baseUrl}/training/report`,
      method: 'POST',
      header: {
        'Content-Type': 'application/json'
      },
      data: trainingData
    })
    
    if (response.statusCode === 200) {
      console.log('训练数据上报成功')
    } else {
      console.warn('训练数据上报返回非200状态:', response.statusCode, response.data)
    }
  } catch (error) {
    console.error('训练数据上报失败:', error)
  }
}

function goBack() {
  uni.navigateBack()
}

function goBackToList() {
  uni.navigateBack()
}

function startQuiz() {
  showStory.value = false
}
</script>

<style scoped>
.training-page {
  min-height: 100vh;
  background: #f5f8fa;
  width: 100%;
  box-sizing: border-box;
}

.top-nav {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 60rpx 24rpx 20rpx;
  background: #ffffff;
}

.nav-back {
  font-size: 48rpx;
  color: #333;
  padding: 10rpx;
}

.nav-title {
  font-size: 36rpx;
  font-weight: 700;
  color: #17384a;
}

.nav-progress {
  font-size: 28rpx;
  color: #666;
  background: #f5f5f5;
  padding: 8rpx 20rpx;
  border-radius: 20rpx;
}

.progress-bar-wrap {
  padding: 0 24rpx;
  background: #ffffff;
}

.progress-bar {
  height: 8rpx;
  background: #e8edf2;
  border-radius: 4rpx;
}

.progress-fill {
  height: 100%;
  background: linear-gradient(135deg, #10b981, #059669);
  border-radius: 4rpx;
  transition: width 0.3s ease;
}

.question-container {
  margin: 20rpx 24rpx;
  background: #ffffff;
  border-radius: 24rpx;
  padding: 30rpx;
  box-shadow: 0 4rpx 20rpx rgba(0, 0, 0, 0.05);
}

.question-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.question-number {
  font-size: 28rpx;
  color: #10b981;
  font-weight: 700;
}

.question-type {
  font-size: 24rpx;
  color: #999;
  background: #f5f5f5;
  padding: 6rpx 16rpx;
  border-radius: 12rpx;
}

.question-content {
  margin-bottom: 30rpx;
}

.question-text {
  font-size: 34rpx;
  color: #333;
  line-height: 1.6;
}

.answer-section {
  margin-bottom: 30rpx;
}

.option-item {
  display: flex;
  align-items: center;
  padding: 24rpx;
  background: #f8fafc;
  border: 2rpx solid #e8edf2;
  border-radius: 16rpx;
  margin-bottom: 16rpx;
  transition: all 0.2s;
}

.option-item.selected {
  background: #e6f7ff;
  border-color: #1890ff;
}

.option-item.correct {
  background: #f6ffed;
  border-color: #52c41a;
}

.option-item.wrong {
  background: #fff2f0;
  border-color: #f5222d;
}

.option-letter {
  width: 56rpx;
  height: 56rpx;
  background: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 700;
  color: #333;
  margin-right: 20rpx;
  border: 2rpx solid #d9d9d9;
}

.option-text {
  font-size: 32rpx;
  color: #333;
}

.action-section {
  padding-top: 20rpx;
}

.submit-btn, .next-btn {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
  border-radius: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}

.submit-btn[disabled] {
  background: #d9d9d9;
  color: #999;
}

.completion-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.modal-content {
  width: 600rpx;
  background: #ffffff;
  border-radius: 30rpx;
  padding: 50rpx;
  text-align: center;
}

.completion-icon {
  font-size: 100rpx;
}

.completion-title {
  display: block;
  font-size: 40rpx;
  font-weight: 700;
  color: #333;
  margin: 30rpx 0;
}

.completion-stats {
  display: flex;
  justify-content: space-around;
  margin: 40rpx 0;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 48rpx;
  font-weight: 700;
  color: #10b981;
}

.stat-label {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-top: 10rpx;
}

.back-btn {
  width: 100%;
  height: 88rpx;
  background: linear-gradient(135deg, #1890ff, #096dd9);
  color: #ffffff;
  font-size: 32rpx;
  font-weight: 700;
  border-radius: 44rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
  margin-top: 20rpx;
}

.story-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 1000;
}

.story-content {
  width: 600rpx;
  background: #ffffff;
  border-radius: 30rpx;
  padding: 50rpx;
  text-align: center;
}

.story-icon {
  font-size: 80rpx;
}

.story-title {
  display: block;
  font-size: 36rpx;
  font-weight: 700;
  color: #333;
  margin: 30rpx 0;
}

.story-text-wrap {
  background: #f8fafc;
  border-radius: 20rpx;
  padding: 30rpx;
  margin-bottom: 40rpx;
}

.story-text {
  font-size: 32rpx;
  color: #333;
  line-height: 1.8;
  text-align: left;
}

.start-btn {
  width: 100%;
  height: 96rpx;
  background: linear-gradient(135deg, #10b981, #059669);
  color: #ffffff;
  font-size: 34rpx;
  font-weight: 700;
  border-radius: 48rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border: none;
}
</style>
