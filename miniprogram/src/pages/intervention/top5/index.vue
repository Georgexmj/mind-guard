<template>
  <view class="top5-page">
    <view class="hero-card">
      <text class="hero-kicker">个性化认知训练</text>
      <text class="hero-title">今日干预建议 Top-5</text>
      <text class="hero-desc">建议优先完成前 2 项，训练效果更稳定。</text>
      <text v-if="top5Data" class="hero-time">生成于 {{ formatDate(top5Data.generated_at) }}</text>
    </view>

    <view v-if="loading" class="mg-card state-card">
      <text class="state-text">正在生成推荐方案...</text>
    </view>

    <view v-else-if="errorMsg" class="mg-card state-card">
      <text class="state-title">暂无可用推荐</text>
      <text class="state-text">{{ errorMsg }}</text>
      <button class="primary-btn" @tap="loadTop5">重新获取</button>
      <button class="light-btn" @tap="goToAssessment">先去做一次评估</button>
    </view>

    <view v-else-if="top5Data" class="content-wrap">
      <view class="mg-card metric-card">
        <view class="metric-item">
          <text class="metric-label">风险等级</text>
          <text class="metric-value" :style="{ color: riskColor }">{{ riskLabel }}</text>
        </view>
        <view class="metric-divider" />
        <view class="metric-item">
          <text class="metric-label">MMSE</text>
          <text class="metric-value">{{ top5Data.mmse_score ?? '--' }}</text>
        </view>
        <view class="metric-divider" />
        <view class="metric-item">
          <text class="metric-label">MoCA</text>
          <text class="metric-value">{{ top5Data.moca_score_corrected ?? '--' }}</text>
        </view>
      </view>

      <view class="list-wrap">
        <view v-for="item in recommendations" :key="item.code" class="mg-card rec-card" :class="{ done: item.today_done }">
          <view class="rec-head">
            <view class="head-left">
              <view class="rank-pill">TOP {{ item.rank }}</view>
              <text class="priority-text">优先级 {{ item.priority_score }}</text>
            </view>
            <text v-if="item.today_done" class="done-badge">今日已完成</text>
          </view>

          <text class="rec-title">{{ item.title }}</text>

          <view class="meta-wrap">
            <text class="meta-chip">分类：{{ item.category }}</text>
            <text class="meta-chip">频次：{{ item.frequency }}</text>
            <text class="meta-chip">时长：{{ item.duration_minutes }} 分钟</text>
          </view>

          <text class="domain-line">目标认知域：{{ formatDomains(item.target_domains) }}</text>
          <text class="rationale-line">{{ item.rationale }}</text>
          <text class="evidence-line">证据等级：{{ item.evidence_level }}</text>

          <view class="guide-box">
            <view class="guide-head" @tap="toggleGuide(item.code)">
              <text class="guide-title">执行步骤</text>
              <text class="guide-toggle">{{ isGuideExpanded(item.code) ? '收起' : '展开' }}</text>
            </view>

            <view v-if="isGuideExpanded(item.code)" class="guide-body">
              <text v-for="(step, idx) in item.guide.steps" :key="`${item.code}-step-${idx}`" class="guide-step">
                {{ idx + 1 }}. {{ step }}
              </text>
              <text class="guide-extra">所需材料：{{ formatList(item.guide.materials) }}</text>
              <text class="guide-extra">完成标准：{{ item.guide.completion_hint }}</text>
              <text class="guide-extra">注意事项：{{ formatList(item.guide.precautions) }}</text>
            </view>
          </view>

          <button
            v-if="!item.today_done"
            class="checkin-btn"
            @tap.stop="onTapRecommendation(item)"
          >
            我已完成今日训练
          </button>
          <view v-else class="done-btn">今日已完成，明天继续</view>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { useAuthStore } from '../../../store/auth'
import { api } from '../../../utils/request'

const authStore = useAuthStore()

const loading = ref(false)
const errorMsg = ref('')
const top5Data = ref(null)
const progressPlans = ref([])
const expandedGuideCode = ref('')

const DOMAIN_LABELS = {
  memory: '记忆',
  orientation: '定向',
  language: '语言',
  attention: '注意',
  visuospatial: '视空间',
  executive: '执行功能',
}

const RISK_LABELS = {
  normal: '正常',
  mild_risk: '轻度风险',
  high_risk: '高风险',
}

const RISK_COLORS = {
  normal: '#16a34a',
  mild_risk: '#d97706',
  high_risk: '#dc2626',
}

const TRAINING_PLAYBOOK = {
  memory_association: {
    steps: [
      '准备 6-8 张生活物品卡片，先看后遮挡回忆。',
      '每轮回忆后立刻核对并重复练习 2-3 轮。',
      '记录正确数量，逐步增加难度。',
    ],
    materials: ['卡片或便签', '计时器'],
    precautions: ['每轮题量不宜过大', '出现疲劳及时休息'],
    completion_hint: '当天完成至少 2 轮回忆训练。',
  },
  orientation_calendar: {
    steps: [
      '先口述当天日期、星期、所在地点。',
      '由家属随机提问 3 个定向问题。',
      '答错题目当场纠正并再次复述。',
    ],
    materials: ['日历', '家庭提示卡'],
    precautions: ['固定时间练习效果更好', '纠错时语气平和'],
    completion_hint: '日期、地点、任务三类问题都完成。',
  },
  attention_serial: {
    steps: [
      '进行连续减法练习（如 100-7）。',
      '进行数字复述训练（4-6 位）。',
      '最后做 1 分钟目标符号查找练习。',
    ],
    materials: ['纸笔', '数字题卡'],
    precautions: ['困难时先降低难度', '每 5 分钟可短暂休息'],
    completion_hint: '完成 3 组注意力训练任务。',
  },
  language_fluency: {
    steps: [
      '围绕指定主题进行 1 分钟词语流畅训练。',
      '朗读短文并复述主要内容。',
      '进行 5 分钟日常交流表达训练。',
    ],
    materials: ['短文材料', '计时器'],
    precautions: ['先保证表达完整再追求速度', '可先给关键词提示'],
    completion_hint: '完成词语、复述、表达三项任务。',
  },
}

const recommendations = computed(() => {
  if (!top5Data.value || !Array.isArray(top5Data.value.recommendations)) return []
  const plans = Array.isArray(progressPlans.value) ? progressPlans.value : []
  return top5Data.value.recommendations
    .map((item) => {
      const linkedPlan = findLinkedPlan(item, plans)
      return {
        ...item,
        guide: buildGuide(item),
        linked_plan_id: toNumber(linkedPlan?.plan_id, 0),
        today_done: Boolean(linkedPlan?.today_checked && linkedPlan?.today_completed),
      }
    })
    .sort((a, b) => {
      const doneOrder = Number(a.today_done) - Number(b.today_done)
      if (doneOrder !== 0) return doneOrder
      return Number(a.rank || 0) - Number(b.rank || 0)
    })
})

const riskLabel = computed(() => {
  const level = top5Data.value?.risk_level
  return RISK_LABELS[level] || level || '--'
})

const riskColor = computed(() => {
  const level = top5Data.value?.risk_level
  return RISK_COLORS[level] || '#0f766e'
})

function formatDomains(domains = []) {
  if (!Array.isArray(domains) || domains.length === 0) return '--'
  return domains.map((key) => DOMAIN_LABELS[key] || key).join('、')
}

function formatList(list = []) {
  if (!Array.isArray(list) || list.length === 0) return '--'
  return list.join('、')
}

function toNumber(value, fallback = 0) {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function normalizeTitleKey(text) {
  return String(text || '')
    .trim()
    .toLowerCase()
    .replace(/[\s\-——~（）()【】\[\]·,，。；;：:]/g, '')
}

function findLinkedPlan(item, plans) {
  if (!item || !Array.isArray(plans) || plans.length === 0) return null
  const byCode = plans.find((plan) => String(plan?.recommendation_code || '') === String(item?.code || ''))
  if (byCode) return byCode

  const recKey = normalizeTitleKey(item?.title)
  if (!recKey) return null

  return plans.find((plan) => {
    const planKey = normalizeTitleKey(plan?.plan_title)
    if (!planKey) return false
    return planKey === recKey || planKey.includes(recKey) || recKey.includes(planKey)
  })
}

function buildGuide(item) {
  const fromCatalog = TRAINING_PLAYBOOK[item?.code]
  if (fromCatalog) return fromCatalog

  const domains = formatDomains(item?.target_domains || [])
  const duration = Number(item?.duration_minutes) || 15

  return {
    steps: [
      `在安静环境中进行“${item?.title || '训练项目'}”，建议时长 ${duration} 分钟。`,
      `围绕“${domains}”完成 2-3 轮练习，每轮后短暂休息。`,
      '完成后简短复盘并记录当天感受。',
    ],
    materials: ['纸笔', '计时器'],
    precautions: ['以不疲劳为原则', '不适时及时停止并咨询医生'],
    completion_hint: `当日累计训练达到 ${duration} 分钟。`,
  }
}

function formatDate(raw) {
  if (!raw) return '--'
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return '--'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function goToAssessment() {
  uni.navigateTo({ url: '/pages/assessment/start/index' })
}

function toggleGuide(code) {
  expandedGuideCode.value = expandedGuideCode.value === code ? '' : code
}

function isGuideExpanded(code) {
  return expandedGuideCode.value === code
}

async function onTapRecommendation(item) {
  if (item?.today_done) {
    wx.showToast({ title: '今日已完成，无需重复', icon: 'none' })
    return
  }

  wx.showModal({
    title: item?.title || '训练建议',
    content: '确认已按该方案完成今日训练？',
    confirmText: '确认完成',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      await submitRecommendationStatus(item, { completed: true, successText: '已完成' })
    },
  })
}

async function submitRecommendationStatus(item, { completed, interruptionReason = '', successText = '提交成功' }) {
  try {
    wx.showLoading({ title: '正在提交...' })

    let targetPlanId = toNumber(item?.linked_plan_id, 0)
    if (targetPlanId <= 0) {
      const payload = {
        session_id: top5Data.value?.session_id,
        recommendation_code: item?.code,
        duration_days: 30,
      }
      const plan = await api.createInterventionPlanFromTop5(payload)
      targetPlanId = toNumber(plan?.id, 0)
    }

    if (targetPlanId <= 0) {
      throw new Error('未找到可用计划，请稍后重试。')
    }

    await api.dailyInterventionCheckin({
      plan_id: targetPlanId,
      completed,
      interruption_reason: completed ? undefined : interruptionReason,
    })

    wx.hideLoading()
    wx.showToast({ title: successText, icon: 'success' })
    await loadTop5()
  } catch (e) {
    wx.hideLoading()
    const message = String(e?.message || '')
    const isPermissionError = /No permission|Access denied|403/i.test(message)

    if (isPermissionError) {
      try {
        const progressResp = await api.getInterventionMyProgress().catch(() => null)
        const plans = Array.isArray(progressResp?.plans) ? progressResp.plans : []
        const linkedPlan = findLinkedPlan(item, plans)
        const linkedPlanId = toNumber(linkedPlan?.plan_id, 0)

        if (linkedPlanId > 0) {
          await api.dailyInterventionCheckin({
            plan_id: linkedPlanId,
            completed,
            interruption_reason: completed ? undefined : interruptionReason,
          })
          wx.showToast({ title: successText, icon: 'success' })
          await loadTop5()
          return
        }

        wx.showToast({ title: '暂无自动建计划权限，请联系医生协助。', icon: 'none' })
        return
      } catch {
        wx.showToast({ title: '提交失败，请联系医生协助', icon: 'none' })
        return
      }
    }

    wx.showToast({ title: message || '提交失败，请稍后重试', icon: 'none' })
  }
}

async function loadTop5() {
  loading.value = true
  errorMsg.value = ''

  try {
    const [top5Resp, progressResp] = await Promise.all([
      api.getInterventionTop5(),
      api.getInterventionMyProgress().catch(() => null),
    ])

    top5Data.value = top5Resp || null
    progressPlans.value = Array.isArray(progressResp?.plans) ? progressResp.plans : []

    if (!top5Data.value || recommendations.value.length === 0) {
      errorMsg.value = '当前暂无推荐结果，请先完成一次评估。'
    }
  } catch (error) {
    top5Data.value = null
    progressPlans.value = []

    const message = error instanceof Error ? error.message : '获取推荐失败，请稍后再试。'
    if (/No completed assessment|not found|404/i.test(message)) {
      errorMsg.value = '当前没有可用评估结果，请先完成一次评估。'
      return
    }
    errorMsg.value = message
  } finally {
    loading.value = false
  }
}

onShow(() => {
  if (!authStore.enforceElderRole()) return
  loadTop5()
})
</script>

<style scoped>
.top5-page {
  min-height: 100vh;
  padding: 20rpx 24rpx 44rpx;
}

.hero-card {
  border-radius: 30rpx;
  padding: 26rpx 24rpx;
  background:
    radial-gradient(circle at 94% 10%, rgba(255, 255, 255, 0.26), transparent 40%),
    linear-gradient(135deg, #0f766e 0%, #0284c7 100%);
  box-shadow: 0 24rpx 42rpx rgba(8, 43, 66, 0.28);
  margin-bottom: 14rpx;
}

.hero-kicker {
  display: inline-flex;
  padding: 8rpx 14rpx;
  border-radius: 999rpx;
  border: 2rpx solid rgba(255, 255, 255, 0.34);
  background: rgba(255, 255, 255, 0.18);
  color: #ecfeff;
  font-size: 28rpx;
  font-weight: 700;
}

.hero-title {
  display: block;
  margin-top: 10rpx;
  color: #ffffff;
  font-size: 48rpx;
  font-weight: 800;
}

.hero-desc {
  display: block;
  margin-top: 8rpx;
  color: rgba(239, 252, 255, 0.96);
  font-size: 31rpx;
  line-height: 1.7;
}

.hero-time {
  display: block;
  margin-top: 10rpx;
  color: rgba(233, 249, 255, 0.92);
  font-size: 28rpx;
}

.state-card {
  padding: 28rpx;
}

.state-title {
  display: block;
  color: #17384a;
  font-size: 40rpx;
  font-weight: 800;
}

.state-text {
  display: block;
  margin-top: 10rpx;
  color: #4f697b;
  font-size: 31rpx;
  line-height: 1.72;
}

.primary-btn,
.light-btn {
  width: 100%;
  min-height: 96rpx;
  border-radius: 999rpx;
  margin-top: 12rpx;
  font-size: 34rpx;
  font-weight: 700;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.primary-btn {
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
}

.light-btn {
  background: #ffffff;
  color: #0f766e;
  border: 2rpx solid rgba(15, 118, 110, 0.35);
}

.metric-card {
  padding: 18rpx 16rpx;
  display: flex;
  align-items: stretch;
  border: 2rpx solid rgba(15, 118, 110, 0.18);
  background: linear-gradient(180deg, rgba(255, 255, 255, 0.96), rgba(245, 252, 255, 0.96));
}

.metric-item {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

.metric-divider {
  width: 2rpx;
  margin: 8rpx 2rpx;
  background: #d9e7f2;
}

.metric-label {
  color: #627f91;
  font-size: 29rpx;
}

.metric-value {
  margin-top: 4rpx;
  color: #17384a;
  font-size: 42rpx;
  font-weight: 800;
}

.list-wrap {
  margin-top: 14rpx;
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.rec-card {
  padding: 22rpx 20rpx 20rpx 24rpx;
  border: 2rpx solid #d8e8f3;
  box-shadow: 0 14rpx 24rpx rgba(17, 34, 49, 0.08);
  position: relative;
  overflow: hidden;
}

.rec-card::before {
  content: '';
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 10rpx;
  background: linear-gradient(180deg, #0f766e, #0284c7);
}

.rec-card.done {
  opacity: 0.88;
}

.rec-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 10rpx;
}

.head-left {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.rank-pill {
  border-radius: 999rpx;
  padding: 6rpx 16rpx;
  background: #eaf4ff;
  color: #035d95;
  border: 2rpx solid #b6daff;
  font-size: 28rpx;
  font-weight: 800;
}

.priority-text {
  color: #4f6a7b;
  font-size: 29rpx;
  font-weight: 700;
}

.done-badge {
  border-radius: 999rpx;
  border: 2rpx solid #b7eb8f;
  background: #f6ffed;
  color: #237804;
  font-size: 27rpx;
  padding: 4rpx 12rpx;
  font-weight: 700;
}

.rec-title {
  display: block;
  margin-top: 10rpx;
  color: #16384b;
  font-size: 40rpx;
  font-weight: 800;
  line-height: 1.35;
}

.meta-wrap {
  margin-top: 10rpx;
  display: flex;
  flex-wrap: wrap;
  gap: 8rpx;
}

.meta-chip {
  padding: 6rpx 12rpx;
  border-radius: 999rpx;
  border: 2rpx solid #d2e6f5;
  background: #f3f9ff;
  color: #4f697a;
  font-size: 28rpx;
}

.domain-line,
.rationale-line,
.evidence-line {
  display: block;
  margin-top: 8rpx;
  font-size: 30rpx;
  line-height: 1.72;
}

.domain-line {
  color: #0369a1;
  font-weight: 700;
}

.rationale-line {
  color: #355062;
}

.evidence-line {
  color: #738998;
}

.guide-box {
  margin-top: 12rpx;
  border-radius: 16rpx;
  border: 2rpx solid #d9ecff;
  background: #f7fbff;
  overflow: hidden;
}

.guide-head {
  padding: 12rpx 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
  border-bottom: 2rpx solid #e3f0fb;
}

.guide-title {
  color: #035b92;
  font-size: 32rpx;
  font-weight: 800;
}

.guide-toggle {
  color: #0284c7;
  font-size: 28rpx;
  font-weight: 700;
}

.guide-body {
  padding: 4rpx 14rpx 14rpx;
}

.guide-step,
.guide-extra {
  display: block;
  margin-top: 8rpx;
  color: #304050;
  font-size: 30rpx;
  line-height: 1.72;
}

.checkin-btn,
.done-btn {
  margin-top: 14rpx;
  width: 100%;
  min-height: 98rpx;
  border-radius: 999rpx;
  font-size: 35rpx;
  font-weight: 800;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
}

.checkin-btn {
  border: none;
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
  box-shadow: 0 10rpx 18rpx rgba(15, 118, 110, 0.26);
}

.done-btn {
  border: 2rpx solid #b7eb8f;
  background: #f6ffed;
  color: #237804;
}
</style>
