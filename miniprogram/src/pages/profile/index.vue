<!-- pages/profile/index.vue -->
<template>
  <view class="profile-container">
    <!-- 家属查看模式界面 -->
    <view v-if="isFamilyViewMode && viewingElder" class="family-profile">
      <!-- 绑定信息卡片 -->
      <view class="family-card">
        <view class="card-header">
          <text class="card-title">👨‍👩‍👧 子女与老人绑定信息</text>
        </view>
        <view class="family-content">
          <view class="elder-info">
            <view class="avatar-wrapper">
              <text class="elder-avatar">👵</text>
            </view>
            <view class="elder-detail">
              <text class="elder-name">{{ viewingElder.name || '未知老人' }}</text>
              <text class="elder-meta">已绑定老人</text>
            </view>
          </view>
          <view class="relation-badge">
            <text class="relation-text">子女关系</text>
          </view>
        </view>
        <view class="family-divider"></view>
        <view class="family-info-list">
          <view class="info-item">
            <text class="info-label">老人年龄</text>
            <text class="info-value">{{ viewingElder.age || '--' }}岁</text>
          </view>
          <view class="info-item">
            <text class="info-label">联系电话</text>
            <text class="info-value">{{ viewingElder.phone || '--' }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">上次测评</text>
            <text class="info-value">{{ lastAssessmentTime || '暂无记录' }}</text>
          </view>
          <view class="info-item">
            <text class="info-label">风险等级</text>
            <text :class="['info-value', riskClass]">{{ riskLevelText }}</text>
          </view>
        </view>
        <view class="family-actions">
          <view class="action-btn" @click="goBackToElder">
            <text class="action-icon">👈</text>
            <text class="action-text">返回查看老人</text>
          </view>
          <view class="action-btn" @click="switchAccount">
            <text class="action-icon">🔄</text>
            <text class="action-text">切换账号</text>
          </view>
        </view>
      </view>

      <!-- 家属功能菜单 -->
      <view class="family-menu">
        <view class="menu-title">功能菜单</view>
        <view class="menu-grid">
          <view class="menu-item" @click="goToElderDetail">
            <view class="menu-icon">👤</view>
            <text class="menu-text">老人详情</text>
          </view>
          <view class="menu-item" @click="goToSettings">
            <view class="menu-icon">⚙️</view>
            <text class="menu-text">设置</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 普通用户模式界面 -->
    <view v-else>
      <!-- 顶部用户信息卡片 -->
      <view class="user-card">
        <view class="user-info">
          <view class="user-details">
            <text class="user-name">{{ userName }}</text>
            <text class="user-meta">72岁·女</text>
            <view class="status-badge">
              <text class="status-text">认知状态良好</text>
            </view>
          </view>
        </view>
        <view class="contact-row">
          <view class="contact-item">
            <text class="contact-label">本人电话</text>
            <text class="contact-value">{{ userPhone }}</text>
          </view>
          <view class="contact-item">
            <text class="contact-label">监护人</text>
            <text class="contact-value">李先生</text>
          </view>
        </view>
      </view>

    <!-- 统计卡片 -->
    <view class="stats-card">
      <view class="stat-item">
        <text class="stat-number">{{ assessmentCount }}</text>
        <text class="stat-label">测评次数</text>
      </view>
      <view class="stat-divider"></view>
      <view class="stat-item">
        <text class="stat-number">{{ trainingCount }}</text>
        <text class="stat-label">训练次数</text>
      </view>
      <view class="stat-divider"></view>
      <view class="stat-item">
        <text class="stat-number">{{ continuousDays }}</text>
        <text class="stat-label">连续打卡</text>
      </view>
    </view>

    <!-- 近7天认知得分趋势 -->
    <view class="trend-card">
      <text class="trend-title">📈近7天认知得分趋势</text>
      <view class="trend-chart">
        <view class="trend-bars">
          <view
            v-for="(item, index) in trendData"
            :key="index"
            class="bar-item"
            @click="showDayDetail(index, item.day, item.score)"
          >
            <view class="bar" :style="{ height: item.height + 'rpx' }"></view>
            <text class="bar-label">{{ item.day }}</text>
          </view>
        </view>
      </view>
      <view class="latest-score">
        <text class="score-label">最新得分：</text>
        <text class="score-value">{{ latestScore }}分</text>
      </view>
    </view>

    <!-- 当天详情弹窗 -->
    <view v-if="showModal" class="modal-mask" @click="closeModal">
      <view class="modal-container" @click.stop>
        <view class="modal-header">
          <text class="modal-title">{{ selectedDay }}认知详情</text>
          <view class="modal-close" @click="closeModal">
            <text>✕</text>
          </view>
        </view>
        <scroll-view class="modal-body" scroll-y enhanced :show-scrollbar="false">
          <view class="modal-score-section">
            <text class="score-label-tag">当日得分</text>
            <text class="score-value-big">{{ selectedScore }}<text class="score-unit-small">分</text></text>
          </view>
          <view v-if="dayTrainings.length > 0" class="modal-list-section">
            <text class="section-title">📋 训练记录</text>
            <view class="training-list-modal">
              <view v-for="(training, idx) in dayTrainings" :key="idx" class="training-item-modal">
                <view class="training-left">
                  <text class="training-name-modal">{{ training.name }}</text>
                  <text class="training-time-modal">{{ training.time }}</text>
                </view>
                <view class="training-right">
                  <text class="training-score-modal">{{ training.score }}分</text>
                  <text :class="['training-status-modal', training.status === 'completed' ? 'completed' : 'pending']">
                    {{ training.status === 'completed' ? '✓ 已完成' : '○ 未完成' }}
                  </text>
                </view>
              </view>
            </view>
          </view>
          <view v-if="dayAssessments.length > 0" class="modal-list-section">
            <text class="section-title">📝 测评记录</text>
            <view class="assessment-list-modal">
              <view v-for="(assessment, idx) in dayAssessments" :key="idx" class="assessment-item-modal">
                <text class="assessment-name-modal">{{ assessment.name }}</text>
                <text class="assessment-score-modal">{{ assessment.score }}分</text>
              </view>
            </view>
          </view>
          <view v-if="dayTrainings.length === 0 && dayAssessments.length === 0" class="empty-modal">
            <text class="empty-icon">📭</text>
            <text class="empty-text-modal">当天暂无训练和测评记录</text>
          </view>
        </scroll-view>
      </view>
    </view>

    <!-- 今日用药提醒 -->
    <view class="medicine-card">
      <text class="medicine-title">💊今日用药提醒</text>
      <view class="medicine-list">
        <view v-for="(medicine, index) in medicines" :key="medicine.id" class="medicine-item">
          <view class="medicine-info">
            <text class="medicine-name">{{ medicine.name }}</text>
            <text class="medicine-time">{{ medicine.time }}</text>
          </view>
          <view class="medicine-status" @click="toggleMedicine(index)">
            <view :class="['status-circle', medicine.taken ? 'checked' : '']">
              <text v-if="medicine.taken">✓</text>
            </view>
            <text :class="['status-text', medicine.taken ? 'taken' : 'pending']">
              {{ medicine.taken ? '已服' : '标记服用' }}
            </text>
          </view>
        </view>
      </view>
    </view>

    <!-- 我的成就 -->
    <view class="achievement-card">
      <text class="achievement-title">🏆我的成就</text>
      <view class="achievement-grid">
        <view v-for="(achievement, index) in achievements" :key="index" class="achievement-item" @click="onAchievementTap(index)">
          <view class="achievement-icon" :style="{ backgroundColor: achievement.color }">
            <text>{{ achievement.icon }}</text>
          </view>
          <text class="achievement-name">{{ achievement.name }}</text>
        </view>
      </view>
    </view>

    <!-- 测评记录 -->
    <view class="records-card">
      <text class="records-title">测评记录</text>
      <view class="record-list">
        <view v-for="(assessment, index) in assessments" :key="index" class="record-item" @click="onAssessmentTap(index)">
          <view class="record-info">
            <text class="record-name">{{ assessment.name }}</text>
            <text class="record-date">{{ assessment.date }}</text>
          </view>
          <view class="record-score">
            <text class="score-number">{{ assessment.score }}</text>
            <text class="score-unit">分</text>
          </view>
          <text class="record-risk" :style="{ color: assessment.riskColor }">{{ assessment.risk }}</text>
        </view>
      </view>
    </view>

    <!-- 设置入口 -->
    <view class="settings-card" @click="goToSettings">
      <view class="settings-icon">⚙️</view>
      <view class="settings-info">
        <text class="settings-title">设置</text>
        <text class="settings-desc">调整字体大小、语音播报等</text>
      </view>
      <text class="settings-arrow">›</text>
    </view>
    </view> <!-- 关闭普通用户模式 -->
  </view>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { onShow } from '@dcloudio/uni-app'

// 家属查看模式
const isFamilyViewMode = ref(false)
const viewingElder = ref(null)
const lastAssessmentTime = ref('')
const riskLevel = ref('normal')

const riskLevelText = computed(() => {
  const riskMap = {
    'normal': '正常',
    'mild': '轻度风险',
    'moderate': '中度风险',
    'severe': '重度风险'
  }
  return riskMap[riskLevel.value] || '未知'
})

const riskClass = computed(() => {
  const classMap = {
    'normal': 'risk-normal',
    'mild': 'risk-mild',
    'moderate': 'risk-moderate',
    'severe': 'risk-severe'
  }
  return classMap[riskLevel.value] || ''
})

// 用户信息
const userName = ref('李奶奶')
const userPhone = ref('138****5678')

// 统计数据
const assessmentCount = ref(3)
const trainingCount = ref(12)
const continuousDays = ref('7天')
const latestScore = ref(83)

// 趋势数据
const trendData = ref([
  { day: '周一', height: 80, score: 78 },
  { day: '周二', height: 100, score: 82 },
  { day: '周三', height: 60, score: 75 },
  { day: '周四', height: 90, score: 80 },
  { day: '周五', height: 110, score: 85 },
  { day: '周六', height: 130, score: 88 },
  { day: '今天', height: 120, score: 83 }
])

// 用药提醒
const medicines = ref([
  { id: 1, name: '银杏叶片 2片', time: '① 早饭后', taken: true },
  { id: 2, name: '维生素B12 1片', time: '① 午饭后', taken: true },
  { id: 3, name: '钙片 1片', time: '① 晚饭后', taken: false }
])

// 成就列表
const achievements = ref([
  { name: '初次测评', icon: '🎉', color: '#fef3c7' },
  { name: '连续7天', icon: '📅', color: '#dbeafe' },
  { name: '记忆达人', icon: '🧠', color: '#dcfce7' },
  { name: '训练满星', icon: '⭐', color: '#fef9c3' },
  { name: '月度冠军', icon: '🏆', color: '#fed7aa' },
  { name: '坚持30天', icon: '💪', color: '#e0f2fe' }
])

// 测评记录
const assessments = ref([
  { name: 'MMSE认知量表', date: '2026/4/22', score: 85, risk: '低风险', riskColor: '#22c55e' },
  { name: 'MoCA认知评估', date: '2026/4/17', score: 78, risk: '低风险', riskColor: '#22c55e' }
])

// 弹窗相关
const showModal = ref(false)
const selectedDay = ref('')
const selectedScore = ref(0)
const dayTrainings = ref([])
const dayAssessments = ref([])

// 加载用户信息
const loadUserData = () => {
  try {
    const user = uni.getStorageSync('user')
    if (user) {
      const userData = typeof user === 'string' ? JSON.parse(user) : user
      if (userData.name) userName.value = userData.name
      if (userData.phone) userPhone.value = userData.phone
    }
  } catch (e) {
    console.error('加载用户信息失败', e)
  }
}

// 加载统计数据
const loadStatsData = () => {
  const token = uni.getStorageSync('token')
  if (!token) return
  uni.request({
    url: 'http://localhost:8000/api/v1/elders/stats',
    method: 'GET',
    header: { Authorization: `Bearer ${token}` },
    success: (res) => {
      if (res.statusCode === 200 && res.data) {
        assessmentCount.value = res.data.assessmentCount || 3
        trainingCount.value = res.data.trainingCount || 12
        continuousDays.value = `${res.data.continuousDays || 7}天`
      }
    },
    fail: () => console.log('统计数据接口暂不可用，使用默认值')
  })
}

// 模拟数据
const setMockDayData = (dayName) => {
  const mockDataMap = {
    '周一': { trainings: [{ name: '记忆力训练', time: '10:30', score: 82, status: 'completed' }], assessments: [] },
    '周二': { trainings: [{ name: '反应力训练', time: '09:00', score: 85, status: 'completed' }], assessments: [] },
    '周三': { trainings: [], assessments: [] },
    '周四': { trainings: [], assessments: [] },
    '周五': { trainings: [], assessments: [] },
    '周六': { trainings: [], assessments: [] },
    '今天': { trainings: [{ name: '记忆力训练', time: '09:00', score: 83, status: 'completed' }], assessments: [] }
  }
  const dayData = mockDataMap[dayName] || { trainings: [], assessments: [] }
  dayTrainings.value = dayData.trainings
  dayAssessments.value = dayData.assessments
}

const showDayDetail = (index, day, score) => {
  showModal.value = true
  selectedDay.value = day
  selectedScore.value = score
  setMockDayData(day)
}

const closeModal = () => { showModal.value = false }

const saveMedicineStatusLocal = (medicineId, taken) => {
  try {
    const savedMedicines = uni.getStorageSync('medicines_status') || {}
    savedMedicines[medicineId] = taken
    uni.setStorageSync('medicines_status', savedMedicines)
  } catch (e) { console.error('保存用药状态失败', e) }
}

const loadMedicineStatus = () => {
  try {
    const savedMedicines = uni.getStorageSync('medicines_status') || {}
    medicines.value.forEach(medicine => {
      if (savedMedicines[medicine.id] !== undefined) medicine.taken = savedMedicines[medicine.id]
    })
  } catch (e) { console.error('加载用药状态失败', e) }
}

const toggleMedicine = (index) => {
  const medicine = medicines.value[index]
  if (medicine) {
    medicine.taken = !medicine.taken
    saveMedicineStatusLocal(medicine.id, medicine.taken)
    uni.showToast({ title: medicine.taken ? '已标记为已服' : '已取消', icon: 'success' })
  }
}

const onAchievementTap = (index) => {
  const achievement = achievements.value[index]
  uni.showToast({ title: `${achievement.name} 成就`, icon: 'none' })
}

const onAssessmentTap = (index) => {
  const assessment = assessments.value[index]
  uni.navigateTo({ url: `/pages/result/index?name=${encodeURIComponent(assessment.name)}&date=${assessment.date}` })
}

const goToSettings = () => {
  uni.showToast({
    title: '设置功能建设中',
    icon: 'none'
  })
}

const goToElderDetail = () => {
  uni.navigateTo({ url: '/pages/elder-detail/index' })
}

const goBackToElder = () => {
  uni.switchTab({ url: '/pages/index/index' })
}

const switchAccount = () => {
  uni.setStorageSync('family_view_mode', 'false')
  uni.setStorageSync('viewing_elder', null)
  uni.reLaunch({ url: '/pages/login/index' })
}

const loadFamilyData = () => {
  const familyViewMode = uni.getStorageSync('family_view_mode')
  const elderData = uni.getStorageSync('viewing_elder')
  
  if (familyViewMode === 'true' && elderData) {
    isFamilyViewMode.value = true
    viewingElder.value = typeof elderData === 'string' ? JSON.parse(elderData) : elderData
    
    // 尝试获取老人最新测评数据
    const sessions = uni.getStorageSync('elder_sessions') || []
    if (sessions.length > 0) {
      const latestSession = sessions[0]
      if (latestSession.created_at) {
        const date = new Date(latestSession.created_at)
        lastAssessmentTime.value = `${date.getMonth() + 1}月${date.getDate()}日 ${date.getHours()}:${String(date.getMinutes()).padStart(2, '0')}`
      }
      if (latestSession.risk_level) {
        riskLevel.value = latestSession.risk_level
      }
    }
  } else {
    isFamilyViewMode.value = false
    viewingElder.value = null
  }
}

onMounted(() => {
  loadFamilyData()
  loadUserData()
  loadStatsData()
  loadMedicineStatus()
})

onShow(() => {
  loadFamilyData()
  loadUserData()
})
</script>

<style scoped>
.profile-container {
  min-height: 100vh;
  background-color: #f0f2f5;
  padding-bottom: 40rpx;
}

/* 顶部用户信息卡片 */
.user-card {
  background: linear-gradient(135deg, #0891B2 0%, #0E7490 100%);
  padding: 48rpx 32rpx 40rpx;
  border-radius: 0 0 48rpx 48rpx;
}

.user-info {
  margin-bottom: 40rpx;
}

.user-details {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.user-name {
  font-size: 52rpx;
  font-weight: 700;
  color: white;
  margin-bottom: 8rpx;
  text-align: center;
}

.user-meta {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.85);
  margin-bottom: 20rpx;
  text-align: center;
}

.status-badge {
  background-color: rgba(255, 255, 255, 0.2);
  padding: 12rpx 32rpx;
  border-radius: 40rpx;
  display: inline-block;
}

.status-text {
  font-size: 26rpx;
  color: white;
}

.contact-row {
  display: flex;
  justify-content: space-between;
  background-color: rgba(255, 255, 255, 0.12);
  border-radius: 24rpx;
  padding: 24rpx 40rpx;
}

.contact-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8rpx;
}

.contact-label {
  font-size: 24rpx;
  color: rgba(255, 255, 255, 0.7);
}

.contact-value {
  font-size: 28rpx;
  color: white;
  font-weight: 500;
}

/* 统计卡片 */
.stats-card {
  display: flex;
  background-color: white;
  margin: -32rpx 32rpx 32rpx;
  border-radius: 32rpx;
  padding: 40rpx 0;
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.08);
}

.stat-item {
  flex: 1;
  text-align: center;
}

.stat-number {
  font-size: 56rpx;
  font-weight: 800;
  color: #0891B2;
  display: block;
  margin-bottom: 8rpx;
}

.stat-label {
  font-size: 26rpx;
  color: #64748b;
}

.stat-divider {
  width: 2rpx;
  height: 80rpx;
  background-color: #e2e8f0;
  align-self: center;
}

/* 趋势卡片 */
.trend-card {
  background-color: white;
  margin: 0 32rpx 32rpx;
  border-radius: 32rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.trend-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1e293b;
  display: block;
  margin-bottom: 40rpx;
}

.trend-chart {
  margin-bottom: 32rpx;
}

.trend-bars {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: 320rpx;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
}

.bar {
  width: 48rpx;
  background: linear-gradient(180deg, #0891B2 0%, #22d3ee 100%);
  border-radius: 32rpx 32rpx 12rpx 12rpx;
  min-height: 20rpx;
  margin-bottom: 16rpx;
}

.bar-label {
  font-size: 26rpx;
  color: #94a3b8;
}

.latest-score {
  text-align: center;
  padding-top: 24rpx;
  border-top: 2rpx solid #f1f5f9;
  margin-top: 8rpx;
}

.score-label {
  font-size: 28rpx;
  color: #64748b;
}

.score-value {
  font-size: 40rpx;
  font-weight: 700;
  color: #0891B2;
}

/* 用药提醒卡片 */
.medicine-card {
  background-color: white;
  margin: 0 32rpx 32rpx;
  border-radius: 32rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.medicine-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1e293b;
  display: block;
  margin-bottom: 24rpx;
}

.medicine-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.medicine-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 2rpx solid #f1f5f9;
}

.medicine-item:last-child {
  border-bottom: none;
}

.medicine-info {
  flex: 1;
}

.medicine-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #1e293b;
  display: block;
  margin-bottom: 8rpx;
}

.medicine-time {
  font-size: 24rpx;
  color: #94a3b8;
}

.medicine-status {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 12rpx 0 12rpx 24rpx;
}

.status-circle {
  width: 44rpx;
  height: 44rpx;
  border-radius: 50%;
  border: 3rpx solid #cbd5e1;
  background-color: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.status-circle.checked {
  background-color: #0891B2;
  border-color: #0891B2;
}

.status-circle text {
  color: white;
  font-size: 28rpx;
  font-weight: bold;
}

.status-text {
  font-size: 26rpx;
  font-weight: 500;
  min-width: 100rpx;
}

.status-text.taken {
  color: #16a34a;
}

.status-text.pending {
  color: #64748b;
}

/* 成就卡片 */
.achievement-card {
  background-color: white;
  margin: 0 32rpx 32rpx;
  border-radius: 32rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.achievement-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1e293b;
  display: block;
  margin-bottom: 24rpx;
}

.achievement-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 32rpx;
}

.achievement-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: calc(33.33% - 22rpx);
}

.achievement-icon {
  width: 100rpx;
  height: 100rpx;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 12rpx;
  font-size: 44rpx;
}

.achievement-name {
  font-size: 24rpx;
  color: #475569;
}

/* 测评记录卡片 */
.records-card {
  background-color: white;
  margin: 0 32rpx 40rpx;
  border-radius: 32rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.records-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1e293b;
  display: block;
  margin-bottom: 24rpx;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 24rpx;
}

.record-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16rpx 0;
  border-bottom: 2rpx solid #f1f5f9;
}

.record-item:last-child {
  border-bottom: none;
}

.record-info {
  flex: 2;
}

.record-name {
  font-size: 30rpx;
  font-weight: 500;
  color: #1e293b;
  display: block;
  margin-bottom: 6rpx;
}

.record-date {
  font-size: 24rpx;
  color: #94a3b8;
}

.record-score {
  flex: 1;
  text-align: center;
}

.score-number {
  font-size: 32rpx;
  font-weight: 700;
  color: #0891B2;
}

.score-unit {
  font-size: 24rpx;
  color: #94a3b8;
}

.record-risk {
  flex: 1;
  text-align: right;
  font-size: 24rpx;
  font-weight: 500;
}

/* 设置入口 */
.settings-card {
  display: flex;
  align-items: center;
  background-color: #ffffff;
  margin: 0 32rpx 128rpx;
  padding: 30rpx 32rpx;
  border-radius: 32rpx;
  box-shadow: 0 8rpx 24rpx rgba(15, 23, 42, 0.06);
}

.settings-card:active {
  transform: scale(0.98);
  background-color: #f8fafc;
}

.settings-icon {
  width: 84rpx;
  height: 84rpx;
  margin-right: 24rpx;
  border-radius: 28rpx;
  background: linear-gradient(135deg, #e0f2fe 0%, #cffafe 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 42rpx;
}

.settings-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.settings-title {
  font-size: 32rpx;
  font-weight: 700;
  color: #1e293b;
}

.settings-desc {
  font-size: 26rpx;
  line-height: 1.45;
  color: #64748b;
}

.settings-arrow {
  margin-left: 24rpx;
  font-size: 44rpx;
  color: #94a3b8;
  line-height: 1;
}

/* 弹窗样式 */
.modal-mask {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 9999;
}

.modal-container {
  width: 85%;
  max-height: 80vh;
  background-color: #ffffff;
  border-radius: 40rpx;
  overflow: hidden;
  box-shadow: 0 20rpx 60rpx rgba(0, 0, 0, 0.3);
}

.modal-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 32rpx 40rpx;
  background: linear-gradient(135deg, #0891B2 0%, #0E7490 100%);
}

.modal-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #ffffff;
}

.modal-close {
  width: 56rpx;
  height: 56rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: rgba(255, 255, 255, 0.2);
  border-radius: 50%;
}

.modal-close text {
  font-size: 36rpx;
  color: #ffffff;
  font-weight: 300;
}

.modal-body {
  max-height: 60vh;
  padding: 32rpx 40rpx;
  overflow-y: auto;
}

/* 得分区域 */
.modal-score-section {
  text-align: center;
  padding: 32rpx 0;
  background-color: #f0f9ff;
  border-radius: 32rpx;
  margin-bottom: 32rpx;
}

.score-label-tag {
  font-size: 26rpx;
  color: #64748b;
  display: block;
  margin-bottom: 16rpx;
}

.score-value-big {
  font-size: 72rpx;
  font-weight: 800;
  color: #0891B2;
}

.score-unit-small {
  font-size: 32rpx;
  font-weight: 400;
  color: #94a3b8;
}

/* 列表区块 */
.modal-list-section {
  margin-bottom: 32rpx;
}

.section-title {
  font-size: 28rpx;
  font-weight: 600;
  color: #1e293b;
  display: block;
  margin-bottom: 20rpx;
  padding-left: 8rpx;
}

/* 训练列表项 */
.training-list-modal {
  background-color: #f8fafc;
  border-radius: 24rpx;
  overflow: hidden;
}

.training-item-modal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 32rpx;
  border-bottom: 2rpx solid #e2e8f0;
}

.training-item-modal:last-child {
  border-bottom: none;
}

.training-left {
  flex: 1;
}

.training-name-modal {
  font-size: 30rpx;
  font-weight: 600;
  color: #1e293b;
  display: block;
  margin-bottom: 8rpx;
}

.training-time-modal {
  font-size: 24rpx;
  color: #94a3b8;
}

.training-right {
  text-align: right;
}

.training-score-modal {
  font-size: 30rpx;
  font-weight: 700;
  color: #0891B2;
  display: block;
  margin-bottom: 8rpx;
}

.training-status-modal {
  font-size: 24rpx;
}

.training-status-modal.completed {
  color: #16a34a;
}

.training-status-modal.pending {
  color: #f97316;
}

/* 测评列表项 */
.assessment-list-modal {
  background-color: #f8fafc;
  border-radius: 24rpx;
  overflow: hidden;
}

.assessment-item-modal {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 28rpx 32rpx;
  border-bottom: 2rpx solid #e2e8f0;
}

.assessment-item-modal:last-child {
  border-bottom: none;
}

.assessment-name-modal {
  font-size: 30rpx;
  font-weight: 500;
  color: #1e293b;
}

.assessment-score-modal {
  font-size: 30rpx;
  font-weight: 700;
  color: #0891B2;
}

/* 空状态 */
.empty-modal {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 80rpx 0;
}

.empty-icon {
  font-size: 80rpx;
  margin-bottom: 24rpx;
}

.empty-text-modal {
  font-size: 28rpx;
  color: #94a3b8;
}

/* 家属查看模式样式 */
.family-profile {
  min-height: 100vh;
  background-color: #f0f2f5;
  padding: 32rpx;
  padding-bottom: 120rpx;
}

.family-card {
  background-color: #ffffff;
  border-radius: 32rpx;
  padding: 32rpx;
  margin-bottom: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.card-header {
  margin-bottom: 32rpx;
}

.card-title {
  font-size: 34rpx;
  font-weight: 700;
  color: #1e293b;
}

.family-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24rpx;
}

.elder-info {
  display: flex;
  align-items: center;
  gap: 20rpx;
}

.avatar-wrapper {
  width: 100rpx;
  height: 100rpx;
  background: linear-gradient(135deg, #4A90D9 0%, #2563EB 100%);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.elder-avatar {
  font-size: 56rpx;
}

.elder-detail {
  display: flex;
  flex-direction: column;
  gap: 8rpx;
}

.elder-name {
  font-size: 34rpx;
  font-weight: 700;
  color: #1e293b;
}

.elder-meta {
  font-size: 26rpx;
  color: #64748b;
}

.relation-badge {
  background-color: #dbeafe;
  padding: 12rpx 24rpx;
  border-radius: 32rpx;
}

.relation-text {
  font-size: 26rpx;
  color: #2563eb;
  font-weight: 500;
}

.family-divider {
  height: 2rpx;
  background-color: #e2e8f0;
  margin: 24rpx 0;
}

.family-info-list {
  display: flex;
  flex-direction: column;
  gap: 20rpx;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  font-size: 28rpx;
  color: #64748b;
}

.info-value {
  font-size: 28rpx;
  color: #1e293b;
  font-weight: 500;
}

.risk-normal {
  color: #16a34a;
}

.risk-mild {
  color: #f97316;
}

.risk-moderate {
  color: #eab308;
}

.risk-severe {
  color: #dc2626;
}

.family-actions {
  display: flex;
  gap: 24rpx;
  margin-top: 32rpx;
}

.action-btn {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12rpx;
  padding: 24rpx;
  background-color: #f1f5f9;
  border-radius: 24rpx;
}

.action-icon {
  font-size: 40rpx;
}

.action-text {
  font-size: 26rpx;
  color: #64748b;
}

.family-menu {
  background-color: #ffffff;
  border-radius: 32rpx;
  padding: 32rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.06);
}

.menu-title {
  font-size: 32rpx;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 24rpx;
}

.menu-grid {
  display: flex;
  gap: 32rpx;
}

.menu-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 16rpx;
  padding: 32rpx;
  background-color: #f8fafc;
  border-radius: 24rpx;
}

.menu-icon {
  font-size: 56rpx;
}

.menu-text {
  font-size: 28rpx;
  color: #334155;
}
</style>
