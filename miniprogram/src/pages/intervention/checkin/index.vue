<template>
  <view class="checkin-page">
    <view class="header-card">
      <text class="header-title">每日干预打卡</text>
      <text class="header-desc">完成后请及时打卡，医生会据此跟进干预效果。</text>
    </view>

    <view v-if="loading" class="state-card">
      <text class="state-text">加载中...</text>
    </view>

    <view v-else-if="normalizedPlans.length === 0" class="state-card">
      <text class="state-title">当前暂无进行中的干预计划</text>
      <text class="state-text">请先在“干预推荐 Top-5”或由医生创建计划后再打卡。</text>
    </view>

    <view v-else>
      <view class="summary-card">
        <view class="summary-item">
          <text class="summary-label">计划总数</text>
          <text class="summary-value">{{ summary.total }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">待打卡</text>
          <text class="summary-value warning">{{ summary.todoToday }}</text>
        </view>
        <view class="summary-item">
          <text class="summary-label">今日完成</text>
          <text class="summary-value success">{{ summary.doneToday }}</text>
        </view>
      </view>

      <view class="guide-card">
        <text class="guide-title">如何完成训练并打卡</text>
        <text class="guide-text">1. 先到“干预推荐 Top-5”查看今日训练建议</text>
        <text class="guide-text">2. 按建议完成训练（线下或配合社区活动）</text>
        <text class="guide-text">3. 回到本页点击“今日已完成/今日未完成”</text>
        <button class="guide-btn" @tap="goToTop5">去看训练建议</button>
      </view>

      <view class="plans-wrap">
        <view v-for="plan in normalizedPlans" :key="plan.plan_id" class="plan-card">
          <view class="plan-top">
            <view class="plan-title-wrap">
              <text class="plan-title">{{ plan.plan_title }}</text>
              <text class="plan-id">计划ID：{{ plan.plan_id }}</text>
            </view>
            <text class="status-tag" :class="plan.today_status.className">{{ plan.today_status.label }}</text>
          </view>

          <text class="plan-meta">频次：{{ plan.frequency }}</text>
          <text v-if="plan.total_records > 0" class="plan-meta">
            完成率：{{ plan.completion_rate }}%（{{ plan.completed_count }}/{{ plan.total_records }}）
          </text>
          <text v-else class="plan-meta">完成率：暂无历史打卡</text>
          <text class="plan-meta">连续训练：{{ plan.consecutive_completed_days }} 天</text>

          <text v-if="plan.latest_interruption_reason" class="plan-warning">
            最近中断原因：{{ plan.latest_interruption_reason }}
          </text>

          <view v-if="!(plan.today_checked && plan.today_completed)" class="btn-row">
            <button class="btn-complete" @tap="() => checkinComplete(plan.plan_id)">今日已完成</button>
            <button class="btn-missed" @tap="() => checkinMissed(plan.plan_id)">今日未完成</button>
          </view>
          <text v-else class="done-tip">今日已完成打卡，明天再来</text>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'

import { useAuthStore } from '../../../store/auth'
import { api } from '../../../utils/request'

const authStore = useAuthStore()
const loading = ref(false)
const plans = ref([])
const localTodayStatusMap = ref({})
const focusPlanId = ref(0)

function toNumber(value, fallback = 0) {
  const n = Number(value)
  return Number.isFinite(n) ? n : fallback
}

function looksBrokenText(text) {
  if (!text) return true
  if (text.includes('�')) return true
  if (text.includes('?') || text.includes('？')) return true
  return false
}

function cleanText(text) {
  const raw = String(text || '').trim()
  if (!raw || looksBrokenText(raw)) return ''
  return raw
}

function buildTodayStatus(plan) {
  if (plan.today_checked && plan.today_completed) {
    return { label: '今日已完成', className: 'status-success' }
  }
  if (plan.today_checked && plan.today_completed === false) {
    return { label: '今日未完成', className: 'status-warning' }
  }
  return { label: '今日待打卡', className: 'status-default' }
}

const normalizedPlans = computed(() => {
  const rows = Array.isArray(plans.value) ? plans.value : []
  const uniqueById = new Map()

  rows.forEach((item) => {
    const planId = toNumber(item?.plan_id, -1)
    if (planId <= 0) return

    const title = cleanText(item?.plan_title) || `干预计划-${planId}`
    const frequency = cleanText(item?.frequency) || '未设置'
    const completionRate = toNumber(item?.completion_rate)
    const completedCount = toNumber(item?.completed_count)
    const totalRecords = toNumber(item?.total_records)
    let consecutiveCompletedDays = toNumber(item?.consecutive_completed_days)
    const consecutiveMissedDays = toNumber(item?.consecutive_missed_days)
    const latestReason = cleanText(item?.latest_interruption_reason)
    const localStatus = localTodayStatusMap.value[planId]
    const apiTodayChecked = Boolean(item?.today_checked)
    const apiTodayCompleted = item?.today_completed === true ? true : item?.today_completed === false ? false : null
    const todayChecked = localStatus ? true : apiTodayChecked
    const todayCompleted = localStatus ? localStatus.today_completed : apiTodayCompleted
    if (typeof localStatus?.consecutive_completed_days === 'number') {
      consecutiveCompletedDays = toNumber(localStatus.consecutive_completed_days)
    }
    if (todayChecked && todayCompleted && consecutiveCompletedDays < 1) {
      consecutiveCompletedDays = 1
    }

    uniqueById.set(planId, {
      plan_id: planId,
      plan_title: title,
      frequency,
      completion_rate: completionRate,
      completed_count: completedCount,
      total_records: totalRecords,
      consecutive_completed_days: consecutiveCompletedDays,
      consecutive_missed_days: consecutiveMissedDays,
      latest_interruption_reason: latestReason,
      today_checked: todayChecked,
      today_completed: todayCompleted,
      today_status: buildTodayStatus({ today_checked: todayChecked, today_completed: todayCompleted }),
    })
  })

  const statusRank = (plan) => {
    if (!plan.today_checked) return 0
    if (plan.today_completed === false) return 1
    return 2
  }

  return Array.from(uniqueById.values()).sort((a, b) => {
    const aFocused = focusPlanId.value > 0 && a.plan_id === focusPlanId.value
    const bFocused = focusPlanId.value > 0 && b.plan_id === focusPlanId.value
    if (aFocused !== bFocused) return aFocused ? -1 : 1

    const byStatus = statusRank(a) - statusRank(b)
    if (byStatus !== 0) return byStatus
    return b.plan_id - a.plan_id
  })
})

const summary = computed(() => {
  const list = normalizedPlans.value
  const total = list.length
  const doneToday = list.filter((p) => p.today_checked && p.today_completed).length
  const todoToday = list.filter((p) => !p.today_checked).length
  return { total, doneToday, todoToday }
})

async function loadProgress() {
  loading.value = true
  try {
    const data = await api.getInterventionMyProgress()
    plans.value = Array.isArray(data?.plans) ? data.plans : []
  } catch (e) {
    console.error('load intervention progress failed', e)
    plans.value = []
    wx.showToast({ title: '加载失败，请稍后重试', icon: 'none' })
  } finally {
    loading.value = false
  }
}

async function checkinComplete(planId) {
  try {
    const current = normalizedPlans.value.find((p) => p.plan_id === planId)
    const previousStreak = toNumber(current?.consecutive_completed_days)
    const alreadyDoneToday = Boolean(current?.today_checked && current?.today_completed)
    const nextCompletedStreak = alreadyDoneToday ? Math.max(1, previousStreak) : Math.max(0, previousStreak) + 1

    await api.dailyInterventionCheckin({
      plan_id: planId,
      completed: true,
    })
    localTodayStatusMap.value = {
      ...localTodayStatusMap.value,
      [planId]: {
        today_checked: true,
        today_completed: true,
        consecutive_completed_days: nextCompletedStreak,
      },
    }
    wx.showToast({ title: '已打卡', icon: 'success' })
    loadProgress()
  } catch (e) {
    wx.showToast({ title: e?.message || '打卡失败', icon: 'none' })
  }
}

function checkinMissed(planId) {
  wx.showModal({
    title: '填写中断原因',
    editable: true,
    placeholderText: '例如：身体不适、外出、忘记了',
    success: async (res) => {
      if (!res.confirm) return
      const reason = (res.content || '').trim()
      try {
        await api.dailyInterventionCheckin({
          plan_id: planId,
          completed: false,
          interruption_reason: reason || '未填写',
        })
        localTodayStatusMap.value = {
          ...localTodayStatusMap.value,
          [planId]: {
            today_checked: true,
            today_completed: false,
            consecutive_completed_days: 0,
          },
        }
        wx.showToast({ title: '已记录未完成', icon: 'success' })
        loadProgress()
      } catch (e) {
        wx.showToast({ title: e?.message || '提交失败', icon: 'none' })
      }
    },
  })
}

function goToTop5() {
  uni.navigateTo({ url: '/pages/intervention/top5/index' })
}

onLoad((options) => {
  focusPlanId.value = toNumber(options?.focus_plan_id, 0)
})

onShow(() => {
  if (!authStore.enforceElderRole()) return
  loadProgress()
})
</script>

<style scoped>
.checkin-page {
  min-height: 100vh;
  background: #f1f5f9;
  padding: 24rpx;
}

.header-card {
  background: linear-gradient(135deg, #4a90d9, #1d6fa4);
  border-radius: 20rpx;
  padding: 28rpx;
  margin-bottom: 18rpx;
}

.header-title {
  color: #fff;
  font-size: 40rpx;
  font-weight: bold;
  display: block;
  margin-bottom: 8rpx;
}

.header-desc {
  color: rgba(255, 255, 255, 0.9);
  font-size: 28rpx;
  line-height: 1.6;
  display: block;
}

.state-card,
.summary-card,
.guide-card,
.plan-card {
  background: #fff;
  border-radius: 18rpx;
  box-shadow: 0 3rpx 14rpx rgba(0, 0, 0, 0.07);
}

.state-card {
  padding: 32rpx 24rpx;
}

.state-title {
  display: block;
  color: #1f2d3d;
  font-size: 34rpx;
  font-weight: 600;
  margin-bottom: 10rpx;
}

.state-text {
  display: block;
  color: #6b7785;
  font-size: 28rpx;
}

.summary-card {
  padding: 20rpx 22rpx;
  margin-bottom: 14rpx;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.summary-item {
  display: flex;
  flex-direction: column;
  gap: 6rpx;
}

.summary-label {
  color: #7b8794;
  font-size: 28rpx;
}

.summary-value {
  color: #1f2d3d;
  font-size: 34rpx;
  font-weight: 700;
}

.summary-value.success {
  color: #52c41a;
}

.summary-value.warning {
  color: #fa8c16;
}

.guide-card {
  padding: 20rpx 22rpx;
  margin-bottom: 14rpx;
}

.guide-title {
  display: block;
  color: #1f2d3d;
  font-size: 28rpx;
  font-weight: 700;
  margin-bottom: 8rpx;
}

.guide-text {
  display: block;
  color: #5f6c79;
  font-size: 28rpx;
  line-height: 1.6;
  margin-bottom: 4rpx;
}

.guide-btn {
  margin-top: 10rpx;
  border-radius: 36rpx;
  font-size: 28rpx;
  background: #e6f4ff;
  color: #1677ff;
  border: 2rpx solid #91caff;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 24rpx;
  text-align: center;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.plans-wrap {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.plan-card {
  padding: 22rpx;
}

.plan-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12rpx;
  margin-bottom: 8rpx;
}

.plan-title-wrap {
  display: flex;
  flex-direction: column;
  gap: 4rpx;
}

.plan-title {
  color: #1f2d3d;
  font-size: 32rpx;
  font-weight: 600;
}

.plan-id {
  color: #98a3af;
  font-size: 28rpx;
}

.status-tag {
  flex-shrink: 0;
  border-radius: 24rpx;
  padding: 4rpx 14rpx;
  font-size: 28rpx;
}

.status-default {
  background: #f0f5ff;
  color: #1677ff;
}

.status-success {
  background: #f6ffed;
  color: #52c41a;
}

.status-warning {
  background: #fff7e6;
  color: #fa8c16;
}

.plan-meta {
  display: block;
  color: #5f6c79;
  font-size: 28rpx;
  margin-bottom: 6rpx;
}

.plan-warning {
  display: block;
  color: #d46b08;
  font-size: 28rpx;
  margin: 4rpx 0 10rpx;
}

.btn-row {
  display: flex;
  gap: 12rpx;
}

.btn-complete,
.btn-missed {
  flex: 1;
  border-radius: 40rpx;
  font-size: 28rpx;
  height: 72rpx;
  line-height: 72rpx;
  padding: 0 12rpx;
  text-align: center;
  box-sizing: border-box;
  display: flex;
  align-items: center;
  justify-content: center;
}

.btn-complete {
  background: linear-gradient(135deg, #52c41a, #389e0d);
  color: #fff;
}

.btn-missed {
  background: #fff7e6;
  color: #d46b08;
  border: 2rpx solid #ffd591;
}

.done-tip {
  display: block;
  margin-top: 8rpx;
  color: #52c41a;
  font-size: 28rpx;
  text-align: center;
}
</style>
