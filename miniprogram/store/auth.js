import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isLoggedIn: false
  }),

  getters: {
    userName: (state) => state.user?.name || state.user?.full_name || '用户',
    userPhone: (state) => state.user?.phone || '',
    userRole: (state) => state.user?.role || 'elder'
  },

  actions: {
    /**
     * Initialize auth state from local storage on app launch
     */
    init() {
      try {
        const token = wx.getStorageSync('token')
        const userStr = wx.getStorageSync('user')
        if (token && userStr) {
          this.token = token
          this.user = JSON.parse(userStr)
          this.isLoggedIn = true
          // Navigate to home if we have valid auth
          const pages = getCurrentPages()
          if (pages.length === 0 || pages[pages.length - 1].route === 'pages/login/index') {
            uni.switchTab({ url: '/pages/index/index' })
          }
        } else {
          // Not logged in, redirect to login
          uni.reLaunch({ url: '/pages/login/index' })
        }
      } catch (e) {
        console.error('Auth init error:', e)
        uni.reLaunch({ url: '/pages/login/index' })
      }
    },

    /**
     * Set auth credentials after successful login
     */
    setAuth(user, token) {
      this.user = user
      this.token = token
      this.isLoggedIn = true
      try {
        wx.setStorageSync('token', token)
        wx.setStorageSync('user', JSON.stringify(user))
      } catch (e) {
        console.error('Failed to save auth to storage:', e)
      }
    },

    /**
     * Update user profile data
     */
    updateUser(userData) {
      this.user = { ...this.user, ...userData }
      try {
        wx.setStorageSync('user', JSON.stringify(this.user))
      } catch (e) {
        console.error('Failed to update user in storage:', e)
      }
    },

    /**
     * Logout and clear all stored credentials
     */
    logout() {
      this.user = null
      this.token = null
      this.isLoggedIn = false
      try {
        wx.removeStorageSync('token')
        wx.removeStorageSync('user')
      } catch (e) {
        console.error('Failed to clear storage on logout:', e)
      }
      uni.reLaunch({ url: '/pages/login/index' })
    }
  }
})
