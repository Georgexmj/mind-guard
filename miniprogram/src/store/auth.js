// src/store/auth.js
import { defineStore } from 'pinia'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: null,
    token: null,
    isLoggedIn: false
  }),
  
  getters: {
    userName: (state) => {
      return state.user?.name || state.user?.full_name || '用户'
    },
    userPhone: (state) => {
      return state.user?.phone || ''
    },
    userRole: (state) => {
      return state.user?.role || 'elder'
    },
    isElder: (state) => {
      const role = state.user?.role
      return role === 'elder' || role === 'elderly'
    }
  },
  
  actions: {
    enforceElderRole(showToast = false) {
      if (this.user && !this.isElder) {
        if (showToast) {
          uni.showModal({
            title: '账号类型不支持',
            content: '微信小程序老人端仅支持老人账号登录',
            showCancel: false,
            confirmText: '我知道了'
          })
        }
        this.logout()
        return false
      }
      return true
    },
    
    init() {
      try {
        const token = uni.getStorageSync('token')
        const userStr = uni.getStorageSync('user')
        if (token && userStr) {
          this.token = token
          this.user = JSON.parse(userStr)
          this.isLoggedIn = true
          if (!this.enforceElderRole()) return
          const pages = getCurrentPages()
          if (pages.length === 0 || pages[pages.length - 1]?.route === 'pages/login/index') {
            uni.switchTab({ url: '/pages/index/index' })
          }
        }
      } catch (error) {
        console.error('auth init error', error)
      }
    },
    
    setAuth(user, token) {
      this.user = user
      this.token = token
      this.isLoggedIn = true
      try {
        uni.setStorageSync('token', token)
        uni.setStorageSync('user', JSON.stringify(user))
      } catch (error) {
        console.error('save auth storage failed', error)
      }
      return this.enforceElderRole(true)
    },
    
    updateUser(userData) {
      this.user = { ...this.user, ...userData }
      try {
        uni.setStorageSync('user', JSON.stringify(this.user))
      } catch (error) {
        console.error('update user storage failed', error)
      }
    },
    
    logout() {
      this.user = null
      this.token = null
      this.isLoggedIn = false
      try {
        uni.removeStorageSync('token')
        uni.removeStorageSync('user')
      } catch (error) {
        console.error('clear auth storage failed', error)
      }
      uni.reLaunch({ url: '/pages/login/index' })
    }
  }
})