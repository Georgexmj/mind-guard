<template>
  <view />
</template>

<script setup>
import { onLaunch } from '@dcloudio/uni-app'
import { useAuthStore } from './store/auth'

onLaunch(() => {
  const auth = useAuthStore()
  auth.init()
})
</script>

<style>
:root {
  --mg-bg: #ecf4f8;
  --mg-bg-elevated: #f7fcff;
  --mg-text-primary: #0e2f42;
  --mg-text-secondary: #4f6d80;
  --mg-brand: #0e7a6f;
  --mg-brand-strong: #0b655c;
  --mg-accent: #027dbd;
  --mg-danger: #dc2626;
  --mg-warning: #c97708;
  --mg-success: #15803d;
  --mg-card-border: rgba(17, 34, 49, 0.1);
  --mg-shadow-soft: 0 14rpx 28rpx rgba(17, 34, 49, 0.09);
  --mg-shadow-strong: 0 20rpx 38rpx rgba(17, 34, 49, 0.14);
  --mg-touch-min: 96rpx;
}

page {
  background:
    radial-gradient(circle at 4% -20%, rgba(14, 122, 111, 0.14), transparent 54%),
    radial-gradient(circle at 98% 0%, rgba(2, 125, 189, 0.1), transparent 52%),
    var(--mg-bg);
  color: var(--mg-text-primary);
  font-size: 34rpx;
  line-height: 1.72;
}

view,
text,
label,
button,
input,
textarea {
  box-sizing: border-box;
}

text,
label {
  color: var(--mg-text-primary);
  line-height: 1.72;
}

button {
  min-height: var(--mg-touch-min);
  border-radius: 999rpx;
  font-size: 36rpx;
  font-weight: 700;
  line-height: 1.2;
}

input,
textarea {
  font-size: 34rpx;
  line-height: 1.4;
}

.mg-card {
  background: rgba(255, 255, 255, 0.94);
  border: 2rpx solid var(--mg-card-border);
  border-radius: 26rpx;
  box-shadow: var(--mg-shadow-soft);
  animation: mg-fade-up 0.28s ease-out;
}

.mg-button-primary {
  background: linear-gradient(135deg, var(--mg-brand), var(--mg-accent));
  color: #ffffff;
  border: none;
  box-shadow: 0 12rpx 22rpx rgba(15, 118, 110, 0.24);
}

.mg-button-secondary {
  background: #ffffff;
  color: var(--mg-brand);
  border: 2rpx solid rgba(15, 118, 110, 0.28);
}

button:active {
  transform: scale(0.985);
}

@keyframes mg-fade-up {
  from {
    opacity: 0;
    transform: translateY(8rpx);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@media (prefers-reduced-motion: reduce) {
  .mg-card {
    animation: none;
  }

  button:active {
    transform: none;
  }
}
</style>
