import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isLoggedIn: false,
  }),

  getters: {
    userName: (state) => state.user?.name || state.user?.full_name || '用户',
    userPhone: (state) => state.user?.phone || '',
    userRole: (state) => state.user?.role || 'elder',
    isElder: (state) => {
      const role = state.user?.role
      return role === 'elder' || role === 'elderly'
    },
  },

  actions: {
    enforceElderRole(showToast = false) {
      if (this.user && !this.isElder) {
        if (showToast) {
          wx.showModal({
            title: '账号类型不支持',
            content:
              '微信小程序老人端仅支持“老人账号”登录，请使用 Web 管理端登录管理员或医生账号。',
            showCancel: false,
            confirmText: '我知道了',
          })
        }
        this.logout()
        return false
      }
      return true
    },

    init() {
      try {
        const token = wx.getStorageSync('token')
        const userStr = wx.getStorageSync('user')

        if (token && userStr) {
          this.token = token
          this.user = JSON.parse(userStr)
          this.isLoggedIn = true

          if (!this.enforceElderRole()) return

          const pages = getCurrentPages()
          if (pages.length === 0 || pages[pages.length - 1].route === 'pages/login/index') {
            uni.switchTab({ url: '/pages/index/index' })
          }
        } else {
          uni.reLaunch({ url: '/pages/login/index' })
        }
      } catch (error) {
        console.error('auth init error', error)
        uni.reLaunch({ url: '/pages/login/index' })
      }
    },

    setAuth(user, token) {
      this.user = user
      this.token = token
      this.isLoggedIn = true
      try {
        wx.setStorageSync('token', token)
        wx.setStorageSync('user', JSON.stringify(user))
      } catch (error) {
        console.error('save auth storage failed', error)
      }
      return this.enforceElderRole(true)
    },

    updateUser(userData) {
      this.user = { ...this.user, ...userData }
      try {
        wx.setStorageSync('user', JSON.stringify(this.user))
      } catch (error) {
        console.error('update user storage failed', error)
      }
    },

    logout() {
      this.user = null
      this.token = null
      this.isLoggedIn = false
      try {
        wx.removeStorageSync('token')
        wx.removeStorageSync('user')
      } catch (error) {
        console.error('clear auth storage failed', error)
      }
      uni.reLaunch({ url: '/pages/login/index' })
    },
  },
})
