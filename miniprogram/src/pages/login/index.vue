<template>
  <view class="login-page">
    <view class="hero-panel">
      <view class="logo-badge">MG</view>
      <text class="hero-title">忆守心安</text>
      <text class="hero-subtitle">社区老年认知障碍早筛与干预系统</text>
    </view>

    <view class="mg-card login-card">
      <text class="card-title">欢迎登录</text>

      <view class="field-block">
        <text class="field-label">手机号</text>
        <view class="field-input-wrap">
          <text class="field-prefix">📱</text>
          <input
            v-model="phone"
            class="field-input"
            type="number"
            placeholder="请输入手机号"
            placeholder-class="field-placeholder"
            maxlength="11"
            :disabled="loading"
          />
        </view>
      </view>

      <view class="field-block">
        <text class="field-label">登录密码</text>
        <view class="field-input-wrap">
          <text class="field-prefix">🔒</text>
          <input
            v-model="password"
            class="field-input"
            type="text"
            :password="!showPassword"
            placeholder="请输入登录密码"
            placeholder-class="field-placeholder"
            :disabled="loading"
          />
          <text class="toggle-text" @tap="togglePassword">{{ showPassword ? '隐藏' : '显示' }}</text>
        </view>
      </view>

      <view v-if="errorMsg" class="error-tip">
        <text class="error-tip-text">{{ errorMsg }}</text>
      </view>

      <button
        class="submit-btn"
        :class="{ 'submit-btn-disabled': loginDisabled }"
        :loading="loading"
        :disabled="loginDisabled"
        @tap="handleLogin"
      >
        {{ loading ? '登录中...' : '立即登录' }}
      </button>
    </view>

    <view class="foot-note">
      <text class="foot-note-text">张家界学院 · 社区健康研究中心</text>
    </view>
  </view>
</template>

<script setup>
import { computed, ref } from 'vue'
import { useAuthStore } from '../../store/auth'
import { api } from '../../utils/request'

const auth = useAuthStore()

const phone = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)
const loginDisabled = computed(() => loading.value || !phone.value || !password.value)

function togglePassword() {
  showPassword.value = !showPassword.value
}

function wxLoginCode() {
  return new Promise((resolve, reject) => {
    wx.login({
      success: (res) => resolve(res.code || ''),
      fail: (err) => reject(err),
    })
  })
}

async function handleLogin() {
  errorMsg.value = ''

  if (!phone.value) {
    errorMsg.value = '请输入手机号'
    return
  }
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    errorMsg.value = '请输入有效的手机号'
    return
  }
  if (!password.value) {
    errorMsg.value = '请输入登录密码'
    return
  }
  if (password.value.length < 6) {
    errorMsg.value = '密码长度不能少于 6 位'
    return
  }

  loading.value = true

  try {
    const result = await api.login(phone.value, password.value)

    if (result.access_token && result.user) {
      const accepted = auth.setAuth(result.user, result.access_token)
      if (!accepted) {
        loading.value = false
        return
      }

      try {
        const code = await wxLoginCode()
        if (code && result.user?.id) {
          await api.bindWechatByCode({
            user_id: result.user.id,
            code,
            is_active: true,
          })
        }
      } catch (bindErr) {
        console.warn('bind wechat by code failed', bindErr)
      }

      wx.showToast({
        title: '登录成功',
        icon: 'success',
        duration: 1200,
      })

      setTimeout(() => {
        uni.switchTab({ url: '/pages/index/index' })
      }, 800)
    } else {
      errorMsg.value = '登录失败，请检查账号和密码'
    }
  } catch (err) {
    console.error('login error', err)
    errorMsg.value = err?.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  padding: 70rpx 30rpx 54rpx;
  display: flex;
  flex-direction: column;
}

.hero-panel {
  border-radius: 30rpx;
  padding: 34rpx 28rpx;
  margin-bottom: 24rpx;
  background:
    radial-gradient(circle at 84% 10%, rgba(255, 255, 255, 0.28), transparent 40%),
    linear-gradient(145deg, #0f766e, #0284c7);
  box-shadow: var(--mg-shadow-strong);
  display: flex;
  flex-direction: column;
  align-items: center;
  text-align: center;
}

.logo-badge {
  width: 132rpx;
  height: 132rpx;
  border-radius: 36rpx;
  background: rgba(255, 255, 255, 0.2);
  border: 2rpx solid rgba(255, 255, 255, 0.42);
  color: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 54rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
  margin-bottom: 20rpx;
}

.hero-title {
  color: #ffffff;
  font-size: 58rpx;
  font-weight: 800;
  margin-bottom: 8rpx;
}

.hero-subtitle {
  color: rgba(237, 252, 255, 0.92);
  font-size: 29rpx;
}

.login-card {
  padding: 34rpx 30rpx;
}

.card-title {
  display: block;
  font-size: 42rpx;
  font-weight: 800;
  color: #143445;
  margin-bottom: 20rpx;
}

.field-block {
  margin-bottom: 22rpx;
}

.field-label {
  display: block;
  font-size: 30rpx;
  color: #4f6777;
  font-weight: 600;
  margin-bottom: 8rpx;
}

.field-input-wrap {
  height: 98rpx;
  border-radius: 18rpx;
  border: 2rpx solid rgba(17, 34, 49, 0.12);
  background: #f7fbfd;
  display: flex;
  align-items: center;
  padding: 0 20rpx;
}

.field-prefix {
  font-size: 34rpx;
  margin-right: 10rpx;
}

.field-input {
  flex: 1;
  height: 100%;
  border: none;
  background: transparent;
  color: #153648;
  font-size: 34rpx;
}

.field-placeholder {
  color: #96acbb;
}

.toggle-text {
  font-size: 28rpx;
  color: var(--mg-brand);
  font-weight: 700;
}

.error-tip {
  border-radius: 14rpx;
  background: rgba(220, 38, 38, 0.08);
  border: 2rpx solid rgba(220, 38, 38, 0.18);
  padding: 14rpx 16rpx;
  margin-bottom: 16rpx;
}

.error-tip-text {
  color: var(--mg-danger);
  font-size: 28rpx;
}

.submit-btn {
  width: 100%;
  margin-top: 10rpx;
  height: 116rpx;
  line-height: 116rpx;
  border-radius: 58rpx;
  border: none;
  background: linear-gradient(135deg, #0f766e, #0284c7);
  color: #ffffff;
  font-size: 40rpx;
  font-weight: 800;
  letter-spacing: 2rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  text-align: center;
  box-shadow: 0 14rpx 24rpx rgba(15, 118, 110, 0.26);
}

.submit-btn::after {
  border: none;
}

.submit-btn.submit-btn-disabled {
  background: linear-gradient(135deg, #c7d3dc, #b5c4cf) !important;
  color: #f3f7fa !important;
  opacity: 1;
  box-shadow: none;
}

.foot-note {
  margin-top: auto;
  text-align: center;
  padding-top: 30rpx;
}

.foot-note-text {
  color: #7c94a4;
  font-size: 29rpx;
}
</style>

