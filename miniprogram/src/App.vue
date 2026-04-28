<script setup>
import { onLaunch, onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'

const fontSizeMap = {
  small: 24,
  medium: 28,
  large: 32,
  xlarge: 36
}

onLaunch(() => {
  console.log('App Launch')
  const auth = useAuthStore()
  auth.init()
})

onShow(() => {
  // 页面显示时应用字体大小
  applyFontSize()
})

const applyFontSize = () => {
  try {
    const settings = uni.getStorageSync('app_settings') || {}
    const fontSize = settings.fontSize || 'medium'
    const fontSizeValue = fontSizeMap[fontSize] || 28
    
    // 设置全局变量
    globalThis.currentFontSize = fontSize
    globalThis.currentFontSizeValue = fontSizeValue
    
    console.log('字体大小已应用:', fontSize, fontSizeValue)
  } catch (e) {
    console.error('应用字体大小失败', e)
  }
}

uni.$applyFontSize = applyFontSize
uni.$fontSizeMap = fontSizeMap
</script>

<style lang="scss">
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
  background: linear-gradient(180deg, #FFF9E8 0%, #FEF7E8 30%, #FEF7E8 100%);
  color: var(--mg-text-primary);
  line-height: 1.72;
  min-height: 100vh;
}

view, text, label, button, input, textarea {
  box-sizing: border-box;
}

button {
  min-height: var(--mg-touch-min);
  border-radius: 999rpx;
  font-weight: 700;
  line-height: 1.2;
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
