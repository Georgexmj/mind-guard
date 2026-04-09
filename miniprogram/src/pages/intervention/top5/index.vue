<template>
  <view class="top5-page">
    <view class="header-card">
      <text class="header-title">干预推荐 Top-5</text>
      <text class="header-desc">依据最近一次评估结果，自动生成重点训练方案</text>
    </view>

    <view v-if="loading" class="state-card">
      <text class="state-text">正在生成推荐...</text>
    </view>

    <view v-else-if="errorMsg" class="state-card">
      <text class="state-title">暂无可用推荐</text>
      <text class="state-text">{{ errorMsg }}</text>
      <button class="btn-primary" @tap="loadTop5">重新获取</button>
      <button class="btn-light" @tap="goToAssessment">去做一次评估</button>
    </view>

    <view v-else-if="top5Data" class="content-wrap">
      <view class="summary-card">
        <view class="summary-row">
          <text class="summary-label">风险等级</text>
          <text class="summary-value" :style="{ color: riskColor }">{{ riskLabel }}</text>
        </view>
        <view class="summary-row">
          <text class="summary-label">MMSE 分数</text>
          <text class="summary-value">{{ top5Data.mmse_score ?? '--' }}</text>
        </view>
        <view class="summary-row">
          <text class="summary-label">MoCA（校正后）</text>
          <text class="summary-value">{{ top5Data.moca_score_corrected ?? '--' }}</text>
        </view>
        <text class="summary-date">生成时间：{{ formatDate(top5Data.generated_at) }}</text>
      </view>

      <view class="list-wrap">
        <view
          v-for="item in recommendations"
          :key="item.code"
          class="rec-card"
        >
          <view class="rec-top">
            <view class="rank-wrap">
              <view class="rank-badge">TOP {{ item.rank }}</view>
              <text v-if="item.today_done" class="done-chip">今日已打卡</text>
            </view>
            <text class="rec-score">优先级 {{ item.priority_score }}</text>
          </view>
          <text class="rec-title">{{ item.title }}</text>
          <text class="rec-meta">
            分类：{{ item.category }} | 频次：{{ item.frequency }} | 时长：{{ item.duration_minutes }} 分钟
          </text>
          <text class="rec-domains">目标认知域：{{ formatDomains(item.target_domains) }}</text>
          <text class="rec-rationale">{{ item.rationale }}</text>
          <text class="rec-evidence">证据等级：{{ item.evidence_level }}</text>

          <view class="guide-box">
            <text class="guide-title">具体怎么做</text>
            <text
              v-for="(step, idx) in item.guide.steps"
              :key="`${item.code}-step-${idx}`"
              class="guide-step"
            >
              {{ idx + 1 }}. {{ step }}
            </text>
            <text class="guide-extra">所需物品：{{ formatList(item.guide.materials) }}</text>
            <text class="guide-extra">完成判定：{{ item.guide.completion_hint }}</text>
            <text class="guide-extra">注意事项：{{ formatList(item.guide.precautions) }}</text>
          </view>

          <button v-if="!item.today_done" class="btn-checkin" @tap.stop="() => onTapRecommendation(item)">
            按此方案去打卡
          </button>
          <text v-else class="done-tip">今日已打卡，明天再来</text>
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
  normal: '#52C41A',
  mild_risk: '#FA8C16',
  high_risk: '#F5222D',
}

const TRAINING_PLAYBOOK = {
  memory_association: {
    steps: [
      '准备 6-8 张日常物品卡片（如钥匙、杯子、药盒）。',
      '先看 30 秒并大声说出每个物品名称，再遮住卡片回忆。',
      '回忆后核对错误项，重复 2 轮，总时长控制在 15 分钟内。',
    ],
    materials: ['图片卡片或便签', '计时器'],
    precautions: ['每轮不超过 8 个词，避免疲劳', '错误较多时先减少题量再递增'],
    completion_hint: '完成至少 2 轮回忆训练并记录正确数量。',
  },
  orientation_calendar: {
    steps: [
      '查看当天日历，口述今天日期、星期、季节和所在城市。',
      '对照家中“定位提示卡”回答“现在在什么地方、准备做什么”。',
      '让家属随机追问 3 个定向问题并当场纠正。',
    ],
    materials: ['纸质日历或手机日历', '家庭定位提示卡'],
    precautions: ['优先在固定时间训练（如早餐后）', '纠错时语气平和，避免焦虑'],
    completion_hint: '完成日期/地点/任务三类问题各 1 轮。',
  },
  attention_serial: {
    steps: [
      '从 100 开始连续减 7（100、93、86...），持续 3 分钟。',
      '改为正向数字复述：听 4-6 位数字后立即复述。',
      '最后做 1 分钟“找不同/划消目标数字”强化专注。',
    ],
    materials: ['纸笔', '数字卡或口播题'],
    precautions: ['出现明显卡顿时可改为减 3', '每 5 分钟安排 1 分钟休息'],
    completion_hint: '完成 3 组计算或复述任务且中途无退出。',
  },
  language_fluency: {
    steps: [
      '选择一个主题（水果/动物），1 分钟内尽量多说同类词汇。',
      '朗读 1 段 80-120 字短文并复述主要内容。',
      '与家属进行 5 分钟对话，重点描述“今天做了什么”。',
    ],
    materials: ['短文材料', '计时器'],
    precautions: ['不要追求速度，先保证表达完整', '复述困难时可先看关键词'],
    completion_hint: '完成“词语流畅 + 短文复述 + 日常表达”三项。',
  },
  visuospatial_clock: {
    steps: [
      '在空白纸上画钟面并标出 1-12 数字位置。',
      '按提示画出指定时间（如 10:10、3:45）的时针和分针。',
      '观察并修正数字间距、指针方向和长短比例。',
    ],
    materials: ['A4 纸', '铅笔和橡皮'],
    precautions: ['先画大轮廓再补细节', '避免连续绘制超过 15 分钟'],
    completion_hint: '独立完成至少 2 个时钟并完成一次自检。',
  },
  executive_planning: {
    steps: [
      '选一项生活任务（如“做午饭”）列出 5-7 个步骤。',
      '给每一步标注先后顺序和预计耗时。',
      '执行后回顾：哪些步骤漏掉、哪些顺序需调整。',
    ],
    materials: ['任务清单纸', '笔'],
    precautions: ['任务要具体可执行', '先从 15 分钟内可完成的小任务开始'],
    completion_hint: '完成“计划-执行-复盘”闭环 1 次。',
  },
  aerobic_walk: {
    steps: [
      '热身 3-5 分钟（原地踏步、肩颈活动）。',
      '中等速度步行 20-30 分钟，保持可交谈但略喘。',
      '结束后做 3 分钟放松拉伸并记录步行时长。',
    ],
    materials: ['舒适运动鞋', '水杯', '计步工具'],
    precautions: ['有心血管基础病先遵医嘱', '出现胸闷头晕应立即停止'],
    completion_hint: '有效步行达到方案时长并完成训练记录。',
  },
  social_engagement: {
    steps: [
      '与家属或同伴开展 15 分钟主题交流（近期新闻/回忆话题）。',
      '进行 10-15 分钟桌游或协作活动（如拼图、棋牌）。',
      '结束后口述今天最有印象的 3 件事。',
    ],
    materials: ['交流话题卡', '简单桌游材料'],
    precautions: ['控制环境噪音，减少干扰', '优先选择老人熟悉的话题'],
    completion_hint: '完成交流 + 互动活动，并给出当日回顾。',
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
  return RISK_COLORS[level] || '#4A90D9'
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
    .replace(/[\s\-—_|｜:：()（）【】\[\]·,，。；;！!？?]/g, '')
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
      `准备安静环境，按“${item?.title || '训练项目'}”进行 ${duration} 分钟训练。`,
      `围绕“${domains}”完成 2-3 轮练习，每轮后短暂休息。`,
      '训练结束后回顾完成情况，并在当日完成打卡。',
    ],
    materials: ['纸笔', '计时器'],
    precautions: ['以不疲劳为原则，必要时拆分训练', '不适时及时停止并联系医生'],
    completion_hint: `当日累计训练达到 ${duration} 分钟即可记为完成。`,
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

function goToCheckin(planId = 0) {
  const id = toNumber(planId, 0)
  const url = id > 0
    ? `/pages/intervention/checkin/index?focus_plan_id=${id}`
    : '/pages/intervention/checkin/index'
  uni.navigateTo({ url })
}

async function onTapRecommendation(item) {
  if (item?.today_done) {
    wx.showToast({ title: '今日已打卡，无需重复', icon: 'none' })
    return
  }
  wx.showModal({
    title: item?.title || '训练建议',
    content: '将跳转到“每日干预打卡”页面，可按该建议执行训练并记录完成情况。',
    confirmText: '去打卡',
    cancelText: '取消',
    success: async (res) => {
      if (!res.confirm) return
      try {
        wx.showLoading({ title: '正在关联计划...' })
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
        wx.hideLoading()
        goToCheckin(targetPlanId)
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
              wx.showToast({ title: '已定位到关联计划，正在跳转', icon: 'none' })
              goToCheckin(linkedPlanId)
              return
            }
            wx.showToast({ title: '暂无自动建计划权限，请联系医生创建计划', icon: 'none' })
            goToCheckin()
            return
          } catch (_) {
            wx.showToast({ title: '权限不足，请联系医生创建计划', icon: 'none' })
            return
          }
        }
        wx.showToast({ title: message || '关联失败，请稍后重试', icon: 'none' })
      }
    },
  })
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
  background: #f1f5f9;
  padding: 24rpx 24rpx 36rpx;
}

.header-card {
  background: linear-gradient(135deg, #4a90d9, #1d6fa4);
  border-radius: 20rpx;
  padding: 28rpx;
  margin-bottom: 20rpx;
}

.header-title {
  display: block;
  color: #ffffff;
  font-size: 46rpx;
  font-weight: bold;
  margin-bottom: 12rpx;
}

.header-desc {
  display: block;
  color: rgba(255, 255, 255, 0.9);
  font-size: 30rpx;
  line-height: 1.75;
}

.state-card,
.summary-card,
.rec-card {
  background: #ffffff;
  border-radius: 18rpx;
  box-shadow: 0 3rpx 14rpx rgba(0, 0, 0, 0.07);
}

.state-card {
  padding: 34rpx 28rpx;
}

.state-title {
  display: block;
  font-size: 40rpx;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 12rpx;
}

.state-text {
  display: block;
  font-size: 32rpx;
  color: #677788;
  line-height: 1.75;
  margin-bottom: 20rpx;
}

.btn-primary,
.btn-light {
  width: 100%;
  border-radius: 40rpx;
  font-size: 34rpx;
  height: 86rpx;
  line-height: 86rpx;
  margin-bottom: 12rpx;
}

.btn-primary {
  background: linear-gradient(135deg, #4a90d9, #1d6fa4);
  color: #ffffff;
}

.btn-light {
  background: #ffffff;
  border: 2rpx solid #4a90d9;
  color: #4a90d9;
}

.summary-card {
  padding: 24rpx;
  margin-bottom: 18rpx;
}

.summary-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12rpx;
}

.summary-label {
  color: #6b7785;
  font-size: 32rpx;
}

.summary-value {
  color: #1f2d3d;
  font-size: 38rpx;
  font-weight: 600;
}

.summary-date {
  display: block;
  color: #98a3af;
  font-size: 28rpx;
  margin-top: 8rpx;
}

.list-wrap {
  display: flex;
  flex-direction: column;
  gap: 16rpx;
}

.rec-card {
  padding: 22rpx;
}

.rec-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 10rpx;
}

.rank-wrap {
  display: flex;
  align-items: center;
  gap: 10rpx;
}

.rank-badge {
  background: #eaf4ff;
  color: #1d6fa4;
  border-radius: 14rpx;
  font-size: 30rpx;
  font-weight: 600;
  padding: 8rpx 16rpx;
}

.rec-score {
  color: #6b7785;
  font-size: 30rpx;
}

.done-chip {
  color: #389e0d;
  background: #f6ffed;
  border: 1rpx solid #b7eb8f;
  border-radius: 20rpx;
  padding: 4rpx 14rpx;
  font-size: 28rpx;
  font-weight: 600;
}

.rec-title {
  display: block;
  color: #1f2d3d;
  font-size: 42rpx;
  font-weight: 600;
  margin-bottom: 10rpx;
}

.rec-meta,
.rec-domains,
.rec-rationale,
.rec-evidence {
  display: block;
  font-size: 32rpx;
  line-height: 1.8;
  margin-bottom: 8rpx;
}

.rec-meta {
  color: #4b5563;
}

.rec-domains {
  color: #1d6fa4;
}

.rec-rationale {
  color: #566372;
}

.rec-evidence {
  color: #8a97a5;
  margin-bottom: 10rpx;
}

.guide-box {
  background: #f7fbff;
  border: 1rpx solid #d7ebff;
  border-radius: 14rpx;
  padding: 14rpx 16rpx;
}

.guide-title {
  display: block;
  color: #1d6fa4;
  font-size: 34rpx;
  font-weight: 600;
  margin-bottom: 8rpx;
}

.guide-step {
  display: block;
  color: #2f3b48;
  font-size: 32rpx;
  line-height: 1.85;
  margin-bottom: 6rpx;
}

.guide-extra {
  display: block;
  color: #445261;
  font-size: 30rpx;
  line-height: 1.8;
  margin-top: 6rpx;
}

.btn-checkin {
  margin-top: 14rpx;
  border-radius: 36rpx;
  background: #e6f4ff;
  color: #1677ff;
  border: 2rpx solid #91caff;
  font-size: 34rpx;
  height: 92rpx;
  line-height: 92rpx;
  font-weight: 600;
}

.done-tip {
  display: block;
  margin-top: 16rpx;
  text-align: center;
  color: #389e0d;
  background: #f6ffed;
  border: 1rpx solid #b7eb8f;
  border-radius: 28rpx;
  font-size: 30rpx;
  line-height: 72rpx;
}

</style>
