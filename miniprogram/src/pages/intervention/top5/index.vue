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
            <view class="rank-badge">TOP {{ item.rank }}</view>
            <text class="rec-score">优先级 {{ item.priority_score }}</text>
          </view>
          <text class="rec-title">{{ item.title }}</text>
          <text class="rec-meta">
            分类：{{ item.category }} | 频次：{{ item.frequency }} | 时长：{{ item.duration_minutes }} 分钟
          </text>
          <text class="rec-domains">目标认知域：{{ formatDomains(item.target_domains) }}</text>
          <text class="rec-rationale">{{ item.rationale }}</text>
          <text class="rec-evidence">证据等级：{{ item.evidence_level }}</text>
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

const DOMAIN_LABELS = {
  memory: '记忆力',
  orientation: '定向力',
  language: '语言能力',
  attention: '注意力',
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

const recommendations = computed(() => {
  if (!top5Data.value || !Array.isArray(top5Data.value.recommendations)) return []
  return top5Data.value.recommendations
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

function formatDate(raw) {
  if (!raw) return '--'
  const date = new Date(raw)
  if (Number.isNaN(date.getTime())) return '--'
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')} ${String(date.getHours()).padStart(2, '0')}:${String(date.getMinutes()).padStart(2, '0')}`
}

function goToAssessment() {
  uni.navigateTo({ url: '/pages/assessment/start/index' })
}

async function loadTop5() {
  loading.value = true
  errorMsg.value = ''
  try {
    const data = await api.getInterventionTop5()
    top5Data.value = data || null
    if (!top5Data.value || recommendations.value.length === 0) {
      errorMsg.value = '当前暂无推荐结果，请先完成一次评估。'
    }
  } catch (error) {
    top5Data.value = null
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
  background: linear-gradient(135deg, #4A90D9, #1d6fa4);
  border-radius: 20rpx;
  padding: 28rpx;
  margin-bottom: 20rpx;
}

.header-title {
  display: block;
  color: #ffffff;
  font-size: 40rpx;
  font-weight: bold;
  margin-bottom: 10rpx;
}

.header-desc {
  display: block;
  color: rgba(255, 255, 255, 0.9);
  font-size: 26rpx;
  line-height: 1.6;
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
  font-size: 36rpx;
  font-weight: 600;
  color: #1f2d3d;
  margin-bottom: 12rpx;
}

.state-text {
  display: block;
  font-size: 28rpx;
  color: #677788;
  line-height: 1.6;
  margin-bottom: 20rpx;
}

.btn-primary,
.btn-light {
  width: 100%;
  border-radius: 40rpx;
  font-size: 30rpx;
  margin-bottom: 12rpx;
}

.btn-primary {
  background: linear-gradient(135deg, #4A90D9, #1d6fa4);
  color: #ffffff;
}

.btn-light {
  background: #ffffff;
  border: 2rpx solid #4A90D9;
  color: #4A90D9;
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
  font-size: 28rpx;
}

.summary-value {
  color: #1f2d3d;
  font-size: 32rpx;
  font-weight: 600;
}

.summary-date {
  display: block;
  color: #98a3af;
  font-size: 24rpx;
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

.rank-badge {
  background: #eaf4ff;
  color: #1d6fa4;
  border-radius: 14rpx;
  font-size: 24rpx;
  font-weight: 600;
  padding: 6rpx 14rpx;
}

.rec-score {
  color: #6b7785;
  font-size: 24rpx;
}

.rec-title {
  display: block;
  color: #1f2d3d;
  font-size: 32rpx;
  font-weight: 600;
  margin-bottom: 8rpx;
}

.rec-meta,
.rec-domains,
.rec-rationale,
.rec-evidence {
  display: block;
  font-size: 26rpx;
  line-height: 1.65;
  margin-bottom: 6rpx;
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
  margin-bottom: 0;
}
</style>
