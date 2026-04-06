<template>
  <view class="checkin-page">
    <view class="header-card">
      <text class="header-title">每日干预打卡</text>
      <text class="header-desc">完成后请及时打卡，医生会据此跟进干预效果。</text>
    </view>

    <view v-if="loading" class="state-card">
      <text class="state-text">加载中...</text>
    </view>

    <view v-else-if="plans.length === 0" class="state-card">
      <text class="state-title">当前暂无进行中的干预计划</text>
      <text class="state-text">请先在“干预推荐 Top-5”或医生端创建计划后再打卡。</text>
    </view>

    <view v-else class="plans-wrap">
      <view v-for="plan in plans" :key="plan.plan_id" class="plan-card">
        <text class="plan-title">{{ plan.plan_title }}</text>
        <text class="plan-meta">频次：{{ plan.frequency || '--' }}</text>
        <text class="plan-meta">
          完成率：{{ plan.completion_rate }}%（{{ plan.completed_count }}/{{ plan.total_records }}）
        </text>
        <text class="plan-meta">连续未完成：{{ plan.consecutive_missed_days }} 天</text>
        <text v-if="plan.latest_interruption_reason" class="plan-warning">
          最近中断原因：{{ plan.latest_interruption_reason }}
        </text>
        <view class="btn-row">
          <button class="btn-complete" @tap="() => checkinComplete(plan.plan_id)">今日已完成</button>
          <button class="btn-missed" @tap="() => checkinMissed(plan.plan_id)">今日未完成</button>
        </view>
      </view>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { onShow } from '@dcloudio/uni-app'

import { useAuthStore } from '../../../store/auth'
import { api } from '../../../utils/request'

const authStore = useAuthStore()
const loading = ref(false)
const plans = ref([])

async function loadProgress() {
  loading.value = true
  try {
    const data = await api.getInterventionMyProgress()
    const list = Array.isArray(data?.plans) ? data.plans : []
    plans.value = list
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
    await api.dailyInterventionCheckin({
      plan_id: planId,
      completed: true,
    })
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
        wx.showToast({ title: '已记录未完成', icon: 'success' })
        loadProgress()
      } catch (e) {
        wx.showToast({ title: e?.message || '提交失败', icon: 'none' })
      }
    },
  })
}

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
  background: linear-gradient(135deg, #4A90D9, #1d6fa4);
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
  font-size: 26rpx;
  line-height: 1.6;
  display: block;
}

.state-card,
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

.plans-wrap {
  display: flex;
  flex-direction: column;
  gap: 14rpx;
}

.plan-card {
  padding: 22rpx;
}

.plan-title {
  display: block;
  color: #1f2d3d;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 8rpx;
}

.plan-meta {
  display: block;
  color: #5f6c79;
  font-size: 26rpx;
  margin-bottom: 6rpx;
}

.plan-warning {
  display: block;
  color: #d46b08;
  font-size: 25rpx;
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
}

.btn-complete {
  background: linear-gradient(135deg, #52C41A, #389E0D);
  color: #fff;
}

.btn-missed {
  background: #fff7e6;
  color: #d46b08;
  border: 2rpx solid #ffd591;
}
</style>

