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
  background-color: #f5f7fb;
  font-size: 38rpx;
  line-height: 1.75;
  color: #1f2d3d;
}

view,
text,
label {
  box-sizing: border-box;
}

text,
label {
  font-size: 32rpx;
  line-height: 1.75;
  color: #1f2d3d;
}

/* Large touch targets */
button {
  min-height: 96rpx;
  font-size: 34rpx;
  border-radius: 16rpx;
  line-height: 1.2;
}

input,
textarea {
  font-size: 32rpx;
  line-height: 1.7;
}

.card,
.elder-card {
  background: #ffffff;
  border-radius: 20rpx;
  padding: 30rpx;
  margin: 20rpx 30rpx;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.08);
}

.btn-primary,
.elder-btn-primary {
  background-color: #4a90d9;
  color: #ffffff;
  border: none;
  min-height: 100rpx;
  font-size: 36rpx;
  font-weight: 700;
  border-radius: 48rpx;
  letter-spacing: 1rpx;
}

.btn-secondary,
.elder-btn-secondary {
  background-color: #ffffff;
  color: #4a90d9;
  border: 2rpx solid #4a90d9;
  min-height: 100rpx;
  font-size: 36rpx;
  border-radius: 48rpx;
}
</style>
