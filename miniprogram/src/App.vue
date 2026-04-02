<template>
  <div />
</template>

<script setup>
import { onLaunch, onShow } from '@dcloudio/uni-app'
import { useAuthStore } from './store/auth'

onLaunch(() => {
  const auth = useAuthStore()
  auth.init()
})

onShow(() => {
  // App becomes visible
})
</script>

<style>
/* Global elderly-friendly styles */
page {
  background-color: #F5F5F5;
  font-size: 36rpx;
  line-height: 1.6;
  color: #333333;
}

/* Large touch targets */
button {
  min-height: 88rpx;
  font-size: 34rpx;
  border-radius: 12rpx;
}

/* Global card style */
.card {
  background: #ffffff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin: 20rpx 30rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
}

/* Primary button */
.btn-primary {
  background-color: #4A90D9;
  color: #ffffff;
  border: none;
  min-height: 96rpx;
  font-size: 36rpx;
  font-weight: bold;
  border-radius: 48rpx;
  letter-spacing: 2rpx;
}

/* Secondary button */
.btn-secondary {
  background-color: #ffffff;
  color: #4A90D9;
  border: 2rpx solid #4A90D9;
  min-height: 96rpx;
  font-size: 36rpx;
  border-radius: 48rpx;
}
</style>
