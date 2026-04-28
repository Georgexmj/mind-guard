<template>
  <view class="intervention-page">
    <view class="top-nav">
      <view class="brand-chip">智</view>
      <text class="nav-title">康复训练</text>
      <view class="nav-menu" @click="showMenu">☰</view>
    </view>

    <view class="progress-card">
      <view class="progress-header">
        <text class="progress-kicker">今日已完成 {{ completedCount }} 项训练</text>
        <text class="progress-title">⚡康复训练</text>
        <text class="progress-desc">坚持每日脑力锻炼，让大脑保持活跃</text>
      </view>
      <view class="progress-bar-wrap">
        <view class="progress-bar">
          <view class="progress-fill" :style="{ width: progressPercent + '%' }" />
        </view>
        <text class="progress-text">今日进度 {{ completedCount }}/{{ totalCourses }}</text>
      </view>
    </view>

    <scroll-view class="category-scroll" scroll-x enable-flex>
      <view 
        v-for="cat in categories" 
        :key="cat.id" 
        class="category-tag"
        :class="{ active: activeCategory === cat.id }"
        @tap="activeCategory = cat.id"
      >
        {{ cat.name }}
      </view>
    </scroll-view>

    <view v-if="activeCategory === 'all' && todayRecommendation" class="recommend-card">
      <view class="recommend-header">
        <text class="recommend-badge">推荐</text>
        <text class="recommend-title">今日推荐</text>
      </view>
      <view class="recommend-content" @tap="goToTraining(todayRecommendation)">
        <view class="recommend-icon orange">
          <text class="icon-text">🧠</text>
        </view>
        <view class="recommend-info">
          <text class="recommend-name">{{ todayRecommendation.name }}</text>
          <text class="recommend-category">{{ todayRecommendation.categoryName }}</text>
          <view class="recommend-meta">
            <text class="meta-item">⏱️ {{ todayRecommendation.duration }}</text>
            <text class="meta-item">◎ {{ todayRecommendation.difficulty }}</text>
          </view>
        </view>
        <view class="recommend-arrow">▶</view>
      </view>
    </view>

    <view class="section-header">
      <text class="section-title">全部课程</text>
    </view>

    <view class="course-container">
      <view v-for="(row, rowIndex) in courseRows" :key="rowIndex" class="course-row">
        <view 
          v-for="course in row" 
          :key="course.id" 
          class="course-card"
          @tap="goToTraining(course)"
        >
          <view class="course-icon" :class="course.iconColor">
            <text class="icon-text">{{ course.icon }}</text>
          </view>
          <text class="course-name">{{ course.name }}</text>
          <text class="course-category">{{ course.categoryName }}</text>
          <view class="course-meta">
            <text class="course-duration">{{ course.duration }}</text>
            <text class="course-difficulty" :class="course.difficultyLevel">{{ course.difficulty }}</text>
          </view>
        </view>
      </view>
    </view>

    <view class="bottom-space"></view>
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '../../../store/auth'

const authStore = useAuthStore()
const activeCategory = ref('all')
const completedCount = ref(0)

function checkNewUser() {
  const hasVisited = uni.getStorageSync('hasVisited')
  if (!hasVisited) {
    uni.setStorageSync('hasVisited', 'true')
    uni.setStorageSync('daily_streak', '0')
    uni.setStorageSync('completedCourses', JSON.stringify({}))
    uni.setStorageSync('trainingCourses', '')
  }
}

const loadCompletedCount = () => {
  checkNewUser()
  const today = new Date().toISOString().split('T')[0]
  const completedCourses = uni.getStorageSync('completedCourses') || {}
  completedCount.value = completedCourses[today]?.length || 0
}

onMounted(() => {
  loadCompletedCount()
})

onShow(() => {
  loadCompletedCount()
})

const showMenu = () => {
  uni.showActionSheet({
    itemList: ['关于', '设置', '退出登录'],
    success: (res) => {
      switch (res.tapIndex) {
        case 0:
          uni.showModal({
            title: '关于',
            content: '忆守心安 - 老年认知障碍早筛与干预系统\n版本 1.0.0',
            showCancel: false
          })
          break
        case 1:
          uni.navigateTo({ url: '/pages/settings/index' })
          break
        case 2:
          uni.showModal({
            title: '提示',
            content: '确定要退出登录吗？',
            success: (modalRes) => {
              if (modalRes.confirm) authStore.logout()
            }
          })
          break
      }
    }
  })
}

const categories = [
  { id: 'all', name: '全部' },
  { id: 'attention', name: '注意力训练' },
  { id: 'language', name: '语言能力训练' },
  { id: 'memory', name: '记忆力训练' },
  { id: 'calculation', name: '计算力训练' },
]

const courses = [
  {
    id: 'find_diff',
    name: '找不同游戏',
    category: 'attention',
    categoryName: '注意力训练',
    icon: '🔍',
    iconColor: 'green',
    duration: '10分钟',
    difficulty: '简单',
    difficultyLevel: 'easy',
    questions: [
      { id: 1, type: 'image', content: '请找出两幅图片中的5处不同', timeLimit: 60 },
      { id: 2, type: 'image', content: '请找出两幅图片中的3处不同', timeLimit: 45 },
      { id: 3, type: 'image', content: '请找出两幅图片中的4处不同', timeLimit: 50 },
      { id: 4, type: 'image', content: '请找出两幅图片中的5处不同', timeLimit: 55 },
      { id: 5, type: 'image', content: '请找出两幅图片中的6处不同', timeLimit: 65 },
    ]
  },
  {
    id: 'simple_calc',
    name: '简单计算练习',
    category: 'calculation',
    categoryName: '计算力训练',
    icon: '🧮',
    iconColor: 'purple',
    duration: '15分钟',
    difficulty: '简单',
    difficultyLevel: 'easy',
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
    category: 'attention',
    categoryName: '注意力训练',
    icon: '🎨',
    iconColor: 'blue',
    duration: '15分钟',
    difficulty: '中等',
    difficultyLevel: 'medium',
    questions: [
      { id: 1, type: 'color', content: '请指出红色的方块', colors: ['red', 'blue', 'green', 'yellow'] },
      { id: 2, type: 'color', content: '请找出所有蓝色的圆形', colors: ['red', 'blue', 'blue', 'green'] },
      { id: 3, type: 'color', content: '请选择与示例相同颜色的图形', colors: ['purple', 'orange', 'purple', 'pink'] },
      { id: 4, type: 'color', content: '请按颜色分类这些物品', colors: ['red', 'green', 'blue', 'red'] },
      { id: 5, type: 'color', content: '请找出颜色不同的那个', colors: ['yellow', 'yellow', 'orange', 'yellow'] },
    ]
  },
  {
    id: 'image_memory',
    name: '图片记忆训练',
    category: 'memory',
    categoryName: '记忆力训练',
    icon: '🖼️',
    iconColor: 'lightblue',
    duration: '20分钟',
    difficulty: '中等',
    difficultyLevel: 'medium',
    questions: [
      { id: 1, type: 'memory', content: '请记住以下图片，然后回答问题', images: ['apple', 'banana', 'orange'], timeLimit: 30 },
      { id: 2, type: 'memory', content: '刚才看到了哪些物品？', options: ['苹果', '香蕉', '橙子', '葡萄'] },
      { id: 3, type: 'memory', content: '请回忆图片的顺序', images: ['cat', 'dog', 'bird'], timeLimit: 45 },
      { id: 4, type: 'memory', content: '找出刚才没有出现的图片', options: ['桌子', '椅子', '沙发', '电视'] },
      { id: 5, type: 'memory', content: '请按顺序点击刚才看到的物品', images: ['book', 'pen', 'cup'] },
    ]
  },
  {
    id: 'word_match',
    name: '词语配对游戏',
    category: 'language',
    categoryName: '语言能力训练',
    icon: '📝',
    iconColor: 'amber',
    duration: '12分钟',
    difficulty: '简单',
    difficultyLevel: 'easy',
    questions: [
      { id: 1, type: 'match', content: '请将动物与其叫声配对', pairs: [['狗', '汪汪'], ['猫', '喵喵']] },
      { id: 2, type: 'match', content: '请将职业与其工具配对', pairs: [['医生', '听诊器'], ['厨师', '锅铲']] },
      { id: 3, type: 'match', content: '请将水果与其颜色配对', pairs: [['苹果', '红色'], ['香蕉', '黄色']] },
      { id: 4, type: 'match', content: '请将天气与其图标配对', pairs: [['晴天', '☀️'], ['下雨', '🌧️']] },
      { id: 5, type: 'match', content: '请将交通工具与其用途配对', pairs: [['飞机', '天上飞'], ['汽车', '地上跑']] },
    ]
  },
  {
    id: 'story_retell',
    name: '故事复述训练',
    category: 'language',
    categoryName: '语言能力训练',
    icon: '📖',
    iconColor: 'red',
    duration: '18分钟',
    difficulty: '中等',
    difficultyLevel: 'medium',
    questions: [
      { id: 1, type: 'story', content: '请听故事：小明早上起床，吃了早餐，然后去上学。到了学校，他和同学们一起上课。', timeLimit: 60 },
      { id: 2, type: 'text', content: '请复述刚才听到的故事', answer: '' },
      { id: 3, type: 'story', content: '请听故事：小红在公园里看到一只小鸟，小鸟受伤了。她把小鸟带回家，给它包扎伤口。', timeLimit: 60 },
      { id: 4, type: 'choice', content: '小红在哪里看到小鸟？', options: ['家里', '公园里', '学校', '商店'], answer: '公园里' },
      { id: 5, type: 'text', content: '请说说小红做了什么', answer: '' },
    ]
  },
  {
    id: 'number_sequence',
    name: '数字序列训练',
    category: 'memory',
    categoryName: '记忆力训练',
    icon: '🔢',
    iconColor: 'darkblue',
    duration: '15分钟',
    difficulty: '困难',
    difficultyLevel: 'hard',
    questions: [
      { id: 1, type: 'sequence', content: '请记住数字序列：3 7 2 9', timeLimit: 15 },
      { id: 2, type: 'sequence', content: '请按顺序输入刚才听到的数字', answer: '3729' },
      { id: 3, type: 'sequence', content: '请记住数字序列：5 1 8 4 6', timeLimit: 20 },
      { id: 4, type: 'sequence', content: '请按顺序输入刚才听到的数字', answer: '51846' },
      { id: 5, type: 'sequence', content: '请记住数字序列：9 2 7 5 3 1', timeLimit: 25 },
    ]
  },
  {
    id: 'logic_puzzle',
    name: '逻辑推理游戏',
    category: 'calculation',
    categoryName: '计算力训练',
    icon: '🧩',
    iconColor: 'darkpurple',
    duration: '20分钟',
    difficulty: '困难',
    difficultyLevel: 'hard',
    questions: [
      { id: 1, type: 'logic', content: '如果所有的苹果都是水果，所有的水果都是食物，那么苹果是食物吗？', options: ['是', '不是', '不知道'], answer: '是' },
      { id: 2, type: 'logic', content: '小明比小红高，小红比小刚高，谁最高？', options: ['小明', '小红', '小刚'], answer: '小明' },
      { id: 3, type: 'logic', content: '有三个盒子，只有一个里面有礼物。每个盒子上都写着一句话，只有一句是真的。请问礼物在哪个盒子里？', options: ['盒子A', '盒子B', '盒子C'], answer: '盒子B' },
      { id: 4, type: 'logic', content: '找规律：2, 4, 8, 16, ?', options: ['24', '32', '20', '18'], answer: '32' },
      { id: 5, type: 'logic', content: '找规律：1, 3, 6, 10, ?', options: ['12', '13', '15', '16'], answer: '15' },
    ]
  },
]

const todayRecommendation = computed(() => {
  const now = new Date()
  const dayOfYear = Math.floor((now - new Date(now.getFullYear(), 0, 0)) / 86400000)
  return courses[dayOfYear % courses.length]
})

const filteredCourses = computed(() => {
  if (activeCategory.value === 'all') {
    return courses
  }
  return courses.filter(course => course.category === activeCategory.value)
})

const courseRows = computed(() => {
  const rows = []
  const courses = filteredCourses.value
  for (let i = 0; i < courses.length; i += 2) {
    rows.push(courses.slice(i, i + 2))
  }
  return rows
})

const totalCourses = computed(() => courses.length)

const progressPercent = computed(() => {
  return Math.round((completedCount.value / totalCourses.value) * 100)
})

function goToTraining(course) {
  uni.navigateTo({
    url: `/pages/intervention/training/index?id=${course.id}`
  })
}
</script>

<style scoped>
.intervention-page {
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

.brand-chip {
  width: 80rpx;
  height: 80rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #d36a1f, #f59e0b);
  display: flex;
  align-items: center;
  justify-content: center;
  color: #ffffff;
  font-size: 36rpx;
  font-weight: 800;
}

.nav-title {
  font-size: 40rpx;
  font-weight: 800;
  color: #17384a;
}

.nav-menu {
  font-size: 48rpx;
  color: #6b7c8e;
}

.progress-card {
  margin: 20rpx 24rpx;
  border-radius: 30rpx;
  padding: 28rpx;
  background: linear-gradient(135deg, #10b981, #059669);
  box-shadow: 0 20rpx 40rpx rgba(16, 185, 129, 0.3);
}

.progress-header {
  display: flex;
  flex-direction: column;
}

.progress-kicker {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 700;
}

.progress-title {
  margin-top: 8rpx;
  font-size: 48rpx;
  font-weight: 800;
  color: #ffffff;
}

.progress-desc {
  margin-top: 6rpx;
  font-size: 30rpx;
  color: rgba(255, 255, 255, 0.85);
}

.progress-bar-wrap {
  margin-top: 20rpx;
}

.progress-bar {
  height: 16rpx;
  border-radius: 999rpx;
  background: rgba(255, 255, 255, 0.3);
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 999rpx;
  background: #ffffff;
  transition: width 0.3s ease;
}

.progress-text {
  display: block;
  margin-top: 10rpx;
  text-align: right;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.9);
  font-weight: 700;
}

.category-scroll {
  white-space: nowrap;
  padding: 16rpx 24rpx;
  background: #ffffff;
  border-bottom: 2rpx solid #e8edf2;
}

.category-tag {
  display: inline-flex;
  padding: 14rpx 28rpx;
  margin-right: 16rpx;
  border-radius: 999rpx;
  background: #f5f8fa;
  color: #6b7c8e;
  font-size: 30rpx;
  font-weight: 700;
}

.category-tag.active {
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
}

.recommend-card {
  margin: 20rpx 24rpx;
  border-radius: 24rpx;
  background: linear-gradient(135deg, #fffbeb, #fef3c7);
  padding: 20rpx;
  border: 2rpx solid #fcd34d;
}

.recommend-header {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.recommend-badge {
  padding: 6rpx 14rpx;
  border-radius: 999rpx;
  background: linear-gradient(135deg, #f59e0b, #d97706);
  color: #ffffff;
  font-size: 26rpx;
  font-weight: 700;
}

.recommend-title {
  font-size: 32rpx;
  font-weight: 800;
  color: #92400e;
}

.recommend-content {
  display: flex;
  align-items: center;
  gap: 20rpx;
  margin-top: 16rpx;
}

.recommend-icon {
  width: 96rpx;
  height: 96rpx;
  border-radius: 28rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.recommend-icon.orange {
  background: linear-gradient(135deg, #f97316, #ea580c);
}

.icon-text {
  font-size: 44rpx;
}

.recommend-info {
  flex: 1;
}

.recommend-name {
  display: block;
  font-size: 36rpx;
  font-weight: 800;
  color: #17384a;
}

.recommend-category {
  display: block;
  margin-top: 4rpx;
  font-size: 28rpx;
  color: #6b7c8e;
}

.recommend-meta {
  display: flex;
  gap: 20rpx;
  margin-top: 8rpx;
}

.meta-item {
  font-size: 26rpx;
  color: #8a9ba8;
}

.recommend-arrow {
  font-size: 40rpx;
  color: #92400e;
  font-weight: bold;
}

.section-header {
  padding: 0 24rpx;
  margin-top: 20rpx;
}

.section-title {
  font-size: 34rpx;
  font-weight: 800;
  color: #17384a;
}

.course-container {
  padding: 0 24rpx;
  width: 100%;
  box-sizing: border-box;
}

.course-row {
  display: -webkit-box;
  display: -webkit-flex;
  display: flex;
  -webkit-box-pack: justify;
  -webkit-justify-content: space-between;
  justify-content: space-between;
  margin-bottom: 24rpx;
}

.course-card {
  width: calc(50% - 12rpx);
  border-radius: 24rpx;
  background: #ffffff;
  padding: 28rpx 20rpx;
  border: 2rpx solid #e8edf2;
  text-align: center;
  -webkit-box-sizing: border-box;
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.course-icon {
  width: 88rpx;
  height: 88rpx;
  border-radius: 24rpx;
  display: flex;
  align-items: center;
  justify-content: center;
}

.course-icon.green {
  background: linear-gradient(135deg, #22c55e, #16a34a);
}

.course-icon.purple {
  background: linear-gradient(135deg, #8b5cf6, #7c3aed);
}

.course-icon.blue {
  background: linear-gradient(135deg, #3b82f6, #2563eb);
}

.course-icon.lightblue {
  background: linear-gradient(135deg, #0ea5e9, #0284c7);
}

.course-icon.amber {
  background: linear-gradient(135deg, #fbbf24, #f59e0b);
}

.course-icon.red {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}

.course-icon.darkblue {
  background: linear-gradient(135deg, #1e40af, #1e3a8a);
}

.course-icon.darkpurple {
  background: linear-gradient(135deg, #7c3aed, #6d28d9);
}

.course-name {
  margin-top: 12rpx;
  font-size: 32rpx;
  font-weight: 800;
  color: #17384a;
  text-align: center;
  display: block;
}

.course-category {
  margin-top: 8rpx;
  font-size: 26rpx;
  color: #6b7c8e;
  text-align: center;
  display: block;
}

.course-meta {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 10rpx;
}

.course-duration {
  font-size: 24rpx;
  color: #8a9ba8;
}

.course-difficulty {
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  font-size: 22rpx;
  font-weight: 700;
}

.course-difficulty.easy {
  background: #dcfce7;
  color: #166534;
}

.course-difficulty.medium {
  background: #fef3c7;
  color: #92400e;
}

.course-difficulty.hard {
  background: #fee2e2;
  color: #991b1b;
}

.bottom-space {
  height: 120rpx;
}
</style>