<template>
  <view class="login-container">
    <!-- 品牌区 -->
    <view class="brand">
      <view class="logo">MG</view>
      <view class="app-name">忆守心安</view>
      <view class="slogan">社区老年认知障碍早筛与干预系统</view>
    </view>

    <!-- 欢迎区 -->
    <view class="welcome">
      <view class="title">欢迎回来</view>
      <view class="desc">请选择登录方式，开始使用认知守护服务</view>
    </view>

    <!-- 登录方式切换 -->
    <view class="tab-wrapper">
      <view class="tab" :class="{ active: loginType === 'elder' }" @click="switchLoginType('elder')">
        老人登录
      </view>
      <view class="tab" :class="{ active: loginType === 'child' }" @click="switchLoginType('child')">
        子女查看
      </view>
    </view>

    <!-- 老人登录表单 -->
    <block v-if="loginType === 'elder'">
      <view class="form">
        <!-- 身份证号 -->
        <view class="input-item">
          <view class="label">身份证号</view>
          <input class="input" type="text" placeholder="请输入身份证号" v-model="idCardForLogin" />
        </view>

        <!-- 密码 -->
        <view class="input-item">
          <view class="label">密码</view>
          <view class="password-wrapper">
            <input class="password-input" :password="!showPassword" placeholder="请输入密码" v-model="password" />
            <view class="password-eye" :class="{ hidden: !showPassword }" @tap.stop="togglePassword">
              <view class="eye-outline">
                <view class="eye-dot"></view>
              </view>
            </view>
          </view>
        </view>

        <view class="options">
          <view class="remember" @click="toggleRemember">
            <view :class="['check', { checked: rememberPwd }]">
              <text v-if="rememberPwd" class="check-mark">✓</text>
            </view>
            <text>记住密码</text>
          </view>
          <view class="forgot" @click="goToForgotPwd">忘记密码？</view>
        </view>

        <button class="login-btn" @click="handleLogin">立即登录</button>

        <view class="register">
          <text>需要为老人开通服务？</text>
          <text class="link" @tap.stop="goToChildBind">子女代为关联</text>
        </view>
      </view>

    </block>

    <!-- 子女查看表单 - 三步流程 -->
    <block v-else>
      <!-- 步骤指示器 -->
      <view class="steps">
        <view :class="['step', { active: childStep === 1, done: childStep > 1 }]">1</view>
        <view :class="['step-line', { active: childStep > 1 }]"></view>
        <view :class="['step', { active: childStep === 2, done: childStep > 2 }]">2</view>
        <view :class="['step-line', { active: childStep > 2 }]"></view>
        <view :class="['step', { active: childStep === 3 }]">3</view>
      </view>

      <!-- 第一步：搜索老人 -->
      <view v-if="childStep === 1" class="form child-form">
        <view class="guide-box">
          <text class="guide-text">输入老人姓名搜索，然后用身份证号码进行验证。</text>
        </view>
        <view class="input-item">
          <view class="label">老人姓名</view>
          <view class="search-input-wrapper">
            <text class="search-icon">🔍</text>
            <input class="input" type="text" placeholder="请输入老人姓名" v-model="elderName" />
          </view>
        </view>
        <button class="login-btn" @click="searchElder">搜索老人</button>
        
        <!-- 搜索结果 -->
        <view v-if="searchResults.length > 0" class="search-results">
          <view class="results-label">找到 {{ searchResults.length }} 位，点击选择：</view>
          <view 
            v-for="elder in searchResults" 
            :key="elder.id" 
            class="elder-card"
            @click="selectElder(elder)"
          >
            <view class="elder-avatar">{{ elder.name?.charAt(0) || '?' }}</view>
            <view class="elder-info">
              <view class="elder-name">{{ elder.name }}</view>
              <view class="elder-detail">{{ elder.age || '未知年龄' }} · {{ elder.gender === 'male' ? '男' : '女' }} · {{ elder.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') }}</view>
            </view>
            <view class="arrow">›</view>
          </view>
        </view>
        
        <!-- 未找到提示 -->
        <view v-if="searched && searchResults.length === 0" class="no-result">
          <text>此老人还未绑定</text>
        </view>
      </view>

      <!-- 第二步：确认老人信息 -->
      <view v-if="childStep === 2 && selectedElder" class="form child-form">
        <view class="back-btn" @click="backToSearch">← 返回搜索</view>
        <view class="elder-detail-card">
          <view class="elder-avatar-large">{{ selectedElder.name?.charAt(0) || '?' }}</view>
          <view class="elder-name-large">{{ selectedElder.name }}</view>
          <view class="elder-detail-large">{{ selectedElder.age || '未知年龄' }} · {{ selectedElder.gender === 'male' ? '男' : '女' }}</view>
          <view class="elder-detail-large">手机: {{ selectedElder.phone?.replace(/(\d{3})\d{4}(\d{4})/, '$1****$2') }}</view>
          <view class="id-card-info">
            <text class="id-label">身份证:</text>
            <text class="id-value">{{ selectedElder.id_card?.replace(/(\d{6})\d{8}(\d{4})/, '$1********$2') }}</text>
          </view>
        </view>
        <button class="login-btn" @click="goToVerify">确认，去输入身份证验证</button>
      </view>

      <!-- 第三步：验证身份证 -->
      <view v-if="childStep === 3 && selectedElder" class="form child-form">
        <view class="back-btn" @click="backToConfirm">← 返回</view>
        
        <view class="elder-tag">
          <view class="elder-tag-avatar">{{ selectedElder.name?.charAt(0) || '?' }}</view>
          <view class="elder-tag-info">
            <view class="elder-tag-name">{{ selectedElder.name }}</view>
            <view class="elder-tag-detail">{{ selectedElder.age || '未知年龄' }} · {{ selectedElder.gender === 'male' ? '男' : '女' }}</view>
          </view>
          <view class="close-btn" @click="clearSelection">×</view>
        </view>

        <view class="warning-box">
          <text class="warning-text">请输入 {{ selectedElder.name }} 的完整身份证号码。只有家属才知道完整信息。</text>
        </view>

        <view class="input-item">
          <view class="label">身份证号码</view>
          <input class="input" type="text" placeholder="18位身份证号" v-model="verifyIdCard" maxlength="18" />
          <view class="input-tip">共18位，末位可为数字或X</view>
        </view>
        
        <button :class="['login-btn', { loading: verifying }]" @click="verifyIdCardAndView">
          <text v-if="verifying">验证中...</text>
          <text v-else>验证身份并查看</text>
        </button>
      </view>
    </block>
  </view>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { onReady, onShareAppMessage, onShareTimeline } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'
import { api, getApiBaseUrl } from '@/utils/request'

const authStore = useAuthStore()

const loginType = ref('elder')
const idCardForLogin = ref('')   // 老人登录使用的身份证号
const password = ref('')
const showPassword = ref(false)
const rememberPwd = ref(true)
const childPhone = ref('')       // 子女登录使用的手机号
const childPassword = ref('')    // 子女登录使用的密码

// 子女查看三步流程相关
const childStep = ref(1)         // 1:搜索老人, 2:确认信息, 3:验证身份证
const elderName = ref('')        // 搜索用的老人姓名
const searchResults = ref([])    // 搜索结果
const searched = ref(false)      // 是否已搜索
const selectedElder = ref(null)  // 选中的老人
const verifyIdCard = ref('')     // 验证用的身份证号
const verifying = ref(false)     // 是否正在验证

const switchLoginType = (type) => {
  loginType.value = type
  if (type === 'child') {
    resetChildFlow()
  }
}

const resetChildFlow = () => {
  childStep.value = 1
  elderName.value = ''
  searchResults.value = []
  searched.value = false
  selectedElder.value = null
  verifyIdCard.value = ''
  verifying.value = false
}

const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const toggleRemember = () => {
  rememberPwd.value = !rememberPwd.value
}

// 老人登录处理（使用身份证号 + 密码）
const handleLogin = () => {
  if (!idCardForLogin.value || !password.value) {
    uni.showToast({ title: '请填写身份证号和密码', icon: 'none' })
    return
  }
  uni.showLoading({ title: '登录中...', mask: true })
  uni.request({
    url: `${getApiBaseUrl()}/auth/login`,
    method: 'POST',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: `username=${encodeURIComponent(idCardForLogin.value)}&password=${encodeURIComponent(password.value)}`,
    success: (res) => {
      uni.hideLoading()
      if (res.statusCode === 200 && res.data.access_token) {
        const token = res.data.access_token
        const userData = res.data.user || {}
        const userInfo = {
          id_card: idCardForLogin.value,
          name: userData.name || '用户',
          role: userData.role || 'elder',
          full_name: userData.name || '用户'
        }
        authStore.setAuth(userInfo, token)
        if (rememberPwd.value) {
          uni.setStorageSync('remembered_id_card', idCardForLogin.value)
          uni.setStorageSync('remembered_password', password.value)
        } else {
          uni.removeStorageSync('remembered_id_card')
          uni.removeStorageSync('remembered_password')
        }
        uni.showToast({ title: '登录成功', icon: 'success' })
        setTimeout(() => {
          uni.switchTab({ url: '/pages/index/index' })
        }, 500)
      } else {
        uni.showToast({ title: res.data.message || res.data.detail || '登录失败', icon: 'none' })
      }
    },
    fail: (err) => {
    uni.hideLoading();
    console.error('login error', err);
    // 确保 title 是字符串
    let errorMsg = '网络错误，请检查后端服务';
    if (err.errMsg && typeof err.errMsg === 'string') {
        errorMsg = err.errMsg;
    }
    uni.showToast({ title: errorMsg, icon: 'none' });
}
  })
}


// 子女登录处理（使用手机号 + 密码）
const handleChildLogin = () => {
  if (!childPhone.value || !childPassword.value) {
    uni.showToast({ title: '请填写手机号和密码', icon: 'none' })
    return
  }
  uni.showLoading({ title: '登录中...', mask: true })
  uni.request({
    url: `${getApiBaseUrl()}/auth/login`,
    method: 'POST',
    header: { 'content-type': 'application/x-www-form-urlencoded' },
    data: `username=${encodeURIComponent(childPhone.value)}&password=${encodeURIComponent(childPassword.value)}`,
    success: (res) => {
      uni.hideLoading()
      if (res.statusCode === 200 && res.data.access_token) {
        const token = res.data.access_token
        const userData = res.data.user || {}
        const userInfo = {
          phone: childPhone.value,
          name: userData.name || '用户',
          role: userData.role || 'family',
          full_name: userData.name || '用户'
        }
        authStore.setAuth(userInfo, token)
        uni.showToast({ title: '登录成功', icon: 'success' })
        setTimeout(() => {
          uni.switchTab({ url: '/pages/index/index' })
        }, 500)
      } else {
        uni.showToast({ title: res.data.message || res.data.detail || '登录失败', icon: 'none' })
      }
    },
    fail: (err) => {
      uni.hideLoading()
      console.error('child login error', err)
      let errorMsg = '网络错误，请检查后端服务'
      if (err.errMsg && typeof err.errMsg === 'string') {
        errorMsg = err.errMsg
      }
      uni.showToast({ title: errorMsg, icon: 'none' })
    }
  })
}


// 搜索老人
const searchElder = async () => {
  if (!elderName.value.trim()) {
    uni.showToast({ title: '请输入老人姓名', icon: 'none' })
    return
  }
  uni.showLoading({ title: '搜索中...', mask: true })
  try {
    const data = await api.searchElder(elderName.value)
    searchResults.value = Array.isArray(data) ? data : []
    searched.value = true
  } catch (error) {
    console.error('search elder error', error)
    searchResults.value = []
    searched.value = true
  } finally {
    uni.hideLoading()
  }
}

// 选择老人
const selectElder = (elder) => {
  selectedElder.value = elder
  childStep.value = 2
}

// 返回搜索
const backToSearch = () => {
  childStep.value = 1
  selectedElder.value = null
}

// 去验证身份证页面
const goToVerify = () => {
  childStep.value = 3
}

// 返回确认页面
const backToConfirm = () => {
  childStep.value = 2
  verifyIdCard.value = ''
}

// 清除选择
const clearSelection = () => {
  resetChildFlow()
}

// 验证身份证并查看老人数据
const verifyIdCardAndView = async () => {
  if (!verifyIdCard.value.trim() || verifyIdCard.value.length !== 18) {
    uni.showToast({ title: '请输入18位身份证号', icon: 'none' })
    return
  }
  verifying.value = true
  try {
    const data = await api.verifyElderIdCard(selectedElder.value.id, verifyIdCard.value)
    if (data.success) {
      // 验证成功，保存老人信息并跳转首页
      uni.setStorageSync('viewing_elder', JSON.stringify(selectedElder.value))
      uni.setStorageSync('family_view_mode', 'true')
      uni.showToast({ title: '验证成功', icon: 'success' })
      setTimeout(() => {
        uni.switchTab({ url: '/pages/index/index' })
      }, 500)
    } else {
      uni.showToast({ title: data.message || '身份验证失败', icon: 'none' })
    }
  } catch (error) {
    console.error('verify id card error', error)
    uni.showToast({ title: '验证失败，请重试', icon: 'none' })
  } finally {
    verifying.value = false
  }
}

const goToChildBind = () => {
  switchLoginType('child')
  uni.pageScrollTo({ scrollTop: 0, duration: 200 })
}

const goToForgotPwd = () => {
  uni.navigateTo({ url: '/pages/forgot/index' })
}

onReady(() => {
  uni.showShareMenu({
    withShareTicket: true,
    menus: ['shareAppMessage', 'shareTimeline'],
  })
})

onShareAppMessage(() => ({
  title: '忆守心安：社区老年认知障碍早筛与干预系统',
  path: '/pages/login/index',
}))

onShareTimeline(() => ({
  title: '忆守心安：社区老年认知障碍早筛与干预系统',
  query: '',
}))

onMounted(() => {
  if (authStore.isLoggedIn && authStore.token) {
    uni.switchTab({ url: '/pages/index/index' })
    return
  }
  const rememberedIdCard = uni.getStorageSync('remembered_id_card')
  const rememberedPassword = uni.getStorageSync('remembered_password')
  if (rememberedIdCard === '123456194808151234' || rememberedPassword === 'elder123') {
    uni.removeStorageSync('remembered_id_card')
    uni.removeStorageSync('remembered_password')
    rememberPwd.value = false
    return
  }
  if (rememberedIdCard && rememberedPassword) {
    idCardForLogin.value = rememberedIdCard
    password.value = rememberedPassword
    rememberPwd.value = true
  }
})
</script>

<style scoped>
/* 您原有的样式保持不变，此处省略以节省篇幅，请保留原有样式内容 */
</style>

<style scoped>
.login-container {
  min-height: 100vh;
  background: #FEF7E8;
  padding: 60rpx 48rpx 80rpx;
  box-sizing: border-box;
}

.brand {
  text-align: center;
  margin-bottom: 80rpx;
  background: #ffffff;
  border-radius: 48rpx;
  padding: 60rpx 30rpx 40rpx;
  box-shadow: 0 12rpx 24rpx rgba(0, 0, 0, 0.06);
}

.logo {
  display: inline-block;
  width: 100rpx;
  height: 100rpx;
  background: #E8A74C;
  border-radius: 32rpx;
  color: white;
  text-align: center;
  line-height: 100rpx;
  font-size: 52rpx;
  font-weight: 600;
  margin-bottom: 20rpx;
  box-shadow: 0 10rpx 24rpx rgba(232, 167, 76, 0.25);
}

.app-name {
  display: block;
  font-size: 44rpx;
  font-weight: 600;
  color: #B45F2A;
  letter-spacing: 2rpx;
  margin-bottom: 12rpx;
}

.slogan {
  display: block;
  font-size: 24rpx;
  color: #C97E4A;
}

.welcome {
  margin-bottom: 48rpx;
}

.title {
  display: block;
  font-size: 40rpx;
  font-weight: 600;
  color: #8B4A2A;
  margin-bottom: 12rpx;
}

.desc {
  display: block;
  font-size: 26rpx;
  color: #B87A4A;
}

.tab-wrapper {
  display: flex;
  background: #F5E8DA;
  border-radius: 60rpx;
  padding: 8rpx;
  margin-bottom: 48rpx;
}

.tab {
  flex: 1;
  text-align: center;
  padding: 20rpx 0;
  font-size: 30rpx;
  font-weight: 500;
  color: #B87A4A;
  border-radius: 60rpx;
}

.tab.active {
  background: #E8A74C;
  color: white;
  box-shadow: 0 4rpx 12rpx rgba(232, 167, 76, 0.3);
}

.form {
  background: white;
  border-radius: 32rpx;
  padding: 40rpx 32rpx;
  margin-bottom: 24rpx;
  box-shadow: 0 8rpx 24rpx rgba(0, 0, 0, 0.04);
}

.input-item {
  margin-bottom: 36rpx;
  background: transparent;
  border-bottom: 1px solid #F0E0D0;
  padding-bottom: 12rpx;
}

.label {
  display: block;
  font-size: 28rpx;
  color: #8B5A3A;
  margin-bottom: 12rpx;
}

.input {
  width: 100%;
  font-size: 32rpx;
  color: #4A2A1A;
  border: none;
  outline: none;
  background: transparent;
  padding: 0;
}

.password-wrapper {
  position: relative;
  display: flex;
  align-items: center;
  width: 100%;
}

.password-input {
  flex: 1;
  font-size: 32rpx;
  color: #4A2A1A;
  border: none;
  outline: none;
  background: transparent;
  padding-right: 60rpx;
}

.password-eye {
  position: absolute;
  right: 0;
  top: 50%;
  transform: translateY(-50%);
  width: 76rpx;
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  background: transparent;
  z-index: 3;
}

.eye-outline {
  position: relative;
  width: 48rpx;
  height: 28rpx;
  border: 3rpx solid #B87946;
  border-radius: 50%;
  box-sizing: border-box;
  background: rgba(255, 248, 238, 0.85);
}

.eye-outline::before {
  content: '';
  position: absolute;
  left: -4rpx;
  right: -4rpx;
  top: 50%;
  height: 20rpx;
  border-top: 3rpx solid #B87946;
  border-radius: 50%;
  transform: translateY(-50%);
}

.eye-dot {
  position: absolute;
  left: 50%;
  top: 50%;
  width: 12rpx;
  height: 12rpx;
  border-radius: 50%;
  background: #8B4A2A;
  transform: translate(-50%, -50%);
}

.password-eye.hidden::after {
  content: '';
  position: absolute;
  width: 58rpx;
  height: 4rpx;
  border-radius: 999rpx;
  background: #B45F2A;
  box-shadow: 0 0 0 4rpx #fff;
  transform: rotate(-42deg);
}

.options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 8rpx 0 48rpx;
}

.remember {
  display: flex;
  align-items: center;
  gap: 12rpx;
  font-size: 26rpx;
  color: #8B5A3A;
}

.check {
  width: 32rpx;
  height: 32rpx;
  border: 2rpx solid #D4B896;
  border-radius: 8rpx;
  background: white;
  display: flex;
  align-items: center;
  justify-content: center;
}

.check.checked {
  background: #E8A74C;
  border-color: #E8A74C;
}

.check-mark {
  color: white;
  font-size: 24rpx;
  font-weight: bold;
}

.forgot {
  font-size: 26rpx;
  color: #E8A74C;
}

.login-btn {
  background: #E8A74C;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: 48rpx;
  font-size: 32rpx;
  font-weight: 600;
  color: white;
  box-shadow: 0 8rpx 20rpx rgba(232, 167, 76, 0.25);
  margin-bottom: 32rpx;
  width: 100%;
  text-align: center;
}

.register {
  text-align: center;
  font-size: 26rpx;
  color: #8B5A3A;
  margin-top: 16rpx;
}

.link {
  color: #E8A74C;
  margin-left: 12rpx;
}

.child-form .input-item {
  margin-bottom: 36rpx;
}

.child-hint {
  text-align: center;
  font-size: 24rpx;
  color: #C09060;
  padding-top: 16rpx;
}

/* 步骤指示器 */
.steps {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-bottom: 48rpx;
}

.step {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: #F5E8DA;
  color: #B87A4A;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 500;
  transition: all 0.3s;
}

.step.active {
  background: #4A90D9;
  color: #fff;
}

.step.done {
  background: #4A90D9;
  color: #fff;
}

.step-line {
  width: 80rpx;
  height: 4rpx;
  background: #F5E8DA;
  margin: 0 8rpx;
  transition: all 0.3s;
}

.step-line.active {
  background: #4A90D9;
}

/* 引导框 */
.guide-box {
  background: #E8F5FC;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 32rpx;
}

.guide-text {
  font-size: 26rpx;
  color: #4A90D9;
  line-height: 1.5;
}

/* 搜索输入框 */
.search-input-wrapper {
  display: flex;
  align-items: center;
}

.search-icon {
  font-size: 32rpx;
  margin-right: 16rpx;
  color: #B87A4A;
}

/* 搜索结果 */
.search-results {
  margin-top: 32rpx;
}

.results-label {
  font-size: 26rpx;
  color: #8B5A3A;
  margin-bottom: 16rpx;
  display: block;
}

.elder-card {
  background: #FDF8F2;
  border-radius: 20rpx;
  padding: 24rpx;
  display: flex;
  align-items: center;
  margin-bottom: 16rpx;
}

.elder-card:active {
  background: #F5E8DA;
}

.elder-avatar {
  width: 72rpx;
  height: 72rpx;
  border-radius: 50%;
  background: linear-gradient(145deg, #4A90D9, #357ABD);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32rpx;
  font-weight: 600;
}

.elder-info {
  flex: 1;
  margin-left: 20rpx;
}

.elder-name {
  display: block;
  font-size: 30rpx;
  font-weight: 600;
  color: #333;
}

.elder-detail {
  display: block;
  font-size: 24rpx;
  color: #999;
  margin-top: 8rpx;
}

.arrow {
  font-size: 40rpx;
  color: #ccc;
}

/* 未找到提示 */
.no-result {
  text-align: center;
  padding: 40rpx;
  color: #C09060;
  font-size: 28rpx;
}

/* 返回按钮 */
.back-btn {
  font-size: 28rpx;
  color: #4A90D9;
  margin-bottom: 24rpx;
}

/* 老人详情卡片 */
.elder-detail-card {
  background: #F0F8FF;
  border-radius: 24rpx;
  padding: 40rpx;
  text-align: center;
  margin-bottom: 32rpx;
}

.elder-avatar-large {
  width: 120rpx;
  height: 120rpx;
  border-radius: 50%;
  background: linear-gradient(145deg, #4A90D9, #357ABD);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 52rpx;
  font-weight: 600;
  margin: 0 auto 24rpx;
}

.elder-name-large {
  display: block;
  font-size: 40rpx;
  font-weight: 600;
  color: #333;
  margin-bottom: 12rpx;
}

.elder-detail-large {
  display: block;
  font-size: 28rpx;
  color: #666;
  margin-bottom: 8rpx;
}

.id-card-info {
  display: flex;
  align-items: center;
  justify-content: center;
  margin-top: 24rpx;
  padding-top: 24rpx;
  border-top: 1px solid #E0E0E0;
}

.id-label {
  font-size: 26rpx;
  color: #888;
}

.id-value {
  font-size: 26rpx;
  color: #333;
  margin-left: 12rpx;
  font-family: monospace;
}

/* 老人标签 */
.elder-tag {
  background: #fff;
  border-radius: 20rpx;
  padding: 20rpx 24rpx;
  display: flex;
  align-items: center;
  margin-bottom: 24rpx;
  box-shadow: 0 4rpx 12rpx rgba(0, 0, 0, 0.06);
}

.elder-tag-avatar {
  width: 64rpx;
  height: 64rpx;
  border-radius: 50%;
  background: linear-gradient(145deg, #4A90D9, #357ABD);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 28rpx;
  font-weight: 600;
}

.elder-tag-info {
  flex: 1;
  margin-left: 16rpx;
}

.elder-tag-name {
  display: block;
  font-size: 28rpx;
  font-weight: 500;
  color: #333;
}

.elder-tag-detail {
  display: block;
  font-size: 22rpx;
  color: #999;
}

.close-btn {
  width: 48rpx;
  height: 48rpx;
  border-radius: 50%;
  background: #f5f5f5;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 36rpx;
  color: #999;
}

/* 警告框 */
.warning-box {
  background: #FFF8E6;
  border-radius: 16rpx;
  padding: 20rpx;
  margin-bottom: 32rpx;
}

.warning-text {
  font-size: 26rpx;
  color: #E8A74C;
  line-height: 1.5;
}

/* 输入提示 */
.input-tip {
  font-size: 22rpx;
  color: #999;
  margin-top: 8rpx;
  display: block;
}

/* 按钮加载状态 */
.login-btn.loading {
  opacity: 0.7;
}
</style>
