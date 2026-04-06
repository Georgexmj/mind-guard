<template>
  <view class="login-page">
    <!-- Header / Logo Area -->
    <view class="header">
      <view class="logo-circle">
        <text class="logo-icon">🧠</text>
      </view>
      <text class="app-title">MindGuard</text>
      <text class="app-subtitle">社区认知健康评估系统</text>
    </view>

    <!-- Login Form -->
    <view class="form-card">
      <text class="form-title">欢迎登录</text>

      <!-- Phone Input -->
      <view class="input-group">
        <text class="input-label">手机号码</text>
        <view class="input-wrapper">
          <text class="input-icon">📱</text>
          <input
            v-model="phone"
            class="input-field"
            type="number"
            placeholder="请输入手机号"
            placeholder-class="input-placeholder"
            maxlength="11"
            :disabled="loading"
          />
        </view>
      </view>

      <!-- Password Input -->
      <view class="input-group">
        <text class="input-label">登录密码</text>
        <view class="input-wrapper">
          <text class="input-icon">🔒</text>
          <input
            v-model="password"
            class="input-field"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
            placeholder-class="input-placeholder"
            :disabled="loading"
          />
          <text class="eye-icon" @tap="togglePassword">{{ showPassword ? '🙈' : '👁️' }}</text>
        </view>
      </view>

      <!-- Error Message -->
      <view v-if="errorMsg" class="error-box">
        <text class="error-text">⚠️ {{ errorMsg }}</text>
      </view>

      <!-- Login Button -->
      <button
        class="btn-login"
        :loading="loading"
        :disabled="loading || !phone || !password"
        @tap="handleLogin"
      >
        <text v-if="!loading">登 录</text>
        <text v-else>登录中...</text>
      </button>
    </view>

    <!-- Demo Account Hint -->
    <view class="demo-hint">
      <text class="demo-title">演示账号</text>
      <text class="demo-info">手机号：13800000003</text>
      <text class="demo-info">密　码：elder123</text>
      <button class="btn-demo" @tap="fillDemo">使用演示账号</button>
    </view>

    <!-- Footer -->
    <view class="footer">
      <text class="footer-text">张家界学院 · 社区健康研究中心</text>
    </view>
  </view>
</template>

<script setup>
import { ref } from 'vue'
import { useAuthStore } from '../../store/auth'
import { api } from '../../utils/request'

const auth = useAuthStore()

const phone = ref('')
const password = ref('')
const loading = ref(false)
const errorMsg = ref('')
const showPassword = ref(false)

function togglePassword() {
  showPassword.value = !showPassword.value
}

function fillDemo() {
  phone.value = '13800000003'
  password.value = 'elder123'
  errorMsg.value = ''
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
  // Validation
  errorMsg.value = ''

  if (!phone.value) {
    errorMsg.value = '请输入手机号码'
    return
  }
  if (!/^1[3-9]\d{9}$/.test(phone.value)) {
    errorMsg.value = '请输入正确的手机号码'
    return
  }
  if (!password.value) {
    errorMsg.value = '请输入登录密码'
    return
  }
  if (password.value.length < 6) {
    errorMsg.value = '密码长度不能少于6位'
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
        console.warn('WeChat bind by code failed:', bindErr)
      }

      wx.showToast({
        title: '登录成功',
        icon: 'success',
        duration: 1500
      })

      setTimeout(() => {
        uni.switchTab({ url: '/pages/index/index' })
      }, 1500)
    } else {
      errorMsg.value = '登录失败，请检查账号和密码'
    }
  } catch (err) {
    console.error('Login error:', err)
    errorMsg.value = err.message || '登录失败，请稍后重试'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  background: linear-gradient(160deg, #4A90D9 0%, #2c6fad 40%, #F5F5F5 40%);
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-bottom: 60rpx;
}

/* Header */
.header {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding-top: 80rpx;
  padding-bottom: 60rpx;
}

.logo-circle {
  width: 160rpx;
  height: 160rpx;
  background: rgba(255, 255, 255, 0.25);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 24rpx;
  border: 4rpx solid rgba(255, 255, 255, 0.5);
}

.logo-icon {
  font-size: 80rpx;
  line-height: 1;
}

.app-title {
  font-size: 56rpx;
  font-weight: bold;
  color: #ffffff;
  letter-spacing: 4rpx;
  margin-bottom: 12rpx;
}

.app-subtitle {
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.85);
  letter-spacing: 2rpx;
}

/* Form Card */
.form-card {
  background: #ffffff;
  border-radius: 24rpx;
  padding: 50rpx 40rpx 40rpx;
  margin: 0 30rpx;
  width: calc(100% - 60rpx);
  box-shadow: 0 8rpx 40rpx rgba(0, 0, 0, 0.12);
  box-sizing: border-box;
}

.form-title {
  font-size: 44rpx;
  font-weight: bold;
  color: #333333;
  display: block;
  margin-bottom: 40rpx;
  text-align: center;
}

/* Input Groups */
.input-group {
  margin-bottom: 32rpx;
}

.input-label {
  font-size: 30rpx;
  color: #666666;
  display: block;
  margin-bottom: 12rpx;
  font-weight: 500;
}

.input-wrapper {
  display: flex;
  align-items: center;
  background: #F8F9FA;
  border-radius: 16rpx;
  border: 2rpx solid #E0E0E0;
  padding: 0 20rpx;
  height: 100rpx;
  transition: border-color 0.2s;
}

.input-wrapper:focus-within {
  border-color: #4A90D9;
  background: #F0F6FF;
}

.input-icon {
  font-size: 36rpx;
  margin-right: 16rpx;
}

.input-field {
  flex: 1;
  font-size: 36rpx;
  color: #333333;
  background: transparent;
  border: none;
  height: 100rpx;
}

.input-placeholder {
  color: #AAAAAA;
  font-size: 32rpx;
}

.eye-icon {
  font-size: 36rpx;
  padding: 10rpx;
}

/* Error Box */
.error-box {
  background: #FFF2F0;
  border: 2rpx solid #FFCCC7;
  border-radius: 12rpx;
  padding: 20rpx 24rpx;
  margin-bottom: 24rpx;
}

.error-text {
  font-size: 30rpx;
  color: #F5222D;
  display: block;
}

/* Login Button */
.btn-login {
  width: 100%;
  height: 100rpx;
  background: linear-gradient(135deg, #4A90D9, #2c6fad);
  color: #ffffff;
  font-size: 40rpx;
  font-weight: bold;
  border-radius: 50rpx;
  border: none;
  margin-top: 16rpx;
  letter-spacing: 6rpx;
  box-shadow: 0 8rpx 24rpx rgba(74, 144, 217, 0.4);
}

.btn-login[disabled] {
  background: #B0C4DE;
  box-shadow: none;
}

/* Demo Hint */
.demo-hint {
  background: #FFFBE6;
  border: 2rpx solid #FFE58F;
  border-radius: 20rpx;
  padding: 30rpx;
  margin: 30rpx 30rpx 0;
  width: calc(100% - 60rpx);
  box-sizing: border-box;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.demo-title {
  font-size: 28rpx;
  font-weight: bold;
  color: #875500;
  margin-bottom: 12rpx;
}

.demo-info {
  font-size: 28rpx;
  color: #AD6800;
  display: block;
  margin-bottom: 6rpx;
  letter-spacing: 1rpx;
}

.btn-demo {
  margin-top: 20rpx;
  background: #FAAD14;
  color: #ffffff;
  font-size: 28rpx;
  height: 72rpx;
  border-radius: 36rpx;
  border: none;
  padding: 0 40rpx;
  font-weight: bold;
}

/* Footer */
.footer {
  margin-top: 40rpx;
  text-align: center;
}

.footer-text {
  font-size: 24rpx;
  color: #999999;
}
</style>
